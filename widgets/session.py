import streamlit as st
from globals import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON


def page_config(title: str):
    st.set_page_config(
        page_title=f"Eurostat Data Wizard • {title}",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )

    if "stash" not in st.session_state:
        st.session_state.stash = {}

    if "user" not in st.session_state:
        st.session_state.user = dict(st.experimental_user)
