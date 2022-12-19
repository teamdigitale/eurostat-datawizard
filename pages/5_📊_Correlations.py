import io
from functools import partial
from importlib import import_module

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, Normalize
from pingouin import rm_corr

from globals import MAX_VARIABLES_PLOT
from src.utils import trim_code, tuple2str
from widgets.commons import app_config
from widgets.console import session_console
from widgets.dataframe import empty_eurostat_dataframe
from widgets.stateful.number_input import stateful_number_input

sns.set()


def pandas_rm_corr(x, y, subject):
    x, y, subject = (
        pd.Series(x, name="x"),
        pd.Series(y, name="y"),
        pd.Series(subject, name="subject"),
    )
    data = pd.concat([x, y, subject], axis=1)
    return rm_corr(data=data, x="x", y="y", subject="subject").r.squeeze()


def pandas_rm_corr_pval(x, y, subject):
    x, y, subject = (
        pd.Series(x, name="x"),
        pd.Series(y, name="y"),
        pd.Series(subject, name="subject"),
    )
    data = pd.concat([x, y, subject], axis=1)
    return rm_corr(data=data, x="x", y="y", subject="subject").pval.squeeze()


@st.experimental_memo
def compute_correlation(df: pd.DataFrame):
    corr = df.corr(
        method=partial(pandas_rm_corr, subject=df.index.get_level_values("geo"))  # type: ignore
    )
    pval = df.corr(
        method=partial(pandas_rm_corr_pval, subject=df.index.get_level_values("geo"))  # type: ignore
    )
    return corr, pval


def OrBu():
    colors = [
        (1.0, 0.7, 0.0),  # Orange (#cc7a00)
        (1.0, 0.9, 0.5),  # gradient
        (1.0, 1.0, 1.0),  # White
        (0.9, 0.9, 1.0),  # gradient
        (0.0, 0.4, 0.8),  # Blue (#0066cc)
    ]
    return LinearSegmentedColormap.from_list("OrBu", colors)


def plot_heatmap(corr: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(18, 16), dpi=150)
    plt.title("Correlation heatmap")
    ax = sns.heatmap(
        corr,
        annot=True,
        vmin=-1,
        vmax=+1,
        cmap=OrBu(),
        fmt=".2f",
        ax=ax,
    )
    ax.set_facecolor("white")  # Background color (hence, NaN color)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, horizontalalignment="right")
    return fig, ax


if __name__ == "__main__":
    app_config("Correlations")

    stash = empty_eurostat_dataframe()
    try:
        with st.spinner(text="Fetching data"):
            if "history" in st.session_state:
                stash = import_module("pages.3_🛒_Stash").load_stash(
                    st.session_state.history
                )
            else:
                st.warning("No stash found. Select some data to plot.")
    except ValueError as ve:
        st.error(ve)

    if stash.empty:
        st.warning("No stash found. Select some data to plot.")
    else:
        stash = stash.unstack(stash.index.names.difference(["geo", "time"]))  # type: ignore

        # Flags warning
        flags = set(np.unique(stash["flag"].astype(str)))
        flags.remove("nan")
        if flags:
            st.warning(
                f"Found flags: {list(flags)}. Computation will include these datapoints. Remove these flags in the `Data` page if you don't want to use it."
            )

        stash = stash["value"]
        n_variables = len(stash.columns)

        with st.sidebar:
            pval_threshold = stateful_number_input(
                label="Adjust p-value threshold",
                key="_pval_threshold",
                min_value=0.01,
                max_value=1.0,
                value=0.01,
            )

        # Correlations
        if (
            n_variables <= MAX_VARIABLES_PLOT
        ):  # TODO Totally arbitrary threshold, can be inferred?
            not_enough_datapoints = (
                stash.groupby("geo").transform(lambda c: c.count()) < 2
            )
            stash = stash.mask(not_enough_datapoints)
            stash.columns = [
                tuple2str(map(trim_code, i), " • ")
                for i in stash.columns.to_flat_index()
            ]
            scores, pvals = compute_correlation(stash)  # type: ignore
            scores = scores.mask(pvals > pval_threshold)
            f, ax = plot_heatmap(scores)
            with io.BytesIO() as buffer:
                f.savefig(buffer, bbox_inches="tight")
                buffer.seek(0)
                st.image(buffer)
            # st.pyplot(f, dpi=150)  # NOTE pyplot does not render custom dpi
        else:
            st.error(
                f"""
                {n_variables} variables found in `Stash`, plot computation was interrupt to prevent overload. 
                
                Reduce variables up to {MAX_VARIABLES_PLOT}. You can check data size in the `Stash` page, selecting `Wide-format`.
                """
            )

    session_console()
