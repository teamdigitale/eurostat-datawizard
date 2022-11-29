import os
import pandas as pd
import streamlit as st
from widgets.console import show_console
from widgets.session import app_config
from widgets.index import (
    get_last_index_update,
    load_codelist_reverse_index,
    load_table_of_contents,
)
from widgets.download import download_dataframe_button
from sklearn.manifold import TSNE
import plotly.express as px


@st.experimental_memo
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


@st.experimental_memo
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


@st.experimental_memo
def cluster_datasets(adjacency: pd.DataFrame, toc: pd.DataFrame) -> pd.DataFrame:
    # Project datasets into 2D space
    tsne = TSNE(n_components=2, learning_rate="auto", metric="cosine", init="pca")
    xy = pd.DataFrame(
        tsne.fit_transform(adjacency), index=adjacency.index, columns=["1st", "2nd"]
    )
    xy.index.name = "code"
    # Join datasets with label
    return xy.join(toc).reset_index()


def show_clustering(data: pd.DataFrame, margin: int = 5):
    fig = px.scatter(
        data.rename(columns={"title_theme": "Themes"}),
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
        height=1300,
    )
    fig.update_layout(legend=dict(orientation="h"))
    st.plotly_chart(figure_or_data=fig, use_container_width=True)


if __name__ == "__main__":
    app_config("Map")

    st.header("Datasets map")
    if os.environ["ENV"] == "streamlit":
        dataset2d_path = "cache/clustermap.csv.gz"
        if not os.path.exists(dataset2d_path):
            st.error(
                "Datasets clustering is too expensive for Streamlit Cloud limited resources. You can compute this offline, cloning the repo."
            )
            buffer = st.file_uploader("Load clustering offline results", "gz")
            if buffer:
                with open(dataset2d_path, "wb") as f:
                    f.write(buffer.getbuffer())
                    st.experimental_rerun()
        else:
            show_clustering(pd.read_csv(dataset2d_path))
    else:
        if not get_last_index_update():
            st.warning("Create an index first!")
        else:
            labeled_toc = build_labeled_toc()
            adj = build_adjacency_matrix()
            datasets2d = cluster_datasets(adj, labeled_toc)
            show_clustering(datasets2d)
            download_dataframe_button(datasets2d, filename_prefix="clustermap")

    show_console()  # For debugging
