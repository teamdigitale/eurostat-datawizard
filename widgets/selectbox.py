import streamlit as st
import pandas as pd
from typing import List

session = st.session_state


@st.experimental_memo(show_spinner=False)
def build_toc_list(toc: pd.Series) -> List[str]:
    # ex: I_IUIF | Internet use: ...
    toc = toc.index + " | " + toc.values  # type: ignore
    return ["Scroll options or start typing"] + toc.to_list()


def update_selectbox_idx(options: List[str], session_key: str):
    session[f"{session_key}_idx"] = options.index(session[session_key])


def stateful_selectbox(
    label: str,
    toc: pd.Series,
    dataset_codes: List[str] | None = None,
    session_key: str | None = "selected_option",
):
    # List (filtered) datasets
    datasets = build_toc_list(
        toc.loc[toc.index.intersection(dataset_codes)] if dataset_codes else toc  # type: ignore
    )

    if session_key and f"{session_key}_idx" not in session:
        session[f"{session_key}_idx"] = 0
    return st.sidebar.selectbox(
        label=label,
        options=datasets,
        index=session[f"{session_key}_idx"] if session_key else 0,
        key=session_key if session_key else None,
        on_change=update_selectbox_idx if session_key else None,
        args=(datasets, session_key) if session_key else None,
    )
