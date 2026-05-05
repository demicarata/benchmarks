import numpy as np

def correlate_with_traces(hypothesis, traces):
    """Pearson correlation between hypothesis vector and each sample column."""
    h = hypothesis.astype(float)
    h = (h - h.mean()) / h.std()
    t = traces - traces.mean(axis=0)
    t = t / (t.std(axis=0) + 1e-12) 
    return (h @ t) / len(h)

def hw(values):
    return np.array([bin(int(v) & 0xFFFFFFFF).count('1') for v in values])