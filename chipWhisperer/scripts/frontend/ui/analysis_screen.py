import sys
import streamlit as st
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from capture import FIRMWARE_CONFIGS

DEFAULT_CPA_PARAMS = {
    "threshold": 0.1,
}
 
DEFAULT_TVLA_PARAMS = {
    "t_threshold": 4.5,
    "low_hw_max":  12,
    "high_hw_min": 20,
}

def _job_label(job):
    label = FIRMWARE_CONFIGS[job["effect"]]["label"]
    if job["variant"]:
        label += f" › {job['variant']}"
    return f"{label} — {job['chip'].upper()} — trace set #{job['index']}"

def _jobs_from_session():
    jobs = []
    for r in st.session_state.get("results", []):
        p = Path(r["traces_path"])
        index = int(p.stem.replace("traces", ""))
        chip  = p.parent.name
        parts = p.parts
        if parts[-4] == "pip_reg_overwrite" or parts[-4] in (
            v for cfg in FIRMWARE_CONFIGS.values()
            if "variants" in cfg for v in cfg["variants"]
        ):
            variant = parts[-2]   
            effect  = parts[-4]
            variant = parts[-3]
            chip    = parts[-2]
        else:
            effect  = parts[-3]
            variant = None
            chip    = parts[-2]
 
        jobs.append({
            "effect":  effect,
            "variant": variant,
            "chip":    chip,
            "index":   index,
        })
    return jobs


def render():
    st.title("Analysis")

    all_jobs = _jobs_from_session()
    
    if not all_jobs:
        st.warning("No capture results in this session. Run a capture first.")
        if st.button("← Back to capture"):
            st.session_state.phase = "config"
            st.rerun()
        return


    st.write("Select datasets to analyse:")
    selected = []
    with st.container(border=True):
        for job in all_jobs:
            label   = _job_label(job)
            checked = st.checkbox(label, value=True, key=f"job_{label}")
            if checked:
                selected.append(job)


    st.write("Select analyis method(s):")

    with st.container(border=True):
        use_cpa  = st.checkbox("CPA  (Correlation Power Analysis)",  value=True)
        use_tvla = st.checkbox("TVLA (Test Vector Leakage Assessment)", value=True)
 
        cpa_params  = dict(DEFAULT_CPA_PARAMS)
        tvla_params = dict(DEFAULT_TVLA_PARAMS)
 
        if use_cpa:
            st.markdown("**CPA parameters**")
            cpa_params["threshold"] = st.number_input(
                "Correlation threshold",
                min_value=0.0, max_value=1.0,
                value=float(DEFAULT_CPA_PARAMS["threshold"]),
                step=0.01, format="%.3f",
            )
 
        if use_tvla:
            st.markdown("**TVLA parameters**")
            col1, col2, col3 = st.columns(3)
            with col1:
                tvla_params["t_threshold"] = st.number_input(
                    "t-threshold",
                    min_value=0.0, value=float(DEFAULT_TVLA_PARAMS["t_threshold"]),
                    step=0.1, format="%.1f",
                )
            with col2:
                tvla_params["low_hw_max"] = st.number_input(
                    "Low HW max",
                    min_value=0, max_value=32,
                    value=int(DEFAULT_TVLA_PARAMS["low_hw_max"]),
                )
            with col3:
                tvla_params["high_hw_min"] = st.number_input(
                    "High HW min",
                    min_value=0, max_value=32,
                    value=int(DEFAULT_TVLA_PARAMS["high_hw_min"]),
                )

    if not use_cpa and not use_tvla:
        st.warning("Select at least one analysis method.")
 
    run = st.button(
        "▶ Run Analysis",
        disabled=not selected or (not use_cpa and not use_tvla),
    )

    if run:
        with st.spinner("Running analysis…"):
            try:
                results = run_analysis(selected, use_cpa, use_tvla, cpa_params, tvla_params)
                st.session_state.analysis_results = results
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return



