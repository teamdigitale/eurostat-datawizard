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
from widgets.dataframe import empty_eurostat_dataframe
from widgets.stateful.multiselect import stateful_multiselect
from widgets.stateful.selectbox import stateful_selectbox
from widgets.stateful.slider import stateful_slider
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


def import_dataset():
    try:
        with st.sidebar:
            with st.spinner(text="Fetching table of contents"):
                toc, _ = load_table_of_contents()
    except Exception as e:
        st.sidebar.error(e)
        return empty_eurostat_dataframe()

    try:
        with st.sidebar:
            with st.spinner(text="Fetching index"):
                codelist = load_codelist_reverse_index()
    except Exception as e:
        codelist = None

    tab1, tab2 = st.sidebar.tabs(["Filter datasets by variable", "Map Selection"])

    with tab1:
        if codelist is None:
            dataset_codes = None
            st.sidebar.warning(
                "Filter datasets by variable not available without index."
            )
        else:
            with st.sidebar:
                with st.spinner(text="Fetching index"):
                    variables = build_dimension_list(codelist)
            selected_variable = stateful_selectbox(
                label="Filter datasets by variable",
                options=range(len(variables)),
                format_func=lambda i: variables[i],
                key="selected_variable",
                on_change=reset_user_selections,
            )
            selected_variable = variables[selected_variable]  # type: ignore

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
            label="Choose a dataset",
            options=range(len(datasets)),
            format_func=lambda i: datasets[i],
            key="selected_dataset",
        )
        dataset_code_title = datasets[dataset_code_title]  # type: ignore

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

                st.subheader(f"Variable selection: {dataset_code_title}")

                # Flags management
                flags = dataset.flag.fillna("<NA>").unique().tolist()

                flags_container = st.container()

                if st.checkbox(
                    "Select all",
                    key=f"_{dataset_code}.flags_all",
                    value=sorted(session[f"_{dataset_code}.flags_default"])
                    == sorted(history["flags"])
                    if f"_{dataset_code}.flags_default" in session
                    else False,
                    disabled=f"_{dataset_code}.flags_default" not in session,
                ):
                    del session[f"_{dataset_code}.flags_default"]

                with flags_container:
                    history["flags"] = stateful_multiselect(
                        label="Select FLAG",
                        options=flags,
                        default=flags,
                        key=f"_{dataset_code}.flags",
                    )

                # Indexes management
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
                        index_container = st.container()

                        if st.checkbox(
                            "Select all",
                            key=f"_{dataset_code}.indexes.time_all",
                            value=sorted(
                                session[f"_{dataset_code}.indexes.time_default"]
                            )
                            == sorted(history["indexes"]["time"])
                            if f"_{dataset_code}.indexes.time_default" in session
                            else False,
                            disabled=f"_{dataset_code}.indexes.time_default"
                            not in session,
                        ):
                            del session[f"_{dataset_code}.indexes.time_default"]
                        with index_container:
                            m, M = indexes["time"][0], indexes["time"][1]
                            M = M if m < M else M + 1  # RangeError fix
                            history["indexes"]["time"] = stateful_slider(
                                label="Select TIME [min: 1 year]",
                                min_value=m,
                                max_value=M,
                                value=(m, M),
                                key=f"_{dataset_code}.indexes.time",
                            )
                    else:
                        index_container = st.container()

                        if st.checkbox(
                            "Select all",
                            key=f"_{dataset_code}.indexes.{name}_all",
                            value=sorted(
                                session[f"_{dataset_code}.indexes.{name}_default"]
                            )
                            == sorted(history["indexes"][name])
                            if f"_{dataset_code}.indexes.{name}_default" in session
                            else False,
                            disabled=f"_{dataset_code}.indexes.{name}_default"
                            not in session,
                        ):
                            del session[f"_{dataset_code}.indexes.{name}_default"]

                        with index_container:
                            history["indexes"][name] = stateful_multiselect(
                                label=f"Select {name.upper()}",
                                options=indexes[name],
                                default=indexes[name],
                                key=f"_{dataset_code}.indexes.{name}",
                            )

                return dataset

        except (ValueError, AssertionError, NotImplementedError) as e:
            st.error(e)

    return empty_eurostat_dataframe()


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
            max-width: 500px;
            font-size: 0.8rem;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    dataset = import_dataset()

    show_console()
