import os
import numpy as np

def select_option(prompt, options):
    print(f"\n{prompt}")

    for i, opt in enumerate(options):
        print(f"  {i+1}. {opt}")
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(options)}")

def select_index(data_dir):
    """List available trace files and let user pick one."""
    files = sorted([
        f for f in os.listdir(data_dir)
        if f.startswith("traces") and f.endswith(".npy")
    ])
    if not files:
        raise FileNotFoundError(f"No trace files found in {data_dir}")
    print(f"\nAvailable trace files in {data_dir}:")
    for i, f in enumerate(files):
        index = f.replace("traces", "").replace(".npy", "")
        traces_path = os.path.join(data_dir, f)
        shares_path = os.path.join(data_dir, f"shares{index}.npy")
        n_traces = np.load(traces_path, mmap_mode='r').shape[0]
        print(f"  {i+1}. {f} / shares{index}.npy  ({n_traces} traces)")
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(files):
                index = files[choice - 1].replace("traces", "").replace(".npy", "")
                return index
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(files)}")