import numpy as np
from scipy import stats

def tvla_specific(traces, labels, low_hw_max, high_hw_min):
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

def tvla_non_specific(traces, is_fixed):

    # Non-specific TVLA: fixed-input group vs random-input group

    is_fixed = np.asarray(is_fixed, dtype=bool)
    group_fixed  = traces[is_fixed]
    group_random = traces[~is_fixed]
    n_fixed, n_random = len(group_fixed), len(group_random)
    if n_fixed < 5 or n_random < 5:
        raise ValueError(
            f"Not enough traces in fixed/random groups "
            f"(fixed: {n_fixed}, random: {n_random})."
        )
    t, _ = stats.ttest_ind(group_fixed, group_random, axis=0, equal_var=False)
    return np.nan_to_num(t, nan=0.0), n_fixed, n_random