# League gradient-conflict results

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
| pcgrad | baron | 20.724 | 0.785 | 0.141 | 0.926 |
| pcgrad | dragon | 14.102 | 0.551 | 0.394 | 0.945 |
| pcgrad | teamfight | 3.410 | 0.639 | 0.221 | 0.860 |
| pcgrad | macro | 12.745 | 0.658 | 0.252 | 0.911 |
| snapshot | baron | 18.636 | 0.814 | 0.133 | 0.947 |
| snapshot | dragon | 11.743 | 0.479 | 0.347 | 0.826 |
| snapshot | teamfight | 2.590 | 0.599 | 0.161 | 0.760 |
| snapshot | macro | 10.990 | 0.631 | 0.214 | 0.845 |
| tcn | baron | 20.734 | 0.821 | 0.145 | 0.966 |
| tcn | dragon | 13.532 | 0.523 | 0.377 | 0.899 |
| tcn | teamfight | 2.834 | 0.530 | 0.196 | 0.726 |
| tcn | macro | 12.367 | 0.625 | 0.239 | 0.864 |

### Overall PCGrad minus ordinary joint differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -0.154 [-0.460, 0.168] | -0.021 [-0.031, -0.012] | -0.000 [-0.002, 0.002] | -0.021 [-0.031, -0.011] |
| dragon | 0.927 [0.761, 1.089] | 0.044 [0.037, 0.051] | 0.013 [0.009, 0.017] | 0.057 [0.049, 0.065] |
| teamfight | 0.328 [0.258, 0.402] | 0.086 [0.077, 0.096] | 0.016 [0.011, 0.021] | 0.102 [0.092, 0.113] |
| macro | 0.367 [0.249, 0.490] | 0.036 [0.031, 0.041] | 0.010 [0.007, 0.012] | 0.046 [0.040, 0.052] |

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
| pcgrad | baron | 21.222 | 0.737 | 0.148 | 0.885 |
| pcgrad | dragon | 13.924 | 0.570 | 0.385 | 0.955 |
| pcgrad | teamfight | 3.411 | 0.643 | 0.205 | 0.848 |
| pcgrad | macro | 12.852 | 0.650 | 0.246 | 0.896 |
| snapshot | baron | 19.586 | 0.763 | 0.136 | 0.899 |
| snapshot | dragon | 11.587 | 0.490 | 0.340 | 0.830 |
| snapshot | teamfight | 2.452 | 0.580 | 0.143 | 0.723 |
| snapshot | macro | 11.208 | 0.611 | 0.206 | 0.817 |
| tcn | baron | 21.097 | 0.768 | 0.147 | 0.915 |
| tcn | dragon | 13.296 | 0.533 | 0.367 | 0.900 |
| tcn | teamfight | 2.856 | 0.534 | 0.183 | 0.718 |
| tcn | macro | 12.417 | 0.612 | 0.232 | 0.844 |

### Europe PCGrad minus ordinary joint differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | 0.021 [-0.402, 0.478] | -0.020 [-0.032, -0.006] | 0.001 [-0.002, 0.004] | -0.019 [-0.032, -0.005] |
| dragon | 0.872 [0.647, 1.097] | 0.046 [0.037, 0.056] | 0.010 [0.004, 0.015] | 0.056 [0.045, 0.067] |
| teamfight | 0.314 [0.221, 0.419] | 0.085 [0.072, 0.099] | 0.011 [0.005, 0.017] | 0.096 [0.082, 0.111] |
| macro | 0.402 [0.231, 0.578] | 0.037 [0.030, 0.045] | 0.007 [0.004, 0.010] | 0.044 [0.037, 0.052] |

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
| pcgrad | baron | 20.233 | 0.833 | 0.135 | 0.968 |
| pcgrad | dragon | 14.276 | 0.532 | 0.403 | 0.936 |
| pcgrad | teamfight | 3.409 | 0.635 | 0.237 | 0.872 |
| pcgrad | macro | 12.639 | 0.667 | 0.258 | 0.925 |
| snapshot | baron | 17.699 | 0.865 | 0.130 | 0.996 |
| snapshot | dragon | 11.894 | 0.469 | 0.354 | 0.823 |
| snapshot | teamfight | 2.730 | 0.618 | 0.180 | 0.798 |
| snapshot | macro | 10.774 | 0.651 | 0.221 | 0.872 |
| tcn | baron | 20.376 | 0.874 | 0.142 | 1.017 |
| tcn | dragon | 13.760 | 0.512 | 0.386 | 0.899 |
| tcn | teamfight | 2.811 | 0.526 | 0.209 | 0.734 |
| tcn | macro | 12.316 | 0.637 | 0.246 | 0.883 |

### Americas PCGrad minus ordinary joint differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | -0.327 [-0.751, 0.099] | -0.023 [-0.039, -0.008] | -0.001 [-0.004, 0.002] | -0.024 [-0.039, -0.009] |
| dragon | 0.980 [0.753, 1.209] | 0.041 [0.031, 0.051] | 0.017 [0.011, 0.022] | 0.058 [0.046, 0.070] |
| teamfight | 0.343 [0.247, 0.454] | 0.087 [0.074, 0.101] | 0.021 [0.014, 0.028] | 0.108 [0.093, 0.124] |
| macro | 0.332 [0.167, 0.506] | 0.035 [0.027, 0.043] | 0.012 [0.009, 0.016] | 0.047 [0.039, 0.056] |

### All paired macro contrasts

| Contrast | Mean and interval | 20260930 | 20261001 | 20261002 |
|---|---:|---:|---:|---:|
| leagueews_minus_gru | 4.623 [4.223, 5.064] | 4.932 [4.465, 5.424] | 3.379 [2.911, 3.858] | 5.559 [5.046, 6.074] |
| leagueews_minus_independent | 0.445 [0.251, 0.644] | 1.053 [0.783, 1.332] | 0.024 [-0.250, 0.304] | 0.258 [-0.044, 0.566] |
| leagueews_minus_snapshot | 1.389 [1.135, 1.637] | 1.515 [1.191, 1.818] | 1.504 [1.173, 1.829] | 1.147 [0.842, 1.468] |
| leagueews_minus_tcn | 0.012 [-0.156, 0.178] | 0.802 [0.543, 1.067] | -0.318 [-0.561, -0.073] | -0.448 [-0.720, -0.198] |
| pcgrad_minus_gru | 4.990 [4.573, 5.463] | 4.724 [4.258, 5.214] | 4.140 [3.692, 4.615] | 6.107 [5.568, 6.672] |
| pcgrad_minus_independent | 0.812 [0.616, 1.021] | 0.845 [0.566, 1.108] | 0.786 [0.500, 1.064] | 0.805 [0.513, 1.093] |
| pcgrad_minus_leagueews | 0.367 [0.249, 0.490] | -0.208 [-0.399, -0.011] | 0.762 [0.558, 0.965] | 0.548 [0.302, 0.785] |
| pcgrad_minus_snapshot | 1.756 [1.493, 2.025] | 1.307 [1.003, 1.608] | 2.266 [1.953, 2.590] | 1.695 [1.373, 2.018] |
| pcgrad_minus_tcn | 0.379 [0.218, 0.542] | 0.594 [0.329, 0.865] | 0.444 [0.186, 0.678] | 0.099 [-0.169, 0.374] |

### Every seed at each event

| Seed | Event | PCGrad recall | Joint recall | Difference and interval |
|---|---|---:|---:|---:|
| 20260930 | baron | 20.611 | 21.012 | -0.401 [-0.911, 0.121] |
| 20260930 | dragon | 14.008 | 14.035 | -0.026 [-0.254, 0.206] |
| 20260930 | teamfight | 3.077 | 3.274 | -0.197 [-0.306, -0.087] |
| 20260930 | macro | 12.565 | 12.773 | -0.208 [-0.399, -0.011] |
| 20261001 | baron | 20.580 | 21.290 | -0.710 [-1.214, -0.184] |
| 20261001 | dragon | 14.812 | 12.358 | 2.454 [2.152, 2.744] |
| 20261001 | teamfight | 3.511 | 2.970 | 0.541 [0.412, 0.672] |
| 20261001 | macro | 12.968 | 12.206 | 0.762 [0.558, 0.965] |
| 20261002 | baron | 20.981 | 20.333 | 0.648 [0.031, 1.304] |
| 20261002 | dragon | 13.488 | 13.134 | 0.353 [0.088, 0.622] |
| 20261002 | teamfight | 3.642 | 3.001 | 0.642 [0.498, 0.790] |
| 20261002 | macro | 12.704 | 12.156 | 0.548 [0.302, 0.785] |

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
| pcgrad | baron | 20.580 | 20.981 | 0.223 |
| pcgrad | dragon | 13.488 | 14.812 | 0.667 |
| pcgrad | teamfight | 3.077 | 3.642 | 0.296 |
| pcgrad | macro | 12.565 | 12.968 | 0.204 |
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
| pcgrad | 20261001 | dragon | europe | 1.014000 |
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
| pcgrad | baron | 25.280 | 0.670 | 0.276 | 0.946 |
| pcgrad | dragon | 8.818 | 0.128 | 0.506 | 0.634 |
| pcgrad | teamfight | 3.452 | 0.339 | 0.259 | 0.599 |
| pcgrad | macro | 12.517 | 0.379 | 0.347 | 0.726 |
| snapshot | baron | 23.048 | 0.648 | 0.242 | 0.889 |
| snapshot | dragon | 8.912 | 0.124 | 0.415 | 0.539 |
| snapshot | teamfight | 3.538 | 0.461 | 0.233 | 0.694 |
| snapshot | macro | 11.833 | 0.411 | 0.297 | 0.707 |
| tcn | baron | 23.439 | 0.636 | 0.270 | 0.906 |
| tcn | dragon | 10.154 | 0.150 | 0.537 | 0.687 |
| tcn | teamfight | 3.487 | 0.354 | 0.262 | 0.616 |
| tcn | macro | 12.360 | 0.380 | 0.356 | 0.737 |

### Overall PCGrad minus ordinary joint differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | 1.738 [1.296, 2.194] | 0.062 [0.053, 0.071] | 0.009 [0.006, 0.012] | 0.071 [0.061, 0.081] |
| dragon | -0.827 [-0.993, -0.673] | -0.014 [-0.019, -0.010] | -0.021 [-0.027, -0.015] | -0.035 [-0.043, -0.027] |
| teamfight | -0.783 [-0.886, -0.685] | -0.105 [-0.115, -0.096] | -0.051 [-0.058, -0.044] | -0.156 [-0.168, -0.144] |
| macro | 0.043 [-0.121, 0.207] | -0.019 [-0.024, -0.014] | -0.021 [-0.024, -0.018] | -0.040 [-0.046, -0.035] |

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
| pcgrad | baron | 25.280 | 0.632 | 0.284 | 0.916 |
| pcgrad | dragon | 9.167 | 0.121 | 0.484 | 0.604 |
| pcgrad | teamfight | 3.481 | 0.331 | 0.246 | 0.577 |
| pcgrad | macro | 12.642 | 0.361 | 0.338 | 0.699 |
| snapshot | baron | 22.567 | 0.600 | 0.250 | 0.850 |
| snapshot | dragon | 9.436 | 0.115 | 0.390 | 0.505 |
| snapshot | teamfight | 3.404 | 0.442 | 0.208 | 0.650 |
| snapshot | macro | 11.802 | 0.386 | 0.283 | 0.668 |
| tcn | baron | 23.499 | 0.590 | 0.276 | 0.867 |
| tcn | dragon | 10.661 | 0.144 | 0.511 | 0.655 |
| tcn | teamfight | 3.548 | 0.346 | 0.249 | 0.594 |
| tcn | macro | 12.569 | 0.360 | 0.345 | 0.705 |

### Europe PCGrad minus ordinary joint differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | 1.925 [1.297, 2.582] | 0.061 [0.048, 0.073] | 0.007 [0.003, 0.012] | 0.068 [0.054, 0.082] |
| dragon | -0.944 [-1.194, -0.713] | -0.015 [-0.022, -0.008] | -0.024 [-0.033, -0.016] | -0.039 [-0.050, -0.028] |
| teamfight | -0.889 [-1.048, -0.733] | -0.108 [-0.120, -0.094] | -0.051 [-0.061, -0.042] | -0.159 [-0.177, -0.142] |
| macro | 0.031 [-0.199, 0.265] | -0.021 [-0.027, -0.014] | -0.023 [-0.027, -0.018] | -0.043 [-0.051, -0.035] |

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
| pcgrad | baron | 25.281 | 0.708 | 0.267 | 0.975 |
| pcgrad | dragon | 8.480 | 0.134 | 0.528 | 0.663 |
| pcgrad | teamfight | 3.423 | 0.348 | 0.272 | 0.620 |
| pcgrad | macro | 12.394 | 0.397 | 0.356 | 0.753 |
| snapshot | baron | 23.523 | 0.695 | 0.233 | 0.928 |
| snapshot | dragon | 8.404 | 0.132 | 0.441 | 0.573 |
| snapshot | teamfight | 3.674 | 0.480 | 0.257 | 0.737 |
| snapshot | macro | 11.867 | 0.436 | 0.310 | 0.746 |
| tcn | baron | 23.380 | 0.682 | 0.264 | 0.946 |
| tcn | dragon | 9.662 | 0.156 | 0.564 | 0.719 |
| tcn | teamfight | 3.426 | 0.362 | 0.276 | 0.638 |
| tcn | macro | 12.156 | 0.400 | 0.368 | 0.768 |

### Americas PCGrad minus ordinary joint differences

| Event | Recall and interval | False and interval | Late and interval | False plus late and interval |
|---|---:|---:|---:|---:|
| baron | 1.553 [0.932, 2.160] | 0.063 [0.051, 0.077] | 0.010 [0.005, 0.015] | 0.074 [0.060, 0.087] |
| dragon | -0.713 [-0.924, -0.498] | -0.014 [-0.021, -0.008] | -0.018 [-0.027, -0.010] | -0.032 [-0.043, -0.021] |
| teamfight | -0.676 [-0.808, -0.544] | -0.103 [-0.117, -0.090] | -0.050 [-0.059, -0.041] | -0.153 [-0.171, -0.137] |
| macro | 0.055 [-0.164, 0.274] | -0.018 [-0.025, -0.011] | -0.019 [-0.024, -0.015] | -0.037 [-0.045, -0.029] |

### All paired macro contrasts

| Contrast | Mean and interval | 20260930 | 20261001 | 20261002 |
|---|---:|---:|---:|---:|
| leagueews_minus_gru | -0.843 [-1.358, -0.307] | -0.742 [-1.330, -0.164] | -0.780 [-1.349, -0.186] | -1.007 [-1.678, -0.352] |
| leagueews_minus_independent | -0.270 [-0.559, 0.008] | 0.088 [-0.289, 0.462] | -1.000 [-1.409, -0.604] | 0.101 [-0.299, 0.494] |
| leagueews_minus_snapshot | 0.641 [0.311, 0.976] | 0.207 [-0.215, 0.636] | 1.307 [0.889, 1.734] | 0.409 [-0.007, 0.837] |
| leagueews_minus_tcn | 0.114 [-0.110, 0.330] | -0.279 [-0.613, 0.071] | 1.996 [1.661, 2.329] | -1.376 [-1.738, -1.019] |
| pcgrad_minus_gru | -0.800 [-1.314, -0.275] | -0.303 [-0.916, 0.276] | -0.824 [-1.416, -0.211] | -1.274 [-1.913, -0.591] |
| pcgrad_minus_independent | -0.228 [-0.527, 0.052] | 0.526 [0.145, 0.914] | -1.043 [-1.465, -0.641] | -0.166 [-0.568, 0.203] |
| pcgrad_minus_leagueews | 0.043 [-0.121, 0.207] | 0.439 [0.181, 0.700] | -0.044 [-0.309, 0.225] | -0.266 [-0.556, 0.022] |
| pcgrad_minus_snapshot | 0.684 [0.353, 1.033] | 0.646 [0.215, 1.068] | 1.263 [0.849, 1.685] | 0.142 [-0.259, 0.566] |
| pcgrad_minus_tcn | 0.157 [-0.072, 0.385] | 0.160 [-0.176, 0.516] | 1.952 [1.617, 2.277] | -1.642 [-1.992, -1.287] |

### Every seed at each event

| Seed | Event | PCGrad recall | Joint recall | Difference and interval |
|---|---|---:|---:|---:|
| 20260930 | baron | 25.671 | 23.110 | 2.561 [1.835, 3.314] |
| 20260930 | dragon | 7.882 | 8.915 | -1.033 [-1.281, -0.796] |
| 20260930 | teamfight | 3.531 | 3.743 | -0.212 [-0.343, -0.081] |
| 20260930 | macro | 12.362 | 11.923 | 0.439 [0.181, 0.700] |
| 20261001 | baron | 26.103 | 23.696 | 2.407 [1.682, 3.152] |
| 20261001 | dragon | 9.074 | 10.107 | -1.033 [-1.308, -0.786] |
| 20261001 | teamfight | 3.779 | 5.284 | -1.505 [-1.685, -1.322] |
| 20261001 | macro | 12.985 | 13.029 | -0.044 [-0.309, 0.225] |
| 20261002 | baron | 24.067 | 23.820 | 0.247 [-0.558, 1.053] |
| 20261002 | dragon | 9.498 | 9.913 | -0.415 [-0.698, -0.149] |
| 20261002 | teamfight | 3.046 | 3.678 | -0.631 [-0.792, -0.474] |
| 20261002 | macro | 12.204 | 12.470 | -0.266 [-0.556, 0.022] |

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
| pcgrad | baron | 24.067 | 26.103 | 1.073 |
| pcgrad | dragon | 7.882 | 9.498 | 0.838 |
| pcgrad | teamfight | 3.046 | 3.779 | 0.373 |
| pcgrad | macro | 12.204 | 12.985 | 0.413 |
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
| pcgrad | 20261001 | baron | americas | 1.002667 |
| tcn | 20261002 | baron | americas | 1.034000 |
