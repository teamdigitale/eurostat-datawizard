import logging

import pandas as pd
import streamlit as st

from datawizard.data import (
    fetch_table_of_contents,
    get_cached_session,
    fetch_metabase,
    fetch_codelist,
    parse_codelist,
    metabase2datasets,
)
from st_widgets.commons import (
    app_config,
    get_logger,
    global_download_lock,
    load_dataset,
)
from st_widgets.console import session_console
from st_widgets.stateful.multiselect import stateful_multiselect
from st_widgets.stateful.selectbox import stateful_selectbox
from st_widgets.stateful.slider import stateful_slider

logging = get_logger(__name__)
session = st.session_state
app_config("Data Import")


def reset_user_selections():
    # NOTE Because datasets list change, reset the selected idx
    if "_selected_dataset_options" in session:
        session.pop("_selected_dataset_options")
    if "_selected_dataset_index" in session:
        session.pop("_selected_dataset_index")
    # NOTE Override "Filter datasets by (map) selection"
    if "_selected_map_selection" in session:
        session["_selected_map_selection"] = False


@st.cache_data()
def load_toc() -> pd.Series | None:
    # Return a series with datasets code as index and descriptions as values.
    # ex: key: EI_BSCO_M  - value: Consumers ...
    try:
        with st.sidebar:
            with st.spinner(text="Fetching table of contents"):
                with global_download_lock():
                    toc = fetch_table_of_contents()
                toc = toc["title"]
                return toc
    except Exception as e:
        st.sidebar.error(e)


@st.cache_data()
def load_dimension2dataset() -> pd.DataFrame:
    # Return an index of code + dimension and a list of datasets using them
    req = get_cached_session()
    metabase = fetch_metabase(req)
    codelist = parse_codelist(fetch_codelist(req))
    return metabase2datasets(metabase, codelist)


def build_multiselect_with_selectall_button(options, key: str, label: str):
    container = st.container()

    if st.button(
        "Select all",
        key=f"{key}_all",
    ):
        del session[f"{key}_default"]
        st.experimental_rerun()

    with container:
        return stateful_multiselect(
            label=f"{label} ({len(session[key]) if key in session else len(options)}/{len(options)})",
            options=options,
            default=options,
            key=key,
        )


def save_datasets_to_stash():
    toc = load_toc()

    # Datasets search criteria
    if toc is not None:
        with st.sidebar:
            tab1, tab2 = st.tabs(["Select a dataset", "Filter by dimension"])

            with tab1:
                dataset_code = stateful_selectbox(
                    label="Choose a dataset",
                    options=toc.index,
                    format_func=lambda i: i + " | " + toc.loc[i],
                    key="_selected_dataset",
                )
                logging.info(f"Selectbox selection: {dataset_code}")

                # Create or reuse a filtering history for this code
                if dataset_code not in session["history"]:
                    session["history"][dataset_code] = dict()
                history = session["history"][dataset_code]

                history["stash"] = tab1.checkbox(
                    "Save into Stash",
                    value=history["stash"] if "stash" in history else False,
                )

            with tab2:
                # with st.spinner(text="Downloading metadata"):
                tab2.markdown(
                    """ 🚧 Work in progress 🚧  
                    Select only dimensions of interest to filter the dataset list in the previous tab"""
                )
                tab2.data_editor(load_dimension2dataset().reset_index())

        # Dataset filtering criteria
        if dataset_code is not None:
            dataset = load_dataset(dataset_code)

            st.subheader(
                f"Variable selection: {dataset_code + ' | ' + toc.loc[dataset_code]}"
            )

            # Flags filtering handles
            flags = dataset.flag.fillna("<NA>").unique().tolist()
            history["flags"] = build_multiselect_with_selectall_button(
                flags, key=f"_{dataset_code}.flags", label="Select FLAG"
            )

            # Indexes filtering handles (all the available dimensions)
            indexes = {n: dataset.index.levels[i].to_list() for i, n in enumerate(dataset.index.names)}  # type: ignore
            if "time" in indexes:
                indexes["time"] = [
                    min(indexes["time"]).year,
                    max(indexes["time"]).year,
                ]

            if "indexes" not in history:
                history["indexes"] = dict()

            for name in dataset.index.names:
                if name == "time":
                    m, M = indexes["time"][0], indexes["time"][1]
                    M = M if m < M else M + 1  # RangeError fix
                    history["indexes"]["time"] = stateful_slider(
                        label="Select TIME [min: 1 year]",
                        min_value=m,
                        max_value=M,
                        value=(m, M),
                        key=f"_{dataset_code}.indexes.time",
                    )
                else:
                    history["indexes"][name] = build_multiselect_with_selectall_button(
                        indexes[name],
                        key=f"_{dataset_code}.indexes.{name}",
                        label=f"Select {name.upper()}",
                    )


def change_font_size():
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


if __name__ == "__main__":
    change_font_size()
    save_datasets_to_stash()
    session_console()
