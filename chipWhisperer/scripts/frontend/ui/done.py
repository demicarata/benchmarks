import streamlit as st

def _reset():
    for k in ("phase", "jobs", "job_index", "progress", "results", "thread", "error",
              "chip", "n_traces", "n_samples"):
        st.session_state.pop(k, None)

def render():
    st.title("Capture Complete")
 
    if st.session_state.get("error"):
        st.error(f"An error occurred:\n\n{st.session_state.error}")
    else:
        st.success(f"All {len(st.session_state.results)} job(s) completed successfully.")
 
    st.write("### Results")
 
    for r in st.session_state.results:
        with st.container(border=True):
            st.markdown(f"**{r['label']}**")
 
            col1, col2 = st.columns(2)
            col1.metric("Traces captured", r["captured"])
            col2.metric("Traces skipped",  r["skipped"])
 
            st.code(r["traces_path"], language=None)
            st.code(r["shares_path"], language=None)
 
    st.markdown("---")
    col_a, col_b = st.columns(2)
   
    with col_a:
        if st.button("New Capture"):
            _reset()
            st.rerun()
 
    with col_b:
        if st.button("Go to Analysis →"):
            st.session_state.analysis_results = None
            st.session_state.phase = "analysis"
            st.rerun()


