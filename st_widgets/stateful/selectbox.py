from st_widgets.commons import get_logger
from functools import partial
from typing import Any, List, MutableMapping, Optional

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.state import WidgetCallback
from streamlit.type_util import Key, OptionSequence, T

from st_widgets.stateful import _on_change_factory

logger = get_logger(__name__)


def _update_index(
    session: MutableMapping[Key, Any], key: str, options: OptionSequence[T]
):
    # Retrieve the index out of any `options` type
    options = pd.Series(options)
    session[f"{key}_index"] = int(options[options == session[key]].index[0])


def stateful_selectbox(
    label: str,
    options: List,
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
    if f"{key}_options" not in session:
        session[f"{key}_options"] = options

    if f"{key}_index" not in session:
        session[f"{key}_index"] = index

    if list(options) != list(session[f"{key}_options"]):
        # If options change, reset also the index
        session[f"{key}_options"] = options
        session[f"{key}_index"] = index

    position.selectbox(
        label=label,
        options=session[f"{key}_options"],
        index=session[f"{key}_index"],
        key=key,
        on_change=_on_change_factory(partial(_update_index, session, key, options))(
            on_change
        ),
        **kwargs,
    )

    options = session[f"{key}_options"]
    index = session[f"{key}_index"]
    return options[index]
