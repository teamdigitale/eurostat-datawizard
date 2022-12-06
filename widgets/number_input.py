import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.type_util import Key
from typing import Union, Any, MutableMapping, Optional
from streamlit.elements.number_input import Number
from streamlit.runtime.state.widgets import NoValue
from streamlit.runtime.state.session_state import WidgetCallback


def _update_value(
    session: MutableMapping[Key, Any],
    key: str,
):
    session[f"{key}_value"] = session[key]


def _on_change_factory(session, key):
    # Inspiration: https://www.artima.com/weblogs/viewpost.jsp?thread=240845#decorator-functions-with-decorator-arguments
    def decorator(function):
        def wrapper(*args, **kwargs):
            _update_value(session, key)
            return function(*args, **kwargs) if function else None

        return wrapper

    return decorator


def stateful_number_input(
    label: str,
    key: str,
    value: Union[NoValue, Number, None] = NoValue(),
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    on_change: Optional[WidgetCallback] = None,
    **kwargs,
):
    """
    A stateful number input that preserves value.
    """

    if f"{key}_value" not in session:
        session[f"{key}_value"] = value

    return position.number_input(
        label,
        value=session[f"{key}_value"],
        key=key,
        on_change=_on_change_factory(session, key)(on_change),
        **kwargs,
    )
