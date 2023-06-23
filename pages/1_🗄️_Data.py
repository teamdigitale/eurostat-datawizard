from threading import Lock
from typing import List, Mapping

import pandas as pd
import streamlit as st

from datawizard.data import fetch_table_of_contents
from st_widgets.commons import app_config, global_download_lock, load_dataset
from st_widgets.console import session_console
from st_widgets.dataframe import empty_eurostat_dataframe
from st_widgets.stateful.multiselect import stateful_multiselect
from st_widgets.stateful.selectbox import stateful_selectbox
from st_widgets.stateful.slider import stateful_slider

session = st.session_state


@st.experimental_memo()
def fetch_toc() -> pd.Series:
    # Return a series with datasets code as index and descriptions as values.
    # ex: key:EI_BSCO_M  - value: Consumers ...
    with global_download_lock():
        toc = fetch_table_of_contents()
    toc = toc["title"].squeeze()
    return toc  # type: ignore


@st.experimental_memo()
def build_toc_list(toc: pd.Series) -> List[str]:
    # Return a list concatenating dataset code and description.
    # ex: EI_BSCO_M | Consumers ...
    toc = toc.index + " | " + toc.values  # type: ignore
    return ["Scroll options or start typing"] + toc.to_list()


def reset_user_selections():
    # NOTE Because datasets list change, reset the selected idx
    if "_selected_dataset_options" in session:
        session.pop("_selected_dataset_options")
    if "_selected_dataset_index" in session:
        session.pop("_selected_dataset_index")
    # NOTE Override "Filter datasets by (map) selection"
    if "_selected_map_selection" in session:
        session["_selected_map_selection"] = False


def load_dataset_codes_and_descriptions():
    try:
        with st.sidebar:
            with st.spinner(text="Fetching table of contents"):
                return fetch_toc()
    except Exception as e:
        st.sidebar.error(e)


def save_datasets_to_stash():
    toc = load_dataset_codes_and_descriptions()

    with st.sidebar:
        datasets = build_toc_list(toc)  # type: ignore
        dataset_code_title = stateful_selectbox(
            label="Choose a dataset",
            options=range(len(datasets)),
            format_func=lambda i: datasets[i],
            key="_selected_dataset",
        )
        dataset_code_title = datasets[dataset_code_title]  # type: ignore

    if dataset_code_title and dataset_code_title != "Scroll options or start typing":
        dataset_code = dataset_code_title.split(" | ", maxsplit=1)[0]
        try:
            with st.spinner(text="Downloading data"):
                dataset = load_dataset(dataset_code)

                # Create or reuse a filtering history for this code
                if dataset_code not in session["history"]:
                    session["history"][dataset_code] = dict()
                history = session["history"][dataset_code]

                history["stash"] = st.sidebar.checkbox(
                    "Save into Stash",
                    value=history["stash"] if "stash" in history else False,
                )

                st.subheader(f"Variable selection: {dataset_code_title}")

                # Flags management
                flags = dataset.flag.fillna("<NA>").unique().tolist()

                flags_container = st.container()

                if st.button(
                    "Select all",
                    key=f"_{dataset_code}.flags_all",
                ):
                    del session[f"_{dataset_code}.flags_default"]
                    st.experimental_rerun()

                with flags_container:
                    history["flags"] = stateful_multiselect(
                        label="Select FLAG",
                        options=flags,
                        default=flags,
                        key=f"_{dataset_code}.flags",
                    )

                # Indexes management
                indexes = {n: dataset.index.levels[i].to_list() for i, n in enumerate(dataset.index.names)}  # type: ignore
                if "time" in indexes:
                    indexes["time"] = [
                        min(indexes["time"]).year,
                        max(indexes["time"]).year,
                    ]

                if "indexes" not in history:
                    history["indexes"] = dict()

                for name in dataset.index.names:
                    index_container = st.container()

                    if st.button(
                        "Select all",
                        key=f"_{dataset_code}.indexes.{name}_all",
                    ):
                        del session[f"_{dataset_code}.indexes.{name}_default"]
                        st.experimental_rerun()

                    if name == "time":
                        with index_container:
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
                        with index_container:
                            history["indexes"][name] = stateful_multiselect(
                                label=f"Select {name.upper()}",
                                options=indexes[name],
                                default=indexes[name],
                                key=f"_{dataset_code}.indexes.{name}",
                            )

        except (ValueError, AssertionError, NotImplementedError) as e:
            st.error(e)


def page_init():
    if "history" not in session:
        session["history"] = dict()


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
    app_config("Data Import")
    page_init()
    change_font_size()
    save_datasets_to_stash()
    session_console()
