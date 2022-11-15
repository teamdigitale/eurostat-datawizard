import streamlit as st


def show_console():
    with st.expander("Session console"):
        st.write(st.session_state)
