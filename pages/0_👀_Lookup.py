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
from st_widgets.stateful.data_editor import _update_data, stateful_data_editor

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
        """ Select only dimensions of interest to filter the dataset list in the `Data` page. Click anywhere in the table and type `CMD+F` or `CTRL+F` to search."""
    )
    meta = load_metabase2datasets()
    codes = load_dimensions_and_codes(meta)
    codes = codes.reset_index().assign(selected=False)

    with st.form("_selected_codes_form"):
        key = "_selected_codes"

        if f"{key}_data" not in session:
            session[f"{key}_data"] = codes

        st.data_editor(
            session[f"{key}_data"],
            disabled=["code", "dimension", "description"],
            use_container_width=True,
            key=key,
            on_change=_update_data(session, key),
        )

        submitted = st.form_submit_button("Add")
        if submitted:
            selected_codes = session[f"{key}_data"]
            selected_codes_mask = selected_codes["selected"].values
        else:
            selected_codes_mask = codes["selected"].values

    # TODO  Retrieve selected dimension after page change
    st.markdown("Selected dimension overview:")
    selected_datasets_by_code = meta.reset_index()[selected_codes_mask]
    st.dataframe(
        selected_datasets_by_code[
            ["dimension", "dimension_label", "code", "code_label", "dataset"]
        ],
        hide_index=False,
        use_container_width=True,
    )

    dataset_counts = selected_datasets_by_code["dataset"].explode().value_counts()
    st.sidebar.dataframe(dataset_counts)

    session["lookup_datasets"] = (
        dataset_counts.index.str.upper().tolist() if not dataset_counts.empty else None
    )

    session_console()
