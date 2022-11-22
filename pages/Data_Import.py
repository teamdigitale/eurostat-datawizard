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
    filter_dataset,
    split_dimensions_and_attributes_from,
)
from src.utils import concat_keys_to_values
from widgets.console import show_console
from widgets.dataframe import st_dataframe_with_index_and_rows_cols_count
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


def patch_streamlit_session_state():
    # Reset filter widget was needed to prevent the following to be raised:
    # `Exception in thread ScriptRunner.scriptThread:`
    # [...]
    # `streamlit.errors.StreamlitAPIException: Every Multiselect default value must exist in options`
    for k in session:
        if k.startswith("_"):
            del session[k]


# NOTE Caching is managed manually, do not cache with streamlit
def load_codelist_reverse_index() -> pd.Series | None:
    if os.path.exists(VARS_INDEX_PATH):
        return pd.read_pickle(VARS_INDEX_PATH)
    return None


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


def update_dataset_idx(datasets: List[str]):
    session.selected_dataset_idx = datasets.index(session.selected_dataset)


def import_dataset():
    toc = session.toc
    codelist = session.codelist

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
        toc.loc[toc.index.intersection(dataset_codes)] if dataset_codes else toc
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

    indexes = dict()
    flags = list()

    dataset_code_title = session.selected_dataset
    if dataset_code_title != "Scroll options or start typing":
        try:
            with st.sidebar:
                with st.spinner(text="Prepare filters"):
                    session.dataset = load_dataset(
                        dataset_code_title.split(" | ", maxsplit=1)[0]
                    )
        except (ValueError, AssertionError, NotImplementedError) as e:
            st.sidebar.error(e)

    if not session.dataset.empty:
        st.sidebar.subheader("Filter dataset")

        st.sidebar.multiselect(
            label="Select FLAG",
            options=session.dataset.flag.unique().tolist(),
            default=session.dataset.flag.unique().tolist(),
            key="selected_flags",
        )

        indexes = dict()
        for i, name in enumerate(session.dataset.index.names):
            indexes[name] = session.dataset.index.levels[i].to_list()  # type: ignore
            if name == "time":
                m, M = min(indexes[name]).year, max(indexes[name]).year
                M = M if m < M else M + 1  # RangeError fix
                indexes[name] = st.sidebar.slider(
                    "Select TIME [min: 1 year]",
                    m,
                    M,
                    (m, M),
                    1,
                    key=f"_indexes_{name}",  # Required by `patch_session_state`
                )
            else:
                indexes[name] = st.sidebar.multiselect(
                    f"Select {name.upper()}",
                    indexes[name],
                    indexes[name],
                    key=f"_indexes_{name}",  # Required by `patch_session_state`
                )

        # patch_streamlit_session_state()

        session.dataset = filter_dataset(
            session.dataset, indexes, session.selected_flags
        )
    return session.dataset, dataset_code_title, indexes, session.selected_flags


def show_dataset(dataset, dataset_code_title, indexes, flags):
    view = st_dataframe_with_index_and_rows_cols_count(
        dataset, f"{dataset_code_title}", use_container_width=True
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.button(
            "Add to Stash",
            on_click=update_stash,
            args=(dataset_code_title.split(" | ", maxsplit=1)[0], indexes, flags),
            disabled=dataset.empty,
        )
    with col2:
        download_dataframe_button(view)


def page_init():
    if "toc" not in session:
        try:
            with st.sidebar:
                with st.spinner(text="Fetching table of contents"):
                    session.toc = load_table_of_contents()
        except Exception as e:
            st.sidebar.error(e)

    if "codelist" not in session:
        try:
            with st.sidebar:
                with st.spinner(text="Fetching codelist"):
                    session.codelist = load_codelist_reverse_index()
        except Exception as e:
            st.sidebar.error(e)

    if "selected_variable_idx" not in session:
        session.selected_variable_idx = 0

    if "selected_dataset_idx" not in session:
        session.selected_dataset_idx = 0

    if "dataset" not in session:
        session.dataset = pd.DataFrame.from_dict(
            {
                "index": [],
                "columns": ["flag", "value"],
                "data": None,
                "index_names": ["geo", "time"],
                "column_names": [None],
            },
            orient="tight",
        )


if __name__ == "__main__":
    app_config("Data Import")
    page_init()

    dataset, dataset_code_title, indexes, flags = import_dataset()

    show_dataset(dataset, dataset_code_title, indexes, flags)

    show_console()  # For debugging
