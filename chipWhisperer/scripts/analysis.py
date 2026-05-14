import numpy as np
import json
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from cpa import correlate_with_traces, hw
from tvla import tvla
from helpers import select_option, select_index

EFFECTS = [
    "mem_remnant",
    "reg_overwrite",
    "pip_reg_overwrite",
]

PIP_REG_VARIANTS = ["opAxopA", "opAxopB", "opBxopA", "opBxopB"]

CHIP_OPTIONS     = ["stm32f3", "stm32f0"]
 
EFFECT_COLUMN = {
    # which column of shares[:,?] is the hypothesis variable for each effect
    "mem_remnant":       2,   # secret = x0 XOR x1
    "reg_overwrite":     2,   # secret
    "pip_reg_overwrite": 2,   # secret
}
 
CPA_THRESHOLD = 0.1
TVLA_T_THRESHOLD = 4.5
LOW_HW_MAX = 12
HIGH_HW_MIN = 20

# ---- IO and folders

def find_report(reports_dir, chip, index):
    """Return path to existing report for this chip+index, or None."""
    path = os.path.join(reports_dir, f"{chip}_{index}.json")
    return path if os.path.exists(path) else None
 
 
def next_report_path(reports_dir, chip, index):
    """
    Return a report path that doesn't exist yet.
    Tries {chip}_{index}.json, then {chip}_{index}_1.json, _2.json, etc.
    """
    base = os.path.join(reports_dir, f"{chip}_{index}.json")
    if not os.path.exists(base):
        return base
    n = 1
    while True:
        path = os.path.join(reports_dir, f"{chip}_{index}_{n}.json")
        if not os.path.exists(path):
            return path
        n += 1

def load_report(path):
    with open(path, "r") as f:
        return json.load(f)
    
def save_report(path, report):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    
def new_report(chip, index):
    return {
        "report_version": "1.0",
        "device":         chip,
        "trace_index":    index,
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "last_updated":   datetime.now(timezone.utc).isoformat(),
        "effects":        {e: "not_tested" for e in EFFECTS},
    }


# ---- Analysis ----

def run_cpa_on_effect(effect, shares, traces):
    # TODO: What happens if there are multiple peaks, or if there is a very small difference between the samples with teh highest correlation?
    col = EFFECT_COLUMN[effect]
    values = shares[:, col]
    hypothesis = hw(values)
    corr = correlate_with_traces(hypothesis, traces)

    max_abs  = float(np.max(np.abs(corr)))
    peak_idx = int(np.argmax(np.abs(corr)))
 
    return {
        "leakage_detected": max_abs >= CPA_THRESHOLD,
        "n_traces":         len(traces),
        "peak_correlation": round(max_abs, 4),
        "peak_sample":      peak_idx,
    }

def run_tvla_on_effect(effect, shares, traces):
    col    = EFFECT_COLUMN[effect]
    values = shares[:, col]
    labels = hw(values)
 
    t_trace, n_a, n_b = tvla(traces, labels, LOW_HW_MAX, HIGH_HW_MIN)
 
    max_abs_t   = float(np.max(np.abs(t_trace)))
    peak_sample = int(np.argmax(np.abs(t_trace)))
 
    return {
        "leakage_detected": max_abs_t >= TVLA_T_THRESHOLD,
        "n_traces":         len(traces),
        "n_group_a":        n_a,
        "n_group_b":        n_b,
        "group_a":          f"HW <= {LOW_HW_MAX}",
        "group_b":          f"HW >= {HIGH_HW_MIN}",
        "max_abs_t":        round(max_abs_t, 4),
        "peak_sample":      peak_sample,
    }

def main():
    effect = select_option("Select which effect you want to analyse:", EFFECTS)
    chip   = select_option("Select chip:", CHIP_OPTIONS)

     # Variant selection and report key for pip_reg_overwrite
    variant = None
    effect_report_key = effect

    if effect == "pip_reg_overwrite":
        variant = select_option("Select variant:", PIP_REG_VARIANTS)
        effect_report_key = f"pip_reg_overwrite/{variant}"
        data_dir = os.path.join("data", effect, variant, chip)
    else:
        data_dir = os.path.join("data", effect, chip)
        
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"No data found for {effect} on {chip} in {data_dir}")
    
    index = select_index(data_dir)

    traces = np.load(os.path.join(data_dir, f"traces{index}.npy"))
    shares = np.load(os.path.join(data_dir, f"shares{index}.npy"))

    print (f"Loaded {len(traces)} traces with {traces.shape[1]} samples each")

    reports_dir = os.path.join("reports")
    existing_path = find_report(reports_dir, chip, index)

    ## TODO: Fix this logic to properly create a new report with just the new effect
    ## TODO: Also make it so reports are not inherently tied to a single batch of runs
    ## Also make it so multiple runs can be taken into account when analysing an effect, instead of just one batch of traces

    if existing_path:
        report = load_report(existing_path)
        if report["effects"].get(effect) != "not_tested":
            print(f"\nWarning: '{effect}' is already analysed in {existing_path}.")
            print("Creating a new report file instead.")
            report_path = next_report_path(reports_dir, chip, index)
            # carry over existing results into the new file so context is preserved
            report = new_report(chip, index)
            existing = load_report(existing_path)
            report["effects"].update(existing["effects"])
        else:
            report_path = existing_path
            print(f"\nMerging into existing report: {existing_path}")
        report["last_updated"] = datetime.now(timezone.utc).isoformat()
    else:
        report      = new_report(chip, index)
        report_path = os.path.join(reports_dir, f"{chip}_{index}.json")

    cpa_result = run_cpa_on_effect(effect, shares, traces)
    tvla_result = run_tvla_on_effect(effect, shares, traces)

    result = dict(cpa_result)
    result["tvla"] = tvla_result
    report["effects"][effect] = result

    save_report(report_path, report)

if __name__ == "__main__":
    main()