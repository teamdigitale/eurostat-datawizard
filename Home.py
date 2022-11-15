import streamlit as st

if __name__ == "__main__":
    st.set_page_config(
        page_title="Eurostat Data Wizard • Home",
        page_icon="🇪🇺",
    )

    with open("README.md", "r") as readme:
        app_description = "".join([next(readme) for _ in range(11)])

    app_description = app_description.replace("# Eurostat", "# 🇪🇺 Eurostat")

    st.markdown(app_description)
