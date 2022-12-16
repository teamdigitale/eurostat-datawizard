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
        # NOTE private variables will be filtered to avoid collision with internal
        # widget state, like:
        # StreamlitAPIException: st.session_state.selected_variable cannot be
        # modified after the widget with key selected_variable is instantiated.
        [py_dict.pop(key) for key in list(py_dict.keys()) if key.startswith("_")]
        if "time" in py_dict:
            py_dict["time"] = pd.to_datetime(py_dict["time"])
        st.session_state.update(py_dict)
        widget.write(st.session_state)


def session_console():
    with st.expander("Session console"):
        download_session_state()
        session_container = st.empty()
        session_container.write(st.session_state)
        upload_session_state(session_container)
