from functools import partial
from importlib import import_module

import numpy as np
import pandas as pd
import streamlit as st
from pingouin import rm_corr

from widgets.console import show_console
from widgets.dataframe import empty_eurostat_dataframe
from widgets.session import app_config
import plotly.express as px
from matplotlib.colors import LinearSegmentedColormap
from src.utils import tuple2str
import matplotlib.pyplot as plt
import seaborn as sns

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


def compute(df: pd.DataFrame):
    corr = df.corr(
        method=partial(pandas_rm_corr, subject=df.index.get_level_values("geo"))  # type: ignore
    )
    pval = df.corr(
        method=partial(pandas_rm_corr_pval, subject=df.index.get_level_values("geo"))  # type: ignore
    )
    return corr, pval


def RdWtBu():
    p = [-1, -0.5, 0.5, 1]
    f = lambda x: np.interp(x, p, [0, 0.5, 0.5, 1])
    return LinearSegmentedColormap.from_list(
        "RdWtBu", list(zip(np.linspace(0, 1), plt.cm.RdBu(f(np.linspace(-1, +1)))))  # type: ignore
    )


def plot(corr, pval, cmap):
    fig, ax = plt.subplots(figsize=(18, 16))
    ax = sns.heatmap(
        corr.mask(pval > 0.05),
        annot=True,
        vmin=-1,
        vmax=+1,
        cmap=cmap,
        fmt=".2f",
        ax=ax,
    )
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

        # Correlations
        MAX_CORRELATION_PLOT = 100
        if (
            n_variables < MAX_CORRELATION_PLOT
        ):  # TODO Totally arbitrary threshold, can be inferred?
            not_enough_datapoints = stash.groupby("geo").count() < 3
            # stash = stash.mask(not_enough_datapoints)
            stash.columns = [tuple2str(i, " • ") for i in stash.columns.to_flat_index()]
            scores, pvals = compute(stash)  # type: ignore
            f, ax = plot(scores, pvals, RdWtBu())
            st.pyplot(f)
        else:
            st.error(
                f"""
                {n_variables} variables found in `Stash`, plot computation was interrupt to prevent overload. 
                
                Reduce variables up to {MAX_CORRELATION_PLOT}. You can check data size in the `Stash` page, selecting `Wide-format`.
                """
            )

    show_console()
