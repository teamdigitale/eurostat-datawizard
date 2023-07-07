import logging
import os
from threading import Lock

import pandas as pd
import streamlit as st

from datawizard.data import (
    append_code_descriptions,
    cast_time_to_datetimeindex,
    fetch_codelist,
    fetch_and_preprocess_dataset,
    fetch_metabase,
    get_cached_session,
    metabase2datasets,
    parse_codelist,
)
from datawizard.definitions import LOGGING_FORMAT
from globals import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON
from st_widgets.dataframe import empty_eurostat_dataframe, filter_dataset_replacing_NA


def app_config(title: str):
    """Setup page & session state. Must be the first script instruction called."""
    st.set_page_config(
        page_title=f"Eurostat Data Wizard • {title}",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )

    if "history" not in st.session_state:
        st.session_state["history"] = dict()


def get_logger(name: str):
    # logging.DEBUG level is polluted by streamlit events
    log_level = logging.INFO if os.environ["ENV"] == "dev" else logging.WARNING

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Create a console handler and set its log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Create a formatter and add it to the console handler
    formatter = logging.Formatter(LOGGING_FORMAT)
    console_handler.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(console_handler)

    return logger


@st.cache_resource
def global_download_lock():
    """Lock any further execution of downloading."""
    return Lock()


@st.cache_data()
def load_metabase2datasets() -> pd.DataFrame:
    # Return an index of code + dimension and a list of datasets using them
    req = get_cached_session()
    metabase = fetch_metabase(req)
    codelist = parse_codelist(fetch_codelist(req))
    return metabase2datasets(metabase, codelist)


@st.cache_data()
def load_dimensions_and_codes(metabase2datasets: pd.DataFrame) -> pd.Series:
    # Arrage metabase as an index of dimensions + descriptions
    codes_dims = (
        metabase2datasets.reset_index()[
            ["dimension", "code", "dimension_label", "code_label"]
        ]
        .set_index(["dimension", "code"])
        .sort_index()
    )
    codes_dims = codes_dims["dimension_label"].str.cat(
        codes_dims["code_label"], sep=": "
    )
    codes_dims.name = "description"
    return codes_dims


@st.cache_data()
def load_codelist() -> pd.DataFrame:
    req = get_cached_session()
    codelist = parse_codelist(fetch_codelist(req))
    return codelist


@st.cache_data()
def load_dataset(code: str, codelist: pd.DataFrame) -> pd.DataFrame:
    # Return desiderd dataset by code in `long-format` (time as index)
    with global_download_lock():
        data = fetch_and_preprocess_dataset(code)
    data = cast_time_to_datetimeindex(data)
    data = append_code_descriptions(data, codelist)
    # `flag` shown before `value` to be near others filter key
    return data[["flag", "value"]]


@st.cache_data()
def load_stash(stash: dict) -> pd.DataFrame:
    data = empty_eurostat_dataframe()
    for code, properties in stash.items():
        indexes, flags, stash = (
            properties["indexes"],
            properties["flags"],
            properties["stash"],
        )
        if stash:
            codelist = load_codelist()
            df = load_dataset(code, codelist)
            df = filter_dataset_replacing_NA(
                df,
                indexes,
                flags,
            )
            # Append dataset code to data as first level
            df = pd.concat(
                {code: df},
                names=["dataset"],
            )
            # Merging with index resetted to preserve unique columns
            data = pd.concat([data.reset_index(), df.reset_index()])
            # Restore a global index based on current stash
            data = data.set_index(data.columns.difference(["flag", "value"]).to_list())
    return data


def read_stash_from_history(history):
    # Filter stash dataset only
    return {k: v for k, v in history.items() if v["stash"]}


def reduce_multiselect_font_size():
    st.markdown(
        """
    <style>
        .stMultiSelect [data-baseweb=select] span{
            max-width: 500px;
            font-size: 0.8rem;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
