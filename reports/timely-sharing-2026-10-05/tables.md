# Useful-lead task-sharing evidence

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
| timely_independent | 16.790 / 0.6339 | 10.395 / 0.6432 | 2.653 / 0.6035 | 9.946 / 0.6269 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | -0.0671 [-0.1766, +0.0509] | +0.0003 [-0.0063, +0.0073] | -0.0837, -0.0126, -0.1051 |
| leagueews-minus-current_only | +0.7171 [+0.5431, +0.8813] | -0.0101 [-0.0178, -0.0026] | +0.8251, +0.7580, +0.5681 |
| leagueews-minus-gru | +3.3809 [+3.0613, +3.7204] | +0.0064 [-0.0085, +0.0205] | +2.9995, +3.0401, +4.1030 |
| leagueews-minus-independent | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | +0.1200, -0.0894, -0.0868 |
| leagueews-minus-snapshot | +0.9479 [+0.7639, +1.1342] | -0.0084 [-0.0172, +0.0005] | +0.9041, +1.0516, +0.8879 |
| leagueews-minus-tcn | +0.0476 [-0.0630, +0.1608] | -0.0030 [-0.0074, +0.0017] | +0.0106, +0.0769, +0.0554 |
| sharing_effect_difference_timely_minus_cumulative | -0.0422 [-0.1652, +0.0800] | -0.0018 [-0.0075, +0.0040] | -0.0085, +0.0584, -0.1765 |
| timely_clock_history-minus-timely_current_only | +0.1170 [+0.0140, +0.2186] | +0.0018 [-0.0025, +0.0061] | +0.0184, +0.1838, +0.1488 |
| timely_current_only-minus-current_only | +0.5176 [+0.3858, +0.6438] | -0.0053 [-0.0133, +0.0030] | +0.6248, +0.4581, +0.4699 |
| timely_independent-minus-independent | +0.4927 [+0.3512, +0.6462] | -0.0033 [-0.0115, +0.0053] | +0.5497, +0.3871, +0.5414 |
| timely_leagueews-minus-leagueews | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |
| timely_leagueews-minus-timely_clock_history | +0.5330 [+0.3739, +0.6958] | -0.0117 [-0.0193, -0.0038] | +0.7230, +0.5616, +0.3142 |
| timely_leagueews-minus-timely_clock_only | +2.9334 [+2.6308, +3.2524] | -0.0093 [-0.0214, +0.0033] | +3.0772, +2.9184, +2.8047 |
| timely_leagueews-minus-timely_current_only | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |
| timely_leagueews-minus-timely_independent | -0.0610 [-0.2192, +0.0992] | -0.0006 [-0.0070, +0.0061] | +0.1115, -0.0310, -0.2634 |
| timely_leagueews-minus-timely_tcn | +0.1757 [+0.0613, +0.2903] | -0.0047 [-0.0097, +0.0005] | +0.2784, +0.1977, +0.0509 |

### Sharing effects and target interaction by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_independent: baron | -0.5136 [-0.9183, -0.0769] | +0.0041 [-0.0082, +0.0164] | +0.0144, -0.5367, -1.0187 |
| timely_leagueews-minus-timely_independent: dragon | +0.3278 [+0.1363, +0.5017] | -0.0075 [-0.0167, +0.0013] | +0.2695, +0.4897, +0.2243 |
| timely_leagueews-minus-timely_independent: teamfight | +0.0029 [-0.0965, +0.1017] | +0.0017 [-0.0103, +0.0145] | +0.0506, -0.0460, +0.0043 |
| timely_leagueews-minus-timely_independent: macro | -0.0610 [-0.2192, +0.0992] | -0.0006 [-0.0070, +0.0061] | +0.1115, -0.0310, -0.2634 |
| leagueews-minus-independent: baron | -0.4359 [-0.8298, -0.0303] | +0.0053 [-0.0070, +0.0169] | -0.0037, -0.5429, -0.7610 |
| leagueews-minus-independent: dragon | +0.3189 [+0.1726, +0.4731] | +0.0002 [-0.0076, +0.0076] | +0.2725, +0.2671, +0.4171 |
| leagueews-minus-independent: teamfight | +0.0608 [-0.0113, +0.1295] | -0.0020 [-0.0116, +0.0079] | +0.0913, +0.0076, +0.0835 |
| leagueews-minus-independent: macro | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | +0.1200, -0.0894, -0.0868 |
| sharing_effect_difference_timely_minus_cumulative: baron | -0.0778 [-0.3605, +0.2183] | -0.0012 [-0.0094, +0.0072] | +0.0181, +0.0062, -0.2577 |
| sharing_effect_difference_timely_minus_cumulative: dragon | +0.0090 [-0.1931, +0.1923] | -0.0077 [-0.0181, +0.0034] | -0.0030, +0.2226, -0.1928 |
| sharing_effect_difference_timely_minus_cumulative: teamfight | -0.0578 [-0.1552, +0.0393] | +0.0037 [-0.0086, +0.0164] | -0.0407, -0.0536, -0.0792 |
| sharing_effect_difference_timely_minus_cumulative: macro | -0.0422 [-0.1652, +0.0800] | -0.0018 [-0.0075, +0.0040] | -0.0085, +0.0584, -0.1765 |

### Useful-lead joint minus independent: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.1099 [-0.3031, +0.0922] | -0.0083 [-0.0141, -0.0024] | +0.0268, +0.2236, -0.5800 |
| 0.5 | +0.3167 [+0.0887, +0.5473] | +0.0549 [+0.0466, +0.0634] | +0.3078, +0.2367, +0.4056 |
| 0.75 | +0.9116 [+0.6862, +1.1386] | +0.0799 [+0.0703, +0.0896] | +0.5806, +1.5408, +0.6133 |
| 1.0 | -0.2926 [-0.5025, -0.0696] | -0.0427 [-0.0527, -0.0326] | +0.1246, -0.9662, -0.0362 |
| mean | +0.2065 [+0.0392, +0.3699] | +0.0209 [+0.0146, +0.0272] | +0.2599, +0.2587, +0.1007 |

### Useful-lead joint minus independent: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.1099 [-0.3031, +0.0922] | -0.0083 [-0.0141, -0.0024] | +0.0268, +0.2236, -0.5800 |
| 0.5 | +0.1593 [-0.0677, +0.3885] | +0.0246 [+0.0161, +0.0329] | +0.5443, +0.0666, -0.1329 |
| 0.75 | +1.0099 [+0.7840, +1.2349] | +0.0863 [+0.0764, +0.0963] | +1.3486, +1.3454, +0.3356 |
| 1.0 | -0.3063 [-0.5128, -0.0848] | -0.0440 [-0.0541, -0.0336] | +0.1246, -0.7605, -0.2831 |
| mean | +0.1883 [+0.0272, +0.3502] | +0.0147 [+0.0083, +0.0211] | +0.5111, +0.2188, -0.1651 |

### Useful-lead joint minus independent: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.0630 [-0.1148, +0.2480] | -0.0013 [-0.0069, +0.0044] | +0.2138, +0.1222, -0.1469 |
| 0.5 | -0.1119 [-0.3279, +0.1025] | +0.0008 [-0.0072, +0.0083] | +0.1076, -0.0651, -0.3782 |
| 0.75 | -0.1309 [-0.3371, +0.0836] | -0.0015 [-0.0100, +0.0075] | +0.0074, -0.0971, -0.3030 |
| 1.0 | -0.0640 [-0.2517, +0.1303] | -0.0004 [-0.0098, +0.0095] | +0.1173, -0.0840, -0.2254 |
| mean | -0.0610 [-0.2192, +0.0992] | -0.0006 [-0.0070, +0.0061] | +0.1115, -0.0310, -0.2634 |

### Useful-lead joint minus independent: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1478 [-0.0577, +0.3445] | +0.0060 [-0.0005, +0.0125] | +0.4326, +0.0335, -0.0226 |
| 0.5 | -0.0619 [-0.2993, +0.1692] | +0.0050 [-0.0035, +0.0133] | +0.2087, +0.0155, -0.4100 |
| 0.75 | -0.0149 [-0.2327, +0.2116] | +0.0066 [-0.0026, +0.0163] | +0.0408, +0.1053, -0.1909 |
| 1.0 | +0.0839 [-0.1236, +0.3013] | +0.0087 [-0.0019, +0.0193] | +0.2969, +0.0766, -0.1219 |
| mean | +0.0387 [-0.1249, +0.2041] | +0.0066 [-0.0003, +0.0134] | +0.2447, +0.0577, -0.1863 |

### Useful-lead joint minus independent: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.0782 [-0.1255, +0.2730] | +0.0021 [-0.0043, +0.0086] | +0.3080, -0.0374, -0.0359 |
| 0.5 | -0.1793 [-0.4096, +0.0509] | -0.0036 [-0.0122, +0.0049] | +0.1367, -0.0611, -0.6135 |
| 0.75 | -0.0799 [-0.3044, +0.1450] | -0.0010 [-0.0105, +0.0086] | +0.1555, -0.0676, -0.3276 |
| 1.0 | -0.0041 [-0.2131, +0.2111] | +0.0033 [-0.0076, +0.0139] | +0.1190, +0.0729, -0.2041 |
| mean | -0.0463 [-0.2066, +0.1180] | +0.0002 [-0.0067, +0.0069] | +0.1798, -0.0233, -0.2953 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_leagueews-minus-timely_independent: baron | -0.9424 [-1.5495, -0.2884] | -0.0174 [-0.0342, -0.0006] | -0.3895, -0.8680, -1.5698 |
| europe: timely_leagueews-minus-timely_independent: dragon | +0.3633 [+0.0904, +0.6262] | +0.0054 [-0.0071, +0.0174] | +0.2967, +0.6784, +0.1146 |
| europe: timely_leagueews-minus-timely_independent: teamfight | +0.0134 [-0.1150, +0.1463] | -0.0002 [-0.0176, +0.0173] | +0.0638, +0.0487, -0.0724 |
| europe: timely_leagueews-minus-timely_independent: macro | -0.1886 [-0.4274, +0.0511] | -0.0041 [-0.0130, +0.0048] | -0.0097, -0.0470, -0.5092 |
| europe: leagueews-minus-independent: baron | -0.8408 [-1.4304, -0.2362] | -0.0105 [-0.0265, +0.0059] | -0.4613, -1.0559, -1.0053 |
| europe: leagueews-minus-independent: dragon | +0.4065 [+0.2121, +0.5972] | +0.0046 [-0.0055, +0.0148] | +0.3983, +0.4572, +0.3640 |
| europe: leagueews-minus-independent: teamfight | +0.0589 [-0.0371, +0.1549] | -0.0053 [-0.0179, +0.0075] | +0.0463, +0.0353, +0.0951 |
| europe: leagueews-minus-independent: macro | -0.1251 [-0.3270, +0.0964] | -0.0037 [-0.0117, +0.0040] | -0.0056, -0.1878, -0.1821 |
| europe: sharing_effect_difference_timely_minus_cumulative: baron | -0.1016 [-0.4904, +0.3046] | -0.0069 [-0.0176, +0.0048] | +0.0718, +0.1879, -0.5645 |
| europe: sharing_effect_difference_timely_minus_cumulative: dragon | -0.0432 [-0.3402, +0.2257] | +0.0008 [-0.0134, +0.0146] | -0.1016, +0.2212, -0.2494 |
| europe: sharing_effect_difference_timely_minus_cumulative: teamfight | -0.0456 [-0.1821, +0.0924] | +0.0051 [-0.0122, +0.0215] | +0.0175, +0.0134, -0.1675 |
| europe: sharing_effect_difference_timely_minus_cumulative: macro | -0.0635 [-0.2335, +0.0984] | -0.0003 [-0.0084, +0.0077] | -0.0041, +0.1408, -0.3271 |
| americas: timely_leagueews-minus-timely_independent: baron | -0.0904 [-0.6327, +0.4896] | +0.0255 [+0.0070, +0.0445] | +0.4131, -0.2096, -0.4746 |
| americas: timely_leagueews-minus-timely_independent: dragon | +0.2935 [+0.0503, +0.5214] | -0.0204 [-0.0332, -0.0074] | +0.2430, +0.3067, +0.3306 |
| americas: timely_leagueews-minus-timely_independent: teamfight | -0.0076 [-0.1506, +0.1382] | +0.0036 [-0.0138, +0.0205] | +0.0372, -0.1423, +0.0823 |
| americas: timely_leagueews-minus-timely_independent: macro | +0.0651 [-0.1444, +0.2762] | +0.0029 [-0.0066, +0.0122] | +0.2311, -0.0151, -0.0206 |
| americas: leagueews-minus-independent: baron | -0.0361 [-0.5461, +0.5136] | +0.0211 [+0.0030, +0.0388] | +0.4480, -0.0365, -0.5198 |
| americas: leagueews-minus-independent: dragon | +0.2339 [+0.0160, +0.4476] | -0.0042 [-0.0149, +0.0065] | +0.1504, +0.0827, +0.4685 |
| americas: leagueews-minus-independent: teamfight | +0.0627 [-0.0390, +0.1672] | +0.0014 [-0.0125, +0.0160] | +0.1370, -0.0206, +0.0716 |
| americas: leagueews-minus-independent: macro | +0.0868 [-0.1084, +0.2845] | +0.0061 [-0.0022, +0.0143] | +0.2451, +0.0085, +0.0067 |
| americas: sharing_effect_difference_timely_minus_cumulative: baron | -0.0543 [-0.4483, +0.3573] | +0.0044 [-0.0079, +0.0173] | -0.0349, -0.1731, +0.0452 |
| americas: sharing_effect_difference_timely_minus_cumulative: dragon | +0.0596 [-0.2141, +0.3192] | -0.0163 [-0.0310, -0.0024] | +0.0926, +0.2240, -0.1378 |
| americas: sharing_effect_difference_timely_minus_cumulative: teamfight | -0.0703 [-0.2124, +0.0685] | +0.0022 [-0.0164, +0.0208] | -0.0998, -0.1218, +0.0107 |
| americas: sharing_effect_difference_timely_minus_cumulative: macro | -0.0217 [-0.1891, +0.1329] | -0.0032 [-0.0115, +0.0052] | -0.0140, -0.0236, -0.0273 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_independent: baron | -0.3600 [-0.8855, +0.2077] | +0.0086 [-0.0113, +0.0282] | +0.2160, -0.7097, -0.5862 |
| timely_leagueews-minus-timely_independent: dragon | +0.5679 [+0.2850, +0.8409] | -0.0031 [-0.0171, +0.0114] | +0.6091, +0.8739, +0.2207 |
| timely_leagueews-minus-timely_independent: teamfight | +0.0438 [-0.1013, +0.1826] | +0.0206 [+0.0014, +0.0403] | +0.0657, +0.0657, +0.0000 |
| timely_leagueews-minus-timely_independent: macro | +0.0839 [-0.1236, +0.3013] | +0.0087 [-0.0019, +0.0193] | +0.2969, +0.0766, -0.1219 |
| leagueews-minus-independent: baron | -0.4423 [-0.9873, +0.1058] | +0.0152 [-0.0046, +0.0333] | +0.2160, -0.7097, -0.8331 |
| leagueews-minus-independent: dragon | +0.4914 [+0.2692, +0.7254] | -0.0007 [-0.0119, +0.0104] | +0.3001, +0.6532, +0.5208 |
| leagueews-minus-independent: teamfight | -0.0471 [-0.1571, +0.0643] | -0.0370 [-0.0524, -0.0209] | +0.0101, -0.1061, -0.0455 |
| leagueews-minus-independent: macro | +0.0007 [-0.1937, +0.2048] | -0.0075 [-0.0163, +0.0020] | +0.1754, -0.0542, -0.1193 |
| sharing_effect_difference_timely_minus_cumulative: baron | +0.0823 [-0.4277, +0.6023] | -0.0067 [-0.0217, +0.0094] | +0.0000, +0.0000, +0.2468 |
| sharing_effect_difference_timely_minus_cumulative: dragon | +0.0765 [-0.2571, +0.4076] | -0.0024 [-0.0189, +0.0143] | +0.3089, +0.2207, -0.3001 |
| sharing_effect_difference_timely_minus_cumulative: teamfight | +0.0909 [-0.0547, +0.2507] | +0.0576 [+0.0361, +0.0790] | +0.0556, +0.1718, +0.0455 |
| sharing_effect_difference_timely_minus_cumulative: macro | +0.0832 [-0.1272, +0.2877] | +0.0161 [+0.0062, +0.0267] | +0.1215, +0.1308, -0.0026 |

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
| timely_independent | 21.587 / 0.6341 | 21.670 / 0.6097 | 5.080 / 0.6184 | 16.112 / 0.6207 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | +0.0103 [-0.1558, +0.1801] | +0.0089 [+0.0014, +0.0170] | +0.0379, -0.0906, +0.0837 |
| leagueews-minus-current_only | +0.0791 [-0.1184, +0.2619] | -0.0053 [-0.0124, +0.0017] | +0.2043, +0.1901, -0.1572 |
| leagueews-minus-gru | +0.6296 [+0.2694, +0.9920] | +0.0034 [-0.0108, +0.0173] | +0.0340, +0.1626, +1.6921 |
| leagueews-minus-independent | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | +0.1335, -0.3347, -0.1036 |
| leagueews-minus-snapshot | +0.4238 [+0.2114, +0.6347] | -0.0066 [-0.0144, +0.0013] | +0.2788, +0.4714, +0.5213 |
| leagueews-minus-tcn | +0.2977 [+0.1526, +0.4329] | -0.0033 [-0.0077, +0.0007] | +0.0664, +0.4455, +0.3811 |
| sharing_effect_difference_timely_minus_cumulative | -0.5625 [-0.7758, -0.3427] | +0.0027 [-0.0036, +0.0091] | -0.4917, -0.5293, -0.6666 |
| timely_clock_history-minus-timely_current_only | -0.0426 [-0.1855, +0.0879] | +0.0055 [+0.0014, +0.0093] | +0.0756, +0.0438, -0.2473 |
| timely_current_only-minus-current_only | +3.9853 [+3.7507, +4.2310] | -0.0131 [-0.0222, -0.0030] | +4.1749, +3.9879, +3.7932 |
| timely_independent-minus-independent | +4.5582 [+4.3122, +4.8259] | -0.0068 [-0.0169, +0.0038] | +4.7045, +4.4265, +4.5436 |
| timely_leagueews-minus-leagueews | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |
| timely_leagueews-minus-timely_clock_history | +0.1320 [-0.0635, +0.3245] | -0.0018 [-0.0082, +0.0047] | +0.1666, +0.0556, +0.1739 |
| timely_leagueews-minus-timely_clock_only | +2.1385 [+1.8057, +2.4602] | +0.0065 [-0.0058, +0.0187] | +2.4487, +1.8945, +2.0722 |
| timely_leagueews-minus-timely_current_only | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |
| timely_leagueews-minus-timely_independent | -0.6641 [-0.9246, -0.3971] | +0.0051 [-0.0013, +0.0114] | -0.3581, -0.8640, -0.7702 |
| timely_leagueews-minus-timely_tcn | +0.5375 [+0.3787, +0.6945] | -0.0006 [-0.0059, +0.0044] | +0.7025, +0.4249, +0.4851 |

### Sharing effects and target interaction by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_independent: baron | -2.1798 [-2.9278, -1.4145] | +0.0131 [-0.0009, +0.0270] | -1.3259, -2.5605, -2.6529 |
| timely_leagueews-minus-timely_independent: dragon | +0.0604 [-0.0892, +0.2086] | -0.0014 [-0.0073, +0.0047] | +0.0736, -0.0846, +0.1920 |
| timely_leagueews-minus-timely_independent: teamfight | +0.1271 [-0.0085, +0.2584] | +0.0037 [-0.0087, +0.0163] | +0.1779, +0.0532, +0.1502 |
| timely_leagueews-minus-timely_independent: macro | -0.6641 [-0.9246, -0.3971] | +0.0051 [-0.0013, +0.0114] | -0.3581, -0.8640, -0.7702 |
| leagueews-minus-independent: baron | -0.7940 [-1.3504, -0.2578] | +0.0081 [-0.0032, +0.0188] | -0.2669, -1.3564, -0.7587 |
| leagueews-minus-independent: dragon | +0.3351 [+0.2452, +0.4215] | -0.0024 [-0.0071, +0.0022] | +0.3948, +0.2483, +0.3621 |
| leagueews-minus-independent: teamfight | +0.1542 [+0.0664, +0.2415] | +0.0015 [-0.0071, +0.0104] | +0.2727, +0.1041, +0.0857 |
| leagueews-minus-independent: macro | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | +0.1335, -0.3347, -0.1036 |
| sharing_effect_difference_timely_minus_cumulative: baron | -1.3858 [-2.0010, -0.7554] | +0.0050 [-0.0069, +0.0176] | -1.0590, -1.2041, -1.8942 |
| sharing_effect_difference_timely_minus_cumulative: dragon | -0.2747 [-0.4341, -0.1187] | +0.0010 [-0.0059, +0.0081] | -0.3212, -0.3329, -0.1701 |
| sharing_effect_difference_timely_minus_cumulative: teamfight | -0.0271 [-0.1604, +0.1017] | +0.0022 [-0.0113, +0.0149] | -0.0948, -0.0509, +0.0644 |
| sharing_effect_difference_timely_minus_cumulative: macro | -0.5625 [-0.7758, -0.3427] | +0.0027 [-0.0036, +0.0091] | -0.4917, -0.5293, -0.6666 |

### Useful-lead joint minus independent: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -2.1973 [-2.4497, -1.9539] | -0.0386 [-0.0444, -0.0333] | -1.8057, -1.0227, -3.7636 |
| 0.5 | -2.2313 [-2.5602, -1.9224] | -0.0530 [-0.0604, -0.0457] | -1.6950, -1.1032, -3.8957 |
| 0.75 | -0.9665 [-1.2880, -0.6231] | -0.0225 [-0.0306, -0.0145] | -2.8658, -1.0579, +1.0243 |
| 1.0 | -0.0337 [-0.3768, +0.3229] | +0.0630 [+0.0541, +0.0720] | -1.9740, +1.5682, +0.3048 |
| mean | -1.3572 [-1.6069, -1.1085] | -0.0128 [-0.0184, -0.0073] | -2.0851, -0.4039, -1.5826 |

### Useful-lead joint minus independent: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -2.1221 [-2.3866, -1.8758] | -0.0360 [-0.0416, -0.0305] | -0.7802, -2.1055, -3.4807 |
| 0.5 | -1.8233 [-2.1532, -1.5152] | -0.0395 [-0.0467, -0.0321] | -0.4711, -1.1032, -3.8957 |
| 0.75 | -1.0420 [-1.3739, -0.7036] | -0.0226 [-0.0313, -0.0143] | -1.2127, -1.0579, -0.8555 |
| 1.0 | -0.6026 [-0.9416, -0.2454] | +0.0173 [+0.0078, +0.0264] | -1.9740, +0.9721, -0.8060 |
| mean | -1.3975 [-1.6460, -1.1498] | -0.0202 [-0.0261, -0.0145] | -1.1095, -0.8236, -2.2595 |

### Useful-lead joint minus independent: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.5274 [-0.7738, -0.2948] | +0.0050 [-0.0007, +0.0108] | -0.1648, -0.5828, -0.8346 |
| 0.5 | -0.7732 [-1.0780, -0.4648] | +0.0034 [-0.0035, +0.0103] | -0.2970, -0.9766, -1.0459 |
| 0.75 | -0.7286 [-1.0485, -0.3971] | +0.0057 [-0.0025, +0.0140] | -0.4287, -1.0394, -0.7177 |
| 1.0 | -0.6272 [-0.9549, -0.2916] | +0.0066 [-0.0027, +0.0152] | -0.5420, -0.8569, -0.4827 |
| mean | -0.6641 [-0.9246, -0.3971] | +0.0051 [-0.0013, +0.0114] | -0.3581, -0.8640, -0.7702 |

### Useful-lead joint minus independent: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.6108 [-0.9142, -0.3192] | -0.0002 [-0.0064, +0.0062] | -0.1568, -0.6609, -1.0148 |
| 0.5 | -0.5594 [-0.8971, -0.2208] | +0.0084 [+0.0003, +0.0160] | -0.3066, -0.8775, -0.4941 |
| 0.75 | -0.4439 [-0.7886, -0.0962] | +0.0166 [+0.0076, +0.0252] | -0.1425, -0.8643, -0.3248 |
| 1.0 | -0.6015 [-0.9442, -0.2376] | +0.0026 [-0.0074, +0.0122] | -0.0813, -1.0802, -0.6430 |
| mean | -0.5539 [-0.8260, -0.2785] | +0.0068 [+0.0004, +0.0128] | -0.1718, -0.8707, -0.6192 |

### Useful-lead joint minus independent: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.5257 [-0.8297, -0.2355] | +0.0020 [-0.0044, +0.0084] | -0.0983, -0.6683, -0.8104 |
| 0.5 | -0.6680 [-1.0023, -0.3236] | +0.0016 [-0.0065, +0.0094] | -0.2617, -0.9029, -0.8393 |
| 0.75 | -0.6091 [-0.9478, -0.2637] | +0.0164 [+0.0072, +0.0252] | -0.2482, -1.0274, -0.5517 |
| 1.0 | -0.5716 [-0.9123, -0.2015] | +0.0035 [-0.0073, +0.0135] | -0.3031, -0.7802, -0.6314 |
| mean | -0.5936 [-0.8621, -0.3171] | +0.0059 [-0.0005, +0.0120] | -0.2278, -0.8447, -0.7082 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_leagueews-minus-timely_independent: baron | -2.9553 [-4.0126, -1.8772] | +0.0050 [-0.0140, +0.0234] | -1.2901, -3.4421, -4.1336 |
| europe: timely_leagueews-minus-timely_independent: dragon | +0.1810 [-0.0180, +0.4016] | +0.0007 [-0.0078, +0.0087] | +0.3713, -0.1112, +0.2828 |
| europe: timely_leagueews-minus-timely_independent: teamfight | +0.0702 [-0.1145, +0.2442] | +0.0099 [-0.0075, +0.0266] | +0.1053, -0.0107, +0.1159 |
| europe: timely_leagueews-minus-timely_independent: macro | -0.9014 [-1.2666, -0.5206] | +0.0052 [-0.0038, +0.0135] | -0.2712, -1.1880, -1.2450 |
| europe: leagueews-minus-independent: baron | -1.3280 [-2.1173, -0.5625] | -0.0144 [-0.0290, +0.0010] | -0.5646, -2.1838, -1.2357 |
| europe: leagueews-minus-independent: dragon | +0.4397 [+0.3036, +0.5743] | -0.0010 [-0.0085, +0.0061] | +0.4614, +0.3255, +0.5323 |
| europe: leagueews-minus-independent: teamfight | +0.1377 [+0.0090, +0.2693] | +0.0051 [-0.0085, +0.0190] | +0.1812, +0.1672, +0.0646 |
| europe: leagueews-minus-independent: macro | -0.2502 [-0.5141, +0.0086] | -0.0034 [-0.0102, +0.0037] | +0.0260, -0.5637, -0.2129 |
| europe: sharing_effect_difference_timely_minus_cumulative: baron | -1.6272 [-2.4180, -0.7539] | +0.0194 [+0.0036, +0.0349] | -0.7255, -1.2583, -2.8979 |
| europe: sharing_effect_difference_timely_minus_cumulative: dragon | -0.2588 [-0.4961, -0.0257] | +0.0017 [-0.0085, +0.0125] | -0.0901, -0.4367, -0.2495 |
| europe: sharing_effect_difference_timely_minus_cumulative: teamfight | -0.0675 [-0.2733, +0.1179] | +0.0048 [-0.0148, +0.0241] | -0.0759, -0.1779, +0.0513 |
| europe: sharing_effect_difference_timely_minus_cumulative: macro | -0.6512 [-0.9390, -0.3457] | +0.0086 [-0.0001, +0.0176] | -0.2972, -0.6243, -1.0320 |
| americas: timely_leagueews-minus-timely_independent: baron | -1.4142 [-2.4455, -0.3425] | +0.0212 [+0.0026, +0.0399] | -1.3613, -1.6902, -1.1912 |
| americas: timely_leagueews-minus-timely_independent: dragon | -0.0566 [-0.2597, +0.1552] | -0.0035 [-0.0116, +0.0046] | -0.2151, -0.0587, +0.1040 |
| americas: timely_leagueews-minus-timely_independent: teamfight | +0.1849 [+0.0021, +0.3572] | -0.0024 [-0.0197, +0.0138] | +0.2517, +0.1181, +0.1850 |
| americas: timely_leagueews-minus-timely_independent: macro | -0.4286 [-0.7882, -0.0580] | +0.0051 [-0.0036, +0.0135] | -0.4416, -0.5436, -0.3008 |
| americas: leagueews-minus-independent: baron | -0.2668 [-1.0154, +0.4709] | +0.0306 [+0.0138, +0.0475] | +0.0270, -0.5397, -0.2878 |
| americas: leagueews-minus-independent: dragon | +0.2336 [+0.1189, +0.3450] | -0.0038 [-0.0095, +0.0019] | +0.3302, +0.1734, +0.1970 |
| americas: leagueews-minus-independent: teamfight | +0.1709 [+0.0608, +0.2811] | -0.0020 [-0.0138, +0.0090] | +0.3656, +0.0399, +0.1072 |
| americas: leagueews-minus-independent: macro | +0.0459 [-0.2116, +0.3028] | +0.0083 [+0.0013, +0.0154] | +0.2409, -0.1088, +0.0055 |
| americas: sharing_effect_difference_timely_minus_cumulative: baron | -1.1474 [-2.0244, -0.2226] | -0.0095 [-0.0261, +0.0079] | -1.3882, -1.1505, -0.9035 |
| americas: sharing_effect_difference_timely_minus_cumulative: dragon | -0.2902 [-0.5123, -0.0701] | +0.0003 [-0.0086, +0.0098] | -0.5453, -0.2322, -0.0931 |
| americas: sharing_effect_difference_timely_minus_cumulative: teamfight | +0.0140 [-0.1563, +0.1749] | -0.0005 [-0.0183, +0.0160] | -0.1139, +0.0781, +0.0778 |
| americas: sharing_effect_difference_timely_minus_cumulative: macro | -0.4745 [-0.7929, -0.1628] | -0.0032 [-0.0120, +0.0052] | -0.6825, -0.4349, -0.3062 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_independent: baron | -2.5095 [-3.5247, -1.5065] | -0.0056 [-0.0261, +0.0147] | -1.5119, -3.5483, -2.4684 |
| timely_leagueews-minus-timely_independent: dragon | +0.6679 [+0.4154, +0.9199] | +0.0152 [+0.0028, +0.0264] | +0.8739, +0.3531, +0.7768 |
| timely_leagueews-minus-timely_independent: teamfight | +0.0370 [-0.1476, +0.2185] | -0.0019 [-0.0204, +0.0162] | +0.3940, -0.0455, -0.2374 |
| timely_leagueews-minus-timely_independent: macro | -0.6015 [-0.9442, -0.2376] | +0.0026 [-0.0074, +0.0122] | -0.0813, -1.0802, -0.6430 |
| leagueews-minus-independent: baron | -1.5324 [-2.3626, -0.7246] | -0.0049 [-0.0232, +0.0130] | -0.7714, -2.2832, -1.5427 |
| leagueews-minus-independent: dragon | +0.4943 [+0.2297, +0.7540] | +0.0052 [-0.0061, +0.0164] | +0.2825, +0.8386, +0.3619 |
| leagueews-minus-independent: teamfight | +0.3452 [+0.1807, +0.5113] | +0.0114 [-0.0052, +0.0300] | +0.6113, +0.3183, +0.1061 |
| leagueews-minus-independent: macro | -0.2310 [-0.5309, +0.0604] | +0.0039 [-0.0052, +0.0134] | +0.0408, -0.3755, -0.3582 |
| sharing_effect_difference_timely_minus_cumulative: baron | -0.9771 [-1.9342, -0.0409] | -0.0007 [-0.0194, +0.0191] | -0.7405, -1.2650, -0.9256 |
| sharing_effect_difference_timely_minus_cumulative: dragon | +0.1736 [-0.1992, +0.5389] | +0.0100 [-0.0066, +0.0261] | +0.5914, -0.4855, +0.4149 |
| sharing_effect_difference_timely_minus_cumulative: teamfight | -0.3082 [-0.5288, -0.0814] | -0.0133 [-0.0370, +0.0101] | -0.2172, -0.3637, -0.3435 |
| sharing_effect_difference_timely_minus_cumulative: macro | -0.3705 [-0.7231, -0.0245] | -0.0013 [-0.0130, +0.0100] | -0.1221, -0.7047, -0.2848 |

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
| event_point_nonharm | False |
| no_extra_burden | False |
| practical_promotion | not established; diagnostic study cannot erase prior failed budget gates |
| primary_full_input_regional_hard_one_violations | 12 |
| primary_independent_regional_hard_one_violations | 10 |
| regional_sharing_consistency | False |
| sharing_support | False |

All model/event/region/seed results and paired intervals are retained in `analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`. Neither a diagnostic pass nor input exclusion establishes novelty or a causal effect of game actions. Previously failed regional gates remain failed.
