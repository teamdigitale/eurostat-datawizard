from st_widgets.commons import get_logger
from functools import partial
from typing import Any, MutableMapping, Optional
import pyarrow as pa
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.state import WidgetCallback
from streamlit.type_util import Key
from streamlit.elements.data_editor import DataTypes, _apply_dataframe_edits
from streamlit.elements.lib.column_config_utils import determine_dataframe_schema

from st_widgets.stateful import _on_change_factory

logger = get_logger(__name__)


def _update_data(session: MutableMapping[Key, Any], key: str):
    data = session[f"{key}_data"]
    edited_rows = session[key]
    data_schema = determine_dataframe_schema(data, pa.Table.from_pandas(data))
    _apply_dataframe_edits(data, edited_rows, data_schema)


def stateful_data_editor(
    data: DataTypes,
    key: str,
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    **kwargs,
):
    """
    A stateful data editor that preserves modification.
    """
    if f"{key}_data" not in session:
        session[f"{key}_data"] = data

    position.data_editor(
        data=session[f"{key}_data"],
        key=key,
        on_change=_on_change_factory(partial(_update_data, session, key))(on_change),
        **kwargs,
    )
    return session[f"{key}_data"]
