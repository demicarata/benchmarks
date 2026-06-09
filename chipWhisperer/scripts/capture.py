import chipwhisperer as cw
import numpy as np
import time
import os
from pathlib import Path

#---- Firmware Configuration ----

_SCRIPTS = Path(__file__).resolve().parent
_FIRMWARE = _SCRIPTS.parent / "firmware"
 
def _fw(relative_path):
    return str(_FIRMWARE / relative_path)

PIP_REG_VARIANTS = ["opA1xopA2", "opA1xopB2", "opB1xopA2", "opB1xopB2", "opA1xopA3", "opA1xopB3", "opB1xopA3", "opB1xopB3"]

FIRMWARE_CONFIGS = {
    "mem_remnant": {
        "label":   "Memory Remnant",
        "cmd_len": 8,
        "chips": {
            "stm32f3": _fw("memory_remnant/memory-remnant-asm-bench-CW308_STM32F3.hex"),
            "stm32f0": _fw("memory_remnant/memory-remnant-asm-bench-CW308_STM32F0.hex"),
        },
    },
    "reg_overwrite": {
        "label":   "Register Overwrite",
        "cmd_len": 12,
        "chips": {
            "stm32f3": _fw("register_overwrite/register-overwrite-asm-bench-CW308_STM32F3.hex"),
            "stm32f0": _fw("register_overwrite/register-overwrite-asm-bench-CW308_STM32F0.hex"),
        },
    },
    "pip_reg_overwrite": {
        "label":   "Pipeline Register Overwrite",
        "cmd_len": 16,
        "variants": {
            v: {
                "label": v,
                "chips": {
                    "stm32f3": _fw(f"pipeline_register_overwrite/{v}/pipeline-register-overwrite-asm-bench-{v}-CW308_STM32F3.hex"),
                    "stm32f0": _fw(f"pipeline_register_overwrite/{v}/pipeline-register-overwrite-asm-bench-{v}-CW308_STM32F0.hex"),
                },
            }
            for v in PIP_REG_VARIANTS
        },
    },
}


CHIP_OPTIONS = ["stm32f3", "stm32f0"]

#---- Payload Generation ----

def make_payload(firmware_key, rng):
    """Generate (payload_bytes, share_tuple) for a given firmware."""
    secret = rng.integers(0, 2**32, dtype=np.uint32)
    x0     = rng.integers(0, 2**32, dtype=np.uint32)
    x1     = np.uint32(secret ^ x0)

    if firmware_key == "mem_remnant":
        # 8 bytes: x0 | x1
        payload = bytearray(x0.tobytes() + x1.tobytes())

    elif firmware_key == "reg_overwrite":
        # 12 bytes: x0 | x1 | dummy
        dummy = rng.integers(0, 2**32, dtype=np.uint32)
        payload = bytearray(x0.tobytes() + x1.tobytes() + dummy.tobytes())

    elif firmware_key == "pip_reg_overwrite":
        # 16 bytes: x0 | m0 | x1 | m1
        m0 = rng.integers(0, 2**32, dtype=np.uint32)
        m1 = rng.integers(0, 2**32, dtype=np.uint32)
        payload = bytearray(x0.tobytes() + m0.tobytes() + x1.tobytes() + m1.tobytes())

    return payload, (int(x0), int(x1), int(secret))

#---- Helpers ----

def select_option(prompt, options):
    print(f"\n{prompt}")
    if isinstance(options, dict):
        keys = list(options.keys())
        labels = [options[k] if isinstance(options[k], str) else options[k]["label"] for k in keys]
    else:
        keys = options
        labels = options
    for i, label in enumerate(labels):
        print(f"  {i+1}. {label}")
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(keys):
                return keys[choice - 1]
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(keys)}")

def get_output_dir(firmware_key, chip, variant=None):
    """Return output directory path, creating it if needed."""
    base = _SCRIPTS.parent.parent / "data"
    path = base / firmware_key / variant / chip if variant \
           else base / firmware_key / chip
    path.mkdir(parents=True, exist_ok=True)
    return path



def next_index(output_dir):
    """Find the next available file index in output_dir."""
    index = 0
    while (output_dir / f"traces{index}.npy").exists():
        index += 1
    return index

def make_fixed_payload(firmware_key):
    x0     = np.uint32(0)
    x1     = np.uint32(0)
    secret = np.uint32(0)  # x0 XOR x1 = 0

    if firmware_key == "mem_remnant":
        payload = bytearray(x0.tobytes() + x1.tobytes())

    elif firmware_key == "reg_overwrite":
        dummy   = np.uint32(0)
        payload = bytearray(x0.tobytes() + x1.tobytes() + dummy.tobytes())

    elif firmware_key == "pip_reg_overwrite":
        m0      = np.uint32(0)
        m1      = np.uint32(0)
        payload = bytearray(x0.tobytes() + m0.tobytes() + x1.tobytes() + m1.tobytes())

    return payload, (int(x0), int(x1), int(secret))



#---- Main Capture Loop ----

def run_capture(firmware_key, chip, n_traces, n_samples, variant=None, fixed_ratio=None, progress_cb=None):
    print(f"fixed_ratio={fixed_ratio}")

    if fixed_ratio is not None:
        n_traces = n_traces * 2

    config = FIRMWARE_CONFIGS[firmware_key]

    if variant:
        hex_path = config["variants"][variant]["chips"][chip]
    else:
        hex_path = config["chips"][chip]
    
    scope = cw.scope()
    target = None

    try:
        scope.default_setup()
        time.sleep(0.1)

        target = cw.target(scope, cw.targets.SimpleSerial2)
        cw.program_target(scope, cw.programmers.STM32FProgrammer, hex_path)

        # Hacking hacks B)
        if chip == "stm32f0":
            target.baud = 38400

        time.sleep(0.1)
        target.flush()

        scope.adc.samples = n_samples 

        traces = []
        shares = []
        is_fixed = []
        rng = np.random.default_rng()
        skipped = 0

        if fixed_ratio is not None:
            fixed_payload, fixed_share = make_fixed_payload(firmware_key)

        for i in range(n_traces):
            if fixed_ratio is not None and rng.random() < fixed_ratio:
                payload, share = fixed_payload, fixed_share
                trace_is_fixed = True
            else:
                payload, share = make_payload(firmware_key, rng)
                trace_is_fixed = False

            scope.arm()
            time.sleep(0.01)
            target.send_cmd(0x01, 0x00, payload)
            ret     = target.simpleserial_wait_ack(timeout=500)
            timeout = scope.capture()

            if timeout or ret is None:
                skipped += 1
                continue

            traces.append(scope.get_last_trace())
            shares.append(share)

            if fixed_ratio is not None:
                is_fixed.append(trace_is_fixed)

            if progress_cb is not None:
                progress_cb(len(traces), skipped, n_traces)

    finally:
        if target is not None:
            target.dis()
        scope.dis()

    output_dir = get_output_dir(firmware_key, chip, variant)
    index = next_index(output_dir)

    traces_path = output_dir / f"traces{index}.npy"
    shares_path = output_dir / f"shares{index}.npy"


    np.save(traces_path, np.array(traces))
    np.save(shares_path, np.array(shares))

    fixed_path = None
    if fixed_ratio is not None:
        fixed_path = output_dir / f"fixed{index}.npy"
        np.save(fixed_path, np.array(is_fixed, dtype=bool))

    return {
        "traces_path": traces_path,
        "shares_path": shares_path,
        "captured":    len(traces),
        "skipped":     skipped,
    }

def main():
    firmware_key = select_option("Select effect to test:", FIRMWARE_CONFIGS)
    chip = select_option("Select chip:", CHIP_OPTIONS)
    config = FIRMWARE_CONFIGS[firmware_key]
    cmd_len = config["cmd_len"]

    # If this firmware has variants, prompt for one
    variant = None
    if "variants" in config:
        variant = select_option("Select variant:", config["variants"])
        hex_path = config["variants"][variant]["chips"][chip]
    else:
        hex_path = config["chips"][chip]

    print(f"\nSelected: {config['label']} on {chip}")
    print(f"Firmware: {hex_path}")
    print(f"Payload size: {cmd_len} bytes")
    
    n_traces  = int(input("\nNumber of traces to capture [default 20000]: ") or 20000)
    n_samples = int(input("ADC samples per trace [default 1000]: ") or 1000)
 
    def cli_progress(captured, skipped, total):
        if (captured + skipped) % 1000 == 0:
            print(f"  {captured + skipped}/{total} — captured {captured}, skipped {skipped}")
 
    result = run_capture(firmware_key, chip, n_traces, n_samples, variant, progress_cb=cli_progress)

    print(f"\nDone. Captured {result['captured']} traces, skipped {result['skipped']}.")
    print(f"Saved traces to {result['traces_path']}")
    print(f"Saved shares to {result['shares_path']}")


if __name__ == "__main__":
    main()