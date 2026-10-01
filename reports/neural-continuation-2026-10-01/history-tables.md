# League history ablation tables

The two variants have the same architecture, parameter count, training data, initial seeds and update budget. Current-only replaces past values and missingness with current state, retaining ages and valid lengths. Recall is a percentage and differences are percentage points. Burden is false-plus-late warnings per match. Brackets are conditional paired 95% intervals.

## Useful lead of 10 to 30 seconds

| Event | Full history recall | Current-only recall | Recall difference and interval | Full burden | Current-only burden |
|---|---|---|---|---|---|
| baron | 20.878 | 18.441 | 2.438 [1.818, 3.074] | 0.948 | 0.906 |
| dragon | 13.176 | 13.346 | -0.171 [-0.392, 0.047] | 0.889 | 0.917 |
| teamfight | 3.082 | 2.795 | 0.286 [0.115, 0.453] | 0.758 | 0.816 |
| macro | 12.379 | 11.527 | 0.851 [0.625, 1.074] | 0.865 | 0.880 |

### Macro recall by seed

| Seed | Full history | Current-only | Difference and interval | Both variants meet all regional budgets |
|---|---|---|---|---|
| 20260930 | 12.773 | 11.709 | 1.064 [0.766, 1.347] | False |
| 20261001 | 12.206 | 11.763 | 0.443 [0.130, 0.759] | False |
| 20261002 | 12.156 | 11.110 | 1.046 [0.738, 1.347] | True |

### Regional event comparisons averaged over fixed seeds

| Region | Event | Full history recall | Current-only recall | Difference and interval | Full burden | Current-only burden |
|---|---|---|---|---|---|---|
| europe | baron | 21.201 | 19.337 | 1.863 [0.916, 2.797] | 0.904 | 0.859 |
| europe | dragon | 13.051 | 13.099 | -0.048 [-0.337, 0.252] | 0.899 | 0.923 |
| europe | teamfight | 3.097 | 2.673 | 0.424 [0.198, 0.669] | 0.752 | 0.784 |
| americas | baron | 20.560 | 17.556 | 3.004 [2.153, 3.889] | 0.992 | 0.953 |
| americas | dragon | 13.296 | 13.586 | -0.290 [-0.596, 0.023] | 0.878 | 0.910 |
| americas | teamfight | 3.066 | 2.920 | 0.146 [-0.094, 0.386] | 0.763 | 0.847 |

### Regional budget failures

| Variant | Seed | Event | Route | False plus late per match |
|---|---|---|---|---|
| Full history | 20261001 | baron | americas | 1.011333 |
| Current-only | 20260930 | baron | americas | 1.011333 |

## Useful lead of 20 to 60 seconds

| Event | Full history recall | Current-only recall | Recall difference and interval | Full burden | Current-only burden |
|---|---|---|---|---|---|
| baron | 23.542 | 24.128 | -0.586 [-1.425, 0.229] | 0.875 | 0.898 |
| dragon | 9.645 | 8.433 | 1.212 [0.968, 1.470] | 0.669 | 0.589 |
| teamfight | 4.235 | 4.205 | 0.030 [-0.191, 0.250] | 0.755 | 0.727 |
| macro | 12.474 | 12.255 | 0.219 [-0.093, 0.504] | 0.766 | 0.738 |

### Macro recall by seed

| Seed | Full history | Current-only | Difference and interval | Both variants meet all regional budgets |
|---|---|---|---|---|
| 20260930 | 11.923 | 12.564 | -0.641 [-1.038, -0.276] | False |
| 20261001 | 13.029 | 12.077 | 0.953 [0.553, 1.339] | True |
| 20261002 | 12.470 | 12.125 | 0.345 [-0.077, 0.756] | True |

### Regional event comparisons averaged over fixed seeds

| Region | Event | Full history recall | Current-only recall | Difference and interval | Full burden | Current-only burden |
|---|---|---|---|---|---|---|
| europe | baron | 23.354 | 24.348 | -0.994 [-2.158, 0.215] | 0.848 | 0.863 |
| europe | dragon | 10.111 | 8.880 | 1.231 [0.882, 1.604] | 0.643 | 0.559 |
| europe | teamfight | 4.370 | 4.102 | 0.267 [-0.058, 0.598] | 0.735 | 0.690 |
| americas | baron | 23.728 | 23.912 | -0.184 [-1.373, 0.981] | 0.902 | 0.933 |
| americas | dragon | 9.193 | 7.999 | 1.194 [0.859, 1.524] | 0.694 | 0.620 |
| americas | teamfight | 4.098 | 4.309 | -0.211 [-0.512, 0.095] | 0.774 | 0.763 |

### Regional budget failures

| Variant | Seed | Event | Route | False plus late per match |
|---|---|---|---|---|
| Current-only | 20260930 | baron | americas | 1.019333 |
