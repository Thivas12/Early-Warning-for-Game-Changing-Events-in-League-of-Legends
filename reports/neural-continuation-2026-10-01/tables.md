# League neural study tables

Recall is a percentage; recall differences are percentage points. Burden is false-plus-late warnings per match. Brackets contain conditional 95% paired whole-match bootstrap intervals. Seed means average fixed model performances; the three seeds are not independent match populations.

## Useful lead of 10 to 30 seconds

| Family | Event | Mean recall and interval | Recall seed range | Mean burden and interval |
|---|---|---|---|---|
| LeagueEWS | baron | 20.878 [19.636, 22.178] | 20.333 to 21.290 | 0.948 [0.907, 0.993] |
| LeagueEWS | dragon | 13.176 [12.645, 13.723] | 12.358 to 14.035 | 0.889 [0.857, 0.921] |
| LeagueEWS | teamfight | 3.082 [2.856, 3.304] | 2.970 to 3.274 | 0.758 [0.727, 0.793] |
| LeagueEWS | macro | 12.379 [11.903, 12.860] | 12.156 to 12.773 | 0.865 [0.840, 0.892] |
| GRU | baron | 12.085 [11.159, 13.047] | 9.534 to 15.088 | 0.851 [0.815, 0.889] |
| GRU | dragon | 8.977 [8.539, 9.416] | 8.094 to 9.877 | 0.822 [0.795, 0.849] |
| GRU | teamfight | 2.204 [2.038, 2.374] | 2.016 to 2.435 | 0.681 [0.654, 0.708] |
| GRU | macro | 7.755 [7.403, 8.108] | 6.597 to 8.827 | 0.785 [0.764, 0.807] |
| TCN | baron | 20.734 [19.430, 22.031] | 20.457 to 20.981 | 0.966 [0.924, 1.011] |
| TCN | dragon | 13.532 [13.007, 14.088] | 12.402 to 14.820 | 0.899 [0.868, 0.932] |
| TCN | teamfight | 2.834 [2.609, 3.044] | 2.536 to 3.218 | 0.726 [0.695, 0.759] |
| TCN | macro | 12.367 [11.880, 12.842] | 11.972 to 12.604 | 0.864 [0.839, 0.891] |
| Snapshot | baron | 18.636 [17.432, 19.905] | 18.050 to 19.192 | 0.947 [0.905, 0.991] |
| Snapshot | dragon | 11.743 [11.250, 12.257] | 11.554 to 11.987 | 0.826 [0.797, 0.857] |
| Snapshot | teamfight | 2.590 [2.372, 2.799] | 2.501 to 2.672 | 0.760 [0.724, 0.799] |
| Snapshot | macro | 10.990 [10.550, 11.457] | 10.702 to 11.258 | 0.845 [0.819, 0.871] |

### Macro recall by seed

| Family | Seed | Macro recall and interval | All event and region budgets met |
|---|---|---|---|
| LeagueEWS | 20260930 | 12.773 [12.271, 13.284] | True |
| LeagueEWS | 20261001 | 12.206 [11.702, 12.697] | False |
| LeagueEWS | 20261002 | 12.156 [11.679, 12.660] | True |
| GRU | 20260930 | 7.842 [7.453, 8.240] | True |
| GRU | 20261001 | 8.827 [8.382, 9.250] | False |
| GRU | 20261002 | 6.597 [6.238, 6.979] | True |
| TCN | 20260930 | 11.972 [11.473, 12.464] | False |
| TCN | 20261001 | 12.524 [12.014, 13.047] | False |
| TCN | 20261002 | 12.604 [12.107, 13.123] | False |
| Snapshot | 20260930 | 11.258 [10.800, 11.750] | False |
| Snapshot | 20261001 | 10.702 [10.251, 11.186] | True |
| Snapshot | 20261002 | 11.009 [10.546, 11.480] | True |

### Paired macro recall differences

LeagueEWS minus GRU at 10-30 seconds is primary. Other contrasts are exploratory.

| Contrast | Mean difference and interval | 20260930 | 20261001 | 20261002 |
|---|---|---|---|---|
| gru minus snapshot | -3.234 [-3.645, -2.847] | -3.417 [-3.866, -2.987] | -1.874 [-2.317, -1.463] | -4.412 [-4.926, -3.891] |
| leagueews minus gru | 4.623 [4.223, 5.064] | 4.932 [4.465, 5.424] | 3.379 [2.911, 3.858] | 5.559 [5.046, 6.074] |
| leagueews minus snapshot | 1.389 [1.135, 1.637] | 1.515 [1.191, 1.818] | 1.504 [1.173, 1.829] | 1.147 [0.842, 1.468] |
| leagueews minus tcn | 0.012 [-0.156, 0.178] | 0.802 [0.543, 1.067] | -0.318 [-0.561, -0.073] | -0.448 [-0.720, -0.198] |
| tcn minus gru | 4.611 [4.205, 5.050] | 4.130 [3.668, 4.603] | 3.697 [3.237, 4.169] | 6.007 [5.492, 6.544] |
| tcn minus snapshot | 1.377 [1.115, 1.627] | 0.713 [0.397, 1.025] | 1.822 [1.485, 2.161] | 1.596 [1.283, 1.910] |

### Regional event results averaged over fixed seeds

| Family | Event | Europe recall | Europe burden | Americas recall | Americas burden |
|---|---|---|---|---|---|
| LeagueEWS | baron | 21.201 | 0.904 | 20.560 | 0.992 |
| LeagueEWS | dragon | 13.051 | 0.899 | 13.296 | 0.878 |
| LeagueEWS | teamfight | 3.097 | 0.752 | 3.066 | 0.763 |
| GRU | baron | 12.195 | 0.780 | 11.976 | 0.922 |
| GRU | dragon | 8.862 | 0.799 | 9.088 | 0.845 |
| GRU | teamfight | 2.288 | 0.664 | 2.119 | 0.697 |
| TCN | baron | 21.097 | 0.915 | 20.376 | 1.017 |
| TCN | dragon | 13.296 | 0.900 | 13.760 | 0.899 |
| TCN | teamfight | 2.856 | 0.718 | 2.811 | 0.734 |
| Snapshot | baron | 19.586 | 0.899 | 17.699 | 0.996 |
| Snapshot | dragon | 11.587 | 0.830 | 11.894 | 0.823 |
| Snapshot | teamfight | 2.452 | 0.723 | 2.730 | 0.798 |

### Regional budget failures

Each budget is per event and region. A mean below one does not erase a failing seed.

| Family | Seed | Event | Route | False plus late per match |
|---|---|---|---|---|
| LeagueEWS | 20261001 | baron | americas | 1.011333 |
| GRU | 20261001 | baron | americas | 1.012000 |
| TCN | 20260930 | baron | americas | 1.020000 |
| TCN | 20261001 | baron | americas | 1.026000 |
| TCN | 20261002 | baron | americas | 1.004000 |
| Snapshot | 20260930 | baron | americas | 1.032000 |

## Useful lead of 20 to 60 seconds

| Family | Event | Mean recall and interval | Recall seed range | Mean burden and interval |
|---|---|---|---|---|
| LeagueEWS | baron | 23.542 [22.226, 24.982] | 23.110 to 23.820 | 0.875 [0.834, 0.914] |
| LeagueEWS | dragon | 9.645 [9.174, 10.140] | 8.915 to 10.107 | 0.669 [0.642, 0.696] |
| LeagueEWS | teamfight | 4.235 [3.980, 4.489] | 3.678 to 5.284 | 0.755 [0.722, 0.789] |
| LeagueEWS | macro | 12.474 [11.972, 12.993] | 11.923 to 13.029 | 0.766 [0.743, 0.790] |
| GRU | baron | 18.564 [17.468, 19.662] | 14.286 to 21.166 | 0.885 [0.847, 0.924] |
| GRU | dragon | 18.130 [17.580, 18.676] | 14.838 to 22.191 | 0.738 [0.711, 0.765] |
| GRU | teamfight | 3.257 [3.049, 3.473] | 2.900 to 3.956 | 0.542 [0.517, 0.567] |
| GRU | macro | 13.317 [12.889, 13.733] | 12.665 to 13.810 | 0.722 [0.702, 0.744] |
| TCN | baron | 23.439 [22.102, 24.873] | 21.660 to 25.949 | 0.906 [0.864, 0.948] |
| TCN | dragon | 10.154 [9.676, 10.644] | 7.803 to 12.340 | 0.687 [0.661, 0.715] |
| TCN | teamfight | 3.487 [3.252, 3.710] | 3.248 to 3.637 | 0.616 [0.588, 0.647] |
| TCN | macro | 12.360 [11.879, 12.861] | 11.033 to 13.846 | 0.737 [0.714, 0.761] |
| Snapshot | baron | 23.048 [21.677, 24.472] | 21.135 to 24.375 | 0.889 [0.848, 0.933] |
| Snapshot | dragon | 8.912 [8.474, 9.390] | 8.421 to 9.833 | 0.539 [0.515, 0.564] |
| Snapshot | teamfight | 3.538 [3.301, 3.767] | 2.369 to 4.178 | 0.694 [0.657, 0.731] |
| Snapshot | macro | 11.833 [11.339, 12.342] | 11.715 to 12.061 | 0.707 [0.683, 0.733] |

### Macro recall by seed

| Family | Seed | Macro recall and interval | All event and region budgets met |
|---|---|---|---|
| LeagueEWS | 20260930 | 11.923 [11.397, 12.473] | True |
| LeagueEWS | 20261001 | 13.029 [12.504, 13.569] | True |
| LeagueEWS | 20261002 | 12.470 [11.927, 13.026] | True |
| GRU | 20260930 | 12.665 [12.169, 13.156] | True |
| GRU | 20261001 | 13.810 [13.275, 14.340] | False |
| GRU | 20261002 | 13.477 [13.034, 13.943] | True |
| TCN | 20260930 | 12.201 [11.684, 12.732] | True |
| TCN | 20261001 | 11.033 [10.519, 11.583] | True |
| TCN | 20261002 | 13.846 [13.309, 14.411] | False |
| Snapshot | 20260930 | 11.715 [11.226, 12.240] | True |
| Snapshot | 20261001 | 11.722 [11.193, 12.287] | True |
| Snapshot | 20261002 | 12.061 [11.527, 12.602] | True |

### Paired macro recall differences

LeagueEWS minus GRU at 10-30 seconds is primary. Other contrasts are exploratory.

| Contrast | Mean difference and interval | 20260930 | 20261001 | 20261002 |
|---|---|---|---|---|
| gru minus snapshot | 1.484 [0.975, 1.991] | 0.949 [0.384, 1.529] | 2.088 [1.515, 2.625] | 1.416 [0.754, 2.067] |
| leagueews minus gru | -0.843 [-1.358, -0.307] | -0.742 [-1.330, -0.164] | -0.780 [-1.349, -0.186] | -1.007 [-1.678, -0.352] |
| leagueews minus snapshot | 0.641 [0.311, 0.976] | 0.207 [-0.215, 0.636] | 1.307 [0.889, 1.734] | 0.409 [-0.007, 0.837] |
| leagueews minus tcn | 0.114 [-0.110, 0.330] | -0.279 [-0.613, 0.071] | 1.996 [1.661, 2.329] | -1.376 [-1.738, -1.019] |
| tcn minus gru | -0.957 [-1.479, -0.422] | -0.463 [-1.086, 0.131] | -2.776 [-3.317, -2.197] | 0.368 [-0.312, 1.048] |
| tcn minus snapshot | 0.527 [0.197, 0.852] | 0.486 [0.074, 0.886] | -0.688 [-1.099, -0.282] | 1.784 [1.347, 2.210] |

### Regional event results averaged over fixed seeds

| Family | Event | Europe recall | Europe burden | Americas recall | Americas burden |
|---|---|---|---|---|---|
| LeagueEWS | baron | 23.354 | 0.848 | 23.728 | 0.902 |
| LeagueEWS | dragon | 10.111 | 0.643 | 9.193 | 0.694 |
| LeagueEWS | teamfight | 4.370 | 0.735 | 4.098 | 0.774 |
| GRU | baron | 18.157 | 0.820 | 18.966 | 0.950 |
| GRU | dragon | 18.011 | 0.726 | 18.246 | 0.750 |
| GRU | teamfight | 3.157 | 0.536 | 3.358 | 0.548 |
| TCN | baron | 23.499 | 0.867 | 23.380 | 0.946 |
| TCN | dragon | 10.661 | 0.655 | 9.662 | 0.719 |
| TCN | teamfight | 3.548 | 0.594 | 3.426 | 0.638 |
| Snapshot | baron | 22.567 | 0.850 | 23.523 | 0.928 |
| Snapshot | dragon | 9.436 | 0.505 | 8.404 | 0.573 |
| Snapshot | teamfight | 3.404 | 0.650 | 3.674 | 0.737 |

### Regional budget failures

Each budget is per event and region. A mean below one does not erase a failing seed.

| Family | Seed | Event | Route | False plus late per match |
|---|---|---|---|---|
| GRU | 20261001 | baron | americas | 1.004000 |
| TCN | 20261002 | baron | americas | 1.034000 |

