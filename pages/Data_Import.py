import os
from threading import Lock
from typing import List
import pandas as pd
import streamlit as st
from widgets.session import app_config
from globals import VARS_INDEX_PATH
from src.eurostat import (
    cast_time_to_datetimeindex,
    fetch_dataset_and_metadata,
    fetch_table_of_contents,
    split_dimensions_and_attributes_from,
)
from src.utils import concat_keys_to_values
from widgets.console import show_console
from widgets.dataframe import (
    st_dataframe_with_index_and_rows_cols_count,
    filter_dataset_replacing_NA,
)
from widgets.download import download_dataframe_button


session = st.session_state


@st.experimental_singleton(show_spinner=False)
def eust_lock():
    """A shared lock amongst sessions to prevent concurrent dataset write."""
    # NOTE Because it can't be assessed from outside `eust` package if fetching
    # is coming from internet (and so writing a file) or internal cache.
    return Lock()


@st.experimental_memo(show_spinner=False)
def load_dataset(code: str) -> pd.DataFrame:
    with eust_lock():
        data, meta = fetch_dataset_and_metadata(code)
    dims, attrs = split_dimensions_and_attributes_from(meta, code)
    data = cast_time_to_datetimeindex(data)
    dims = concat_keys_to_values(dims.to_dict())
    data = data.rename(index=dims).sort_index()
    data = data.assign(flag=data.flag.map(attrs.to_dict()))
    # `flag` shown before `value` to make it more readable as filterable
    return data[["flag", "value"]]


def update_stash(code, indexes, flags):
    session.stash.update({code: {"indexes": indexes, "flags": flags}})


# NOTE Caching is managed manually, do not cache with streamlit
def load_codelist_reverse_index() -> pd.Series:
    return pd.read_pickle(VARS_INDEX_PATH)


# NOTE `persist` preserve caching also when page is left
@st.experimental_memo(show_spinner=False, persist="disk")
def load_table_of_contents() -> pd.Series:
    return fetch_table_of_contents()


@st.experimental_memo(show_spinner=False)
def build_toc_list(toc: pd.Series) -> List[str]:
    # ex: I_IUIF | Internet use: ...
    toc = toc.index + " | " + toc.values  # type: ignore
    return ["Scroll options or start typing"] + toc.to_list()


@st.experimental_memo(show_spinner=False)
def build_dimension_list(dimensions: pd.Series) -> List[str]:
    # ex: ei_bsco_m | Consumers ...
    return ["Scroll options or start typing"] + dimensions.index.to_list()


def update_variable_idx(variables: List[str]):
    session.selected_variable_idx = variables.index(session.selected_variable)
    # NOTE Because datasets list change, reset the selected idx
    session.selected_dataset_idx = 0


def update_dataset_idx(datasets: List[str]):
    session.selected_dataset_idx = datasets.index(session.selected_dataset)


def update_history_default_flags(dataset_code: str):
    session.history[dataset_code]["default_flag"] = session[
        f"{dataset_code}_selected_flags"
    ]


def update_history_default_indexes(dataset_code: str, name: str):
    session.history[dataset_code]["default_indexes"][name] = session[
        f"{dataset_code}_selected_indexes_{name}"
    ]


def import_dataset():
    try:
        with st.sidebar:
            with st.spinner(text="Fetching table of contents"):
                toc = load_table_of_contents()
    except Exception as e:
        st.sidebar.error(e)
        return

    try:
        with st.sidebar:
            with st.spinner(text="Fetching codelist"):
                codelist = load_codelist_reverse_index()
    except Exception as e:
        st.sidebar.error(e)
        return

    variables = build_dimension_list(codelist)
    st.sidebar.selectbox(
        label="Filter datasets by variable",
        options=variables,
        index=session.selected_variable_idx,
        key="selected_variable",
        on_change=update_variable_idx,
        args=(variables,),
    )
    # Get a toc subsets or the entire toc list
    dataset_codes = codelist.get(session.selected_variable, default=None)
    datasets = build_toc_list(
        toc.loc[toc.index.intersection(dataset_codes)] if dataset_codes else toc  # type: ignore
    )
    # List (filtered) datasets
    st.sidebar.selectbox(
        label="Choose a dataset",
        options=datasets,
        index=session.selected_dataset_idx,
        key="selected_dataset",
        on_change=update_dataset_idx,
        args=(datasets,),
    )

    dataset_code_title = session.selected_dataset
    if dataset_code_title != "Scroll options or start typing":
        dataset_code = dataset_code_title.split(" | ", maxsplit=1)[0]
        try:
            with st.sidebar:
                with st.spinner(text="Prepare filters"):
                    dataset = load_dataset(dataset_code)

                    # Create or reuse a filtering history for this code
                    if dataset_code not in session.history:
                        session.history[dataset_code] = dict()
                    history = session.history[dataset_code]

                    # Flags management
                    flags = dataset.flag.fillna("<NA>").unique().tolist()
                    if "default_flag" not in history:
                        history["default_flag"] = (
                            flags
                            if "selected_flags" not in history
                            else history["selected_flags"]
                        )

                    st.sidebar.subheader("Filter dataset")
                    history["selected_flags"] = st.sidebar.multiselect(
                        label="Select FLAG",
                        options=flags,
                        default=history["default_flag"],
                        key=f"{dataset_code}_selected_flags",
                        on_change=update_history_default_flags,
                        args=(dataset_code,),
                    )

                    # Indexes management
                    indexes = {n: dataset.index.levels[i].to_list() for i, n in enumerate(dataset.index.names)}  # type: ignore
                    if "time" in indexes:
                        indexes["time"] = (
                            min(indexes["time"]).year,
                            max(indexes["time"]).year,
                        )

                    if "default_indexes" not in history:
                        history["default_indexes"] = (
                            indexes
                            if "selected_indexes" not in history
                            else history["selected_indexes"]
                        )

                    if "selected_indexes" not in history:
                        # NOTE managed manually because `key` can be only a string and callback do not host returned value
                        history["selected_indexes"] = dict()
                    for name in dataset.index.names:
                        if name == "time":
                            m, M = indexes[name][0], indexes[name][1]
                            M = M if m < M else M + 1  # RangeError fix
                            history["selected_indexes"][name] = st.sidebar.slider(
                                label="Select TIME [min: 1 year]",
                                min_value=m,
                                max_value=M,
                                value=history["default_indexes"][name],
                                step=1,
                                key=f"{dataset_code}_selected_indexes_{name}",
                                on_change=update_history_default_indexes,
                                args=(
                                    dataset_code,
                                    name,
                                ),
                            )
                        else:
                            history["selected_indexes"][name] = st.sidebar.multiselect(
                                label=f"Select {name.upper()}",
                                options=indexes[name],
                                default=history["default_indexes"][name],
                                key=f"{dataset_code}_selected_indexes_{name}",
                                on_change=update_history_default_indexes,
                                args=(
                                    dataset_code,
                                    name,
                                ),
                            )

                    return dataset

        except (ValueError, AssertionError, NotImplementedError) as e:
            st.sidebar.error(e)

    return pd.DataFrame.from_dict(
        {
            "index": [],
            "columns": ["flag", "value"],
            "data": None,
            "index_names": ["geo", "time"],
            "column_names": [None],
        },
        orient="tight",
    )


def show_dataset(dataset):
    dataset_code_title = session.selected_dataset
    dataset_code = dataset_code_title.split(" | ", maxsplit=1)[0]

    if not dataset.empty:
        view = filter_dataset_replacing_NA(
            dataset,
            session.history[dataset_code]["selected_indexes"],
            session.history[dataset_code]["selected_flags"],
        )
    else:
        view = dataset

    view = st_dataframe_with_index_and_rows_cols_count(
        view, f"{dataset_code_title}", use_container_width=True
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.button(
            "Add to Stash",
            on_click=update_stash,
            args=(
                dataset_code,
                session.history[dataset_code]["selected_indexes"]
                if not dataset.empty
                else None,
                session.history[dataset_code]["selected_flags"]
                if not dataset.empty
                else None,
            ),
            disabled=view.empty,
        )
    with col2:
        download_dataframe_button(view)


def page_init():
    if "selected_variable_idx" not in session:
        session.selected_variable_idx = 0

    if "selected_dataset_idx" not in session:
        session.selected_dataset_idx = 0

    if "history" not in session:
        session.history = dict()


if __name__ == "__main__":
    app_config("Data Import")
    page_init()

    dataset = import_dataset()

    show_dataset(dataset)

    show_console()  # For debugging
