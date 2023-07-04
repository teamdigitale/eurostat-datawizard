from st_widgets.commons import get_logger
from functools import partial
from typing import Any, MutableMapping, Optional

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
    options: OptionSequence[T],
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
        options=options,
        index=session[f"{key}_index"],
        key=key,
        on_change=_on_change_factory(partial(_update_index, session, key, options))(
            on_change
        ),
        **kwargs,
    )
