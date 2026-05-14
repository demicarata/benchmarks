import numpy as np
from scipy import stats

def tvla(traces, labels, low_hw_max, high_hw_min):
    # Specific TVLA: split traces by extreme HW groups, run sample-wise Welch t-test.

    group_a = traces[labels <= low_hw_max]
    group_b = traces[labels >= high_hw_min]
 
    n_a, n_b = len(group_a), len(group_b)
 
    if n_a < 5 or n_b < 5:
        raise ValueError(
            f"Not enough traces in extreme HW groups "
            f"(group A HW<={low_hw_max}: {n_a}, group B HW>={high_hw_min}: {n_b}). "
            f"Collect more traces or relax the HW boundaries."
        )
 
    t, _ = stats.ttest_ind(group_a, group_b, axis=0, equal_var=False)
    return np.nan_to_num(t, nan=0.0), n_a, n_b
