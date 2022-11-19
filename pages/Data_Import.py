import time
from threading import Lock
from typing import List, Mapping

import pandas as pd
import streamlit as st
from requests import ConnectionError, HTTPError

from globals import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON
from src.eurostat import (
    eurostat_sdmx_request,
    cast_time_to_datetimeindex,
    fetch_dataset_and_metadata,
    fetch_dataset_codelist,
    fetch_table_of_contents,
    filter_dataset,
    split_dimensions_and_attributes_from,
)
from widgets.console import show_console
from widgets.dataframe import st_dataframe_with_index_and_rows_cols_count
from widgets.download import download_dataframe_button


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
    """A shared lock amongst sessions to prevent concurrent write."""
    return Lock()


@st.experimental_memo(show_spinner=False)
def load_dataset(code: str) -> pd.DataFrame:
    with global_lock():
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


@st.experimental_singleton
def api_endpoint():
    return eurostat_sdmx_request()


# NOTE `persist` preserve caching also when page is left
@st.experimental_memo(show_spinner=False, persist="disk")
def load_codelist_reverse_index(datasets: List[str]) -> pd.Series:
    """Obtain codelist and in which dataset is used each."""
    req = api_endpoint()
    codelist = pd.DataFrame()
    current_message = st.sidebar.empty()
    progress_bar = st.sidebar.progress(0.0)
    progress_value = 0.0
    status = st.sidebar.empty()
    len_datasets = len(datasets)
    datasets_not_loaded = []
    for n, dataset in enumerate(datasets):
        current_message.text(f"Loading {dataset} ({n}/{len_datasets})")
        try:
            codes, cached = fetch_dataset_codelist(req, dataset)
            codes = codes.assign(dataset=dataset)
            codelist = pd.concat([codelist, codes])
            status.success(
                f"Loaded{' from cache' if cached else ' from Eurostat'}",
                icon="♻️" if cached else "✅",
            )
        except HTTPError as e:
            # NOTE Usually happens if a dataset was not found
            status.warning(e, icon="⚠️")
            datasets_not_loaded.append(dataset)
        except ConnectionError as e:
            # NOTE Usually happens when Eurostat reset connection
            status.warning(e, icon="⚠️")
            datasets_not_loaded.append(dataset)
            time.sleep(1)  # Cooldown before resume requests
        progress_value = n / len_datasets
        progress_bar.progress(progress_value)

    current_message.empty()
    progress_bar.empty()
    if len(datasets_not_loaded) > 0:
        status.warning(
            f"Unable to load: {datasets_not_loaded}. Retry only if it is mandatory.",
            icon="⚠️",
        )
    else:
        status.success(
            f"All datasets were loaded.",
            icon="✅",
        )
    # time.sleep(3)  # NOTE This would allow user to get a report but slows execution
    status.empty()

    # Aggregate datasets dimension for a reverse index
    codelist = (
        codelist.assign(name=codelist.name.str.capitalize())
        .groupby(["dimension", "name"])["dataset"]
        .unique()
    )
    codelist = codelist[codelist.apply(len) > 0]
    codelist.index = codelist.index.to_flat_index().str.join(" | ")
    codelist.name = "datasets"
    return codelist.apply(lambda x: x.tolist())


# NOTE `persist` preserve caching also when page is left
@st.experimental_memo(show_spinner=False, persist="disk")
def load_table_of_contents() -> pd.Series:
    return fetch_table_of_contents()


@st.experimental_memo(show_spinner=False)
def build_toc_list(toc: pd.Series, first_value: str) -> List[str]:
    toc = toc.index + " | " + toc.values  # type: ignore
    return [first_value] + toc.to_list()


@st.experimental_memo(show_spinner=False)
def build_dimension_list(dimensions: pd.Series, first_value: str) -> List[str]:
    return [first_value] + dimensions.index.to_list()


def import_dataset():
    dimension_code_name = (
        "Scroll options or start typing"  # ex: I_IUIF | Internet use: ...
    )
    dataset_code_title = (
        "Scroll options or start typing"  # ex: ei_bsco_m | Consumers ...
    )
    try:
        with st.sidebar:
            with st.spinner(text="Fetching datasets metadata"):
                toc = load_table_of_contents()
                dimensions = load_codelist_reverse_index(toc.index.to_list())
                dimension_code_name = st.sidebar.selectbox(
                    "Filter datasets by dimension",
                    build_dimension_list(dimensions, dimension_code_name),
                )
                # Get a toc subsets or the entire toc list
                dataset_codes = dimensions.get(dimension_code_name, default=None)
                dataset_codes_title = build_toc_list(toc.loc[toc.index.intersection(dataset_codes)] if dataset_codes else toc, dataset_code_title)  # type: ignore
                # List (filtered) datasets
                dataset_code_title = str(
                    st.sidebar.selectbox("Choose a dataset", dataset_codes_title)  # type: ignore
                ).split(" | ")[0]
    except Exception as e:
        st.sidebar.error(e)

    dataset = pd.DataFrame()
    indexes = dict()
    flags = list()

    if dataset_code_title != "Scroll options or start typing":
        try:
            with st.sidebar:
                with st.spinner(text="Fetching data"):
                    dataset = load_dataset(dataset_code_title)
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


def show_dataset(dataset, dataset_code, indexes, flags):
    st.subheader("Dataset")
    view = st_dataframe_with_index_and_rows_cols_count(
        dataset, use_container_width=True
    )

    with st.container():
        col1, col2 = st.columns(2, gap="small")
        with col1:
            st.button(
                "Add to Stash",
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
