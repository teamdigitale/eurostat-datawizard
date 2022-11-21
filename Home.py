import os
from threading import Lock
import pandas as pd
import streamlit as st
from requests import ConnectionError, HTTPError
from datetime import datetime
import time
from globals import (
    INITIAL_SIDEBAR_STATE,
    LAYOUT,
    MENU_ITEMS,
    PAGE_ICON,
    VARS_INDEX_PATH,
)
from pages.Data_Import import load_table_of_contents
from src.eurostat import (
    eurostat_sdmx_request,
    fetch_dataset_codelist,
)


def page_config():
    st.set_page_config(
        page_title="Eurostat Data Wizard • Home",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )

    if "stash" not in st.session_state:
        st.session_state.stash = {}


@st.experimental_singleton(show_spinner=False)
def api_endpoint():
    return eurostat_sdmx_request()


@st.experimental_singleton(show_spinner=False)
def index_lock():
    """A shared lock amongst sessions to prevent concurrent index write."""
    return Lock()


def save_index_file():
    """Obtain codelist and in which dataset is used each."""
    datasets = load_table_of_contents().index.to_list()
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
            f"Unable to load: {datasets_not_loaded}. Refresh only if you find it useful. All the metadata succesfully received will be loaded from cache.",
            icon="⚠️",
        )
    else:
        status.success(
            f"All datasets were loaded.",
            icon="✅",
        )

    # Aggregate datasets dimension for a reverse index
    codelist = (
        codelist.assign(name=codelist.name.str.capitalize())
        .groupby(["dimension", "name"])["dataset"]
        .unique()
    )
    codelist = codelist[codelist.apply(len) > 0]
    codelist.index = codelist.index.to_flat_index().str.join(" | ")
    codelist.name = "datasets"
    codelist.index.name = "code"
    codelist.apply(lambda x: x.tolist()).to_pickle(VARS_INDEX_PATH)


def get_last_index_update() -> datetime | None:
    if os.path.exists(VARS_INDEX_PATH):
        return datetime.fromtimestamp(os.path.getmtime(VARS_INDEX_PATH))
    return None


def index_helper(message_widget):
    last_update = get_last_index_update()

    col1, col2 = st.sidebar.columns(2, gap="large")
    with col1:
        st.markdown(
            f"""Index @ {last_update.isoformat(sep=' ', timespec='seconds') if last_update else 'never created'}"""
        )
    with col2:
        if st.button("Refresh" if last_update else "Create"):
            with index_lock():
                message_widget.empty()
                save_index_file()
                st.experimental_rerun()
        else:
            message_widget.empty()


if __name__ == "__main__":
    page_config()

    with open("README.md", "r") as readme:
        app_description = "".join([next(readme) for _ in range(17)])
    app_description = app_description.replace("# Eurostat", "# 🇪🇺 Eurostat")
    app_description = app_description.replace(
        "You can play with a (resource limited) working version [here](https://eurostat-datawizard.streamlit.app).",
        "",
    )
    st.markdown(app_description)

    message = st.sidebar.empty()
    message.markdown("💤 A previous indexing is still running.")
    index_helper(message)
