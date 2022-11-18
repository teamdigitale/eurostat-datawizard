import streamlit as st
from globals import INITIAL_SIDEBAR_STATE, LAYOUT, MENU_ITEMS, PAGE_ICON

# from pages.Data_Import import load_table_of_contents, load_codelist_reverse_index


def page_config():
    st.set_page_config(
        page_title="Eurostat Data Wizard • Home",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )


def initialize_session():
    if "stash" not in st.session_state:
        st.session_state.stash = {}

    # BUG streamlit does not allow caching between multipage.
    # # Trigger functions to allow caching
    # with st.sidebar:
    #     with st.spinner("App initializing, please wait before use:"):
    #         toc = load_table_of_contents()
    #         _ = load_codelist_reverse_index(toc.index.to_list())


if __name__ == "__main__":
    page_config()

    with open("README.md", "r") as readme:
        app_description = "".join([next(readme) for _ in range(14)])

    app_description = app_description.replace("# Eurostat", "# 🇪🇺 Eurostat")

    st.markdown(app_description)

    initialize_session()
