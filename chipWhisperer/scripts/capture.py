import chipwhisperer as cw
import numpy as np
import time
import os

#---- Firmware Configuration ----

FIRMWARE_CONFIGS = {
    "mem_remnant": {
        "label":    "Memory Remnant",
        "cmd_len":  8,
        "chips": {
            "stm32f3": "chipWhisperer/firmware/memory_remnant/memory-remnant-asm-bench-CW308_STM32F3.hex",
            "stm32f0": "chipWhisperer/firmware/memory_remnant/memory-remnant-asm-bench-CW308_STM32F0.hex",
        }
    },
    "reg_overwrite": {
        "label":    "Register Overwrite",
        "cmd_len":  12,
        "chips": {
            "stm32f3": "chipWhisperer/firmware/register_overwrite/register-overwrite-asm-bench-CW308_STM32F3.hex",
            "stm32f0": "chipWhisperer/firmware/register_overwrite/register-overwrite-asm-bench-CW308_STM32F0.hex",
        }
    },
    "pip_reg_overwrite": {
        "label":    "Pipeline Register Overwrite",
        "cmd_len":  16,
        "chips": {
            "stm32f3": "chipWhisperer/firmware/pipeline_register_overwrite/pipeline-register-overwrite-asm-bench-CW308_STM32F3.hex",
            "stm32f0": "chipWhisperer/firmware/pipeline_register_overwrite/pipeline-register-overwrite-asm-bench-CW308_STM32F0.hex",
        }
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

def get_output_dir(firmware_key, chip):
    """Return output directory path, creating it if needed."""
    path = os.path.join("data", firmware_key, chip)
    os.makedirs(path, exist_ok=True)
    return path

def next_index(output_dir):
    """Find the next available file index in output_dir."""
    index = 0
    while os.path.exists(os.path.join(output_dir, f"traces{index}.npy")):
        index += 1
    return index


#---- Main Capture Loop ----

def main():
    firmware_key = select_option("Select effect to test:", FIRMWARE_CONFIGS)
    chip = select_option("Select chip:", CHIP_OPTIONS)
    config = FIRMWARE_CONFIGS[firmware_key]
    hex_path = config["chips"][chip]
    cmd_len = config["cmd_len"]

    print(f"\nSelected: {config['label']} on {chip}")
    print(f"Firmware: {hex_path}")
    print(f"Payload size: {cmd_len} bytes")
    
    scope = cw.scope()
    scope.default_setup()
    target = cw.target(scope, cw.targets.SimpleSerial2)

    cw.program_target(scope, cw.programmers.STM32FProgrammer, hex_path)
    time.sleep(0.1)
    target.flush()

    N = int(input("\nNumber of traces to capture [default 20000]: ") or 20000)
    samples = int(input("ADC samples per trace [default 1000]: ") or 1000)

    scope.adc.samples = samples 

    traces = []
    shares = []
    rng = np.random.default_rng()
    skipped = 0

    print(f"\nStarting capture of {N} traces...")

    for i in range(N):
        payload, share = make_payload(firmware_key, rng)

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

        if (i + 1) % 1000 == 0:
            print(f"  {i+1}/{N} captured, {skipped} skipped so far")

    print(f"\nDone. Captured {len(traces)} traces, skipped {skipped}.")

    output_dir = get_output_dir(firmware_key, chip)
    index = next_index(output_dir)

    traces_path = os.path.join(output_dir, f"traces{index}.npy")
    shares_path = os.path.join(output_dir, f"shares{index}.npy")

    np.save(traces_path, np.array(traces))
    np.save(shares_path, np.array(shares))

    print(f"Saved traces to {traces_path}")
    print(f"Saved shares to {shares_path}")

if __name__ == "__main__":
    main()