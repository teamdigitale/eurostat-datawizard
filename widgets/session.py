import streamlit as st
from globals import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON


def app_config(title: str):
    """Setup page & session state. Must be the first script instruction called."""
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


def remove_temporary_session_vars():
    """Some variables were marked with a starting `_` because are not intended to
    be retained but rather as throw-away variable.
    """
    for k in st.session_state:
        if k.startswith("_"):
            del st.session_state[k]
