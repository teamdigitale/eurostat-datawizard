import logging

import pandas as pd
import streamlit as st

from datawizard.data import (
    fetch_codelist,
    fetch_metabase,
    fetch_table_of_contents,
    get_cached_session,
    metabase2datasets,
    parse_codelist,
)
from st_widgets.commons import (
    app_config,
    get_logger,
    global_download_lock,
    load_dataset,
)
from st_widgets.console import session_console
from st_widgets.resettable_multiselect import resettable_multiselect
from st_widgets.stateful.selectbox import stateful_selectbox
from st_widgets.stateful.slider import stateful_slider

logging = get_logger(__name__)
session = st.session_state
app_config("Data Import")


@st.cache_data()
def load_toc() -> pd.Series | None:
    # Return a series with datasets code as index and descriptions as values.
    # ex: key: EI_BSCO_M  - value: Consumers ...
    try:
        with st.sidebar:
            with st.spinner(text="Fetching table of contents"):
                with global_download_lock():
                    toc = fetch_table_of_contents()
                    # TODO Derived dataset are not found:
                    # HTTPError: 404 Client Error: Not Found for url: ...
                    toc = toc[~toc.index.str.contains("$", regex=False)]
                toc = toc["title"]
                return toc
    except Exception as e:
        st.sidebar.error(e)


@st.cache_data()
def load_metabase2datasets() -> pd.DataFrame:
    # Return an index of code + dimension and a list of datasets using them
    req = get_cached_session()
    metabase = fetch_metabase(req)
    codelist = parse_codelist(fetch_codelist(req))
    return metabase2datasets(metabase, codelist)


@st.cache_data()
def load_dimensions(metabase2datasets: pd.DataFrame) -> pd.Series:
    # Arrage metabase as an index of dimensions + descriptions
    codes_dims = metabase2datasets.reset_index()[
        ["dimension", "code", "dimension_label", "code_label"]
    ].set_index(["dimension", "code"])
    codes_dims = codes_dims["dimension_label"].str.cat(
        codes_dims["code_label"], sep=": "
    )
    return codes_dims


def save_datasets_to_stash():
    toc = load_toc()

    # Datasets search criteria
    if toc is not None:
        with st.sidebar:
            tab1, tab2 = st.tabs(["Datasets", "Dimensions"])

            with tab1:
                dataset_code = stateful_selectbox(
                    label="Select dataset (type to search)",
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
                # TODO All the combinations are too heavy to load!
                # Moreover, because streamlit always reload itself, it gets painful to add dimensions
                tab2.markdown(
                    """ 🚧 Work in progress 🚧  
                    Select only dimensions of interest to filter the dataset list in the previous tab"""
                )
                meta = load_metabase2datasets()
                codes_dims = load_dimensions(meta)
                codes_dims_list = codes_dims.index.tolist()
                resettable_multiselect(
                    "Select dimensions (type to search)",
                    options=codes_dims_list,
                    key="_selected_codes",
                    format_func=lambda code_dim: f"{code_dim[0]}, {code_dim[1]} | {codes_dims.loc[code_dim]}",
                )

        # Dataset filtering criteria
        if dataset_code is not None:
            st.subheader(
                f"Variable selection: {dataset_code + ' | ' + toc.loc[dataset_code]}"
            )

            dataset = load_dataset(dataset_code)

            # Flags filtering handles
            flags = dataset.flag.fillna("<NA>").unique().tolist()
            history["flags"] = resettable_multiselect(
                "Select FLAG", flags, default=flags, key=f"_{dataset_code}.flags"
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
                    codes_dims, M = indexes["time"][0], indexes["time"][1]
                    M = M if codes_dims < M else M + 1  # RangeError fix
                    history["indexes"]["time"] = stateful_slider(
                        label="Select TIME [min: 1 year]",
                        min_value=codes_dims,
                        max_value=M,
                        value=(codes_dims, M),
                        key=f"_{dataset_code}.indexes.time",
                    )
                else:
                    history["indexes"][name] = resettable_multiselect(
                        f"Select {name.upper()}",
                        indexes[name],
                        default=indexes[name],
                        key=f"_{dataset_code}.indexes.{name}",
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
