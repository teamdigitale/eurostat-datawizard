import os

import streamlit as st

from st_widgets.commons import app_config
from st_widgets.console import session_console

app_config("Home")

with open("README.md", "r") as readme:
    app_description = "".join([next(readme) for _ in range(18)])

st.markdown(app_description)

session_console()
