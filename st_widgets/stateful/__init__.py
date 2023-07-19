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

from .data_editor import stateful_data_editor
from .multiselect import stateful_multiselect
from .number_input import stateful_number_input
from .selectbox import stateful_selectbox
from .slider import stateful_slider
