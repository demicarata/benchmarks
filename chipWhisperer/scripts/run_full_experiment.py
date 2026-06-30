import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from cpa import correlate_with_traces, hw

# ---- Hardcoded config ----

CHIP        = "stm32f3"
HEX_PATH    = "chipWhisperer/firmware/full_experiment/full_experiment-CW308_STM32F3_mit3.hex"
N_TRACES    = 1000
N_SAMPLES   = 500

def next_index():
    os.makedirs("data", exist_ok=True)
    i = 0
    while os.path.exists(f"data/combined_gadget_traces_{i}.npy"):
        i += 1
    return i
 
INDEX = next_index()
 
def out_paths(index):
    tag = f"_{index}" if index is not None else ""
    return (
        f"data/combined_gadget_traces{tag}.npy",
        f"data/combined_gadget_shares{tag}.npy",
        f"plots/combined_gadget_cpa{tag}.png",
    )

 
def make_payload(rng):
    a0 = rng.integers(0, 2**32, dtype=np.uint32)
    a1 = rng.integers(0, 2**32, dtype=np.uint32)
    b0 = rng.integers(0, 2**32, dtype=np.uint32)
    b1 = rng.integers(0, 2**32, dtype=np.uint32)

    secret = np.uint32(a0 ^ a1)
    payload = bytearray(a0.tobytes() + a1.tobytes() + b0.tobytes() + b1.tobytes())

    return payload, (int(a0), int(a1), int(secret))
 
def capture(index):
    traces_out, shares_out, _ = out_paths(index)
    scope = cw.scope()
    target = None
    traces = []
    shares = []
    skipped = 0

    try:
        scope.default_setup()
        time.sleep(0.1)
        target = cw.target(scope, cw.targets.SimpleSerial2)
        cw.program_target(scope, cw.programmers.STM32FProgrammer, HEX_PATH)

        if CHIP == "stm32f0":
            target.baud = 38400

        time.sleep(0.1)
        target.flush()
        scope.adc.samples = N_SAMPLES
        rng = np.random.default_rng()

        for i in range(N_TRACES):
            payload, share = make_payload(rng)
            scope.arm()
            time.sleep(0.01)
            target.send_cmd(0x01, 0x00, payload)
            ret = target.simpleserial_wait_ack(timeout=500)
            timeout = scope.capture()

            if timeout or ret is None:
                skipped += 1
                continue

            traces.append(scope.get_last_trace())
            shares.append(share)

            if (i + 1) % 1000 == 0:
                print(f"  {i+1}/{N_TRACES} — captured {len(traces)}, skipped {skipped}")
    finally:
        if target is not None:
            target.dis()
        scope.dis()

    os.makedirs(os.path.dirname(traces_out), exist_ok=True)

    traces = np.array(traces)
    shares = np.array(shares)
    np.save(traces_out, traces)
    np.save(shares_out, shares)

    print(f"Captured {len(traces)} traces, skipped {skipped}")
    print(f"Saved -> {traces_out}, {shares_out}")

    return traces, shares
 
def plot(traces, shares, index):
    _, _, plot_out = out_paths(index)
    x0 = shares[:, 0]
    x1 = shares[:, 1]
    secret = shares[:, 2]
    num_traces, num_samples = traces.shape
    samples = np.arange(num_samples)

    corr_secret = correlate_with_traces(hw(secret), traces)
    corr_x0 = correlate_with_traces(hw(x0), traces)
    corr_x1 = correlate_with_traces(hw(x1), traces)

    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(samples, np.abs(corr_secret), color='darkorange')
    ax.axhline(0, color='k', linewidth=0.5)
    ax.set_ylabel("|Correlation|")
    ax.set_title("HW(secret) = HW(a0 XOR a1)")
    ax.set_xlabel("Sample")
    ax.set_ylim(-0.02, 0.72)
    tag = f" / run {index}" if index is not None else ""
    fig.suptitle(f"combined_gadget / {CHIP} / {num_traces} traces{tag}", fontsize=11)
    plt.tight_layout()

    os.makedirs(os.path.dirname(plot_out), exist_ok=True)
    plt.savefig(plot_out, dpi=150)
    print(f"Saved plot -> {plot_out}")
    plt.show()
    print(f"Peak |corr| HW(a0):     {np.max(np.abs(corr_x0)):.4f} at sample {np.argmax(np.abs(corr_x0))}")
    print(f"Peak |corr| HW(a1):     {np.max(np.abs(corr_x1)):.4f} at sample {np.argmax(np.abs(corr_x1))}")
    print(f"Peak |corr| HW(secret): {np.max(np.abs(corr_secret)):.4f} at sample {np.argmax(np.abs(corr_secret))}")


if __name__ == "__main__":
    #traces, shares = capture(INDEX)
    traces = np.load("data/combined_gadget_traces_5.npy")
    shares = np.load("data/combined_gadget_shares_5.npy")

    plot(traces, shares, 5)
