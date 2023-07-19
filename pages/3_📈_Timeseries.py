import plotly.express as px
import streamlit as st
from plotly.subplots import make_subplots

from datawizard.utils import trim_code, tuple2str
from globals import MAX_VARIABLES_PLOT
from st_widgets.commons import app_config, load_stash, read_stash_from_history
from st_widgets.console import session_console
from st_widgets.dataframe import empty_eurostat_dataframe
from st_widgets.stateful import stateful_number_input

session = st.session_state
app_config("Timeseries")


def plot_column_idx(df, i, annotate=False):
    fig = px.line(
        color=df.index.get_level_values("geo"),
        x=df.index.get_level_values("time"),
        y=df["value"].iloc[:, i],
        hover_name=df["flag"].iloc[:, i].fillna(""),
        labels=dict(x="Time", y="Value", geo="Country"),
        markers=True,
        text=df.index.get_level_values("geo") if annotate else None,
    )
    if annotation:
        fig.update_traces(textposition="middle right")
    return fig


if __name__ == "__main__":
    stash = empty_eurostat_dataframe()
    try:
        with st.spinner(text="Fetching data"):
            if "history" in st.session_state:
                stash = load_stash(read_stash_from_history(st.session_state.history))
            else:
                st.warning("No stash found. Select some data to plot.")
    except ValueError as ve:
        st.error(ve)

    with st.sidebar:
        plot_height = stateful_number_input(
            "Adjust plot height [px]", value=500, step=100, key="_plot_height"
        )
        annotation = st.checkbox("Annotation")

    if stash.empty:
        st.warning("No stash found. Select some data to plot.")
    else:
        stash = stash.unstack(stash.index.names.difference(["geo", "time"]))  # type: ignore
        n_variables = len(stash["value"].columns)
        if (
            n_variables <= MAX_VARIABLES_PLOT
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
            # Subplot titles size: https://community.plotly.com/t/setting-subplot-title-font-sizes/46612
            fig.update_annotations(font=dict(size=12))
            # Cycle stash columns by flag, value pairs
            for i in range(n_variables):
                fig.add_traces(
                    plot_column_idx(stash, i, annotate=annotation)
                    .update_traces(dict(showlegend=True if i < 1 else False))
                    .data,
                    rows=i + 1,
                    cols=1,
                )
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
                
                Reduce variables up to {MAX_VARIABLES_PLOT}. You can check data size in the `Stash` page, selecting `Wide-format`.
                """
            )

    session_console()
