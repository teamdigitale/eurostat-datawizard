import streamlit as st

from st_widgets.stateful.multiselect import stateful_multiselect


def multiselectall(options, key: str, label: str, session=st.session_state):
    container = st.container()

    if st.button(
        "Select all",
        key=f"{key}_all",
    ):
        del session[f"{key}_default"]
        st.experimental_rerun()

    with container:
        return stateful_multiselect(
            label=f"{label} ({len(session[key]) if key in session else len(options)}/{len(options)})",
            options=options,
            default=options,
            key=key,
        )
