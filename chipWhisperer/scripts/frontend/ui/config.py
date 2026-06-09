import streamlit as st
from pathlib import Path
import sys
from collections import defaultdict
 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
 
from analysis import discover_available_jobs, get_data_dir
from capture import FIRMWARE_CONFIGS, PIP_REG_VARIANTS


def _job_display(job):
    label = FIRMWARE_CONFIGS[job["effect"]]["label"]
    if job["variant"]:
        label += f" / {job['variant']}"
    return f"{label}  —  {job['chip'].upper()}  —  trace set #{job['index']}"


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
            for v in PIP_REG_VARIANTS:
                if st.checkbox(v):
                    pip_variants.append(v)
            st.markdown("</div>", unsafe_allow_html=True)
 

    chip_display = {"STM32F0": "stm32f0", "STM32F3": "stm32f3"}
    chip_label   = st.selectbox("Target Board", list(chip_display.keys()))

    n_traces = st.number_input("Number of traces:", min_value=10, max_value=100000, value=1000)
    n_samples = st.number_input("Number of samples", min_value=10, max_value=10000, value=100)

    use_fixed = st.checkbox(
    "Interleave fixed-input traces",
    help="Required for non-specific (fixed-vs-random) TVLA. Uses an all-zero fixed payload interleaved 50/50 with random traces. Will double the amount of traces, and therefore the time.")

    start = st.button("Start Capture")

    if start and pip_reg and not pip_variants:
        st.warning("Please select which variant(s) to test for the pipeline register overwrite effect.", )
        start = False

    if start and not (mem_rem or reg_over or pip_reg):
        st.warning("Please select at least one effect to capture.")
        start = False

    if start:
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
        st.session_state.use_fixed = use_fixed
        st.session_state.progress  = {}
        print(f"DEBUG storing use_fixed={use_fixed}")
        st.rerun()

######### Existing traces

    st.divider()
    st.subheader("Use Existing Traces")
 
    all_jobs = discover_available_jobs()
 
    if not all_jobs:
        st.caption("No captured data found on disk.")
    else:
        EFFECT_DISPLAY = {
            "mem_remnant":       "Memory Remnant",
            "reg_overwrite":     "Register Overwrite",
            "pip_reg_overwrite": "Pipeline Register Overwrite",
        }

        EFFECT_ORDER = ["mem_remnant", "reg_overwrite", "pip_reg_overwrite"]

        grouped = defaultdict(lambda: defaultdict(list))
        for job in all_jobs:
            grouped[job["chip"].upper()][job["effect"]].append(job)

        selected = []

        for chip, effects in sorted(grouped.items()):
            n = sum(len(j) for j in effects.values())
            st.markdown(
                f'<p class="chip-heading">{chip}'
                f'<span class="chip-count">{n} trace(s)</span></p>',
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                for effect in EFFECT_ORDER:
                    if effect not in effects:
                        continue
                    jobs = effects[effect]
                    label = EFFECT_DISPLAY.get(effect, effect)
                    st.markdown(
                        f'<p class="effect-heading">{label}</p>',
                        unsafe_allow_html=True,
                    )
                    for job in jobs:
                        display = _job_display(job)
                        checked = st.checkbox(
                            display, value=False, key=f"existing_{display}"
                        )
                        if checked:
                            selected.append(job)
                    st.divider()
 
        load = st.button("Load Selected for Analysis", disabled=not selected)
 
        if load:
            results = []
            for job in selected:
                data_dir    = get_data_dir(job["effect"], job["chip"], job["variant"])
                traces_path = data_dir / f"traces{job['index']}.npy"
                shares_path = data_dir / f"shares{job['index']}.npy"
                results.append({
                    "traces_path": str(traces_path),
                    "shares_path": str(shares_path),
                })
 
            st.session_state.results = results
            st.session_state.phase   = "analysis"
            st.rerun()

