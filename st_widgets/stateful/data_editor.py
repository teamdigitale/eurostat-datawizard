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

from st_widgets.stateful.base import _on_change_factory

logger = get_logger(__name__)


def _update_data(session: MutableMapping[Key, Any], key: str):
    data = session[f"{key}_data"]
    if key in session:  # means that `data_editor` has `edited_rows` to be applied
        edited_rows = session[key]
        data_schema = determine_dataframe_schema(data, pa.Table.from_pandas(data))
        _apply_dataframe_edits(data, edited_rows, data_schema)


def stateful_data_editor(
    data: DataTypes,
    key: str,
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    multiedit: bool = False,
    **kwargs,
):
    """
    A stateful data editor that preserves modification.
    Can be configured to accept multiple editing before reload (performed on button click).
    """
    if f"{key}_data" not in session:
        session[f"{key}_data"] = data

    if multiedit:
        with position.form(f"{key}_form"):
            position.data_editor(
                data=session[f"{key}_data"],
                key=key,
                # TODO For unknown reasons, use `_on_change_factory` here cause:
                # `StreamlitAPIException: With forms, callbacks can only be defined on the st.form_submit_button.
                # Defining callbacks on other widgets inside a form is not allowed.`
                # Anyway, `_update_data` IS a callback and it is working.
                on_change=_update_data(session, key),
                **kwargs,
            )

            submitted = position.form_submit_button("Edit")
            if submitted:
                return session[f"{key}_data"]

    else:
        position.data_editor(
            data=session[f"{key}_data"],
            key=key,
            on_change=_on_change_factory(partial(_update_data, session, key))(
                on_change
            ),
            **kwargs,
        )
        return session[f"{key}_data"]
