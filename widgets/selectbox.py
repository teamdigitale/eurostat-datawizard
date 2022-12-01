import streamlit as st
import pandas as pd
from typing import List

session = st.session_state


def update_selectbox_idx(options: List[str], session_key: str):
    session[f"{session_key}_idx"] = options.index(session[session_key])


def stateful_selectbox(
    label: str,
    options: List[str],
    session_key: str | None = "selected_option",
    **kwargs,
):
    """
    A stateful selectbox.
    It manages autonomously index, key, on_change, args. DO NOT OVERRIDE THESE PARAMS!
    """

    if session_key and f"{session_key}_idx" not in session:
        session[f"{session_key}_idx"] = 0
    return st.sidebar.selectbox(
        label=label,
        options=options,
        index=session[f"{session_key}_idx"] if session_key else 0,
        key=session_key if session_key else None,
        on_change=update_selectbox_idx if session_key else None,
        args=(options, session_key) if session_key else None,
        **kwargs,
    )
