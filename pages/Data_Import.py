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
    st.session_state.stash.update({code: {"indexes": indexes, "flags": flags}})


def patch_streamlit_session_state():
    # Reset filter widget was needed to prevent the following to be raised:
    # `Exception in thread ScriptRunner.scriptThread:`
    # [...]
    # `streamlit.errors.StreamlitAPIException: Every Multiselect default value must exist in options`
    for k in st.session_state:
        if k.startswith("_"):
            del st.session_state[k]


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
    st.session_state.selected_variable_idx = variables.index(
        st.session_state.selected_variable
    )


def update_dataset_idx(datasets: List[str]):
    st.session_state.selected_dataset_idx = datasets.index(
        st.session_state.selected_dataset
    )


def import_dataset():
    toc = st.session_state.toc
    codelist = st.session_state.codelist

    variables = build_dimension_list(codelist)
    st.sidebar.selectbox(
        label="Filter datasets by variable",
        options=variables,
        index=st.session_state.selected_variable_idx,
        key="selected_variable",
        on_change=update_variable_idx,
        args=(variables,),
    )
    # Get a toc subsets or the entire toc list
    dataset_codes = codelist.get(st.session_state.selected_variable, default=None)
    datasets = build_toc_list(
        toc.loc[toc.index.intersection(dataset_codes)] if dataset_codes else toc
    )
    # List (filtered) datasets
    st.sidebar.selectbox(
        label="Choose a dataset",
        options=datasets,
        index=st.session_state.selected_dataset_idx,
        key="selected_dataset",
        on_change=update_dataset_idx,
        args=(datasets,),
    )

    dataset = pd.DataFrame()
    indexes = dict()
    flags = list()

    dataset_code_title = st.session_state.selected_dataset
    if dataset_code_title != "Scroll options or start typing":
        try:
            with st.sidebar:
                with st.spinner(text="Prepare filters"):
                    dataset = load_dataset(
                        dataset_code_title.split(" | ", maxsplit=1)[0]
                    )
        except (ValueError, AssertionError, NotImplementedError) as e:
            st.sidebar.error(e)

    if not dataset.empty:
        st.sidebar.subheader("Filter dataset")

        flags = dataset.flag.unique().tolist()
        flags = st.sidebar.multiselect(
            "Select FLAG",
            flags,
            flags,
            key="_flags",  # Required by `patch_session_state`
        )

        indexes = dict()
        for i, name in enumerate(dataset.index.names):
            indexes[name] = dataset.index.levels[i].to_list()  # type: ignore
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

        patch_streamlit_session_state()

        dataset = filter_dataset(dataset, indexes, flags)
    return dataset, dataset_code_title, indexes, flags


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
    if "toc" not in st.session_state:
        try:
            with st.sidebar:
                with st.spinner(text="Fetching table of contents"):
                    st.session_state.toc = load_table_of_contents()
        except Exception as e:
            st.sidebar.error(e)

    if "codelist" not in st.session_state:
        try:
            with st.sidebar:
                with st.spinner(text="Fetching codelist"):
                    st.session_state.codelist = load_codelist_reverse_index()
        except Exception as e:
            st.sidebar.error(e)

    if "selected_variable_idx" not in st.session_state:
        st.session_state.selected_variable_idx = 0

    if "selected_dataset_idx" not in st.session_state:
        st.session_state.selected_dataset_idx = 0


if __name__ == "__main__":
    app_config("Data Import")
    page_init()

    dataset, dataset_code_title, indexes, flags = import_dataset()

    show_dataset(dataset, dataset_code_title, indexes, flags)

    show_console()  # For debugging
