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
    load_codelist,
    load_dataset,
    reduce_multiselect_font_size,
)
from st_widgets.console import session_console
from st_widgets.stateful.multiselect import stateful_multiselect
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


def save_datasets_to_stash():
    toc = load_toc()

    # Datasets search criteria
    if toc is not None:
        with st.sidebar:
            using_lookup = "lookup_datasets" in session and session["lookup_datasets"]
            dataset_code = stateful_selectbox(
                label=f"Select dataset {'from `lookup` page ' if using_lookup else ''}(type to search)",
                options=session["lookup_datasets"]
                if using_lookup
                else toc.index.tolist(),
                format_func=lambda i: i + " | " + toc.loc[i],
                key="_selected_dataset",
            )

            # Create or reuse a filtering history for this code
            if dataset_code not in session["history"]:
                session["history"][dataset_code] = dict()
            history = session["history"][dataset_code]
            history["stash"] = True

        # Dataset filtering criteria
        if dataset_code is not None:
            st.subheader(
                f"Variable selection: {dataset_code + ' | ' + toc.loc[dataset_code]}"
            )

            codelist = load_codelist()
            dataset = load_dataset(dataset_code, codelist)

            # Flags filtering handles
            flags = dataset.flag.fillna("<NA>").unique().tolist()
            history["flags"] = stateful_multiselect(
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
                    history["indexes"][name] = stateful_multiselect(
                        f"Select {name.upper()}",
                        indexes[name],
                        default=indexes[name],
                        key=f"_{dataset_code}.indexes.{name}",
                    )


if __name__ == "__main__":
    reduce_multiselect_font_size()
    save_datasets_to_stash()
    session_console()
