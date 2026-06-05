import sys
import streamlit as st
from pathlib import Path
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from analysis import run_analysis, save_report, get_reports_dir, get_plots_dir
from plotCorrelation import plot_cpa, plot_tvla
from datetime import datetime
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
        if parts[-4] == "pip_reg_overwrite": 
            effect  = "pip_reg_overwrite"
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

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Configuration")

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

                tvla_mode = st.radio(
                    "TVLA mode",
                    ["Specific (HW-grouped)", "Non-specific (fixed-vs-random)"],
                    horizontal=True,
                )

                tvla_params["mode"] = "specific" if tvla_mode == "Specific (HW-grouped)" else "fixed_vs_random"

                col1, col2, col3 = st.columns(3)
                with col1:
                    tvla_params["t_threshold"] = st.number_input(
                        "t-threshold",
                        min_value=0.0, value=float(DEFAULT_TVLA_PARAMS["t_threshold"]),
                        step=0.1, format="%.1f",
                    )

                if tvla_params["mode"] == "specific":
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
                    report, per_job = run_analysis(
                        selected, use_cpa, use_tvla, cpa_params, tvla_params
                    )
                    
                    st.session_state.analysis_results = {
                        "report":      report,
                        "per_job":     per_job,
                        "cpa_params":  cpa_params,
                        "tvla_params": tvla_params,

                    }
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    return

        ar = st.session_state.get("analysis_results")
        if not ar:
            return
                
        st.write("Report")

        with st.expander("View JSON", expanded=True):
            st.json(ar["report"])

        if "report_filename" not in st.session_state:
            st.session_state.report_filename = f"{ar['report']['device']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        col_name, col_btn = st.columns([3, 1])
        with col_name:
            filename = st.text_input(
                "Filename", 
                key="report_filename",
                label_visibility="collapsed",
                placeholder="report filename (no .json needed)")
            
        with col_btn:
            save =  st.button("Save to disk")
                

        if save:
            stem = filename if filename.endswith(".json") else filename + ".json"
            path = get_reports_dir() / stem
            save_report(path, ar["report"])
            st.caption(f"Saved to `{path}`")

    with col_right:

        if not ar:
            st.info("Results will appear here after running the analysis.")
        else:
            st.subheader("Results")

        saved_cpa_thresh  = ar.get("cpa_params",  DEFAULT_CPA_PARAMS) .get("threshold",   DEFAULT_CPA_PARAMS["threshold"])
        saved_tvla_thresh = ar.get("tvla_params", DEFAULT_TVLA_PARAMS).get("t_threshold", DEFAULT_TVLA_PARAMS["t_threshold"])


        for i, r in enumerate(ar["per_job"]):
            with st.container(border=True):
                st.markdown(f"**{_job_label(r)}**")

                if r.get("cpa_result"):
                    c = r["cpa_result"]
                    detected = "Leakage detected" if c["leakage_detected"] else "No leakage"
                    st.markdown(f"CPA — {detected}")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Peak correlation", c["peak_correlation"])
                    col2.metric("Peak sample",      c["peak_sample"])
                    col3.metric("Traces",           c["n_traces"])

                    if st.toggle("Show CPA plot", key=f"cpa_plot_{i}"):
                        fig = plot_cpa(c, saved_cpa_thresh)
                        if fig:
                            st.pyplot(fig, width='stretch')
                            if st.button("Save CPA plot", key=f"save_cpa_{i}"):
                                plots_dir = get_plots_dir(r["effect"], r["chip"], r["variant"])
                                plots_dir.mkdir(parents=True, exist_ok=True)
                                save_path = plots_dir / f"cpa{r['index']}.png"
                                fig.savefig(save_path, dpi=150, bbox_inches="tight")
                                st.caption(f"Saved to `{save_path}`")
                            plt.close(fig)
                        else:
                                st.caption("No correlation trace available.")
                    

                if r.get("tvla_result"):
                    t = r["tvla_result"]
                    detected = "Leakage detected" if t["leakage_detected"] else "No leakage"
                    st.markdown(f"TVLA — {detected}")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Max |t|",     t["max_abs_t"])
                    col2.metric("Peak sample", t["peak_sample"])
                    col3.metric("Group A / B", f"{t['n_group_a']} / {t['n_group_b']}")

                    if st.toggle("Show TVLA plot", key=f"tvla_plot_{i}"):
                        fig = plot_tvla(t, saved_tvla_thresh)
                        if fig:
                            st.pyplot(fig, width='stretch')
                            if st.button("Save TVLA plot", key=f"save_tvla_{i}"):
                                mode = t.get("tvla_mode", "specific")
                                stem = f"tvla_non_specific{r['index']}" if mode == "fixed_vs_random" else f"tvla_specific{r['index']}"
                                plots_dir = get_plots_dir(r["effect"], r["chip"], r["variant"])
                                plots_dir.mkdir(parents=True, exist_ok=True)
                                save_path = plots_dir / f"{stem}.png"
                                fig.savefig(save_path, dpi=150, bbox_inches="tight")
                                st.caption(f"Saved to `{save_path}`")
                            plt.close(fig)
                        else:
                            st.caption("No t-trace available.")





