from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st


def download_dataframe_button(
    dataframe: pd.DataFrame, filename_prefix: str = "EurostatDataWizard"
):
    now = datetime.now().isoformat(timespec="seconds")
    with BytesIO() as buffer:
        # Data downloaded is the `view` to be consistent with what user sees
        dataframe.to_csv(buffer, index=False, compression={"method": "gzip"})
        st.download_button(
            "Download",
            buffer.getvalue(),
            file_name=f"{filename_prefix}_{now}.csv.gz",
            mime="application/gzip",
            disabled=dataframe.empty,
        )
