from typing import Any, MutableMapping, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.state import WidgetCallback
from streamlit.type_util import Key, OptionSequence, T

from st_widgets.stateful.multiselect import stateful_multiselect


def multiselectall(
    label: str,
    options: OptionSequence[T],
    key: str,
    default: Optional[Any] = None,
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    **kwargs,
):
    container = st.container()

    if st.button(
        "Select all",
        key=f"{key}_all",
    ):
        del session[f"{key}_default"]
        st.experimental_rerun()

    with container:
        return stateful_multiselect(
            label=f"{label} ({len(session[key]) if key in session else len(default) if default else 0}/{len(options)})",  # type: ignore
            options=options,
            default=default,
            key=key,
            **kwargs,
        )
