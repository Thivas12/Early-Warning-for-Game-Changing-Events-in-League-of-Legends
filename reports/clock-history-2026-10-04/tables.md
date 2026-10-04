# Useful-lead conditional-history evidence

Recall is percent; differences are percentage points. Burden is false-plus-late warnings per match per event. Intervals are pointwise conditional 95% intervals from paired whole-match bootstrap draws. The four-budget mean averages fixed operating points, not independent matches. Seed order: 20260930, 20261001, 20261002. These adaptively selected studies use previously inspected calibration matches.

## 10-30-second warnings

### Four-budget matched-early mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| leagueews | 16.321 / 0.6361 | 9.559 / 0.6419 | 2.424 / 0.6160 | 9.435 / 0.6313 |
| gru | 9.071 / 0.6161 | 7.145 / 0.6467 | 1.944 / 0.6121 | 6.054 / 0.6250 |
| tcn | 16.127 / 0.6505 | 9.688 / 0.6419 | 2.346 / 0.6104 | 9.387 / 0.6343 |
| snapshot | 14.060 / 0.6322 | 9.235 / 0.6490 | 2.166 / 0.6378 | 8.487 / 0.6397 |
| current_only | 14.455 / 0.6380 | 9.474 / 0.6453 | 2.224 / 0.6411 | 8.718 / 0.6414 |
| independent | 16.757 / 0.6308 | 9.241 / 0.6417 | 2.363 / 0.6180 | 9.453 / 0.6301 |
| pcgrad | 16.355 / 0.6371 | 9.610 / 0.6362 | 2.420 / 0.6102 | 9.462 / 0.6278 |
| timely_leagueews | 16.276 / 0.6380 | 10.723 / 0.6357 | 2.656 / 0.6052 | 9.885 / 0.6263 |
| timely_tcn | 16.183 / 0.6489 | 10.378 / 0.6353 | 2.568 / 0.6086 | 9.710 / 0.6309 |
| timely_current_only | 14.744 / 0.6412 | 10.538 / 0.6328 | 2.423 / 0.6343 | 9.235 / 0.6361 |
| timely_clock_only | 9.737 / 0.6346 | 9.654 / 0.6373 | 1.463 / 0.6348 | 6.952 / 0.6356 |
| timely_clock_history | 14.943 / 0.6425 | 10.675 / 0.6348 | 2.438 / 0.6365 | 9.352 / 0.6379 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | -0.0671 [-0.1766, +0.0509] | +0.0003 [-0.0063, +0.0073] | -0.0837, -0.0126, -0.1051 |
| leagueews-minus-current_only | +0.7171 [+0.5431, +0.8813] | -0.0101 [-0.0178, -0.0026] | +0.8251, +0.7580, +0.5681 |
| leagueews-minus-gru | +3.3809 [+3.0613, +3.7204] | +0.0064 [-0.0085, +0.0205] | +2.9995, +3.0401, +4.1030 |
| leagueews-minus-independent | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | +0.1200, -0.0894, -0.0868 |
| leagueews-minus-snapshot | +0.9479 [+0.7639, +1.1342] | -0.0084 [-0.0172, +0.0005] | +0.9041, +1.0516, +0.8879 |
| leagueews-minus-tcn | +0.0476 [-0.0630, +0.1608] | -0.0030 [-0.0074, +0.0017] | +0.0106, +0.0769, +0.0554 |
| timely_clock_history-minus-timely_current_only | +0.1170 [+0.0140, +0.2186] | +0.0018 [-0.0025, +0.0061] | +0.0184, +0.1838, +0.1488 |
| timely_current_only-minus-current_only | +0.5176 [+0.3858, +0.6438] | -0.0053 [-0.0133, +0.0030] | +0.6248, +0.4581, +0.4699 |
| timely_leagueews-minus-leagueews | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |
| timely_leagueews-minus-timely_clock_history | +0.5330 [+0.3739, +0.6958] | -0.0117 [-0.0193, -0.0038] | +0.7230, +0.5616, +0.3142 |
| timely_leagueews-minus-timely_clock_only | +2.9334 [+2.6308, +3.2524] | -0.0093 [-0.0214, +0.0033] | +3.0772, +2.9184, +2.8047 |
| timely_leagueews-minus-timely_current_only | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |
| timely_leagueews-minus-timely_tcn | +0.1757 [+0.0613, +0.2903] | -0.0047 [-0.0097, +0.0005] | +0.2784, +0.1977, +0.0509 |

### Paired history components by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_clock_history: baron | +1.3331 [+0.8923, +1.7774] | -0.0046 [-0.0168, +0.0070] | +1.8999, +1.3822, +0.7172 |
| timely_leagueews-minus-timely_clock_history: dragon | +0.0474 [-0.1222, +0.2020] | +0.0009 [-0.0079, +0.0091] | +0.0185, +0.0803, +0.0435 |
| timely_leagueews-minus-timely_clock_history: teamfight | +0.2183 [+0.0928, +0.3436] | -0.0313 [-0.0492, -0.0132] | +0.2506, +0.2223, +0.1820 |
| timely_leagueews-minus-timely_clock_history: macro | +0.5330 [+0.3739, +0.6958] | -0.0117 [-0.0193, -0.0038] | +0.7230, +0.5616, +0.3142 |
| timely_clock_history-minus-timely_current_only: baron | +0.1988 [-0.0794, +0.4815] | +0.0014 [-0.0061, +0.0084] | -0.0666, +0.3406, +0.3224 |
| timely_clock_history-minus-timely_current_only: dragon | +0.1376 [+0.0143, +0.2633] | +0.0020 [-0.0048, +0.0089] | +0.0645, +0.2112, +0.1373 |
| timely_clock_history-minus-timely_current_only: teamfight | +0.0146 [-0.0329, +0.0670] | +0.0022 [-0.0061, +0.0103] | +0.0574, -0.0003, -0.0132 |
| timely_clock_history-minus-timely_current_only: macro | +0.1170 [+0.0140, +0.2186] | +0.0018 [-0.0025, +0.0061] | +0.0184, +0.1838, +0.1488 |
| timely_leagueews-minus-timely_current_only: baron | +1.5319 [+1.0534, +2.0068] | -0.0032 [-0.0166, +0.0097] | +1.8333, +1.7228, +1.0396 |
| timely_leagueews-minus-timely_current_only: dragon | +0.1851 [+0.0183, +0.3491] | +0.0029 [-0.0055, +0.0109] | +0.0830, +0.2915, +0.1808 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.2330 [+0.1078, +0.3600] | -0.0292 [-0.0483, -0.0102] | +0.3080, +0.2221, +0.1688 |
| timely_leagueews-minus-timely_current_only: macro | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |

### Conditional non-timing history: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2926 [+0.0993, +0.4917] | -0.0133 [-0.0193, -0.0074] | +0.2496, +0.8303, -0.2021 |
| 0.5 | +0.9385 [+0.7145, +1.1532] | +0.0100 [+0.0013, +0.0189] | +0.2485, +1.1058, +1.4612 |
| 0.75 | +0.7710 [+0.5414, +1.0049] | +0.0510 [+0.0417, +0.0606] | +0.8845, +1.0281, +0.4006 |
| 1.0 | -0.0461 [-0.2619, +0.1650] | -0.0815 [-0.0930, -0.0699] | +0.5942, -0.5474, -0.1850 |
| mean | +0.4890 [+0.3256, +0.6471] | -0.0085 [-0.0153, -0.0011] | +0.4942, +0.6042, +0.3687 |

### Conditional non-timing history: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2926 [+0.0993, +0.4917] | -0.0133 [-0.0193, -0.0074] | +0.2496, +0.8303, -0.2021 |
| 0.5 | +1.0173 [+0.7993, +1.2384] | +0.0141 [+0.0055, +0.0229] | +0.4850, +1.1058, +1.4612 |
| 0.75 | +1.0545 [+0.8155, +1.2858] | +0.0693 [+0.0600, +0.0794] | +1.7347, +1.0281, +0.4006 |
| 1.0 | +0.0225 [-0.1905, +0.2424] | -0.0753 [-0.0869, -0.0637] | +0.5942, -0.3417, -0.1850 |
| mean | +0.5967 [+0.4387, +0.7561] | -0.0013 [-0.0081, +0.0061] | +0.7659, +0.6556, +0.3687 |

### Conditional non-timing history: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.4584 [+0.2839, +0.6345] | -0.0068 [-0.0127, -0.0008] | +0.7205, +0.6156, +0.0390 |
| 0.5 | +0.5191 [+0.3124, +0.7276] | -0.0140 [-0.0221, -0.0056] | +0.6149, +0.4906, +0.4519 |
| 0.75 | +0.5347 [+0.3188, +0.7436] | -0.0139 [-0.0238, -0.0038] | +0.6829, +0.5504, +0.3709 |
| 1.0 | +0.6196 [+0.4176, +0.8208] | -0.0120 [-0.0232, -0.0013] | +0.8737, +0.5899, +0.3952 |
| mean | +0.5330 [+0.3739, +0.6958] | -0.0117 [-0.0193, -0.0038] | +0.7230, +0.5616, +0.3142 |

### Conditional non-timing history: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.5090 [+0.3011, +0.7188] | -0.0022 [-0.0093, +0.0048] | +0.7637, +0.6078, +0.1556 |
| 0.5 | +0.5767 [+0.3435, +0.8036] | -0.0078 [-0.0169, +0.0019] | +0.7285, +0.6810, +0.3206 |
| 0.75 | +0.4619 [+0.2324, +0.6925] | -0.0176 [-0.0284, -0.0066] | +0.5759, +0.5727, +0.2369 |
| 1.0 | +0.5866 [+0.3622, +0.8042] | -0.0080 [-0.0196, +0.0034] | +0.7337, +0.6686, +0.3575 |
| mean | +0.5335 [+0.3697, +0.6975] | -0.0089 [-0.0163, -0.0010] | +0.7005, +0.6325, +0.2676 |

### Conditional non-timing history: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.5014 [+0.2930, +0.7110] | -0.0038 [-0.0109, +0.0035] | +0.7111, +0.5591, +0.2339 |
| 0.5 | +0.5096 [+0.2850, +0.7336] | -0.0132 [-0.0224, -0.0035] | +0.6182, +0.6414, +0.2691 |
| 0.75 | +0.5849 [+0.3542, +0.8232] | -0.0125 [-0.0234, -0.0014] | +0.7835, +0.6907, +0.2803 |
| 1.0 | +0.6231 [+0.3992, +0.8491] | -0.0094 [-0.0210, +0.0023] | +0.7718, +0.6885, +0.4089 |
| mean | +0.5547 [+0.3924, +0.7180] | -0.0097 [-0.0174, -0.0018] | +0.7212, +0.6449, +0.2981 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_leagueews-minus-timely_clock_history: baron | +1.3158 [+0.6550, +1.9890] | +0.0018 [-0.0150, +0.0176] | +2.0005, +1.2522, +0.6947 |
| europe: timely_leagueews-minus-timely_clock_history: dragon | +0.0586 [-0.1906, +0.3000] | +0.0068 [-0.0053, +0.0193] | +0.0184, +0.2681, -0.1109 |
| europe: timely_leagueews-minus-timely_clock_history: teamfight | +0.2899 [+0.1227, +0.4620] | -0.0406 [-0.0651, -0.0143] | +0.2598, +0.4176, +0.1923 |
| europe: timely_leagueews-minus-timely_clock_history: macro | +0.5548 [+0.2951, +0.8057] | -0.0107 [-0.0209, +0.0002] | +0.7596, +0.6460, +0.2587 |
| europe: timely_clock_history-minus-timely_current_only: baron | +0.1488 [-0.2540, +0.5383] | +0.0003 [-0.0093, +0.0100] | -0.2646, +0.2972, +0.4139 |
| europe: timely_clock_history-minus-timely_current_only: dragon | +0.0298 [-0.1551, +0.2107] | -0.0107 [-0.0195, -0.0013] | -0.0557, +0.1107, +0.0345 |
| europe: timely_clock_history-minus-timely_current_only: teamfight | -0.0221 [-0.0906, +0.0478] | +0.0026 [-0.0086, +0.0130] | +0.0328, -0.0760, -0.0231 |
| europe: timely_clock_history-minus-timely_current_only: macro | +0.0522 [-0.0893, +0.1898] | -0.0026 [-0.0085, +0.0033] | -0.0958, +0.1106, +0.1417 |
| europe: timely_leagueews-minus-timely_current_only: baron | +1.4646 [+0.7576, +2.1575] | +0.0021 [-0.0158, +0.0192] | +1.7360, +1.5494, +1.1086 |
| europe: timely_leagueews-minus-timely_current_only: dragon | +0.0884 [-0.1754, +0.3210] | -0.0039 [-0.0155, +0.0077] | -0.0373, +0.3789, -0.0764 |
| europe: timely_leagueews-minus-timely_current_only: teamfight | +0.2678 [+0.0921, +0.4354] | -0.0380 [-0.0662, -0.0093] | +0.2927, +0.3417, +0.1692 |
| europe: timely_leagueews-minus-timely_current_only: macro | +0.6070 [+0.3423, +0.8661] | -0.0133 [-0.0246, -0.0015] | +0.6638, +0.7566, +0.4005 |
| americas: timely_leagueews-minus-timely_clock_history: baron | +1.3502 [+0.7611, +1.9274] | -0.0110 [-0.0285, +0.0063] | +1.8007, +1.5106, +0.7394 |
| americas: timely_leagueews-minus-timely_clock_history: dragon | +0.0366 [-0.1899, +0.2616] | -0.0051 [-0.0178, +0.0078] | +0.0186, -0.1019, +0.1932 |
| americas: timely_leagueews-minus-timely_clock_history: teamfight | +0.1455 [-0.0415, +0.3308] | -0.0221 [-0.0467, +0.0017] | +0.2412, +0.0239, +0.1715 |
| americas: timely_leagueews-minus-timely_clock_history: macro | +0.5108 [+0.2931, +0.7205] | -0.0127 [-0.0235, -0.0023] | +0.6868, +0.4775, +0.3680 |
| americas: timely_clock_history-minus-timely_current_only: baron | +0.2481 [-0.1367, +0.6268] | +0.0025 [-0.0077, +0.0132] | +0.1288, +0.3834, +0.2322 |
| americas: timely_clock_history-minus-timely_current_only: dragon | +0.2422 [+0.0708, +0.4139] | +0.0147 [+0.0048, +0.0248] | +0.1810, +0.3087, +0.2370 |
| americas: timely_clock_history-minus-timely_current_only: teamfight | +0.0520 [-0.0182, +0.1196] | +0.0018 [-0.0096, +0.0137] | +0.0823, +0.0767, -0.0031 |
| americas: timely_clock_history-minus-timely_current_only: macro | +0.1808 [+0.0375, +0.3198] | +0.0063 [+0.0001, +0.0131] | +0.1307, +0.2563, +0.1554 |
| americas: timely_leagueews-minus-timely_current_only: baron | +1.5984 [+0.9719, +2.2381] | -0.0085 [-0.0269, +0.0106] | +1.9295, +1.8940, +0.9716 |
| americas: timely_leagueews-minus-timely_current_only: dragon | +0.2788 [+0.0471, +0.5062] | +0.0096 [-0.0029, +0.0218] | +0.1996, +0.2068, +0.4302 |
| americas: timely_leagueews-minus-timely_current_only: teamfight | +0.1975 [+0.0133, +0.3812] | -0.0203 [-0.0457, +0.0058] | +0.3236, +0.1006, +0.1684 |
| americas: timely_leagueews-minus-timely_current_only: macro | +0.6916 [+0.4665, +0.9219] | -0.0064 [-0.0173, +0.0052] | +0.8175, +0.7338, +0.5234 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_clock_history: baron | +1.3473 [+0.7719, +1.9233] | -0.0126 [-0.0326, +0.0070] | +2.0364, +1.2033, +0.8022 |
| timely_leagueews-minus-timely_clock_history: dragon | +0.0588 [-0.2066, +0.3161] | -0.0140 [-0.0277, +0.0006] | -0.3001, +0.4590, +0.0177 |
| timely_leagueews-minus-timely_clock_history: teamfight | +0.3536 [+0.1662, +0.5418] | +0.0026 [-0.0240, +0.0298] | +0.4648, +0.3435, +0.2526 |
| timely_leagueews-minus-timely_clock_history: macro | +0.5866 [+0.3622, +0.8042] | -0.0080 [-0.0196, +0.0034] | +0.7337, +0.6686, +0.3575 |
| timely_clock_history-minus-timely_current_only: baron | +0.3291 [-0.1148, +0.7845] | +0.0067 [-0.0058, +0.0184] | +0.0617, +0.8639, +0.0617 |
| timely_clock_history-minus-timely_current_only: dragon | +0.1618 [-0.0148, +0.3512] | +0.0058 [-0.0051, +0.0176] | +0.1059, +0.2383, +0.1412 |
| timely_clock_history-minus-timely_current_only: teamfight | +0.0370 [-0.0478, +0.1268] | +0.0007 [-0.0129, +0.0151] | +0.0303, +0.0455, +0.0354 |
| timely_clock_history-minus-timely_current_only: macro | +0.1760 [+0.0197, +0.3452] | +0.0044 [-0.0030, +0.0120] | +0.0660, +0.3826, +0.0794 |
| timely_leagueews-minus-timely_current_only: baron | +1.6764 [+1.0707, +2.2915] | -0.0059 [-0.0267, +0.0141] | +2.0981, +2.0673, +0.8639 |
| timely_leagueews-minus-timely_current_only: dragon | +0.2207 [-0.0294, +0.4686] | -0.0082 [-0.0220, +0.0058] | -0.1942, +0.6973, +0.1589 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.3907 [+0.1989, +0.5811] | +0.0032 [-0.0260, +0.0321] | +0.4951, +0.3890, +0.2880 |
| timely_leagueews-minus-timely_current_only: macro | +0.7626 [+0.5278, +0.9924] | -0.0036 [-0.0160, +0.0087] | +0.7997, +1.0512, +0.4369 |

### Original registered model comparisons, unchanged policy

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| leagueews-minus-gru: baron | +8.7936 [+7.7853, +9.8901] | +0.0969 [+0.0582, +0.1340] | +9.3798, +6.2018, +10.7991 |
| leagueews-minus-gru: dragon | +4.1987 [+3.6117, +4.7824] | +0.0667 [+0.0337, +0.0959] | +4.1575, +3.3984, +5.0402 |
| leagueews-minus-gru: teamfight | +0.8773 [+0.6747, +1.0723] | +0.0772 [+0.0481, +0.1056] | +1.2579, +0.5355, +0.8386 |
| leagueews-minus-gru: macro | +4.6232 [+4.2226, +5.0636] | +0.0803 [+0.0591, +0.1000] | +4.9317, +3.3785, +5.5593 |
| leagueews-minus-tcn: baron | +0.1440 [-0.2788, +0.5773] | -0.0179 [-0.0325, -0.0040] | +0.2468, +0.3085, -0.1234 |
| leagueews-minus-tcn: dragon | -0.3560 [-0.5589, -0.1463] | -0.0104 [-0.0213, -0.0001] | +1.6330, -1.0151, -1.6859 |
| leagueews-minus-tcn: teamfight | +0.2475 [+0.1405, +0.3520] | +0.0318 [+0.0186, +0.0450] | +0.5254, -0.2475, +0.4648 |
| leagueews-minus-tcn: macro | +0.0118 [-0.1564, +0.1777] | +0.0011 [-0.0062, +0.0084] | +0.8017, -0.3180, -0.4482 |
| leagueews-minus-snapshot: baron | +2.2421 [+1.5687, +2.9261] | +0.0008 [-0.0237, +0.0239] | +1.8204, +3.2397, +1.6662 |
| leagueews-minus-snapshot: dragon | +1.4329 [+1.1570, +1.7188] | +0.0622 [+0.0479, +0.0767] | +2.0478, +0.8032, +1.4476 |
| leagueews-minus-snapshot: teamfight | +0.4917 [+0.3092, +0.6689] | -0.0023 [-0.0283, +0.0262] | +0.6769, +0.4698, +0.3284 |
| leagueews-minus-snapshot: macro | +1.3889 [+1.1347, +1.6374] | +0.0202 [+0.0081, +0.0329] | +1.5151, +1.5043, +1.1474 |
## 20-60-second warnings

### Four-budget matched-early mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| leagueews | 17.211 / 0.6432 | 13.543 / 0.6254 | 3.603 / 0.6214 | 11.452 / 0.6300 |
| gru | 12.970 / 0.6192 | 15.971 / 0.6481 | 3.527 / 0.6125 | 10.823 / 0.6266 |
| tcn | 16.717 / 0.6520 | 13.256 / 0.6286 | 3.490 / 0.6192 | 11.155 / 0.6333 |
| snapshot | 16.418 / 0.6351 | 13.337 / 0.6323 | 3.330 / 0.6423 | 11.028 / 0.6366 |
| current_only | 17.104 / 0.6412 | 13.404 / 0.6277 | 3.612 / 0.6370 | 11.373 / 0.6353 |
| independent | 18.005 / 0.6351 | 13.208 / 0.6278 | 3.449 / 0.6198 | 11.554 / 0.6276 |
| pcgrad | 17.060 / 0.6385 | 13.174 / 0.6254 | 3.518 / 0.6254 | 11.251 / 0.6297 |
| timely_leagueews | 19.407 / 0.6472 | 21.730 / 0.6083 | 5.207 / 0.6221 | 15.448 / 0.6259 |
| timely_tcn | 18.020 / 0.6496 | 21.603 / 0.6098 | 5.108 / 0.6200 | 14.910 / 0.6265 |
| timely_current_only | 19.503 / 0.6443 | 21.659 / 0.6098 | 4.913 / 0.6126 | 15.359 / 0.6222 |
| timely_clock_only | 15.818 / 0.6403 | 20.608 / 0.6140 | 3.502 / 0.6038 | 13.309 / 0.6194 |
| timely_clock_history | 19.074 / 0.6501 | 21.884 / 0.6127 | 4.989 / 0.6204 | 15.316 / 0.6277 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | +0.0103 [-0.1558, +0.1801] | +0.0089 [+0.0014, +0.0170] | +0.0379, -0.0906, +0.0837 |
| leagueews-minus-current_only | +0.0791 [-0.1184, +0.2619] | -0.0053 [-0.0124, +0.0017] | +0.2043, +0.1901, -0.1572 |
| leagueews-minus-gru | +0.6296 [+0.2694, +0.9920] | +0.0034 [-0.0108, +0.0173] | +0.0340, +0.1626, +1.6921 |
| leagueews-minus-independent | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | +0.1335, -0.3347, -0.1036 |
| leagueews-minus-snapshot | +0.4238 [+0.2114, +0.6347] | -0.0066 [-0.0144, +0.0013] | +0.2788, +0.4714, +0.5213 |
| leagueews-minus-tcn | +0.2977 [+0.1526, +0.4329] | -0.0033 [-0.0077, +0.0007] | +0.0664, +0.4455, +0.3811 |
| timely_clock_history-minus-timely_current_only | -0.0426 [-0.1855, +0.0879] | +0.0055 [+0.0014, +0.0093] | +0.0756, +0.0438, -0.2473 |
| timely_current_only-minus-current_only | +3.9853 [+3.7507, +4.2310] | -0.0131 [-0.0222, -0.0030] | +4.1749, +3.9879, +3.7932 |
| timely_leagueews-minus-leagueews | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |
| timely_leagueews-minus-timely_clock_history | +0.1320 [-0.0635, +0.3245] | -0.0018 [-0.0082, +0.0047] | +0.1666, +0.0556, +0.1739 |
| timely_leagueews-minus-timely_clock_only | +2.1385 [+1.8057, +2.4602] | +0.0065 [-0.0058, +0.0187] | +2.4487, +1.8945, +2.0722 |
| timely_leagueews-minus-timely_current_only | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |
| timely_leagueews-minus-timely_tcn | +0.5375 [+0.3787, +0.6945] | -0.0006 [-0.0059, +0.0044] | +0.7025, +0.4249, +0.4851 |

### Paired history components by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_clock_history: baron | +0.3325 [-0.2118, +0.8503] | -0.0029 [-0.0148, +0.0088] | +0.4450, +0.0129, +0.5397 |
| timely_leagueews-minus-timely_clock_history: dragon | -0.1544 [-0.2952, -0.0058] | -0.0044 [-0.0103, +0.0013] | -0.2547, +0.0143, -0.2227 |
| timely_leagueews-minus-timely_clock_history: teamfight | +0.2179 [+0.0703, +0.3646] | +0.0017 [-0.0136, +0.0178] | +0.3095, +0.1397, +0.2046 |
| timely_leagueews-minus-timely_clock_history: macro | +0.1320 [-0.0635, +0.3245] | -0.0018 [-0.0082, +0.0047] | +0.1666, +0.0556, +0.1739 |
| timely_clock_history-minus-timely_current_only: baron | -0.4287 [-0.8235, -0.0577] | +0.0058 [-0.0022, +0.0130] | -0.1651, +0.0074, -1.1285 |
| timely_clock_history-minus-timely_current_only: dragon | +0.2251 [+0.1137, +0.3439] | +0.0029 [-0.0021, +0.0082] | +0.3590, +0.0150, +0.3012 |
| timely_clock_history-minus-timely_current_only: teamfight | +0.0758 [-0.0003, +0.1500] | +0.0078 [+0.0004, +0.0155] | +0.0330, +0.1091, +0.0853 |
| timely_clock_history-minus-timely_current_only: macro | -0.0426 [-0.1855, +0.0879] | +0.0055 [+0.0014, +0.0093] | +0.0756, +0.0438, -0.2473 |
| timely_leagueews-minus-timely_current_only: baron | -0.0962 [-0.6883, +0.4761] | +0.0029 [-0.0090, +0.0142] | +0.2799, +0.0203, -0.5888 |
| timely_leagueews-minus-timely_current_only: dragon | +0.0707 [-0.0817, +0.2316] | -0.0015 [-0.0087, +0.0053] | +0.1042, +0.0294, +0.0785 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.2937 [+0.1365, +0.4407] | +0.0095 [-0.0058, +0.0256] | +0.3425, +0.2488, +0.2899 |
| timely_leagueews-minus-timely_current_only: macro | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |

### Conditional non-timing history: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -1.1296 [-1.2915, -0.9666] | -0.0346 [-0.0393, -0.0300] | +0.1336, -3.1531, -0.3694 |
| 0.5 | -0.5903 [-0.8389, -0.3421] | -0.0229 [-0.0301, -0.0159] | +0.2286, -0.8931, -1.1064 |
| 0.75 | +0.2208 [-0.0630, +0.5040] | +0.0017 [-0.0066, +0.0096] | -0.6366, +1.3955, -0.0966 |
| 1.0 | +0.7242 [+0.4377, +1.0042] | +0.0123 [+0.0024, +0.0219] | -0.4465, +0.9661, +1.6532 |
| mean | -0.1937 [-0.3712, -0.0212] | -0.0109 [-0.0163, -0.0055] | -0.1803, -0.4212, +0.0202 |

### Conditional non-timing history: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -1.0422 [-1.2265, -0.8609] | -0.0246 [-0.0292, -0.0197] | +0.1130, -3.1531, -0.0865 |
| 0.5 | -0.5972 [-0.8611, -0.3438] | -0.0238 [-0.0311, -0.0164] | +0.2080, -0.8931, -1.1064 |
| 0.75 | -0.2130 [-0.5021, +0.0608] | +0.0017 [-0.0067, +0.0100] | -0.7036, +0.1613, -0.0966 |
| 1.0 | +0.0309 [-0.2614, +0.3146] | -0.0194 [-0.0293, -0.0096] | -1.1998, +0.9661, +0.3264 |
| mean | -0.4554 [-0.6415, -0.2809] | -0.0165 [-0.0220, -0.0109] | -0.3956, -0.7297, -0.2408 |

### Conditional non-timing history: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.0378 [-0.2315, +0.1628] | -0.0029 [-0.0082, +0.0026] | +0.0092, +0.0722, -0.1949 |
| 0.5 | -0.0152 [-0.2627, +0.2216] | -0.0020 [-0.0092, +0.0054] | +0.0217, -0.1347, +0.0673 |
| 0.75 | +0.2135 [-0.0426, +0.4759] | +0.0020 [-0.0069, +0.0108] | +0.2137, +0.0113, +0.4155 |
| 1.0 | +0.3677 [+0.1064, +0.6287] | -0.0046 [-0.0140, +0.0046] | +0.4219, +0.2737, +0.4076 |
| mean | +0.1320 [-0.0635, +0.3245] | -0.0018 [-0.0082, +0.0047] | +0.1666, +0.0556, +0.1739 |

### Conditional non-timing history: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.0645 [-0.3061, +0.1805] | -0.0081 [-0.0144, -0.0017] | -0.1897, -0.1908, +0.1870 |
| 0.5 | +0.0274 [-0.2440, +0.3071] | -0.0013 [-0.0092, +0.0068] | +0.0646, +0.0073, +0.0103 |
| 0.75 | +0.3248 [+0.0417, +0.6032] | +0.0038 [-0.0057, +0.0134] | +0.5350, +0.0479, +0.3916 |
| 1.0 | +0.3755 [+0.1028, +0.6600] | +0.0026 [-0.0080, +0.0130] | +0.6698, +0.0610, +0.3957 |
| mean | +0.1658 [-0.0401, +0.3593] | -0.0008 [-0.0072, +0.0059] | +0.2699, -0.0187, +0.2462 |

### Conditional non-timing history: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.0332 [-0.2050, +0.2750] | -0.0032 [-0.0097, +0.0036] | +0.0976, -0.2007, +0.2027 |
| 0.5 | -0.0230 [-0.3039, +0.2650] | -0.0029 [-0.0109, +0.0056] | -0.0375, -0.0940, +0.0625 |
| 0.75 | +0.2416 [-0.0440, +0.5204] | +0.0101 [+0.0006, +0.0193] | +0.4419, +0.0765, +0.2063 |
| 1.0 | +0.3725 [+0.0967, +0.6648] | -0.0017 [-0.0124, +0.0088] | +0.3985, +0.3180, +0.4009 |
| mean | +0.1561 [-0.0533, +0.3535] | +0.0006 [-0.0059, +0.0071] | +0.2251, +0.0249, +0.2181 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_leagueews-minus-timely_clock_history: baron | +0.1567 [-0.6306, +0.9399] | +0.0099 [-0.0061, +0.0263] | +0.5094, +0.0824, -0.1218 |
| europe: timely_leagueews-minus-timely_clock_history: dragon | -0.0039 [-0.2057, +0.1988] | -0.0036 [-0.0118, +0.0045] | +0.0604, +0.0469, -0.1191 |
| europe: timely_leagueews-minus-timely_clock_history: teamfight | +0.2510 [+0.0527, +0.4507] | +0.0174 [-0.0034, +0.0398] | +0.2743, +0.1473, +0.3313 |
| europe: timely_leagueews-minus-timely_clock_history: macro | +0.1346 [-0.1387, +0.4184] | +0.0079 [-0.0014, +0.0169] | +0.2814, +0.0922, +0.0301 |
| europe: timely_clock_history-minus-timely_current_only: baron | -0.2097 [-0.7389, +0.3087] | +0.0004 [-0.0110, +0.0109] | +0.1933, -0.0433, -0.7791 |
| europe: timely_clock_history-minus-timely_current_only: dragon | +0.1803 [+0.0110, +0.3522] | -0.0002 [-0.0073, +0.0069] | +0.3264, -0.0540, +0.2685 |
| europe: timely_clock_history-minus-timely_current_only: teamfight | +0.0400 [-0.0629, +0.1462] | -0.0012 [-0.0111, +0.0082] | -0.0058, +0.0953, +0.0305 |
| europe: timely_clock_history-minus-timely_current_only: macro | +0.0035 [-0.1935, +0.1910] | -0.0004 [-0.0064, +0.0052] | +0.1713, -0.0007, -0.1600 |
| europe: timely_leagueews-minus-timely_current_only: baron | -0.0530 [-0.8412, +0.7657] | +0.0102 [-0.0051, +0.0255] | +0.7027, +0.0391, -0.9008 |
| europe: timely_leagueews-minus-timely_current_only: dragon | +0.1764 [-0.0443, +0.4006] | -0.0038 [-0.0130, +0.0052] | +0.3867, -0.0071, +0.1494 |
| europe: timely_leagueews-minus-timely_current_only: teamfight | +0.2910 [+0.0872, +0.4939] | +0.0162 [-0.0061, +0.0397] | +0.2685, +0.2426, +0.3618 |
| europe: timely_leagueews-minus-timely_current_only: macro | +0.1381 [-0.1474, +0.4398] | +0.0076 [-0.0020, +0.0169] | +0.4527, +0.0915, -0.1299 |
| americas: timely_leagueews-minus-timely_clock_history: baron | +0.5061 [-0.2543, +1.3179] | -0.0156 [-0.0317, +0.0002] | +0.3813, -0.0557, +1.1927 |
| americas: timely_leagueews-minus-timely_clock_history: dragon | -0.3003 [-0.5009, -0.0949] | -0.0051 [-0.0133, +0.0028] | -0.5604, -0.0173, -0.3232 |
| americas: timely_leagueews-minus-timely_clock_history: teamfight | +0.1844 [-0.0243, +0.3933] | -0.0141 [-0.0356, +0.0063] | +0.3454, +0.1320, +0.0758 |
| americas: timely_leagueews-minus-timely_clock_history: macro | +0.1301 [-0.1509, +0.4161] | -0.0116 [-0.0210, -0.0029] | +0.0554, +0.0196, +0.3151 |
| americas: timely_clock_history-minus-timely_current_only: baron | -0.6449 [-1.1827, -0.0993] | +0.0112 [+0.0004, +0.0213] | -0.5188, +0.0575, -1.4734 |
| americas: timely_clock_history-minus-timely_current_only: dragon | +0.2685 [+0.1065, +0.4226] | +0.0059 [-0.0012, +0.0130] | +0.3906, +0.0820, +0.3329 |
| americas: timely_clock_history-minus-timely_current_only: teamfight | +0.1121 [+0.0077, +0.2128] | +0.0169 [+0.0059, +0.0283] | +0.0724, +0.1231, +0.1409 |
| americas: timely_clock_history-minus-timely_current_only: macro | -0.0881 [-0.2800, +0.1032] | +0.0113 [+0.0055, +0.0172] | -0.0186, +0.0875, -0.3332 |
| americas: timely_leagueews-minus-timely_current_only: baron | -0.1388 [-0.9632, +0.7093] | -0.0044 [-0.0215, +0.0124] | -0.1375, +0.0017, -0.2808 |
| americas: timely_leagueews-minus-timely_current_only: dragon | -0.0318 [-0.2470, +0.1832] | +0.0008 [-0.0089, +0.0097] | -0.1697, +0.0647, +0.0097 |
| americas: timely_leagueews-minus-timely_current_only: teamfight | +0.2965 [+0.0674, +0.5250] | +0.0028 [-0.0186, +0.0239] | +0.4178, +0.2550, +0.2168 |
| americas: timely_leagueews-minus-timely_current_only: macro | +0.0420 [-0.2648, +0.3384] | -0.0003 [-0.0095, +0.0085] | +0.0369, +0.1072, -0.0181 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_clock_history: baron | +0.3497 [-0.4338, +1.1218] | -0.0387 [-0.0564, -0.0216] | +0.8331, -0.4628, +0.6788 |
| timely_leagueews-minus-timely_clock_history: dragon | +0.4619 [+0.2127, +0.7220] | +0.0212 [+0.0097, +0.0322] | +0.5649, +0.4237, +0.3972 |
| timely_leagueews-minus-timely_clock_history: teamfight | +0.3149 [+0.0940, +0.5356] | +0.0251 [+0.0002, +0.0498] | +0.6113, +0.2223, +0.1111 |
| timely_leagueews-minus-timely_clock_history: macro | +0.3755 [+0.1028, +0.6600] | +0.0026 [-0.0080, +0.0130] | +0.6698, +0.0610, +0.3957 |
| timely_clock_history-minus-timely_current_only: baron | -0.3188 [-0.9043, +0.2359] | +0.0104 [-0.0016, +0.0222] | -0.4011, +0.5554, -1.1108 |
| timely_clock_history-minus-timely_current_only: dragon | +0.0206 [-0.1939, +0.2246] | -0.0102 [-0.0202, -0.0002] | +0.2736, -0.3001, +0.0883 |
| timely_clock_history-minus-timely_current_only: teamfight | -0.0152 [-0.1394, +0.1106] | -0.0214 [-0.0347, -0.0082] | -0.1869, +0.1465, -0.0051 |
| timely_clock_history-minus-timely_current_only: macro | -0.1045 [-0.3021, +0.0927] | -0.0071 [-0.0139, -0.0001] | -0.1048, +0.1339, -0.3425 |
| timely_leagueews-minus-timely_current_only: baron | +0.0309 [-0.8338, +0.8779] | -0.0282 [-0.0468, -0.0110] | +0.4320, +0.0926, -0.4320 |
| timely_leagueews-minus-timely_current_only: dragon | +0.4825 [+0.2201, +0.7609] | +0.0110 [-0.0014, +0.0239] | +0.8386, +0.1236, +0.4855 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.2997 [+0.0667, +0.5218] | +0.0037 [-0.0210, +0.0291] | +0.4243, +0.3688, +0.1061 |
| timely_leagueews-minus-timely_current_only: macro | +0.2710 [-0.0556, +0.5736] | -0.0045 [-0.0155, +0.0064] | +0.5650, +0.1950, +0.0532 |

### Original registered model comparisons, unchanged policy

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| leagueews-minus-gru: baron | +4.9779 [+3.6898, +6.3047] | -0.0103 [-0.0479, +0.0258] | +2.8695, +2.5301, +9.5341 |
| leagueews-minus-gru: dragon | -8.4856 [-9.1642, -7.8086] | -0.0692 [-0.0968, -0.0430] | -5.9229, -7.2557, -12.2782 |
| leagueews-minus-gru: teamfight | +0.9784 [+0.7082, +1.2461] | +0.2126 [+0.1827, +0.2433] | +0.8285, +2.3844, -0.2778 |
| leagueews-minus-gru: macro | -0.8431 [-1.3576, -0.3069] | +0.0443 [+0.0240, +0.0640] | -0.7416, -0.7804, -1.0073 |
| leagueews-minus-tcn: baron | +0.1028 [-0.5048, +0.6693] | -0.0316 [-0.0456, -0.0176] | +0.4011, +2.0364, -2.1290 |
| leagueews-minus-tcn: dragon | -0.5090 [-0.7429, -0.2679] | -0.0183 [-0.0284, -0.0086] | -1.4035, +2.3038, -2.4274 |
| leagueews-minus-tcn: teamfight | +0.7477 [+0.6222, +0.8808] | +0.1386 [+0.1239, +0.1539] | +0.1667, +1.6469, +0.4294 |
| leagueews-minus-tcn: macro | +0.1138 [-0.1100, +0.3300] | +0.0296 [+0.0222, +0.0371] | -0.2786, +1.9957, -1.3757 |
| leagueews-minus-snapshot: baron | +0.4937 [-0.4321, +1.3947] | -0.0146 [-0.0360, +0.0058] | +1.9747, -0.6788, +0.1851 |
| leagueews-minus-snapshot: dragon | +0.7326 [+0.4333, +1.0366] | +0.1299 [+0.1147, +0.1461] | -0.9180, +1.6859, +1.4300 |
| leagueews-minus-snapshot: teamfight | +0.6971 [+0.4876, +0.9151] | +0.0610 [+0.0337, +0.0917] | -0.4345, +2.9149, -0.3890 |
| leagueews-minus-snapshot: macro | +0.6412 [+0.3113, +0.9763] | +0.0588 [+0.0463, +0.0720] | +0.2074, +1.3073, +0.4087 |

## Prespecified descriptive rules

| Rule | Result |
|---|---|
| conditional_history_event_nonharm | True |
| conditional_history_no_extra_burden | True |
| conditional_history_support | True |
| practical_promotion | not established; diagnostic study cannot erase prior failed budget gates |
| primary_full_input_regional_hard_one_violations | 12 |
| regional_conditional_history_consistency | True |

All model/event/region/seed results and paired intervals are retained in `analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`. Neither a diagnostic pass nor input exclusion establishes novelty or a causal effect of game actions. Previously failed regional gates remain failed.
