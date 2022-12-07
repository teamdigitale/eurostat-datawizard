import os
import time
from datetime import timedelta
from typing import Tuple

import pandas as pd
import streamlit as st
from requests import ConnectionError, HTTPError

from globals import VARS_INDEX_PATH
from src.eurostat import (
    eurostat_sdmx_request,
    fetch_dataset_codelist,
    fetch_table_of_contents,
)


@st.experimental_memo(show_spinner=False, ttl=timedelta(days=90))
def load_table_of_contents() -> Tuple[pd.Series, pd.Series]:
    toc, themes = fetch_table_of_contents()
    return toc, themes


def save_index_file():
    """Obtain codelist and in which dataset is used each."""
    message = st.sidebar.empty()
    message.text("Initializing indexing...")

    codelist = pd.DataFrame()
    progress_bar = st.sidebar.progress(0.0)
    progress_value = 0.0
    status = st.sidebar.empty()
    req = eurostat_sdmx_request()
    toc, _ = load_table_of_contents()
    if os.environ["ENV"] == "demo":
        toc = toc.sample(10)
    datasets = toc.index.to_list()
    len_datasets = len(datasets)
    datasets_not_loaded = []
    for n, dataset in enumerate(datasets):
        message.text(f"Loading {dataset} ({n}/{len_datasets})")
        try:
            codes, cached = fetch_dataset_codelist(req, dataset)
            codes = codes.assign(dataset=dataset)
            codelist = pd.concat([codelist, codes])
            status.success(
                f"Loaded{' from cache' if cached else ' from Eurostat'}",
                icon="♻️" if cached else "✅",
            )
        except HTTPError as e:
            # NOTE Usually happens if a dataset was not found
            status.warning(e, icon="⚠️")
            datasets_not_loaded.append(dataset)
        except ConnectionError as e:
            # NOTE Usually happens when Eurostat reset connection
            status.warning(e, icon="⚠️")
            datasets_not_loaded.append(dataset)
            time.sleep(1)  # Cooldown before resume requests
        progress_value = n / len_datasets
        progress_bar.progress(progress_value)

    progress_bar.empty()
    if len(datasets_not_loaded) > 0:
        status.warning(
            f"Unable to load: {datasets_not_loaded}. Refresh only if you find it useful. All the metadata successfully received will be loaded from cache.",
            icon="⚠️",
        )
    else:
        status.success(
            f"All datasets were loaded.",
            icon="✅",
        )

    # Aggregate datasets dimension for a variable -> list(dataset) index
    message.text("Finalizing indexing...")
    uninformative_parents = ["OBS_FLAG", "OBS_STATUS"]
    codelist = codelist[~codelist.parent.isin(uninformative_parents)]
    codelist = (
        codelist.assign(name=codelist.name.str.capitalize())
        .groupby(["dimension", "name"])["dataset"]
        .unique()
    )
    codelist = codelist[codelist.apply(len) > 0]
    codelist.index = codelist.index.to_flat_index().str.join(" | ")
    codelist.name = "datasets"
    codelist.index.name = "code"
    codelist.apply(lambda x: x.tolist()).to_pickle(VARS_INDEX_PATH)
    message.empty()


# NOTE Caching is managed manually, do not cache with streamlit
def load_codelist_reverse_index() -> pd.Series:
    return pd.read_pickle(VARS_INDEX_PATH)
