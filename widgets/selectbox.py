import streamlit as st
from uuid import uuid4
from streamlit.delta_generator import DeltaGenerator
from streamlit.type_util import Key
from typing import Any, List, MutableMapping, Callable


def _update_index(options: List[str], session: MutableMapping[Key, Any], key: str):
    session[f"{key}_index"] = options.index(session[key])


def _on_change_factory(options, session, key):
    # Source: https://www.artima.com/weblogs/viewpost.jsp?thread=240845#decorator-functions-with-decorator-arguments
    def decorator(function):
        def wrapper(*args, **kwargs):
            _update_index(options, session, key)
            return function(*args, **kwargs)

        return wrapper

    return decorator


def stateful_selectbox(
    label: str,
    options: List[str],
    position: DeltaGenerator = st._main,
    session: MutableMapping[Key, Any] = st.session_state,
    key: str = str(uuid4()),
    on_change: Callable | None = None,
    **kwargs,
):
    """
    A stateful selectbox that preserves index selection.
    """

    if key and f"{key}_index" not in session:
        session[f"{key}_index"] = 0

    return position.selectbox(
        label=label,
        options=options,
        index=session[f"{key}_index"],
        key=key,
        on_change=_on_change_factory(options, session, key)(on_change),
        **kwargs,
    )
