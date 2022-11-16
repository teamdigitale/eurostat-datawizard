from threading import Lock
from typing import List

import pandas as pd
import streamlit as st

from Home import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON
from widgets.console import show_console
from widgets.dataframe import st_dataframe_with_index_and_rows_cols_count
from widgets.download import download_dataframe_button
from src.eurostat import (
    cast_time_to_datetimeindex,
    fetch_dataset_and_metadata,
    fetch_table_of_contents,
    filter_dataset,
    split_dimensions_and_attributes_from,
)


def page_config():
    st.set_page_config(
        page_title="Eurostat Data Wizard • Data Import",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )


@st.experimental_singleton(show_spinner=False)
def global_lock():
    return Lock()


@st.experimental_memo(show_spinner=False)
def load_toc() -> List[str]:
    toc = fetch_table_of_contents()
    toc = toc.values + " | " + toc.index  # type: ignore
    return toc.to_list()


@st.experimental_memo(show_spinner=False)
def load_dataset(code: str) -> pd.DataFrame:
    with global_lock():  # Prevent a possible concurrent write
        data, meta = fetch_dataset_and_metadata(code)
    dims, attrs = split_dimensions_and_attributes_from(meta, code)
    data = cast_time_to_datetimeindex(data)
    data = data.rename(index=dims.to_dict()).sort_index()
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


def import_dataset():

    dataset_code = "Scroll options or start typing"
    try:
        with st.sidebar:
            with st.spinner(text="Fetching datasets"):
                dataset_code = str(
                    st.selectbox("Choose a dataset", [dataset_code] + load_toc())
                ).split(" | ")[0]
    except Exception as e:
        st.sidebar.error(e)

    dataset = pd.DataFrame()
    indexes = dict()
    flags = list()

    if dataset_code != "Scroll options or start typing":
        dataset_code = dataset_code.lower()
        try:
            with st.sidebar:
                with st.spinner(text="Fetching data"):
                    dataset = load_dataset(dataset_code)
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
    return dataset, dataset_code, indexes, flags


def show_dataset(dataset, dataset_code, indexes, flags):
    st.subheader("Dataset")
    view = st_dataframe_with_index_and_rows_cols_count(
        dataset, use_container_width=True
    )

    with st.container():
        col1, col2 = st.columns(2, gap="small")
        with col1:
            st.button(
                "Stash",
                on_click=update_stash,
                args=(dataset_code, indexes, flags),
                disabled=dataset.empty,
            )
        with col2:
            download_dataframe_button(view)


if __name__ == "__main__":
    page_config()

    dataset, dataset_code, indexes, flags = import_dataset()

    show_dataset(dataset, dataset_code, indexes, flags)

    show_console()  # For debugging
