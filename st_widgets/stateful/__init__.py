""" 
Goal of this widget collection is to effortlessy use widgets that need stateful interaction,
like:
- preserving a value while navigating the app and changing pages,
- variables set via session state are write-protected from streamlit, manual set avoid collisions with session state API
  and prevent errors like: 
  StreamlitAPIException st.session_state.<var> cannot be modified after the widget with key <var> is instantiated.
- solving clicking twice to make a setting _stick_:
  https://docs.streamlit.io/knowledge-base/using-streamlit/widget-updating-session-state
"""


def _on_change_factory(_state_function):
    """A wrapper to allow user-defined `function` but also update widget state.

    When called, it always fires `_state_function` with `_session`,`_key` args, needed to preserve widget state.
    """

    # Inspiration: https://www.artima.com/weblogs/viewpost.jsp?thread=240845#decorator-functions-with-decorator-arguments
    def decorator(function):
        def wrapper(*args, **kwargs):
            _state_function()
            return function(*args, **kwargs) if function else None

        return wrapper

    return decorator
