from importlib import import_module

import plotly.express as px
import streamlit as st
from plotly.subplots import make_subplots

from widgets.console import show_console
from widgets.dataframe import empty_eurostat_dataframe
from widgets.session import app_config


def tuple2str(tuple, sep: str = " "):
    return sep.join([v for v in tuple if isinstance(v, str)])


def trim_code(s):
    return s.split(" | ")[1] if isinstance(s, str) else None


def plot_column_idx(df, i):
    fig = px.line(
        color=df.index.get_level_values("geo"),
        x=df.index.get_level_values("time"),
        y=df["value"].iloc[:, i],
        hover_name=df["flag"].iloc[:, i].fillna(""),
        labels=dict(x="Time", y="Value", geo="Country"),
    )
    return fig


if __name__ == "__main__":
    app_config("Viz")

    stash = empty_eurostat_dataframe()
    try:
        with st.spinner(text="Fetching data"):
            if st.session_state.history.keys():
                stash = import_module("pages.3_Stash").load_stash(
                    st.session_state.history
                )
    except ValueError as ve:
        st.error(ve)

    if not stash.empty:
        stash = stash.unstack(stash.index.names.difference(["geo", "time"]))  # type: ignore
        n_variables = len(stash["value"].columns)

        if n_variables < 10:
            sep = " • "
            fig = make_subplots(
                rows=n_variables,
                cols=1,
                shared_xaxes=True,
                subplot_titles=[
                    tuple2str(map(trim_code, stash.columns[i][2:]), sep)  # type: ignore
                    for i in range(n_variables)
                ],
            )
            for i in range(n_variables):
                fig.add_traces(
                    plot_column_idx(stash, i)
                    .update_traces(dict(showlegend=True if i < 1 else False))
                    .data,
                    rows=i + 1,
                    cols=1,
                )
            fig.update_annotations(font=dict(size=10))
            fig.update_layout(
                legend=dict(orientation="h", y=-0.2),
                height=1000,
                width=800,
                title_text="Time Series comparison",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(
                f"""
                {n_variables} variables found in `Stash`, cannot plot. 
                
                Reduce the stash variables by deselecting data in the `Data` page or removing dataset altogether in the `Stash` page.
                """
            )

    show_console()  # For debugging
