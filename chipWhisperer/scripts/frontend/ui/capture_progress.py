import threading
import time
import sys
import streamlit as st
import chipwhisperer as cw
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from capture import FIRMWARE_CONFIGS, run_capture

def _job_key(firmware_key, variant):
    return f"{firmware_key}/{variant}" if variant else firmware_key
 
 
def _job_label(firmware_key, variant):
    label = FIRMWARE_CONFIGS[firmware_key]["label"]
    return f"{label} › {variant}" if variant else label

def _run_all_jobs(jobs, chip, n_traces, n_samples, progress_dict, results_list):
 
    for idx, (fw_key, variant) in enumerate(jobs):
        progress_dict["job_index"] = idx
        jk = _job_key(fw_key, variant)
 
        def cb(captured, skipped, total, _jk=jk):
            progress_dict[_jk] = {
                "captured": captured,
                "skipped":  skipped,
                "total":    total,
            }
 
        try:
            result = run_capture(fw_key, chip, n_traces, n_samples, variant, progress_cb=cb)
            result["label"] = _job_label(fw_key, variant)
            results_list.append(result)
        except Exception:
            progress_dict["error"] = traceback.format_exc()
            return
 
    progress_dict["done"] = True


def _thread_is_running():
    t = st.session_state.get("thread")
    return t is not None and t.is_alive()


def render():
    st.title("Capturing…")

    ### Error state
    if st.session_state.get("capture_error"):
        st.error("Capture failed.")
        st.code(st.session_state.capture_error, language="python")
        if st.button("← Back to config"):
            st.session_state.capture_error  = None
            st.session_state.thread_started = False
            st.session_state.phase          = "config"
            st.rerun()
        return
    
    if not _thread_is_running():
        if not st.session_state.get("progress_dict"):
            # snapshot everything needed into plain Python objects
            jobs      = list(st.session_state.jobs)
            chip      = st.session_state.chip
            n_traces  = st.session_state.n_traces
            n_samples = st.session_state.n_samples

            # shared mutable containers the thread writes into
            progress_dict = {}
            results_list  = []
            st.session_state.progress_dict = progress_dict
            st.session_state.results_list  = results_list
            st.session_state.thread_started = True


            t = threading.Thread(
                target=_run_all_jobs,
                args=(jobs, chip, n_traces, n_samples, progress_dict, results_list),
                daemon=True,
            )
            t.start()
            st.session_state.thread = t
        
    progress_dict = st.session_state.progress_dict
    results_list  = st.session_state.results_list
    jobs          = st.session_state.jobs
    n_traces      = st.session_state.n_traces

    if "error" in progress_dict:
        st.session_state.capture_error = progress_dict["error"]
        st.session_state.progress_dict = {}
        st.rerun()
        return


    ### Progress bar
    
    current_idx = progress_dict.get("job_index", 0)
    st.write(f"Job {min(current_idx + 1, len(jobs))} of {len(jobs)}")
 
    for idx, (fw_key, variant) in enumerate(jobs):
        jk    = _job_key(fw_key, variant)
        label = _job_label(fw_key, variant)
        p     = progress_dict.get(jk, {"captured": 0, "skipped": 0, "total": n_traces})
 
        captured  = p["captured"]
        skipped   = p["skipped"]
        total     = p["total"]
        done_frac = captured / total if total else 0.0
 
        if idx < current_idx or done_frac >= 1.0:
            state = "✔ DONE"
        elif idx == current_idx:
            state = "● RUNNING"
        else:
            state = "○ QUEUED"
 
        st.markdown(f"**{label}** — {state}")
        st.progress(done_frac)
 
        col1, col2, col3 = st.columns(3)
        col1.metric("Captured",  captured)
        col2.metric("Skipped",   skipped)
        col3.metric("Remaining", max(total - captured - skipped, 0))

    if progress_dict.get("done"):
        st.session_state.results       = results_list
        st.session_state.progress_dict = {}
        st.session_state.phase         = "done"
        st.rerun()
        return


 
    time.sleep(0.4)
    st.rerun()

