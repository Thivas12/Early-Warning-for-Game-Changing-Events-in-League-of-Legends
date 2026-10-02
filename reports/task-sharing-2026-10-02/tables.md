# League task sharing results

Recall is a percentage; recall differences are percentage points. Burdens are warnings per match per event. Macro burden averages events, rather than representing a combined attention budget. Intervals are paired whole-match conditional 95% intervals, with region strata and identical sampled matches across events and seeds. Seed means average fixed fitted performances, not predictions or independent populations.

## Useful lead of 10 to 30 seconds

### Overall means over three seeds

| Model | Event | Recall | False | Late | False plus late |
|---|---|---:|---:|---:|---:|
| gru | baron | 12.085 | 0.773 | 0.078 | 0.851 |
| gru | dragon | 8.977 | 0.673 | 0.149 | 0.822 |
| gru | teamfight | 2.204 | 0.571 | 0.110 | 0.681 |
| gru | macro | 7.755 | 0.672 | 0.112 | 0.785 |
| independent | baron | 21.506 | 0.807 | 0.144 | 0.952 |
| independent | dragon | 11.257 | 0.433 | 0.352 | 0.785 |
| independent | teamfight | 3.038 | 0.574 | 0.209 | 0.783 |
| independent | macro | 11.934 | 0.605 | 0.235 | 0.840 |
| leagueews | baron | 20.878 | 0.807 | 0.141 | 0.948 |
| leagueews | dragon | 13.176 | 0.508 | 0.381 | 0.889 |
| leagueews | teamfight | 3.082 | 0.553 | 0.205 | 0.758 |
| leagueews | macro | 12.379 | 0.622 | 0.242 | 0.865 |
| snapshot | baron | 18.636 | 0.814 | 0.133 | 0.947 |
| snapshot | dragon | 11.743 | 0.479 | 0.347 | 0.826 |
| snapshot | teamfight | 2.590 | 0.599 | 0.161 | 0.760 |
| snapshot | macro | 10.990 | 0.631 | 0.214 | 0.845 |
| tcn | baron | 20.734 | 0.821 | 0.145 | 0.966 |
| tcn | dragon | 13.532 | 0.523 | 0.377 | 0.899 |
| tcn | teamfight | 2.834 | 0.530 | 0.196 | 0.726 |
| tcn | macro | 12.367 | 0.625 | 0.239 | 0.864 |

### Overall joint minus independent differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -0.627 [-1.155, -0.071] | -0.001 [-0.020, 0.017] | -0.003 [-0.007, 0.001] | -0.004 [-0.023, 0.015] |
| dragon | 1.918 [1.677, 2.162] | 0.075 [0.064, 0.086] | 0.029 [0.023, 0.035] | 0.104 [0.091, 0.116] |
| teamfight | 0.044 [-0.066, 0.148] | -0.021 [-0.034, -0.008] | -0.004 [-0.009, 0.003] | -0.025 [-0.039, -0.010] |
| macro | 0.445 [0.251, 0.644] | 0.018 [0.009, 0.026] | 0.007 [0.004, 0.011] | 0.025 [0.016, 0.034] |

### Europe means over three seeds

| Model | Event | Recall | False | Late | False plus late |
|---|---|---:|---:|---:|---:|
| gru | baron | 12.195 | 0.702 | 0.078 | 0.780 |
| gru | dragon | 8.862 | 0.653 | 0.146 | 0.799 |
| gru | teamfight | 2.288 | 0.559 | 0.105 | 0.664 |
| gru | macro | 7.782 | 0.638 | 0.110 | 0.748 |
| independent | baron | 22.402 | 0.768 | 0.147 | 0.915 |
| independent | dragon | 11.157 | 0.451 | 0.347 | 0.798 |
| independent | teamfight | 3.050 | 0.580 | 0.192 | 0.772 |
| independent | macro | 12.203 | 0.600 | 0.228 | 0.828 |
| leagueews | baron | 21.201 | 0.757 | 0.147 | 0.904 |
| leagueews | dragon | 13.051 | 0.524 | 0.376 | 0.899 |
| leagueews | teamfight | 3.097 | 0.558 | 0.194 | 0.752 |
| leagueews | macro | 12.450 | 0.613 | 0.239 | 0.852 |
| snapshot | baron | 19.586 | 0.763 | 0.136 | 0.899 |
| snapshot | dragon | 11.587 | 0.490 | 0.340 | 0.830 |
| snapshot | teamfight | 2.452 | 0.580 | 0.143 | 0.723 |
| snapshot | macro | 11.208 | 0.611 | 0.206 | 0.817 |
| tcn | baron | 21.097 | 0.768 | 0.147 | 0.915 |
| tcn | dragon | 13.296 | 0.533 | 0.367 | 0.900 |
| tcn | teamfight | 2.856 | 0.534 | 0.183 | 0.718 |
| tcn | macro | 12.417 | 0.612 | 0.232 | 0.844 |

### Europe joint minus independent differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -1.201 [-2.010, -0.385] | -0.011 [-0.038, 0.014] | -0.000 [-0.006, 0.006] | -0.011 [-0.039, 0.015] |
| dragon | 1.894 [1.572, 2.228] | 0.072 [0.057, 0.088] | 0.029 [0.021, 0.038] | 0.102 [0.084, 0.120] |
| teamfight | 0.047 [-0.094, 0.196] | -0.022 [-0.038, -0.006] | 0.003 [-0.006, 0.012] | -0.019 [-0.038, 0.000] |
| macro | 0.247 [-0.040, 0.537] | 0.013 [0.000, 0.025] | 0.011 [0.006, 0.015] | 0.024 [0.010, 0.036] |

### Americas means over three seeds

| Model | Event | Recall | False | Late | False plus late |
|---|---|---:|---:|---:|---:|
| gru | baron | 11.976 | 0.843 | 0.079 | 0.922 |
| gru | dragon | 9.088 | 0.694 | 0.151 | 0.845 |
| gru | teamfight | 2.119 | 0.582 | 0.115 | 0.697 |
| gru | macro | 7.728 | 0.706 | 0.115 | 0.821 |
| independent | baron | 20.621 | 0.847 | 0.142 | 0.988 |
| independent | dragon | 11.355 | 0.414 | 0.358 | 0.772 |
| independent | teamfight | 3.025 | 0.568 | 0.226 | 0.794 |
| independent | macro | 11.667 | 0.610 | 0.242 | 0.852 |
| leagueews | baron | 20.560 | 0.856 | 0.136 | 0.992 |
| leagueews | dragon | 13.296 | 0.492 | 0.386 | 0.878 |
| leagueews | teamfight | 3.066 | 0.548 | 0.216 | 0.763 |
| leagueews | macro | 12.307 | 0.632 | 0.246 | 0.878 |
| snapshot | baron | 17.699 | 0.865 | 0.130 | 0.996 |
| snapshot | dragon | 11.894 | 0.469 | 0.354 | 0.823 |
| snapshot | teamfight | 2.730 | 0.618 | 0.180 | 0.798 |
| snapshot | macro | 10.774 | 0.651 | 0.221 | 0.872 |
| tcn | baron | 20.376 | 0.874 | 0.142 | 1.017 |
| tcn | dragon | 13.760 | 0.512 | 0.386 | 0.899 |
| tcn | teamfight | 2.811 | 0.526 | 0.209 | 0.734 |
| tcn | macro | 12.316 | 0.637 | 0.246 | 0.883 |

### Americas joint minus independent differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -0.061 [-0.797, 0.705] | 0.010 [-0.019, 0.036] | -0.006 [-0.013, -0.001] | 0.004 [-0.026, 0.032] |
| dragon | 1.942 [1.591, 2.313] | 0.077 [0.063, 0.092] | 0.028 [0.019, 0.037] | 0.106 [0.088, 0.122] |
| teamfight | 0.041 [-0.108, 0.197] | -0.021 [-0.040, -0.002] | -0.010 [-0.019, -0.001] | -0.030 [-0.051, -0.009] |
| macro | 0.640 [0.368, 0.915] | 0.022 [0.009, 0.034] | 0.004 [-0.001, 0.009] | 0.026 [0.013, 0.039] |

### Every seed at each event

| Seed | Event | Joint recall | Independent recall | Difference and interval |
|---|---|---:|---:|---:|
| 20260930 | baron | 21.012 | 21.135 | -0.123 [-0.862, 0.618] |
| 20260930 | dragon | 14.035 | 10.398 | 3.637 [3.286, 4.012] |
| 20260930 | teamfight | 3.274 | 3.627 | -0.354 [-0.505, -0.210] |
| 20260930 | macro | 12.773 | 11.720 | 1.053 [0.783, 1.332] |
| 20261001 | baron | 21.290 | 21.567 | -0.278 [-1.011, 0.508] |
| 20261001 | dragon | 12.358 | 12.331 | 0.026 [-0.292, 0.388] |
| 20261001 | teamfight | 2.970 | 2.647 | 0.323 [0.167, 0.479] |
| 20261001 | macro | 12.206 | 12.182 | 0.024 [-0.250, 0.304] |
| 20261002 | baron | 20.333 | 21.814 | -1.481 [-2.278, -0.650] |
| 20261002 | dragon | 13.134 | 11.042 | 2.092 [1.746, 2.416] |
| 20261002 | teamfight | 3.001 | 2.839 | 0.162 [0.010, 0.318] |
| 20261002 | macro | 12.156 | 11.899 | 0.258 [-0.044, 0.566] |

### Seed variability in timely recall

| Model | Event | Minimum percent | Maximum percent | Sample SD in points |
|---|---|---:|---:|---:|
| gru | baron | 9.534 | 15.088 | 2.804 |
| gru | dragon | 8.094 | 9.877 | 0.892 |
| gru | teamfight | 2.016 | 2.435 | 0.213 |
| gru | macro | 6.597 | 8.827 | 1.118 |
| independent | baron | 21.135 | 21.814 | 0.344 |
| independent | dragon | 10.398 | 12.331 | 0.984 |
| independent | teamfight | 2.647 | 3.627 | 0.519 |
| independent | macro | 11.720 | 12.182 | 0.233 |
| leagueews | baron | 20.333 | 21.290 | 0.492 |
| leagueews | dragon | 12.358 | 14.035 | 0.839 |
| leagueews | teamfight | 2.970 | 3.274 | 0.167 |
| leagueews | macro | 12.156 | 12.773 | 0.343 |
| snapshot | baron | 18.050 | 19.192 | 0.571 |
| snapshot | dragon | 11.554 | 11.987 | 0.222 |
| snapshot | teamfight | 2.501 | 2.672 | 0.086 |
| snapshot | macro | 10.702 | 11.258 | 0.279 |
| tcn | baron | 20.457 | 20.981 | 0.264 |
| tcn | dragon | 12.402 | 14.820 | 1.217 |
| tcn | teamfight | 2.536 | 3.218 | 0.349 |
| tcn | macro | 11.972 | 12.604 | 0.344 |

### Regional warning budget failures

| Model | Seed | Event | Region | False plus late per match |
|---|---|---|---|---:|
| gru | 20261001 | baron | americas | 1.012000 |
| independent | 20260930 | baron | americas | 1.008000 |
| leagueews | 20261001 | baron | americas | 1.011333 |
| snapshot | 20260930 | baron | americas | 1.032000 |
| tcn | 20260930 | baron | americas | 1.020000 |
| tcn | 20261001 | baron | americas | 1.026000 |
| tcn | 20261002 | baron | americas | 1.004000 |

## Useful lead of 20 to 60 seconds

### Overall means over three seeds

| Model | Event | Recall | False | Late | False plus late |
|---|---|---:|---:|---:|---:|
| gru | baron | 18.564 | 0.732 | 0.153 | 0.885 |
| gru | dragon | 18.130 | 0.466 | 0.273 | 0.738 |
| gru | teamfight | 3.257 | 0.409 | 0.133 | 0.542 |
| gru | macro | 13.317 | 0.536 | 0.186 | 0.722 |
| independent | baron | 25.681 | 0.635 | 0.268 | 0.904 |
| independent | dragon | 8.768 | 0.135 | 0.486 | 0.621 |
| independent | teamfight | 3.784 | 0.415 | 0.304 | 0.719 |
| independent | macro | 12.744 | 0.395 | 0.353 | 0.748 |
| leagueews | baron | 23.542 | 0.608 | 0.267 | 0.875 |
| leagueews | dragon | 9.645 | 0.142 | 0.527 | 0.669 |
| leagueews | teamfight | 4.235 | 0.445 | 0.310 | 0.755 |
| leagueews | macro | 12.474 | 0.398 | 0.368 | 0.766 |
| snapshot | baron | 23.048 | 0.648 | 0.242 | 0.889 |
| snapshot | dragon | 8.912 | 0.124 | 0.415 | 0.539 |
| snapshot | teamfight | 3.538 | 0.461 | 0.233 | 0.694 |
| snapshot | macro | 11.833 | 0.411 | 0.297 | 0.707 |
| tcn | baron | 23.439 | 0.636 | 0.270 | 0.906 |
| tcn | dragon | 10.154 | 0.150 | 0.537 | 0.687 |
| tcn | teamfight | 3.487 | 0.354 | 0.262 | 0.616 |
| tcn | macro | 12.360 | 0.380 | 0.356 | 0.737 |

### Overall joint minus independent differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -2.139 [-2.956, -1.371] | -0.027 [-0.044, -0.012] | -0.002 [-0.007, 0.004] | -0.029 [-0.047, -0.012] |
| dragon | 0.877 [0.647, 1.127] | 0.007 [0.001, 0.013] | 0.041 [0.031, 0.050] | 0.048 [0.036, 0.060] |
| teamfight | 0.451 [0.302, 0.600] | 0.030 [0.018, 0.043] | 0.006 [-0.002, 0.015] | 0.036 [0.021, 0.052] |
| macro | -0.270 [-0.559, 0.008] | 0.003 [-0.004, 0.011] | 0.015 [0.010, 0.020] | 0.018 [0.010, 0.027] |

### Europe means over three seeds

| Model | Event | Recall | False | Late | False plus late |
|---|---|---:|---:|---:|---:|
| gru | baron | 18.157 | 0.668 | 0.152 | 0.820 |
| gru | dragon | 18.011 | 0.460 | 0.266 | 0.726 |
| gru | teamfight | 3.157 | 0.398 | 0.138 | 0.536 |
| gru | macro | 13.109 | 0.509 | 0.185 | 0.694 |
| independent | baron | 26.066 | 0.602 | 0.278 | 0.879 |
| independent | dragon | 9.167 | 0.128 | 0.459 | 0.587 |
| independent | teamfight | 4.042 | 0.405 | 0.296 | 0.701 |
| independent | macro | 13.092 | 0.378 | 0.344 | 0.722 |
| leagueews | baron | 23.354 | 0.571 | 0.277 | 0.848 |
| leagueews | dragon | 10.111 | 0.135 | 0.508 | 0.643 |
| leagueews | teamfight | 4.370 | 0.438 | 0.297 | 0.735 |
| leagueews | macro | 12.612 | 0.382 | 0.361 | 0.742 |
| snapshot | baron | 22.567 | 0.600 | 0.250 | 0.850 |
| snapshot | dragon | 9.436 | 0.115 | 0.390 | 0.505 |
| snapshot | teamfight | 3.404 | 0.442 | 0.208 | 0.650 |
| snapshot | macro | 11.802 | 0.386 | 0.283 | 0.668 |
| tcn | baron | 23.499 | 0.590 | 0.276 | 0.867 |
| tcn | dragon | 10.661 | 0.144 | 0.511 | 0.655 |
| tcn | teamfight | 3.548 | 0.346 | 0.249 | 0.594 |
| tcn | macro | 12.569 | 0.360 | 0.345 | 0.705 |

### Europe joint minus independent differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -2.712 [-3.891, -1.538] | -0.031 [-0.052, -0.008] | -0.001 [-0.009, 0.007] | -0.032 [-0.054, -0.007] |
| dragon | 0.944 [0.598, 1.315] | 0.007 [-0.002, 0.017] | 0.049 [0.036, 0.062] | 0.056 [0.040, 0.072] |
| teamfight | 0.327 [0.109, 0.555] | 0.033 [0.016, 0.051] | 0.001 [-0.010, 0.013] | 0.034 [0.013, 0.057] |
| macro | -0.480 [-0.899, -0.058] | 0.003 [-0.007, 0.014] | 0.017 [0.010, 0.023] | 0.020 [0.008, 0.032] |

### Americas means over three seeds

| Model | Event | Recall | False | Late | False plus late |
|---|---|---:|---:|---:|---:|
| gru | baron | 18.966 | 0.796 | 0.154 | 0.950 |
| gru | dragon | 18.246 | 0.471 | 0.280 | 0.750 |
| gru | teamfight | 3.358 | 0.421 | 0.127 | 0.548 |
| gru | macro | 13.523 | 0.563 | 0.187 | 0.750 |
| independent | baron | 25.301 | 0.669 | 0.259 | 0.928 |
| independent | dragon | 8.381 | 0.142 | 0.514 | 0.656 |
| independent | teamfight | 3.521 | 0.424 | 0.312 | 0.736 |
| independent | macro | 12.401 | 0.411 | 0.362 | 0.773 |
| leagueews | baron | 23.728 | 0.645 | 0.257 | 0.902 |
| leagueews | dragon | 9.193 | 0.148 | 0.546 | 0.694 |
| leagueews | teamfight | 4.098 | 0.452 | 0.322 | 0.774 |
| leagueews | macro | 12.340 | 0.415 | 0.375 | 0.790 |
| snapshot | baron | 23.523 | 0.695 | 0.233 | 0.928 |
| snapshot | dragon | 8.404 | 0.132 | 0.441 | 0.573 |
| snapshot | teamfight | 3.674 | 0.480 | 0.257 | 0.737 |
| snapshot | macro | 11.867 | 0.436 | 0.310 | 0.746 |
| tcn | baron | 23.380 | 0.682 | 0.264 | 0.946 |
| tcn | dragon | 9.662 | 0.156 | 0.564 | 0.719 |
| tcn | teamfight | 3.426 | 0.362 | 0.276 | 0.638 |
| tcn | macro | 12.156 | 0.400 | 0.368 | 0.768 |

### Americas joint minus independent differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -1.574 [-2.696, -0.473] | -0.024 [-0.047, -0.000] | -0.002 [-0.010, 0.006] | -0.026 [-0.051, -0.000] |
| dragon | 0.811 [0.493, 1.132] | 0.007 [-0.002, 0.015] | 0.032 [0.018, 0.046] | 0.039 [0.022, 0.055] |
| teamfight | 0.577 [0.365, 0.784] | 0.028 [0.009, 0.047] | 0.010 [-0.002, 0.023] | 0.037 [0.016, 0.060] |
| macro | -0.062 [-0.461, 0.322] | 0.003 [-0.007, 0.014] | 0.013 [0.006, 0.020] | 0.017 [0.004, 0.029] |

### Every seed at each event

| Seed | Event | Joint recall | Independent recall | Difference and interval |
|---|---|---:|---:|---:|
| 20260930 | baron | 23.110 | 23.326 | -0.216 [-1.250, 0.781] |
| 20260930 | dragon | 8.915 | 8.386 | 0.530 [0.195, 0.874] |
| 20260930 | teamfight | 3.743 | 3.794 | -0.051 [-0.258, 0.156] |
| 20260930 | macro | 11.923 | 11.835 | 0.088 [-0.289, 0.462] |
| 20261001 | baron | 23.696 | 27.368 | -3.672 [-4.823, -2.581] |
| 20261001 | dragon | 10.107 | 10.080 | 0.026 [-0.307, 0.365] |
| 20261001 | teamfight | 5.284 | 4.638 | 0.647 [0.437, 0.868] |
| 20261001 | macro | 13.029 | 14.029 | -1.000 [-1.409, -0.604] |
| 20261002 | baron | 23.820 | 26.350 | -2.530 [-3.677, -1.416] |
| 20261002 | dragon | 9.913 | 7.838 | 2.074 [1.739, 2.454] |
| 20261002 | teamfight | 3.678 | 2.920 | 0.758 [0.552, 0.952] |
| 20261002 | macro | 12.470 | 12.369 | 0.101 [-0.299, 0.494] |

### Seed variability in timely recall

| Model | Event | Minimum percent | Maximum percent | Sample SD in points |
|---|---|---:|---:|---:|
| gru | baron | 14.286 | 21.166 | 3.734 |
| gru | dragon | 14.838 | 22.191 | 3.736 |
| gru | teamfight | 2.900 | 3.956 | 0.605 |
| gru | macro | 12.665 | 13.810 | 0.589 |
| independent | baron | 23.326 | 27.368 | 2.102 |
| independent | dragon | 7.838 | 10.080 | 1.169 |
| independent | teamfight | 2.920 | 4.638 | 0.859 |
| independent | macro | 11.835 | 14.029 | 1.144 |
| leagueews | baron | 23.110 | 23.820 | 0.379 |
| leagueews | dragon | 8.915 | 10.107 | 0.639 |
| leagueews | teamfight | 3.678 | 5.284 | 0.909 |
| leagueews | macro | 11.923 | 13.029 | 0.553 |
| snapshot | baron | 21.135 | 24.375 | 1.698 |
| snapshot | dragon | 8.421 | 9.833 | 0.798 |
| snapshot | teamfight | 2.369 | 4.178 | 1.014 |
| snapshot | macro | 11.715 | 12.061 | 0.198 |
| tcn | baron | 21.660 | 25.949 | 2.236 |
| tcn | dragon | 7.803 | 12.340 | 2.273 |
| tcn | teamfight | 3.248 | 3.637 | 0.209 |
| tcn | macro | 11.033 | 13.846 | 1.413 |

### Regional warning budget failures

| Model | Seed | Event | Region | False plus late per match |
|---|---|---|---|---:|
| gru | 20261001 | baron | americas | 1.004000 |
| tcn | 20261002 | baron | americas | 1.034000 |
