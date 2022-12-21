from importlib import import_module

import pandas as pd
import streamlit as st

from widgets.console import session_console
from widgets.dataframe import (
    empty_eurostat_dataframe,
    filter_dataset_replacing_NA,
    st_dataframe_with_index_and_rows_cols_count,
)
from widgets.download import download_dataframe_button
from widgets.commons import app_config


@st.experimental_memo(show_spinner=False)
def load_stash(stash: dict) -> pd.DataFrame:
    data = empty_eurostat_dataframe()
    for code, properties in stash.items():
        indexes, flags, stash = (
            properties["indexes"],
            properties["flags"],
            properties["stash"],
        )
        if stash:
            df = import_module("pages.2_🗄️_Data").load_dataset(code)
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

        remove_code = st.sidebar.selectbox(
            "Remove a dataset",
            ["-"] + [code for code, p in stash.items() if p["stash"]],
        )
        if remove_code != "-":
            stash.pop(remove_code)
            st.experimental_rerun()

        try:
            with st.spinner(text="Fetching data"):
                dataset = load_stash(stash)
        except ValueError as ve:
            st.error(ve)

        tab1, tab2 = st.tabs(["Long-format", "Wide-format"])
        with tab1:
            view = st_dataframe_with_index_and_rows_cols_count(
                dataset, use_container_width=True
            )

            download_dataframe_button(view)
        with tab2:
            n_flags, n_values = 0, 0

            if not dataset.empty:
                dataset = dataset.unstack(dataset.index.names.difference(["geo", "time"]))  # type: ignore
                n_flags, n_values = dataset["flag"].shape[1], dataset["value"].shape[1]
                levels = list(range(len(dataset.columns.names)))
                dataset = dataset.reorder_levels(
                    levels[1:] + levels[:1], axis=1  # type: ignore
                ).sort_index(
                    axis=1
                )  # Move flag, value as last index

            view = st_dataframe_with_index_and_rows_cols_count(
                dataset, show_shape=False, use_container_width=True  # type: ignore
            )
            st.write(
                "{} rows x {} columns ({} flags, {} values)".format(
                    *view.shape, n_flags, n_values
                )
            )
    else:
        st.warning("No stash found. Select some data to plot.")


if __name__ == "__main__":
    app_config("Stash")

    show_stash()

    session_console()
