import pandas as pd
import streamlit as st

from st_widgets.commons import app_config, load_stash, read_stash_from_history
from st_widgets.console import session_console
from st_widgets.dataframe import (
    empty_eurostat_dataframe,
    st_dataframe_with_index_and_rows_cols_count,
)
from st_widgets.download import download_dataframe_button
from st_widgets.stateful import stateful_data_editor

# from st_widgets.stateful import stateful_data_editor

app_config("Stash")


def show_stash():
    if "history" in st.session_state:
        history = st.session_state.history
        history_frame = (
            pd.Series(
                {
                    dataset_code: values["stash"]
                    for dataset_code, values in history.items()
                },
            )
            .to_frame("stash")
            .reset_index()
            .rename(columns={"index": "dataset"})
        )

        with st.sidebar:
            history_frame = stateful_data_editor(
                history_frame,
                disabled=["dataset"],
                use_container_width=True,
                key="_selected_history_dataset",
            )

        for dataset_code, is_stashed in (
            history_frame.set_index("dataset")["stash"].to_dict().items()
        ):
            history[dataset_code]["stash"] = is_stashed

        stash = read_stash_from_history(history)
        dataset = empty_eurostat_dataframe()

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
    show_stash()
    session_console()
