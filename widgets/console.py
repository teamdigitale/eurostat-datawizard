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
        st.session_state.update(json.loads(json_str.getvalue()))


def show_console():
    with st.expander("Session console"):
        download_session_state()
        st.write(st.session_state)
        upload_session_state()
