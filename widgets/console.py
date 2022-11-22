import json
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


def upload_session_state():
    json_str = st.file_uploader("Upload & overwrite existing session", "json")
    if json_str:
        py_dict = json.loads(json_str.getvalue())
        # NOTE UI variables will be filtered to avoid collision like:
        # StreamlitAPIException: st.session_state.selected_variable cannot be
        # modified after the widget with key selected_variable is instantiated.
        [py_dict.pop(key) for key in list(py_dict.keys()) if "selected_" in key]
        st.session_state.update(py_dict)


def show_console():
    with st.expander("Session console"):
        download_session_state()
        st.write(st.session_state)
        upload_session_state()
