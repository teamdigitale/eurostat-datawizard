from typing import Any, MutableMapping, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.state import WidgetCallback
from streamlit.type_util import Key

from st_widgets.stateful import _on_change_factory


def _update_index(session: MutableMapping[Key, Any], key: str):
    session[f"{key}_index"] = session[key]


def stateful_selectbox(
    label: str,
    key: str,
    index: int = 0,
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    **kwargs,
):
    """
    A stateful selectbox that preserves index selection.
    """
    if f"{key}_index" not in session:
        session[f"{key}_index"] = index

    return position.selectbox(
        label=label,
        index=session[f"{key}_index"],
        key=key,
        on_change=_on_change_factory(_update_index, session, key)(on_change),
        **kwargs,
    )
