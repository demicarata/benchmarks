import numpy as np
import matplotlib.pyplot as plt

traces = np.load("traces.npy")
shares = np.load("shares.npy")  # columns: x0, x1, secret

# --- Plot 1: mean trace + std band ---
mean  = traces.mean(axis=0)
std   = traces.std(axis=0)
samples = np.arange(len(mean))

plt.figure(figsize=(12, 4))
plt.plot(samples, mean, label="mean trace")
plt.fill_between(samples, mean - std, mean + std, alpha=0.3, label="±1 std")
plt.xlabel("Sample")
plt.ylabel("Power")
plt.title(f"Mean power trace over {len(traces)} captures")
plt.legend()
plt.tight_layout()
plt.savefig("mean_trace.png", dpi=150)
plt.show()

# --- Plot 2: overlay of first 20 individual traces ---
plt.figure(figsize=(12, 4))
for i in range(20):
    plt.plot(samples, traces[i], alpha=0.4, linewidth=0.8)
plt.xlabel("Sample")
plt.ylabel("Power")
plt.title("Overlay of 20 individual traces")
plt.tight_layout()
plt.savefig("overlay_traces.png", dpi=150)
plt.show()

