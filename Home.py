import streamlit as st
from globals import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON


def page_config():
    st.set_page_config(
        page_title="Eurostat Data Wizard • Home",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )


if __name__ == "__main__":
    page_config()

    with open("README.md", "r") as readme:
        app_description = "".join([next(readme) for _ in range(14)])

    app_description = app_description.replace("# Eurostat", "# 🇪🇺 Eurostat")

    st.markdown(app_description)
