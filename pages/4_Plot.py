from importlib import import_module

import plotly.express as px
import streamlit as st
from plotly.subplots import make_subplots

from globals import MAX_TIMESERIES_PLOT
from widgets.console import show_console
from widgets.dataframe import empty_eurostat_dataframe
from widgets.session import app_config
from widgets.stateful.number_input import stateful_number_input

session = st.session_state


def tuple2str(tuple, sep: str = " "):
    return sep.join([v for v in tuple if isinstance(v, str)])


def trim_code(s):
    code_title = s.split(" | ")
    # Reuse code if title is missing
    title = code_title[1] if len(code_title) > 1 else code_title[0]
    return title if isinstance(s, str) else None


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
    app_config("Plot")

    stash = empty_eurostat_dataframe()
    try:
        with st.spinner(text="Fetching data"):
            if "history" in st.session_state:
                stash = import_module("pages.3_Stash").load_stash(
                    st.session_state.history
                )
            else:
                st.warning("No stash found. Select some data to plot.")
    except ValueError as ve:
        st.error(ve)

    with st.sidebar:
        plot_height = stateful_number_input(
            "Adjust plot height [px]", value=500, step=100, key="plot_height"
        )

    if not stash.empty:
        stash = stash.unstack(stash.index.names.difference(["geo", "time"]))  # type: ignore
        n_variables = len(stash["value"].columns)

        if (
            n_variables < MAX_TIMESERIES_PLOT
        ):  # TODO Totally arbitrary threshold, can be inferred?
            sep = " • "
            fig = make_subplots(
                rows=n_variables,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.15 / n_variables,
                subplot_titles=[
                    tuple2str(map(trim_code, stash.columns[i][1:]), sep)  # type: ignore
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
                legend=dict(orientation="h"),
                height=plot_height,
                title_text="Stacked timeseries",
            )
            # Keep zoom/legend at reload: https://discuss.streamlit.io/t/cant-enter-values-without-updating-a-plotly-figure/28066
            fig.update_layout({"uirevision": "foo"}, overwrite=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(
                f"""
                {n_variables} variables found in `Stash`, plot computation was interrupt to prevent overload. 
                
                Reduce variables up to {MAX_TIMESERIES_PLOT}. You can check data size in the `Stash` page, selecting `Wide-format`.
                """
            )

    show_console()  # For debugging
