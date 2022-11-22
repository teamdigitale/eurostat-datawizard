import streamlit as st
import pandas as pd
from widgets.dataframe import st_dataframe_with_index_and_rows_cols_count
from widgets.download import download_dataframe_button
from widgets.session import app_config
from widgets.console import show_console
from pages.Data_Import import load_dataset, filter_dataset


@st.experimental_memo(show_spinner=False)
def load_stash(stash: dict) -> pd.DataFrame:
    data = pd.DataFrame()
    common_cols = ["geo", "time", "flag", "value"]
    for code, filters in stash.items():
        indexes, flags = filters["indexes"], filters["flags"]
        df = load_dataset(code)
        df = filter_dataset(df, indexes, flags)
        # Append dataset code to data as first level
        df = pd.concat(
            {code: df},
            names=["dataset"],
        )
        # Merge dataset-specific indexes into one field
        # NOTE `unit` columns is not always presents
        df = df.reset_index()
        df = (
            pd.concat(
                [
                    df[["dataset"]],
                    df[df.columns.difference(["dataset"] + common_cols)].agg(
                        " • ".join, axis=1
                    ),
                    df[df.columns.intersection(common_cols)],
                ],
                axis=1,
            )
            .rename(columns={0: "variable"})
            .set_index(["dataset", "variable"] + common_cols[:-2])
        )
        # Append previous loop datasets
        data = pd.concat([data, df])
    return data


def clear_stash():
    st.session_state.stash = {}


def show_stash():
    dataset = pd.DataFrame()
    try:
        with st.spinner(text="Fetching data"):
            if st.session_state.stash.keys():
                dataset = load_stash(st.session_state.stash)
    except ValueError as ve:
        st.error(ve)

    view = st_dataframe_with_index_and_rows_cols_count(
        dataset, "Stash", use_container_width=True
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.button("Clear", on_click=clear_stash, disabled=dataset.empty)
    with col2:
        download_dataframe_button(view)


if __name__ == "__main__":
    app_config("Stash")

    show_stash()

    show_console()  # For debugging
