import streamlit as st

def render():

    st.title("Configuration")

    st.write("Select effects to test against:")
    mem_rem = st.checkbox("Memory Remnant")
    reg_over = st.checkbox("Register Overwrite")
    pip_reg = st.checkbox("Pipeline Register Overwrite")

    pip_variants = []
    if pip_reg:
        with st.container(horizontal=5):
            st.markdown('<div class="pip-variants">', unsafe_allow_html=True)
            opAxopA = st.checkbox("opAxopA")
            opAxopB = st.checkbox("opAxopB")
            opBxopA = st.checkbox("opBxopA")
            opBxopB = st.checkbox("opBxopB")
            st.markdown("</div>", unsafe_allow_html=True)
            if opAxopA: pip_variants.append("opAxopA")
            if opAxopB: pip_variants.append("opAxopB")
            if opBxopA: pip_variants.append("opBxopA")
            if opBxopB: pip_variants.append("opBxopB")
 


    chip_display = {"STM32F0": "stm32f0", "STM32F3": "stm32f3"}
    chip_label   = st.selectbox("Target Board", list(chip_display.keys()))

    n_traces = st.number_input("Number of traces:", min_value=10, max_value=100000)
    n_samples = st.number_input("Number of samples", min_value=10, max_value=10000)

    start = st.button("Start Capture")

    if start and pip_reg and not pip_variants:
        st.warning("Please select which variant(s) to test for the pipeline register overwrite effect.", )
        start = False

    if start and not (mem_rem or reg_over or pip_reg):
        st.warning("Please select at least one effect to capture.")
        start = False

    if start:
        jobs = []
        jobs = []
        if mem_rem:  jobs.append(("mem_remnant",        None))
        if reg_over: jobs.append(("reg_overwrite",      None))
        for v in pip_variants:
            jobs.append(("pip_reg_overwrite", v))
 
        st.session_state.phase     = "capturing"
        st.session_state.jobs      = jobs
        st.session_state.job_index = 0
        st.session_state.results   = []
        st.session_state.error     = None
        st.session_state.chip      = chip_display[chip_label]
        st.session_state.n_traces  = int(n_traces)
        st.session_state.n_samples = int(n_samples)
        st.session_state.progress  = {}
        st.rerun()
