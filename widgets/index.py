import streamlit as st
import pandas as pd
from globals import VARS_INDEX_PATH
from src.eurostat import fetch_table_of_contents

# NOTE Caching is managed manually, do not cache with streamlit
def load_codelist_reverse_index() -> pd.Series:
    return pd.read_pickle(VARS_INDEX_PATH)


# NOTE `persist` preserve caching also when page is left
@st.experimental_memo(show_spinner=False, persist="disk")
def load_table_of_contents() -> pd.Series:
    return fetch_table_of_contents()
