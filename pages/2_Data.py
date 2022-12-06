from threading import Lock
from typing import List
import pandas as pd
import streamlit as st
from widgets.session import app_config
from src.eurostat import (
    cast_time_to_datetimeindex,
    fetch_dataset_and_metadata,
    split_dimensions_and_attributes_from,
)
from src.utils import concat_keys_to_values
from widgets.console import show_console
from widgets.dataframe import (
    empty_eurostat_dataframe,
    filter_dataset_replacing_NA,
)
from widgets.stateful.selectbox import stateful_selectbox
from widgets.index import load_table_of_contents, load_codelist_reverse_index

session = st.session_state


@st.experimental_singleton(show_spinner=False)
def eust_lock():
    """A shared lock amongst sessions to prevent concurrent dataset write."""
    # NOTE Because it can't be assessed from outside `eust` package if fetching
    # is coming from internet (and so writing a file) or internal cache.
    return Lock()


def quote_sanitizer(series: pd.Series) -> pd.Series:
    return series.str.replace('"', "-").str.replace("'", "-")


@st.experimental_memo(show_spinner=False)
def load_dataset(code: str) -> pd.DataFrame:
    with eust_lock():
        data, meta = fetch_dataset_and_metadata(code)
    dims, attrs = split_dimensions_and_attributes_from(meta, code)
    data = cast_time_to_datetimeindex(data)
    dims = concat_keys_to_values(quote_sanitizer(dims).to_dict())
    data = data.rename(index=dims).sort_index()
    data = data.assign(flag=data.flag.map(attrs.to_dict()))
    # `flag` shown before `value` to make it more readable as filterable
    return data[["flag", "value"]]


@st.experimental_memo(show_spinner=False)
def build_toc_list(toc: pd.Series) -> List[str]:
    # ex: I_IUIF | Internet use: ...
    toc = toc.index + " | " + toc.values  # type: ignore
    return ["Scroll options or start typing"] + toc.to_list()


@st.experimental_memo(show_spinner=False)
def build_dimension_list(dimensions: pd.Series) -> List[str]:
    # ex: ei_bsco_m | Consumers ...
    return ["Scroll options or start typing"] + dimensions.index.to_list()


def reset_user_selections():
    # NOTE Because datasets list change, reset the selected idx
    if "selected_dataset_options" in session:
        session.pop("selected_dataset_options")
    if "selected_dataset_index" in session:
        session.pop("selected_dataset_index")
    # NOTE Override "Filter datasets by (map) selection"
    if "selected_map_selection" in session:
        session["selected_map_selection"] = False


def update_history_flags(dataset_code: str):
    session["history"][dataset_code]["flags"] = session[f"_{dataset_code}.flags"]


def update_history_indexes(dataset_code: str, name: str):
    session["history"][dataset_code]["indexes"][name] = session[
        f"_{dataset_code}.indexes.{name}"
    ]


def import_dataset():
    try:
        with st.sidebar:
            with st.spinner(text="Fetching index"):
                toc, _ = load_table_of_contents()
                codelist = load_codelist_reverse_index()
    except Exception as e:
        st.sidebar.error(e)
        return empty_eurostat_dataframe()

    variables = build_dimension_list(codelist)

    tab1, tab2 = st.sidebar.tabs(["Filter datasets by variable", "Map Selection"])

    with tab1:
        selected_variable = stateful_selectbox(
            "Filter datasets by variable",
            variables,
            key="selected_variable",
            on_change=reset_user_selections,
        )

        # Get a toc subsets or the entire toc list
        dataset_codes = codelist.get(selected_variable, default=None)

    with tab2:
        if tab2.checkbox(
            "Filter datasets by selection",
            key="selected_map_selection",
            disabled="map_selection" not in session or session["map_selection"].empty,
        ):
            if "map_selection" in session:
                dataset_codes = session["map_selection"]["code"].to_list()

    # List (filtered) datasets
    datasets = build_toc_list(
        toc.loc[toc.index.intersection(dataset_codes)] if dataset_codes else toc  # type: ignore
    )

    with st.sidebar:
        dataset_code_title = stateful_selectbox(
            "Choose a dataset", datasets, key="selected_dataset"
        )

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

                # Flags management
                flags = dataset.flag.fillna("<NA>").unique().tolist()
                if "flags" not in history:
                    history["flags"] = flags

                st.subheader(f"Variable selection: {dataset_code_title}")
                history["flags"] = st.multiselect(
                    label="Select FLAG",
                    options=flags,
                    default=history["flags"],
                    key=f"_{dataset_code}.flags",
                    on_change=update_history_flags,
                    args=(dataset_code,),
                )

                # Indexes management
                indexes = {n: dataset.index.levels[i].to_list() for i, n in enumerate(dataset.index.names)}  # type: ignore
                if "time" in indexes:
                    indexes["time"] = (
                        min(indexes["time"]).year,
                        max(indexes["time"]).year,
                    )

                if "indexes" not in history:
                    history["indexes"] = indexes

                for name in dataset.index.names:
                    if name == "time":
                        m, M = indexes[name][0], indexes[name][1]
                        M = M if m < M else M + 1  # RangeError fix
                        history["indexes"][name] = st.slider(
                            label="Select TIME [min: 1 year]",
                            min_value=m,
                            max_value=M,
                            value=history["indexes"][name],
                            step=1,
                            key=f"_{dataset_code}.indexes.{name}",
                            on_change=update_history_indexes,
                            args=(
                                dataset_code,
                                name,
                            ),
                        )
                    else:
                        history["indexes"][name] = st.multiselect(
                            label=f"Select {name.upper()}",
                            options=indexes[name],
                            default=history["indexes"][name],
                            key=f"_{dataset_code}.indexes.{name}",
                            on_change=update_history_indexes,
                            args=(
                                dataset_code,
                                name,
                            ),
                        )

                return dataset

        except (ValueError, AssertionError, NotImplementedError) as e:
            st.error(e)

    return empty_eurostat_dataframe()


def show_dataset(dataset):
    dataset_code_title = session.selected_dataset
    dataset_code = dataset_code_title.split(" | ", maxsplit=1)[0]

    if not dataset.empty:
        view = filter_dataset_replacing_NA(
            dataset,
            session["history"][dataset_code]["indexes"],
            session["history"][dataset_code]["flags"],
        )
    else:
        view = dataset


def page_init():
    if "history" not in session:
        session["history"] = dict()


if __name__ == "__main__":
    app_config("Data Import")
    page_init()

    st.markdown(
        """
    <style>
        .stMultiSelect [data-baseweb=select] span{
            max-width: 900px;
            font-size: 0.8rem;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    dataset = import_dataset()

    show_console()  # For debugging
