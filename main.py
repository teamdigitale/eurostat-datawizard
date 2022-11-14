import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
from src.eurostat import (
    fetch_dataset_and_metadata,
    cast_time_to_datetimeindex,
    split_dimensions_and_attributes_from,
    filter_dataset,
)
from threading import Lock


@st.experimental_singleton(show_spinner=False)
def global_lock():
    return Lock()


@st.experimental_memo(show_spinner=False)
def load_dataset(code: str) -> pd.DataFrame:
    with global_lock():  # Prevent a possible concurrent write
        data, meta = fetch_dataset_and_metadata(code)
    dims, attrs = split_dimensions_and_attributes_from(meta, code)
    data = cast_time_to_datetimeindex(data)
    data = data.rename(index=dims.to_dict()).sort_index()
    data = data.assign(flag=data.flag.map(attrs.to_dict()))
    # `flag` shown before `value` to make it more readable as filterable
    return data[["flag", "value"]]


# `max_entries=1` because likely just the last call will be the reused one
@st.experimental_memo(show_spinner=False, max_entries=1)
def load_stash(stash: dict) -> pd.DataFrame:
    data = pd.DataFrame()
    common_cols = ["unit", "geo", "time", "flag", "value"]
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
        df = df.reset_index()
        df = (
            pd.concat(
                [
                    df[["dataset"]],
                    df[df.columns.difference(["dataset"] + common_cols)].agg(
                        " - ".join, axis=1
                    ),
                    df[common_cols],
                ],
                axis=1,
            )
            .rename(columns={0: "variable"})
            .set_index(["dataset", "variable"] + common_cols[:-2])
        )
        # Append previous loop datasets
        data = pd.concat([data, df])
    return data


def update_stash(code, indexes, flags):
    st.session_state.stash.update({code: {"indexes": indexes, "flags": flags}})


def clear_stash():
    st.session_state.stash = {}


def app_config():
    st.set_page_config(
        page_title="Eurostat Data Wizard",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": "Copyright (c) 2022 Presidenza del Consiglio dei Ministri",
        },
    )

    if "stash" not in st.session_state:
        st.session_state.stash = {}


def patch_streamlit_session_state():
    # Reset filter widget was needed to prevent the following to be raised:
    # `Exception in thread ScriptRunner.scriptThread:`
    # [...]
    # `streamlit.errors.StreamlitAPIException: Every Multiselect default value must exist in options`
    for k in st.session_state:
        if k.startswith("_"):
            del st.session_state[k]


def import_dataset():
    st.sidebar.header("Eurostat Data Wizard")
    st.sidebar.subheader("Import a dataset")
    dataset_code = st.sidebar.text_input(
        label="Online data code", placeholder="EI_BSCO_M"
    )

    dataset = pd.DataFrame()
    indexes = dict()
    flags = list()

    if dataset_code != "":
        dataset_code = dataset_code.lower()
        try:
            with st.sidebar:
                with st.spinner(text="Fetching data"):
                    dataset = load_dataset(dataset_code)
        except (ValueError, AssertionError, NotImplementedError) as e:
            st.sidebar.error(e)

    if not dataset.empty:
        st.sidebar.subheader("Filter dataset")

        flags = dataset.flag.unique().tolist()
        flags = st.sidebar.multiselect(
            "Select FLAG",
            flags,
            flags,
            key="_flags",  # Required by `patch_session_state`
        )

        indexes = dict()
        for i, name in enumerate(dataset.index.names):
            indexes[name] = dataset.index.levels[i].to_list()  # type: ignore
            if name == "time":
                m, M = min(indexes[name]).year, max(indexes[name]).year
                indexes[name] = st.sidebar.slider(
                    f"Select TIME [min: 1 year]",
                    m,
                    M,
                    (m, M),
                    1,
                    key=f"_indexes_{name}",  # Required by `patch_session_state`
                )
            else:
                indexes[name] = st.sidebar.multiselect(
                    f"Select {name.upper()}",
                    indexes[name],
                    indexes[name],
                    key=f"_indexes_{name}",  # Required by `patch_session_state`
                )

        patch_streamlit_session_state()

        dataset = filter_dataset(dataset, indexes, flags)
    return dataset, dataset_code, indexes, flags


def show_dataset(dataset, dataset_code, indexes, flags):
    st.subheader("Current dataset")
    # Dataset is shown with `.reset_index` because MultiIndex are not rendered properly
    view = dataset if dataset.empty else dataset.reset_index()
    st.dataframe(view, use_container_width=True)
    st.write("{} rows x {} columns".format(*view.shape))

    st.button(
        "Stash",
        on_click=update_stash,
        args=(dataset_code, indexes, flags),
        disabled=dataset.empty,
    )


def show_stash():
    st.subheader("Stashed datasets")

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
            now = datetime.now().isoformat(timespec="seconds")
            with BytesIO() as buffer:
                # Data downloaded is the `view` to be consistent with what user sees
                view.to_csv(buffer, index=False, compression={"method": "gzip"})
                st.download_button(
                    "Download",
                    buffer.getvalue(),
                    file_name=f"EurostatDataWizard_{now}.csv.gz",
                    mime="application/gzip",
                    disabled=view.empty,
                )


def show_console():
    with st.expander("Session console"):
        st.write(st.session_state)


if __name__ == "__main__":
    app_config()

    dataset, dataset_code, indexes, flags = import_dataset()

    st.header("Data viewer")
    show_dataset(dataset, dataset_code, indexes, flags)
    show_stash()

    # show_console()  # For debugging
