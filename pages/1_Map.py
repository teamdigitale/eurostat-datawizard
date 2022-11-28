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
from sklearn.manifold import TSNE
import plotly.express as px


@st.experimental_memo
def build_labeled_toc() -> pd.DataFrame:
    # Datasets starts with a code that identify its theme like:
    # aact_ali01 (Agricultural labour input statistics: absolute...) ->	aact (Economic accounts for agriculture)
    toc, themes = load_table_of_contents()
    toc = toc.to_frame()
    toc["code_theme"] = toc.index.str.split(r"-|_", regex=True).str[0]
    toc = toc.merge(
        themes.reset_index().rename(
            columns={"code": "code_theme", "title": "title_theme"}
        ),
        how="left",
    )
    return toc


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


if __name__ == "__main__":
    app_config("Map")

    st.header("Datasets map")
    # if os.environ["ENV"] == "streamlit":
    #     st.error(
    #         "Datasets clustering is too expensive for streamlit cloud limited resources. You can compute this offline, cloning the repo."
    #     )
    # else:
    if not get_last_index_update():
        st.warning("Create an index first!")
    else:
        labeled_toc = build_labeled_toc()
        adj = build_adjacency_matrix()
        datasets2d = cluster_datasets(adj, labeled_toc)
        margin = 5
        fig = px.scatter(
            datasets2d.rename(columns={"title_theme": "Themes"}),
            x="1st",
            y="2nd",
            color="Themes",
            hover_data=["code", "title"],
            range_x=(
                datasets2d["1st"].min() - margin,
                datasets2d["1st"].max() + margin,
            ),
            range_y=(
                datasets2d["2nd"].min() - margin,
                datasets2d["2nd"].max() + margin,
            ),
            height=1300,
        )
        fig.update_layout(legend=dict(orientation="h"))
        st.plotly_chart(figure_or_data=fig, use_container_width=True)

    show_console()  # For debugging
