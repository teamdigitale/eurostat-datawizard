from typing import Any, Iterable, MutableMapping, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.state.session_state import WidgetCallback
from streamlit.type_util import Key

from widgets.stateful import _on_change_factory


def _update_index(session: MutableMapping[Key, Any], key: str):
    session[f"{key}_index"] = tuple(session[f"{key}_options"]).index(session[key])


def stateful_selectbox(
    label: str,
    options: Iterable[str],
    key: str,
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    **kwargs,
):
    """
    A stateful selectbox that preserves index selection.
    """

    if f"{key}_options" not in session:
        session[f"{key}_options"] = options

    if f"{key}_index" not in session:
        session[f"{key}_index"] = 0

    return position.selectbox(
        label=label,
        options=session[f"{key}_options"],
        index=session[f"{key}_index"],
        key=key,
        on_change=_on_change_factory(_update_index, session, key)(on_change),
        **kwargs,
    )
