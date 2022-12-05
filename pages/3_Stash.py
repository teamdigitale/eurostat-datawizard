from importlib import import_module

import pandas as pd
import streamlit as st

from widgets.console import show_console
from widgets.dataframe import (
    empty_eurostat_dataframe,
    filter_dataset_replacing_NA,
    st_dataframe_with_index_and_rows_cols_count,
)
from widgets.download import download_dataframe_button
from widgets.selectbox import stateful_selectbox
from widgets.session import app_config


@st.experimental_memo(show_spinner=False)
def load_stash(stash: dict) -> pd.DataFrame:
    data = pd.DataFrame()
    for code, filters in stash.items():
        indexes, flags = filters["indexes"], filters["flags"]
        df = import_module("pages.2_Data").load_dataset(code)
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


def show_stash():
    if "history" in st.session_state:
        stash = st.session_state.history
        dataset = empty_eurostat_dataframe()

        try:
            with st.spinner(text="Fetching data"):
                dataset = load_stash(stash)
        except ValueError as ve:
            st.error(ve)

        view = st_dataframe_with_index_and_rows_cols_count(
            dataset, "Stash", use_container_width=True
        )

        remove_code = st.sidebar.selectbox(
            "Remove a dataset", ["-"] + list(stash.keys())
        )
        if remove_code != "-":
            stash.pop(remove_code)
            st.experimental_rerun()

        download_dataframe_button(view)
    else:
        st.warning("No stash found. Select some data to plot.")


if __name__ == "__main__":
    app_config("Stash")

    show_stash()

    show_console()  # For debugging
