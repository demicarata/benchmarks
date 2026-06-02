import sys
import os
from pathlib import Path
from datetime import datetime
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
 
from capture import (
    run_capture, FIRMWARE_CONFIGS, CHIP_OPTIONS,
    select_option as capture_select,
)
from analysis import (
    run_analysis, save_report, get_reports_dir,
    EFFECTS, PIP_REG_VARIANTS,
    DEFAULT_CPA_PARAMS, DEFAULT_TVLA_PARAMS,
)
from helpers import select_option

### HELPERS

def _prompt_int(prompt, default):
    val = input(f"{prompt} [default {default}]: ").strip()
    return int(val) if val else default
 
def _prompt_float(prompt, default):
    val = input(f"{prompt} [default {default}]: ").strip()
    return float(val) if val else default
 
def _progress(captured, skipped, total):
    if (captured + skipped) % 500 == 0 or (captured + skipped) == total:
        print(f"  {captured + skipped}/{total} — captured {captured}, skipped {skipped}")

#-------------

def do_capture():
    firmware_key = capture_select("Select effect to capture:", FIRMWARE_CONFIGS)
    chip         = capture_select("Select chip:", CHIP_OPTIONS)
    config       = FIRMWARE_CONFIGS[firmware_key]
 
    variant = None
    if "variants" in config:
        variant = capture_select("Select variant:", config["variants"])
 
    n_traces  = _prompt_int("Number of traces to capture", 20000)
    n_samples = _prompt_int("ADC samples per trace",       1000)
 
    print(f"\nStarting capture: {config['label']} on {chip.upper()}"
          + (f" / {variant}" if variant else ""))
 
    result = run_capture(
        firmware_key, chip, n_traces, n_samples,
        variant=variant, progress_cb=_progress,
    )
 
    print(f"\nCapture done.  Captured {result['captured']}, skipped {result['skipped']}.")
    print(f"  traces → {result['traces_path']}")
    print(f"  shares → {result['shares_path']}")
 
    # Return a job dict that matches what run_analysis expects
    p     = Path(result["traces_path"])
    index = int(p.stem.replace("traces", ""))
    parts = p.parts
 
    if parts[-4] == "pip_reg_overwrite":
        effect  = "pip_reg_overwrite"
        variant = parts[-3]
        chip    = parts[-2]
    else:
        effect  = parts[-3]
        variant = None
        chip    = parts[-2]
 
    return {"effect": effect, "variant": variant, "chip": chip, "index": index}


def do_analysis(jobs):
    method_choice = select_option("Select analysis method:", ["CPA", "TVLA", "Both"])
    use_cpa  = method_choice in ("CPA",  "Both")
    use_tvla = method_choice in ("TVLA", "Both")
 
    cpa_params = dict(DEFAULT_CPA_PARAMS)
    if use_cpa:
        cpa_params["threshold"] = _prompt_float(
            "CPA correlation threshold", DEFAULT_CPA_PARAMS["threshold"]
        )
 
    tvla_params = dict(DEFAULT_TVLA_PARAMS)
    if use_tvla:
        tvla_params["t_threshold"] = _prompt_float(
            "TVLA t-threshold", DEFAULT_TVLA_PARAMS["t_threshold"]
        )
        tvla_params["low_hw_max"] = _prompt_int(
            "TVLA low HW max", DEFAULT_TVLA_PARAMS["low_hw_max"]
        )
        tvla_params["high_hw_min"] = _prompt_int(
            "TVLA high HW min", DEFAULT_TVLA_PARAMS["high_hw_min"]
        )
 
    print("\nRunning analysis…")
    report, results = run_analysis(jobs, use_cpa, use_tvla, cpa_params, tvla_params)
 
    # Print per-job summary
    for r in results:
        label = r["effect"]
        if r["variant"]:
            label += f"/{r['variant']}"
        label += f"  {r['chip'].upper()}  #{r['index']}"
        print(f"\n  {label}")
 
        if r.get("cpa_result"):
            c = r["cpa_result"]
            status = "LEAKAGE DETECTED" if c["leakage_detected"] else "no leakage"
            print(f"    CPA  — {status}  |  peak |corr| {c['peak_correlation']}  @ sample {c['peak_sample']}")
 
        if r.get("tvla_result"):
            t = r["tvla_result"]
            status = "LEAKAGE DETECTED" if t["leakage_detected"] else "no leakage"
            print(f"    TVLA — {status}  |  max |t| {t['max_abs_t']}  @ sample {t['peak_sample']}"
                  f"  (groups {t['n_group_a']} / {t['n_group_b']})")
 
    # Save report
    name_input = input("\nReport filename (leave blank for timestamp): ").strip()
    stem       = name_input or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    stem       = stem if stem.endswith(".json") else stem + ".json"
    path       = get_reports_dir() / stem
    save_report(path, report)
    print(f"Report saved to {path}")

def main():
    print("=== SCA Tool CLI ===\n")
 
    mode = select_option("What would you like to do?", [
        "Capture then analyse",
        "Capture only",
        "Analyse existing data",
    ])
 
    if mode == "Capture then analyse":
        jobs = []
        while True:
            job = do_capture()
            jobs.append(job)
            another = input("\nCapture another dataset? [y/N]: ").strip().lower()
            if another != "y":
                break
        do_analysis(jobs)
 
    elif mode == "Capture only":
        while True:
            do_capture()
            another = input("\nCapture another dataset? [y/N]: ").strip().lower()
            if another != "y":
                break
 
    elif mode == "Analyse existing data":
        # Let the user pick one or more effect/chip/index combos from what's on disk
        from analysis import discover_available_jobs
        all_jobs = discover_available_jobs()
        if not all_jobs:
            print("No captured data found. Run a capture first.")
            return
 
        print("\nAvailable datasets:")
        for i, j in enumerate(all_jobs):
            label = j["effect"]
            if j["variant"]:
                label += f"/{j['variant']}"
            print(f"  {i+1}. {label}  —  {j['chip'].upper()}  —  trace set #{j['index']}")
 
        raw = input("\nEnter numbers to analyse (e.g. 1 3 4), or leave blank for all: ").strip()
        if raw:
            chosen = [all_jobs[int(x) - 1] for x in raw.split()]
        else:
            chosen = all_jobs
 
        do_analysis(chosen)
 
 
if __name__ == "__main__":
    main()

