import streamlit as st

PAGE_ICON = "🇪🇺"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"
MENU_ITEMS = {
    "About": """
            Code is [open source](https://github.com/teamdigitale/eurostat-datawizard) by Dipartimento della Trasformazione Digitale.  
            
            Datasets are provided [free of charge](https://ec.europa.eu/eurostat/en/about-us/policies/copyright) by © European Union, 1995 - today.  
            
            Copyright (c) 2022 Presidenza del Consiglio dei Ministri.  
            """
}


def page_config():
    st.set_page_config(
        page_title="Eurostat Data Wizard • Home",
        page_icon=PAGE_ICON,
        layout=LAYOUT,
        initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        menu_items=MENU_ITEMS,  # type: ignore
    )

    if "stash" not in st.session_state:
        st.session_state.stash = {}


if __name__ == "__main__":
    page_config()

    with open("README.md", "r") as readme:
        app_description = "".join([next(readme) for _ in range(13)])

    app_description = app_description.replace("# Eurostat", "# 🇪🇺 Eurostat")

    st.markdown(app_description)
