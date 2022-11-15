import streamlit as st
import pandas as pd
from widgets.download import download_dataframe_button
from Home import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON
from widgets.console import show_console
from pages.Data_Import import load_dataset, filter_dataset

# `max_entries=1` because likely just the last call will be the reused one
@st.experimental_memo(show_spinner=False, max_entries=1)
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
                        " - ".join, axis=1
                    ),
                    df[df.columns.intersection(["unit"] + common_cols)],
                ],
                axis=1,
            )
            .rename(columns={0: "variable"})
            .set_index(
                ["dataset", "variable"]
                + df.columns.intersection(["unit"] + common_cols[:-2]).to_list()
            )
        )
        # Append previous loop datasets
        data = pd.concat([data, df])
    return data


def clear_stash():
    st.session_state.stash = {}


def show_stash():
    st.subheader("Datasets")

    dataset = pd.DataFrame()
    try:
        with st.spinner(text="Fetching data"):
            if st.session_state.stash.keys():
                dataset = load_stash(st.session_state.stash)
    except ValueError as ve:
        st.error(ve)

    # Dataset is shown with `.reset_index` because MultiIndex are not rendered properly
    view = dataset if dataset.empty else dataset.reset_index()
    st.dataframe(view, use_container_width=True)
    st.write("{} rows x {} columns".format(*dataset.shape))

    with st.container():
        col1, col2 = st.columns(2, gap="small")
        with col1:
            st.button("Clear", on_click=clear_stash, disabled=dataset.empty)
        with col2:
            download_dataframe_button(view)


def page_config():
    st.set_page_config(
        page_title="Eurostat Data Wizard • Stash",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )


if __name__ == "__main__":
    page_config()

    show_stash()

    show_console()  # For debugging
