import streamlit as st

from st_widgets.commons import app_config
from st_widgets.console import session_console


app_config("Home")

if __name__ == "__main__":
    with open("README.md", "r") as readme:
        app_description = "".join(readme).split("# Installation")[0]

    st.markdown(app_description)
    session_console()
