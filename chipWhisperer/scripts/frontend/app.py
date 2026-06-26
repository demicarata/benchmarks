import streamlit as st
import sys
from pathlib import Path
from ui import capture_progress, config, done, analysis_screen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(
    page_title="SCARAB",
    layout="wide",
    page_icon='scarab.png'
)

try:
    import chipwhisperer 
except ImportError:
    st.error(
        "ChipWhisperer is not installed or could not be imported. "
        "Install it with `pip install chipwhisperer` and restart the app."
    )
    st.stop()


st.session_state.setdefault("phase",     "config")
st.session_state.setdefault("jobs",      [])
st.session_state.setdefault("job_index", 0)
st.session_state.setdefault("progress",  {})
st.session_state.setdefault("results",   [])
st.session_state.setdefault("error",     None)

phase = st.session_state.phase
 
if phase == "config":
    config.render()
elif phase == "capturing":
    capture_progress.render()
elif phase == "done":
    done.render()
elif phase == "analysis":
    analysis_screen.render()
