from functools import partial
from typing import Any, MutableMapping, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.state import WidgetCallback
from streamlit.type_util import Key, OptionSequence, T

from st_widgets.stateful.base import _on_change_factory


def _update_default(session: MutableMapping[Key, Any], key: str):
    session[f"{key}_default"] = session[key]


def stateful_multiselect(
    label: str,
    options: OptionSequence[T],
    key: str,
    default: Optional[Any] = None,
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    **kwargs,
):
    """
    A stateful multiselect that preserves default selection.
    Can be reset to default state.
    """
    container = st.container()

    if f"{key}_default" not in session:
        session[f"{key}_default"] = default

    if st.button(
        "Reset",
        key=f"{key}_reset",
    ):
        del session[f"{key}_default"]
        st.experimental_rerun()

    with container:
        position.multiselect(
            label=f"{label} ({len(session[key]) if key in session else len(default) if default else 0}/{len(options)})",  # type: ignore
            options=options,
            default=session[f"{key}_default"],
            key=key,
            on_change=_on_change_factory(partial(_update_default, session, key))(
                on_change
            ),
            **kwargs,
        )

        return session[f"{key}_default"]
