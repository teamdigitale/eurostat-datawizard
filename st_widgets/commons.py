from threading import Lock

import pandas as pd
import streamlit as st

from datawizard.data import (
    append_code_descriptions,
    cast_time_to_datetimeindex,
    fetch_dataset_and_metadata,
)
from globals import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON
from st_widgets.dataframe import empty_eurostat_dataframe, filter_dataset_replacing_NA


@st.cache_resource
def global_download_lock():
    """Lock any further execution of downloading."""
    return Lock()


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


@st.cache_data()
def load_dataset(code: str) -> pd.DataFrame:
    # Return desiderd dataset by code in `long-format` (time as index)
    with global_download_lock():
        data, meta = fetch_dataset_and_metadata(code)
    data = cast_time_to_datetimeindex(data)
    data = append_code_descriptions(data, meta)
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
            df = load_dataset(code)
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
