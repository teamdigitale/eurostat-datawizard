import os
from threading import Lock

import streamlit as st

from globals import VARS_INDEX_PATH, get_last_index_update
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
                # In order to load newly updated index
                st.experimental_memo.clear()
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
                    - Indexed dataset: {len(toc)}
                    - Indexed unique variables: {len(codelist)}

                    Most used variables:
                    """
                    )
                    st.sidebar.dataframe(
                        codelist.apply(len)
                        .sort_values(ascending=False)
                        .reset_index()
                        .query("datasets > 1")
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


def show_cache_uploader():
    # NOTE it was simpler upload directly the varsname but choosen to not do, in order
    # to mitigate security problems in uploading a `pickled` file.
    ext = "sqlite"
    cachename = f"cache/sdmx.{ext}"
    # NOTE Available only at first run, without a cache
    if not os.path.exists(cachename):
        cache = st.sidebar.file_uploader("Create index or preload a cache first", ext)
        if cache:
            os.makedirs(os.path.dirname(cachename), exist_ok=True)
            if os.path.exists(VARS_INDEX_PATH):
                os.remove(VARS_INDEX_PATH)
            with open(cachename, "wb") as f:
                f.write(cache.getbuffer())


if __name__ == "__main__":
    app_config("Home")

    with open("README.md", "r") as readme:
        app_description = "".join([next(readme) for _ in range(24)])
    app_description = app_description.replace("# Eurostat", "# 🇪🇺 Eurostat")
    app_description = app_description.replace(
        "[here](https://eurostat-datawizard.streamlit.app)", "here"
    ).replace("repo", "[repo](https://github.com/teamdigitale/eurostat-datawizard)", 1)
    st.markdown(app_description)

    message = st.sidebar.empty()
    message.markdown("💤 A previous indexing is still running.")
    index_helper(message)

    index_describer()

    show_cache_uploader()

    show_console()  # For debugging
