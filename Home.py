import os
from threading import Lock

import streamlit as st

from globals import (
    VARS_INDEX_PATH,
    get_last_index_update,
    CLUSTERING_PATH,
    get_last_clustering_update,
    DEMO_N_DATASET,
)
from widgets.console import show_console
from widgets.index import (
    load_codelist_reverse_index,
    load_table_of_contents,
    save_index_file,
)
from widgets.session import app_config


@st.experimental_singleton(show_spinner=False)
def index_lock():
    """A shared lock amongst sessions to prevent concurrent index write."""
    return Lock()


def index_helper(message_widget):
    last_update = get_last_index_update()

    if os.environ["ENV"] == "demo":
        st.sidebar.warning(
            f"Demo version: you are limited to explore {DEMO_N_DATASET} random datasets."
        )

    col1, col2 = st.sidebar.columns(2, gap="large")
    with col1:
        st.markdown(
            f"""Index @ {last_update.isoformat(sep=' ', timespec='seconds') if last_update else 'never created'}"""
        )
    with col2:
        if st.button("Refresh" if last_update else "Create"):
            with index_lock():
                message_widget.empty()
                save_index_file()
                # In order to load newly updated index and invalidate cache
                st.experimental_memo.clear()
                # With a new index, Map clustering uploaded manually must be invalidated
                if get_last_clustering_update():
                    os.remove(CLUSTERING_PATH)
                st.experimental_rerun()
        else:
            message_widget.empty()


@st.experimental_memo(show_spinner=False)
def index_describer():
    if get_last_index_update():
        try:
            with st.sidebar:
                with st.spinner(text="Fetching index"):
                    toc, _ = load_table_of_contents()
                    codelist = load_codelist_reverse_index()
                    st.sidebar.markdown(
                        f"""
                    - Indexed dataset: {DEMO_N_DATASET if os.environ["ENV"]=="demo" else len(toc)}
                    - Indexed unique variables: {len(codelist)}

                    Most used variables:
                    """
                    )
                    st.sidebar.dataframe(
                        codelist.apply(len)
                        .sort_values(ascending=False)
                        .reset_index()
                        .rename(
                            columns={
                                "code": "code | description",
                                "datasets": "n° datasets",
                            }
                        ),
                        use_container_width=True,
                    )

        except Exception as e:
            st.sidebar.error(e)


if __name__ == "__main__":
    app_config("Home")

    with open("README.md", "r") as readme:
        app_description = "".join([next(readme) for _ in range(29)])
    app_description = app_description.replace("# Eurostat", "# 🇪🇺 Eurostat")
    if os.environ["ENV"] == "demo":
        app_description = app_description.replace(
            "[here](https://eurostat-datawizard.streamlit.app)", "here"
        ).replace(
            "repo", "[repo](https://github.com/teamdigitale/eurostat-datawizard)", 1
        )
    else:
        app_description = app_description.replace(
            "You can play with a (**resource limited**) working version [here](https://eurostat-datawizard.streamlit.app).",
            "",
        ).replace(
            "⚠️ For a better experience, cloning the repo and run it locally is highly suggested! ⚠️",
            "",
        )
    st.markdown(app_description)

    message = st.sidebar.empty()
    message.markdown("💤 A previous indexing is still running.")
    index_helper(message)

    index_describer()

    show_console()  # For debugging
