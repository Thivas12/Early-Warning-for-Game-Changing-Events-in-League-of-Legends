# Warning-efficiency aggregate tables

Recall is percent; differences are percentage points. Burden is false-plus-late warnings per match per event. Mixtures match EARLY cost, not later cost. Intervals are paired whole-match conditional 95% intervals. Budget means give equal weight to four fixed points, not additional matches.

## 10-30 seconds: four-budget mean, matched-early policy

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| leagueews | 16.321 / 0.6361 | 9.559 / 0.6419 | 2.424 / 0.6160 | 9.435 / 0.6313 |
| gru | 9.071 / 0.6161 | 7.145 / 0.6467 | 1.944 / 0.6121 | 6.054 / 0.6250 |
| tcn | 16.127 / 0.6505 | 9.688 / 0.6419 | 2.346 / 0.6104 | 9.387 / 0.6343 |
| snapshot | 14.060 / 0.6322 | 9.235 / 0.6490 | 2.166 / 0.6378 | 8.487 / 0.6397 |
| current_only | 14.455 / 0.6380 | 9.474 / 0.6453 | 2.224 / 0.6411 | 8.718 / 0.6414 |
| independent | 16.757 / 0.6308 | 9.241 / 0.6417 | 2.363 / 0.6180 | 9.453 / 0.6301 |
| pcgrad | 16.355 / 0.6371 | 9.610 / 0.6362 | 2.420 / 0.6102 | 9.462 / 0.6278 |

| Contrast | Macro recall difference [95%] | Burden difference [95%] | False difference | Late difference | Recall differences by seed |
|---|---:|---:|---:|---:|---|
| leagueews-minus-current_only | +0.7171 [+0.5431, +0.8813] | -0.0101 [-0.0178, -0.0026] | -0.02293 | +0.01281 | +0.8251, +0.7580, +0.5681 |
| leagueews-minus-gru | +3.3809 [+3.0613, +3.7204] | +0.0064 [-0.0085, +0.0205] | -0.09236 | +0.09871 | +2.9995, +3.0401, +4.1030 |
| leagueews-minus-independent | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | -0.00034 | +0.00152 | +0.1200, -0.0894, -0.0868 |
| leagueews-minus-snapshot | +0.9479 [+0.7639, +1.1342] | -0.0084 [-0.0172, +0.0005] | -0.02613 | +0.01776 | +0.9041, +1.0516, +0.8879 |
| leagueews-minus-tcn | +0.0476 [-0.0630, +0.1608] | -0.0030 [-0.0074, +0.0017] | -0.00630 | +0.00334 | +0.0106, +0.0769, +0.0554 |
| pcgrad-minus-independent | +0.0084 [-0.1270, +0.1536] | -0.0023 [-0.0076, +0.0032] | -0.00225 | -0.00006 | +0.2107, -0.1225, -0.0629 |
| pcgrad-minus-leagueews | +0.0272 [-0.0364, +0.0983] | -0.0035 [-0.0067, -0.0004] | -0.00191 | -0.00158 | +0.0907, -0.0331, +0.0239 |
| pcgrad-minus-tcn | +0.0748 [-0.0275, +0.1812] | -0.0065 [-0.0110, -0.0022] | -0.00821 | +0.00176 | +0.1013, +0.0438, +0.0793 |

### PCGrad-joint, deterministic

| Early budget | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +0.0873 [-0.0090, +0.1879] | -0.0010 [-0.0041, +0.0020] | +0.0978, +0.4311, -0.2670 |
| 0.5 | +0.1167 [-0.0093, +0.2438] | +0.0221 [+0.0175, +0.0266] | +0.5034, -0.2696, +0.1163 |
| 0.75 | +0.1331 [+0.0152, +0.2480] | +0.0241 [+0.0192, +0.0288] | -0.3095, +0.2668, +0.4420 |
| 1.0 | +0.3670 [+0.2489, +0.4900] | +0.0459 [+0.0401, +0.0517] | -0.2082, +0.7616, +0.5475 |
| mean | +0.1760 [+0.1065, +0.2496] | +0.0228 [+0.0200, +0.0255] | +0.0209, +0.2975, +0.2097 |

### PCGrad-joint, matched_early_mixture

| Early budget | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +0.0409 [-0.0473, +0.1366] | -0.0010 [-0.0043, +0.0021] | +0.1709, -0.0622, +0.0140 |
| 0.5 | -0.0069 [-0.1118, +0.1036] | -0.0049 [-0.0087, -0.0009] | +0.0429, -0.1200, +0.0565 |
| 0.75 | +0.0249 [-0.0806, +0.1291] | -0.0043 [-0.0090, +0.0001] | +0.1019, +0.0122, -0.0394 |
| 1.0 | +0.0498 [-0.0530, +0.1546] | -0.0038 [-0.0088, +0.0010] | +0.0473, +0.0374, +0.0647 |
| mean | +0.0272 [-0.0364, +0.0983] | -0.0035 [-0.0067, -0.0004] | +0.0907, -0.0331, +0.0239 |
## 20-60 seconds: four-budget mean, matched-early policy

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| leagueews | 17.211 / 0.6432 | 13.543 / 0.6254 | 3.603 / 0.6214 | 11.452 / 0.6300 |
| gru | 12.970 / 0.6192 | 15.971 / 0.6481 | 3.527 / 0.6125 | 10.823 / 0.6266 |
| tcn | 16.717 / 0.6520 | 13.256 / 0.6286 | 3.490 / 0.6192 | 11.155 / 0.6333 |
| snapshot | 16.418 / 0.6351 | 13.337 / 0.6323 | 3.330 / 0.6423 | 11.028 / 0.6366 |
| current_only | 17.104 / 0.6412 | 13.404 / 0.6277 | 3.612 / 0.6370 | 11.373 / 0.6353 |
| independent | 18.005 / 0.6351 | 13.208 / 0.6278 | 3.449 / 0.6198 | 11.554 / 0.6276 |
| pcgrad | 17.060 / 0.6385 | 13.174 / 0.6254 | 3.518 / 0.6254 | 11.251 / 0.6297 |

| Contrast | Macro recall difference [95%] | Burden difference [95%] | False difference | Late difference | Recall differences by seed |
|---|---:|---:|---:|---:|---|
| leagueews-minus-current_only | +0.0791 [-0.1184, +0.2619] | -0.0053 [-0.0124, +0.0017] | -0.01385 | +0.00856 | +0.2043, +0.1901, -0.1572 |
| leagueews-minus-gru | +0.6296 [+0.2694, +0.9920] | +0.0034 [-0.0108, +0.0173] | -0.09061 | +0.09405 | +0.0340, +0.1626, +1.6921 |
| leagueews-minus-independent | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | -0.00136 | +0.00379 | +0.1335, -0.3347, -0.1036 |
| leagueews-minus-snapshot | +0.4238 [+0.2114, +0.6347] | -0.0066 [-0.0144, +0.0013] | -0.02243 | +0.01586 | +0.2788, +0.4714, +0.5213 |
| leagueews-minus-tcn | +0.2977 [+0.1526, +0.4329] | -0.0033 [-0.0077, +0.0007] | -0.00296 | -0.00031 | +0.0664, +0.4455, +0.3811 |
| pcgrad-minus-independent | -0.3028 [-0.4930, -0.1204] | +0.0022 [-0.0031, +0.0071] | +0.00134 | +0.00082 | +0.0168, -0.5399, -0.3853 |
| pcgrad-minus-leagueews | -0.2013 [-0.3002, -0.1029] | -0.0003 [-0.0038, +0.0035] | +0.00271 | -0.00297 | -0.1168, -0.2053, -0.2817 |
| pcgrad-minus-tcn | +0.0964 [-0.0491, +0.2348] | -0.0035 [-0.0076, +0.0006] | -0.00025 | -0.00328 | -0.0504, +0.2402, +0.0994 |

### PCGrad-joint, deterministic

| Early budget | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +0.2359 [+0.1438, +0.3309] | +0.0107 [+0.0075, +0.0140] | -0.0092, +0.1128, +0.6040 |
| 0.5 | +0.0081 [-0.1253, +0.1370] | +0.0021 [-0.0014, +0.0059] | +0.0804, +0.7439, -0.8000 |
| 0.75 | -0.7694 [-0.9267, -0.6177] | -0.0273 [-0.0327, -0.0222] | -1.4332, -0.9480, +0.0729 |
| 1.0 | +0.0428 [-0.1210, +0.2068] | -0.0402 [-0.0459, -0.0347] | +0.4387, -0.0438, -0.2665 |
| mean | -0.1207 [-0.2008, -0.0427] | -0.0137 [-0.0166, -0.0107] | -0.2308, -0.0338, -0.0974 |

### PCGrad-joint, matched_early_mixture

| Early budget | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | -0.0803 [-0.1488, -0.0114] | -0.0004 [-0.0024, +0.0016] | -0.0902, -0.0573, -0.0933 |
| 0.5 | -0.1469 [-0.2826, -0.0108] | -0.0002 [-0.0037, +0.0034] | -0.1805, -0.0731, -0.1870 |
| 0.75 | -0.2799 [-0.4070, -0.1479] | -0.0006 [-0.0049, +0.0041] | -0.1236, -0.3618, -0.3543 |
| 1.0 | -0.2979 [-0.4296, -0.1613] | +0.0001 [-0.0051, +0.0059] | -0.0728, -0.3288, -0.4922 |
| mean | -0.2013 [-0.3002, -0.1029] | -0.0003 [-0.0038, +0.0035] | -0.1168, -0.2053, -0.2817 |

## All prespecified gates

| Gate | Result |
|---|---|
| consistent_across_budgets | False |
| no_extra_burden | True |
| no_mean_event_harm | False |
| positive_recall | False |
| regional_hard_budget | False |
| warning_efficiency_screen | False |

## Regional PCGrad-joint, budget-mean matched-early primary

| Region | Event | Recall difference [95%] | Burden difference [95%] |
|---|---|---:|---:|
| europe | baron | +0.0554 [-0.1948, +0.3239] | -0.0016 [-0.0083, +0.0054] |
| europe | dragon | +0.1030 [-0.0167, +0.2209] | -0.0045 [-0.0107, +0.0015] |
| europe | macro | +0.0410 [-0.0563, +0.1402] | -0.0050 [-0.0091, -0.0009] |
| europe | teamfight | -0.0353 [-0.0906, +0.0176] | -0.0088 [-0.0165, -0.0012] |
| americas | baron | +0.0136 [-0.2285, +0.2598] | +0.0038 [-0.0038, +0.0117] |
| americas | dragon | -0.0004 [-0.1207, +0.1233] | -0.0069 [-0.0135, -0.0005] |
| americas | macro | +0.0141 [-0.0814, +0.1116] | -0.0020 [-0.0066, +0.0027] |
| americas | teamfight | +0.0291 [-0.0320, +0.0912] | -0.0029 [-0.0119, +0.0068] |

All seed/region/event/lead/budget failures, including below the hard-one limit, are in `budget-violations.csv`; denominators and expected counts are in `aggregate-counts.csv`. All models' seed points are in `by-seed.csv`; every conditional interval is in `analysis.json`. Seed order is 20260930, 20261001, 20261002.
