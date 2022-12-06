from importlib import import_module
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from plotly.graph_objects import Figure
from sklearn.manifold import TSNE
from streamlit_plotly_events import plotly_events
from globals import CLUSTERING_PATH, get_last_index_update, get_last_clustering_update
from widgets.console import show_console
from widgets.download import download_dataframe_button
from widgets.index import (
    load_codelist_reverse_index,
    load_table_of_contents,
)
from widgets.session import app_config
from widgets.stateful import stateful_selectbox


session = st.session_state


def build_labeled_toc() -> pd.DataFrame:
    # Datasets starts with a code that identify its theme like:
    # aact_ali01 (Agricultural labour input statistics: absolute...) ->	aact (Economic accounts for agriculture)
    # Here, a full-join is created and them filtered the shorter match to find the generic theme of every dataset.
    toc, themes = load_table_of_contents()
    a, b = toc.reset_index(), themes.reset_index()
    a["_join"], b["_join"] = 1, 1
    ab = a.merge(b, on="_join", suffixes=("", "_theme")).drop(columns="_join")
    ab["match"] = ab.apply(lambda x: x["code"].find(x["code_theme"]), axis=1).ge(0)
    ab = ab[ab.match].drop(columns=["code_theme", "match"])
    ab = ab.groupby(
        "code"
    ).first()  # Because of ordering, this is the shorter theme matching
    return ab


def build_adjacency_matrix() -> pd.DataFrame:
    # Reverse variable index (var -> List(dataset)) can build an adjacency matrix to
    # describe a dataset by the variable used by it.
    codelist = load_codelist_reverse_index()
    adj = pd.get_dummies(codelist.explode())
    adj = adj.groupby("code").any()
    adj = adj.T  # Orient datasets as records and variables as features
    adj = adj.loc[
        :, adj.sum() > 1
    ]  # Remove dataset unique features to speed-up clustering
    return adj


@st.experimental_memo(persist="disk")
def cluster_datasets() -> pd.DataFrame:
    toc = build_labeled_toc()
    adj = build_adjacency_matrix()
    # Project datasets into 2D space
    tsne = TSNE(n_components=2, learning_rate="auto", metric="cosine", init="pca")
    xy = pd.DataFrame(tsne.fit_transform(adj), index=adj.index, columns=["1st", "2nd"])
    xy.index.name = "code"
    # Join datasets with label
    return xy.join(toc).reset_index()


@st.experimental_memo(persist="disk")
def plot_clustering(
    data: pd.DataFrame, mark: str | None = None, margin: int = 5
) -> Figure:
    data = data.rename(columns={"title_theme": "Themes"})
    fig = px.scatter(
        data,
        x="1st",
        y="2nd",
        color="Themes",
        hover_data=["code", "title"],
        range_x=(
            data["1st"].min() - margin,
            data["1st"].max() + margin,
        ),
        range_y=(
            data["2nd"].min() - margin,
            data["2nd"].max() + margin,
        ),
        category_orders={"Themes": sorted(data["Themes"].astype(str).unique())},
    )
    if mark:
        fig.add_traces(
            px.scatter(
                data[data.code == mark],
                x="1st",
                y="2nd",
                color="Themes",
                hover_data=["code", "title"],
            )
            .update_traces(
                marker=dict(
                    size=30, symbol="x-open-dot", color="red", line=dict(width=3)
                ),
            )
            .data
        )
    fig = fig.update_layout(legend=dict(orientation="h"))
    # Keep zoom/legend at reload: https://discuss.streamlit.io/t/cant-enter-values-without-updating-a-plotly-figure/28066
    fig = fig.update_layout({"uirevision": "foo"}, overwrite=True)
    return fig


@st.experimental_memo
def coordinates_as_index(data: pd.DataFrame) -> pd.DataFrame:
    return data.set_index(["1st", "2nd"]).sort_index()


def show_upload_button():
    buffer = st.file_uploader("Load clustering offline results", "gz")
    if buffer:
        with open(CLUSTERING_PATH, "wb") as f:
            f.write(buffer.getbuffer())
            st.experimental_rerun()


if __name__ == "__main__":
    app_config("Map")

    st.header("Datasets map")
    st.markdown(
        """Each datapoint is an Eurostat dataset. Closer the datasets, more the variable shared among them."""
    )

    if "map_selection" not in session:
        session["map_selection"] = pd.DataFrame(columns=["code", "title"])

    if os.environ["ENV"] == "streamlit" and not get_last_clustering_update():
        st.error(
            "Datasets clustering is too expensive for Streamlit Cloud limited resources. You can compute this offline, cloning the repo."
        )
        show_upload_button()
        # NOTE When a new index is computed, CLUSTERING_PATH is also removed and enable again this branch.
    else:
        if not get_last_index_update():
            st.warning("Create an index first!")
        else:
            # List datasets
            toc, _ = load_table_of_contents()
            datasets = import_module("pages.2_Data").build_toc_list(toc)
            mark = stateful_selectbox(
                "Mark a dataset", datasets, position=st.sidebar, key="pinpoint"
            )

            datasets2d = (
                pd.read_csv(CLUSTERING_PATH)
                if os.environ["ENV"] == "streamlit"
                else cluster_datasets()
            )

            selection = plotly_events(
                plot_clustering(
                    datasets2d,
                    mark=mark.split(" | ")[0]
                    if mark and mark != "Scroll options or start typing"
                    else None,
                ),
                click_event=True,
                select_event=True,
                # use_container_width=True,  # Not supported by plotly_events
                override_height=1300,
                override_width="100%",
            )
            if selection:
                selection = [(s["x"], s["y"]) for s in selection]
                selection = coordinates_as_index(datasets2d).loc[selection]
                selection = selection.drop(columns="title_theme").reset_index(drop=True)
                session["map_selection"] = selection

            st.sidebar.dataframe(
                session["map_selection"],
                use_container_width=True,
            )

            download_dataframe_button(datasets2d, filename_prefix="clustermap")

    show_console()  # For debugging
