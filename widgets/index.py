import os
import streamlit as st
import pandas as pd
from datetime import datetime
from globals import VARS_INDEX_PATH
from src.eurostat import fetch_table_of_contents


def get_last_index_update() -> datetime | None:
    if os.path.exists(VARS_INDEX_PATH):
        return datetime.fromtimestamp(os.path.getmtime(VARS_INDEX_PATH))
    return None


# NOTE Caching is managed manually, do not cache with streamlit
def load_codelist_reverse_index() -> pd.Series:
    return pd.read_pickle(VARS_INDEX_PATH)


# NOTE `persist` preserve caching also when page is left
@st.experimental_memo(show_spinner=False, persist="disk")
def load_table_of_contents() -> pd.Series:
    return fetch_table_of_contents()
