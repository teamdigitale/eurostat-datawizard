import pandas as pd
import streamlit as st


def st_dataframe_with_index_and_rows_cols_count(
    dataset: pd.DataFrame, title: str, *args, **kwargs
):
    st.subheader("Dataset" if dataset.empty else title)
    # Dataset is shown with `.reset_index` because MultiIndex are not rendered properly
    view = dataset if dataset.empty else dataset.reset_index()
    st.dataframe(view, *args, **kwargs)
    st.write("{} rows x {} columns".format(*view.shape))
    return view
