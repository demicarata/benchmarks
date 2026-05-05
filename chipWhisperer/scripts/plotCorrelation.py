import numpy as np
import matplotlib.pyplot as plt
import os
import sys


# --- Config ----

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from cpa import correlate_with_traces, hw
from helpers import select_option, select_index

FIRMWARE_OPTIONS = ["mem_remnant", "reg_overwrite", "pip_reg_overwrite"]
CHIP_OPTIONS     = ["stm32f3", "stm32f0"]

# ---- Compute correlations ----

def main():
    firmware = select_option("Select for which effect you want to analyse traces:", FIRMWARE_OPTIONS)
    chip     = select_option("Select chip:", CHIP_OPTIONS)

    data_dir = os.path.join("data", firmware, chip)
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"No data found for {firmware} on {chip} in {data_dir}")
    
    index = select_index(data_dir)

    traces_path = os.path.join(data_dir, f"traces{index}.npy")
    shares_path = os.path.join(data_dir, f"shares{index}.npy")

    traces = np.load(traces_path)
    shares = np.load(shares_path)

    x0      = shares[:, 0]
    x1      = shares[:, 1]
    secret  = shares[:, 2]

    num_traces, num_samples = traces.shape
    samples = np.arange(num_samples)

    print(f"Loaded {num_traces} traces, {num_samples} samples each")

    # What we expect to see if the remnant effect is real:
    hw_secret = hw(secret)

    # Test for leakage of x0 and x1 themselves with each ldr
    hw_x0 = hw(x0)
    hw_x1 = hw(x1)

    corr_secret = correlate_with_traces(hw_secret, traces)  # remnant leakage
    corr_x0     = correlate_with_traces(hw_x0,     traces)  # first LDR leakage
    corr_x1     = correlate_with_traces(hw_x1,     traces)  # second LDR leakage

    # --- Plot ---
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

    axes[0].plot(samples, corr_x0, color='steelblue')
    axes[0].axhline(0, color='k', linewidth=0.5)
    axes[0].set_ylabel("Correlation")
    axes[0].set_title("HW(x0) — expected leakage at first LDR")

    axes[1].plot(samples, corr_x1, color='darkorange')
    axes[1].axhline(0, color='k', linewidth=0.5)
    axes[1].set_ylabel("Correlation")
    axes[1].set_title("HW(x1) — expected leakage at second LDR")

    axes[2].plot(samples, corr_secret, color='crimson')
    axes[2].axhline(0, color='k', linewidth=0.5)
    axes[2].set_ylabel("Correlation")
    axes[2].set_title("HW(secret) = HW(x0 XOR x1) — remnant leakage hypothesis")
    axes[2].set_xlabel("Sample")

    fig.suptitle(f"{firmware} / {chip} / run {index} ({num_traces} traces)", fontsize=11)
    plt.tight_layout()

    plot_dir = os.path.join("plots", firmware, chip)
    os.makedirs(plot_dir, exist_ok=True)
    plot_path = os.path.join(plot_dir, f"cpa_{index}.png")
    plt.savefig(plot_path, dpi=150)
    print(f"Saved plot -> {plot_path}")
    plt.show()

    # --- Print peak correlations ---
    print(f"Peak |corr| HW(x0):     {np.max(np.abs(corr_x0)):.4f} at sample {np.argmax(np.abs(corr_x0))}")
    print(f"Peak |corr| HW(x1):     {np.max(np.abs(corr_x1)):.4f} at sample {np.argmax(np.abs(corr_x1))}")
    print(f"Peak |corr| HW(secret): {np.max(np.abs(corr_secret)):.4f} at sample {np.argmax(np.abs(corr_secret))}")

if __name__ == "__main__":
    main()