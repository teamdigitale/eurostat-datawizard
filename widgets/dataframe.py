import numpy as np
import pandas as pd
import streamlit as st
from typing import Dict, List
from src.eurostat import filter_dataset


def filter_dataset_replacing_NA(
    dataset: pd.DataFrame,
    indexes: Dict[str, List[str]],
    flags: list,
    placeholder: str = "<NA>",
) -> pd.DataFrame:
    """Manage every NaN as it was the same.

    Because np.nan != np.nan, matching a np.nan can't be performed from the original
    function. Than we wrap the filtering by replacing nan with a placeholder.
    """
    return filter_dataset(
        dataset, indexes, [np.nan if f == placeholder else f for f in flags]
    )


def st_dataframe_with_index_and_rows_cols_count(
    dataset: pd.DataFrame, title: str, *args, **kwargs
):
    st.subheader("Dataset" if dataset.empty else title)
    # Dataset is shown with `.reset_index` because MultiIndex are not rendered properly
    view = dataset if dataset.empty else dataset.reset_index()
    st.dataframe(view, *args, **kwargs)
    st.write("{} rows x {} columns".format(*view.shape))
    return view
