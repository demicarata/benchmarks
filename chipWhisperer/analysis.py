import numpy as np
import matplotlib.pyplot as plt

traces = np.load("traces.npy")
shares = np.load("shares.npy")  # columns: x0, x1, secret

x0      = shares[:, 0]
x1      = shares[:, 1]
secret  = shares[:, 2]

num_traces, num_samples = traces.shape
samples = np.arange(num_samples)

print(f"Loaded {num_traces} traces, {num_samples} samples each")

# What we expect to see if the remnant effect is real:
hw_secret = np.array([bin(int(s) & 0xFFFFFFFF).count('1') for s in secret]) 

# Test for leakage of x0 and x1 themselves with each ldr
hw_x0 = np.array([bin(int(s) & 0xFFFFFFFF).count('1') for s in x0]) 
hw_x1 = np.array([bin(int(s) & 0xFFFFFFFF).count('1') for s in x1]) 

# --- Compute correlations ---
def correlate_with_traces(hypothesis, traces):
    """Pearson correlation between hypothesis vector and each sample column."""
    h = hypothesis.astype(float)
    h = (h - h.mean()) / h.std()
    t = traces - traces.mean(axis=0)
    t = t / (t.std(axis=0) + 1e-12) 
    return (h @ t) / len(h)

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

plt.tight_layout()
plt.savefig("cpa_remnant.png", dpi=150)
plt.show()

# --- Print peak correlations ---
print(f"Peak |corr| HW(x0):     {np.max(np.abs(corr_x0)):.4f} at sample {np.argmax(np.abs(corr_x0))}")
print(f"Peak |corr| HW(x1):     {np.max(np.abs(corr_x1)):.4f} at sample {np.argmax(np.abs(corr_x1))}")
print(f"Peak |corr| HW(secret): {np.max(np.abs(corr_secret)):.4f} at sample {np.argmax(np.abs(corr_secret))}")
print(f"corr_secret at second LDR (sample 38): {corr_secret[38]:.4f}")
print(f"corr_x0     at second LDR (sample 38): {corr_x0[38]:.4f}")
print(f"corr_x1     at second LDR (sample 38): {corr_x1[38]:.4f}")