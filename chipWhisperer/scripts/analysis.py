import numpy as np
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

_SCRIPTS = Path(__file__).resolve().parent
_DATA    = _SCRIPTS.parent.parent / "data"


from cpa import correlate_with_traces, hw
from tvla import tvla_specific, tvla_non_specific
from helpers import select_option, select_index

EFFECTS = [
    "mem_remnant",
    "reg_overwrite",
    "pip_reg_overwrite",
]

PIP_REG_VARIANTS = ["opA1xopA2", "opA1xopB2", "opB1xopA2", "opB1xopB2", "opA1xopA3", "opA1xopB3", "opB1xopA3", "opB1xopB3"]

CHIP_OPTIONS     = ["stm32f3", "stm32f0"]
 
EFFECT_COLUMN = {
    # which column of shares[:,?] is the hypothesis variable for each effect
    "mem_remnant":       2,   # secret = x0 XOR x1
    "reg_overwrite":     2,   # secret
    "pip_reg_overwrite": 2,   # secret
}
 
DEFAULT_CPA_PARAMS = {
    "threshold": 0.1,
}
 
DEFAULT_TVLA_PARAMS = {
    "t_threshold": 4.5,
    "low_hw_max":  12,
    "high_hw_min": 20,
}


# ---- IO and folders

def get_reports_dir():
    path = _SCRIPTS.parent.parent / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path
 
def get_data_dir(effect, chip, variant=None):
    if variant:
        return _DATA / effect / variant / chip
    return _DATA / effect / chip

def get_plots_dir(effect, chip, variant=None):
    base = _SCRIPTS.parent.parent / "plots"
    if variant:
        return base / effect / variant / chip
    return base / effect / chip

def find_report(chip, index):
    path = get_reports_dir() / f"{chip}_{index}.json"
    return path if path.exists() else None
 
def next_report_path(chip, index):
    base = get_reports_dir() / f"{chip}_{index}.json"
    if not base.exists():
        return base
    n = 1
    while True:
        path = get_reports_dir / f"{chip}_{index}_{n}.json"
        if not path.exists():
            return path
        n += 1

def load_report(path):
    with open(path, "r") as f:
        return json.load(f)
    
def save_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

# ---- Analysis ----

def run_cpa(effect, shares, traces, params):
    col = EFFECT_COLUMN[effect]
    values = shares[:, col]
    hypothesis = hw(values)
    corr = correlate_with_traces(hypothesis, traces)

    max_abs  = float(np.max(np.abs(corr)))
    peak_idx = int(np.argmax(np.abs(corr)))
 
    return {
        "leakage_detected": max_abs >= params["threshold"],
        "n_traces":         len(traces),
        "peak_correlation": round(max_abs, 4),
        "peak_sample":      peak_idx,
        "threshold":        params["threshold"],
        "correlations":     corr.tolist(),
    }


def run_tvla(effect, shares, traces, params, data_dir, index):
    mode = params.get("mode", "specific")

    if mode == "fixed_vs_random":
        fixed_path = data_dir / f"fixed{index}.npy"
        if not fixed_path.exists():
            raise FileNotFoundError(
                f"Non-specific TVLA selected but no fixed-input data found for trace set #{index}. "
                f"Re-capture with 'Interleave fixed-input traces' enabled."
            )
        is_fixed = np.load(fixed_path)
        t_trace, n_a, n_b = tvla_non_specific(traces, is_fixed)
        group_a_label, group_b_label = "fixed", "random"
    else:
        col    = EFFECT_COLUMN[effect]
        values = shares[:, col]
        labels = hw(values)
        t_trace, n_a, n_b = tvla_specific(traces, labels, params["low_hw_max"], params["high_hw_min"])
        group_a_label = f"HW <= {params['low_hw_max']}"
        group_b_label = f"HW >= {params['high_hw_min']}"
 
    max_abs_t   = float(np.max(np.abs(t_trace)))
    peak_sample = int(np.argmax(np.abs(t_trace)))
 
    return {
        "tvla_mode":        mode,
        "leakage_detected": max_abs_t >= params["t_threshold"],
        "n_traces":         len(traces),
        "n_group_a":        n_a,
        "n_group_b":        n_b,
        "group_a":          group_a_label,
        "group_b":          group_b_label,
        "max_abs_t":        round(max_abs_t, 4),
        "peak_sample":      peak_sample,
        "t_threshold":      params["t_threshold"],
        "t_trace":          t_trace.tolist(),
    }

def _report_entry(result):
    if result is None:
        return None
    return {k: v for k, v in result.items() if k not in ("correlations", "t_trace")}

def is_already_analysed(report, effect, variant=None):
    """Check whether the given effect (and variant) has already been analysed."""
    effect_data = report["effects"].get(effect, {})
    if effect == "pip_reg_overwrite":
        variant_data = effect_data.get(variant, {})
        return variant_data.get("cpa") != "not_tested" or variant_data.get("tvla") != "not_tested"
    return effect_data.get("cpa") != "not_tested" or effect_data.get("tvla") != "not_tested"

def discover_available_jobs():
    jobs = []
    if not _DATA.exists():
        return jobs
 
    for effect in EFFECTS:
        effect_dir = _DATA / effect
        if not effect_dir.exists():
            continue
 
        if effect == "pip_reg_overwrite":
            for variant in PIP_REG_VARIANTS:
                variant_dir = effect_dir / variant
                if not variant_dir.exists():
                    continue
                for chip_dir in variant_dir.iterdir():
                    if not chip_dir.is_dir():
                        continue
                    chip = chip_dir.name
                    indices = _find_trace_indices(chip_dir)
                    for idx in indices:
                        jobs.append({"effect": effect, "variant": variant, "chip": chip, "index": idx})
        else:
            for chip_dir in effect_dir.iterdir():
                if not chip_dir.is_dir():
                    continue
                chip = chip_dir.name
                indices = _find_trace_indices(chip_dir)
                for idx in indices:
                    jobs.append({"effect": effect, "variant": None, "chip": chip, "index": idx})
 
    return jobs


def _find_trace_indices(directory):
    indices = []
    i = 0
    while (directory / f"traces{i}.npy").exists():
        indices.append(i)
        i += 1
    return indices

def run_analysis(jobs, use_cpa, use_tvla, cpa_params=None, tvla_params=None):
    cpa_params = cpa_params or DEFAULT_CPA_PARAMS
    tvla_params = tvla_params or DEFAULT_TVLA_PARAMS

    report = {
        "report_version": "1.0",
        "device":         jobs[0]["chip"],
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "last_updated":   datetime.now(timezone.utc).isoformat(),
        "methods": {
            "cpa":  cpa_params  if use_cpa  else None,
            "tvla": tvla_params if use_tvla else None,
        },
        "effects": {},
    }
 
    per_job_results = []
 
    for job in jobs:
        effect  = job["effect"]
        variant = job["variant"]
        chip    = job["chip"]
        index   = job["index"]
 
        data_dir    = get_data_dir(effect, chip, variant)
        traces      = np.load(data_dir / f"traces{index}.npy")
        shares      = np.load(data_dir / f"shares{index}.npy")

        # Filter out fixed-input traces for CPA and specific TVLA
        fixed_path  = data_dir / f"fixed{index}.npy"
        is_fixed    = np.load(fixed_path) if fixed_path.exists() else None
        random_mask = ~is_fixed if is_fixed is not None else np.ones(len(traces), dtype=bool)

        cpa_traces  = traces[random_mask]
        cpa_shares  = shares[random_mask]

        # Fixed-vs-random TVLA needs all traces; specific TVLA only random
        tvla_uses_all = is_fixed is not None and tvla_params.get("mode") == "fixed_vs_random"
        tvla_traces   = traces if tvla_uses_all else traces[random_mask]
        tvla_shares   = shares if tvla_uses_all else shares[random_mask]
 
        cpa_result  = run_cpa(effect, cpa_shares, cpa_traces, cpa_params) if use_cpa else None
        tvla_result = run_tvla(effect, tvla_shares, tvla_traces, tvla_params, data_dir, index) if use_tvla else None
 
        report_key = f"{effect}/{variant}" if variant else effect
        entry = {"trace_index": index}
        if cpa_result:
            entry["cpa"] = _report_entry(cpa_result)
        if tvla_result:
            entry["tvla"] = _report_entry(tvla_result)
        report["effects"][report_key] = entry
 
        per_job_results.append({
            **job,
            "cpa_result":  cpa_result,
            "tvla_result": tvla_result,
        })
 
    return report, per_job_results


def main():
    effect = select_option("Select which effect you want to analyse:", EFFECTS)
    chip   = select_option("Select chip:", CHIP_OPTIONS)

     # Variant selection and report key for pip_reg_overwrite
    variant = None

    if effect == "pip_reg_overwrite":
        variant = select_option("Select variant:", PIP_REG_VARIANTS)
    
    data_dir = get_data_dir(effect, chip, variant)
    if not data_dir.exists():
        raise FileNotFoundError(f"No data found at {data_dir}")
    
    index = select_index(str(data_dir))
    
    method_choice = select_option("Select analysis method:", ["CPA", "TVLA", "Both"])
    use_cpa  = method_choice in ("CPA",  "Both")
    use_tvla = method_choice in ("TVLA", "Both")

    cpa_params = dict(DEFAULT_CPA_PARAMS)
    if use_cpa:
        val = input(f"CPA threshold [{DEFAULT_CPA_PARAMS['threshold']}]: ").strip()
        if val:
            cpa_params["threshold"] = float(val)
 
    tvla_params = dict(DEFAULT_TVLA_PARAMS)
    if use_tvla:
        tvla_mode = select_option("Select TVLA mode:", ["Specific (HW-grouped)", "Non-specific (fixed-vs-random)"])
        tvla_params["mode"] = "specific" if tvla_mode == "Specific (HW-grouped)" else "fixed_vs_random"
        val = input(f"TVLA t-threshold [{DEFAULT_TVLA_PARAMS['t_threshold']}]: ").strip()
        if val:
            tvla_params["t_threshold"] = float(val)
        if tvla_params["mode"] == "specific":
            for key, label in [("low_hw_max", "Low HW max"), ("high_hw_min", "High HW min")]:
                val = input(f"{label} [{DEFAULT_TVLA_PARAMS[key]}]: ").strip()
                if val:
                    tvla_params[key] = int(val)
    
    jobs   = [{
        "effect": effect,
        "variant": variant, 
        "chip": chip, 
        "index": index
        }]
    
    report, results = run_analysis(jobs, use_cpa, use_tvla, cpa_params, tvla_params)
 
    name_input  = input("Report filename (leave blank for timestamp): ").strip()
    stem        = name_input or f"{chip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    stem        = stem if stem.endswith(".json") else stem + ".json"
    report_path = get_reports_dir() / stem
    save_report(report_path, report)
 
    r = results[0]

    if r["cpa_result"]:
        print(f"CPA:  {r['cpa_result']}")
    if r["tvla_result"]:
        print(f"TVLA: {r['tvla_result']}")

if __name__ == "__main__":
    main()