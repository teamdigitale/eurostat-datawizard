import streamlit as st
from datetime import datetime
from src.utils import get_last_file_update

PAGE_ICON = "🇪🇺"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"
MENU_ITEMS = {
    "About": """
            Code is [open source](https://github.com/teamdigitale/eurostat-datawizard) by Dipartimento della Trasformazione Digitale.  
            
            Datasets are provided [free of charge](https://ec.europa.eu/eurostat/en/about-us/policies/copyright) by © European Union, 1995 - today.  
            
            Copyright (c) 2022 Presidenza del Consiglio dei Ministri.  
            """
}
VARS_INDEX_PATH = "cache/vars_index.pickle"
CLUSTERING_PATH = "cache/clustermap.csv.gz"
DEMO_N_DATASET = 5


def get_last_index_update() -> datetime | None:
    return get_last_file_update(VARS_INDEX_PATH)


def get_last_clustering_update() -> datetime | None:
    return get_last_file_update(CLUSTERING_PATH)
