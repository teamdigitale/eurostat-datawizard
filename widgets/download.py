import streamlit as st
from datetime import datetime
from io import BytesIO


def download_dataframe_button(view):
    now = datetime.now().isoformat(timespec="seconds")
    with BytesIO() as buffer:
        # Data downloaded is the `view` to be consistent with what user sees
        view.to_csv(buffer, index=False, compression={"method": "gzip"})
        st.download_button(
            "Download",
            buffer.getvalue(),
            file_name=f"EurostatDataWizard_{now}.csv.gz",
            mime="application/gzip",
            disabled=view.empty,
        )
