import streamlit as st
import pandas as pd

from st_widgets.commons import (
    app_config,
    get_logger,
    load_dimensions_and_codes,
    load_metabase2datasets,
    reduce_multiselect_font_size,
)
from st_widgets.console import session_console
from st_widgets.stateful.multiselect import stateful_multiselect

logging = get_logger(__name__)
session = st.session_state
app_config("Data Import")


@st.cache_data
def load_dimensions(metabase2datasets: pd.DataFrame) -> pd.Series:
    # Return a series with dimensions code as index and descriptions as values.
    return (
        metabase2datasets.reset_index()[["dimension", "dimension_label"]]
        .drop_duplicates()
        .set_index("dimension")
        .squeeze()
        .sort_index()
    )


if __name__ == "__main__":
    reduce_multiselect_font_size()
    st.markdown(
        """ 🚧 Work in progress 🚧  
        Select only dimensions of interest to filter the dataset list in the `Data` page. Click anywhere in the table and type `CMD/CTRL+F` to search."""
    )
    meta = load_metabase2datasets()
    codes = load_dimensions_and_codes(meta)
    st.data_editor(
        codes.reset_index().assign(selected=True),
        disabled=["code", "dimension", "description"],
        use_container_width=True,
        key="_selected_codes",
    )

    # TODO subset meta["dataset"] based on selected dimensions

    session_console()
