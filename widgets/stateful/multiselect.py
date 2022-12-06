from typing import Any, Iterable, MutableMapping, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.state.session_state import WidgetCallback
from streamlit.type_util import Key

from widgets.stateful import _on_change_factory


def _update_default(session: MutableMapping[Key, Any], key: str):
    session[f"{key}_default"] = session[key]


def stateful_multiselect(
    label: str,
    options: Iterable[str],
    key: str,
    default: Optional[Any] = None,
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    **kwargs,
):
    """
    A stateful multiselect that preserves default selection.
    """

    if f"{key}_options" not in session:
        session[f"{key}_options"] = options

    if f"{key}_default" not in session:
        session[f"{key}_default"] = default

    return position.multiselect(
        label=label,
        options=session[f"{key}_options"],
        default=session[f"{key}_default"],
        key=key,
        on_change=_on_change_factory(_update_default, session, key)(on_change),
        **kwargs,
    )
