import streamlit as st
from uuid import uuid4
from streamlit.delta_generator import DeltaGenerator
from streamlit.type_util import Key
from typing import Any, List, MutableMapping


def _update_index(options: List[str], session: MutableMapping[Key, Any], key: str):
    session[f"{key}_idx"] = options.index(session[key])


def stateful_selectbox(
    label: str,
    options: List[str],
    position: DeltaGenerator = st._main,
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

    return position.selectbox(
        label=label,
        options=options,
        index=session[f"{key}_idx"],
        key=key,
        on_change=_update_index,
        args=(options, session, key),
        **kwargs,
    )
