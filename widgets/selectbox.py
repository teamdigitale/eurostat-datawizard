import streamlit as st
from uuid import uuid4
from streamlit.type_util import Key
from typing import Any, List, Literal, MutableMapping


def update_selectbox_idx(
    options: List[str], session: MutableMapping[Key, Any], key: str
):
    session[f"{key}_idx"] = options.index(session[key])


def stateful_selectbox(
    label: str,
    options: List[str],
    position: Literal["sidebar"] | None = None,
    session: MutableMapping[Key, Any] = st.session_state,
    key: str = str(uuid4()),
    **kwargs,
):
    """
    A stateful selectbox.
    It manages autonomously index, on_change and args.
    """

    if key and f"{key}_idx" not in session:
        session[f"{key}_idx"] = 0

    pos = st if not position else st.sidebar

    return pos.selectbox(
        label=label,
        options=options,
        index=session[f"{key}_idx"],
        key=key,
        on_change=update_selectbox_idx,
        args=(options, session, key),
        **kwargs,
    )
