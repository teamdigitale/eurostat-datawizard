import json
from typing import Mapping
import pandas as pd
import streamlit as st
from datetime import datetime
from src.utils import PandasJSONEncoder


def download_session_state():
    now = datetime.now().isoformat(timespec="seconds")
    st.download_button(
        "Download",
        json.dumps(st.session_state.to_dict(), cls=PandasJSONEncoder),
        file_name=f"EurostatDataWizard_session_{now}.json",
        mime="application/json",
    )


def update_dict(d, u):
    # Source: https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def upload_session_state(widget):
    json_str = st.file_uploader("Upload & overwrite existing session", "json")
    if json_str:
        py_dict = json.loads(json_str.getvalue())
        # NOTE variables set via session state are write-protected from streamlit.
        # So they are marked as private variables by convention and will be filtered
        # to avoid collision with session state API, that fires error like:
        # StreamlitAPIException: st.session_state._selected_variable cannot be
        # modified after the widget with key _selected_variable is instantiated.
        # [py_dict.pop(key) for key in list(py_dict.keys()) if key.startswith("_")]
        # TODO remove above when stateful_widgets manage session state manually
        if "time" in py_dict:
            py_dict["time"] = pd.to_datetime(py_dict["time"])
        st.session_state.clear()
        st.session_state.update(py_dict)
        widget.json(st.session_state, expanded=False)


def session_console():
    with st.expander("Session console"):
        col1, col2 = st.columns(2)
        session_container = st.empty()
        with col1:
            download_session_state()
        with col2:
            upload_session_state(session_container)
        session_container.json(st.session_state, expanded=False)
