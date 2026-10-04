# Useful-lead input-control evidence

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

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | -0.0671 [-0.1766, +0.0509] | +0.0003 [-0.0063, +0.0073] | -0.0837, -0.0126, -0.1051 |
| leagueews-minus-current_only | +0.7171 [+0.5431, +0.8813] | -0.0101 [-0.0178, -0.0026] | +0.8251, +0.7580, +0.5681 |
| leagueews-minus-gru | +3.3809 [+3.0613, +3.7204] | +0.0064 [-0.0085, +0.0205] | +2.9995, +3.0401, +4.1030 |
| leagueews-minus-independent | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | +0.1200, -0.0894, -0.0868 |
| leagueews-minus-snapshot | +0.9479 [+0.7639, +1.1342] | -0.0084 [-0.0172, +0.0005] | +0.9041, +1.0516, +0.8879 |
| leagueews-minus-tcn | +0.0476 [-0.0630, +0.1608] | -0.0030 [-0.0074, +0.0017] | +0.0106, +0.0769, +0.0554 |
| timely_current_only-minus-current_only | +0.5176 [+0.3858, +0.6438] | -0.0053 [-0.0133, +0.0030] | +0.6248, +0.4581, +0.4699 |
| timely_leagueews-minus-leagueews | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |
| timely_leagueews-minus-timely_clock_only | +2.9334 [+2.6308, +3.2524] | -0.0093 [-0.0214, +0.0033] | +3.0772, +2.9184, +2.8047 |
| timely_leagueews-minus-timely_current_only | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |
| timely_leagueews-minus-timely_tcn | +0.1757 [+0.0613, +0.2903] | -0.0047 [-0.0097, +0.0005] | +0.2784, +0.1977, +0.0509 |

### Input effects and target interaction by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_current_only: baron | +1.5319 [+1.0534, +2.0068] | -0.0032 [-0.0166, +0.0097] | +1.8333, +1.7228, +1.0396 |
| timely_leagueews-minus-timely_current_only: dragon | +0.1851 [+0.0183, +0.3491] | +0.0029 [-0.0055, +0.0109] | +0.0830, +0.2915, +0.1808 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.2330 [+0.1078, +0.3600] | -0.0292 [-0.0483, -0.0102] | +0.3080, +0.2221, +0.1688 |
| timely_leagueews-minus-timely_current_only: macro | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |
| timely_leagueews-minus-timely_clock_only: baron | +6.5389 [+5.6402, +7.4506] | +0.0033 [-0.0223, +0.0291] | +7.0889, +6.4137, +6.1141 |
| timely_leagueews-minus-timely_clock_only: dragon | +1.0684 [+0.7926, +1.3350] | -0.0016 [-0.0165, +0.0125] | +0.9261, +1.2010, +1.0782 |
| timely_leagueews-minus-timely_clock_only: teamfight | +1.1930 [+1.0204, +1.3566] | -0.0296 [-0.0533, -0.0044] | +1.2165, +1.1407, +1.2217 |
| timely_leagueews-minus-timely_clock_only: macro | +2.9334 [+2.6308, +3.2524] | -0.0093 [-0.0214, +0.0033] | +3.0772, +2.9184, +2.8047 |
| history_effect_difference_timely_minus_cumulative: baron | -0.3343 [-0.5861, -0.0504] | -0.0013 [-0.0090, +0.0062] | -0.4111, -0.2679, -0.3238 |
| history_effect_difference_timely_minus_cumulative: dragon | +0.1000 [-0.0841, +0.2824] | +0.0063 [-0.0031, +0.0158] | +0.1372, +0.1341, +0.0288 |
| history_effect_difference_timely_minus_cumulative: teamfight | +0.0330 [-0.0767, +0.1420] | -0.0041 [-0.0190, +0.0121] | +0.0230, +0.0962, -0.0202 |
| history_effect_difference_timely_minus_cumulative: macro | -0.0671 [-0.1766, +0.0509] | +0.0003 [-0.0063, +0.0073] | -0.0837, -0.0126, -0.1051 |

### History effect: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.3117 [+0.1030, +0.5167] | -0.0183 [-0.0246, -0.0118] | +0.6829, +0.8185, -0.5662 |
| 0.5 | +1.1030 [+0.8698, +1.3472] | +0.0211 [+0.0119, +0.0301] | +0.4235, +1.2560, +1.6294 |
| 0.75 | -0.0688 [-0.3084, +0.1756] | -0.0704 [-0.0804, -0.0600] | -1.0025, +0.1831, +0.6130 |
| 1.0 | +0.7823 [+0.5409, +1.0193] | -0.0076 [-0.0192, +0.0035] | +1.5092, +0.8143, +0.0235 |
| mean | +0.5321 [+0.3512, +0.7063] | -0.0188 [-0.0264, -0.0113] | +0.4033, +0.7680, +0.4249 |

### History effect: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.3117 [+0.1030, +0.5167] | -0.0183 [-0.0246, -0.0118] | +0.6829, +0.8185, -0.5662 |
| 0.5 | +1.1818 [+0.9480, +1.4311] | +0.0253 [+0.0161, +0.0341] | +0.6601, +1.2560, +1.6294 |
| 0.75 | +0.2798 [+0.0291, +0.5276] | -0.0468 [-0.0571, -0.0365] | +0.0432, +0.1831, +0.6130 |
| 1.0 | +0.7858 [+0.5485, +1.0193] | -0.0089 [-0.0206, +0.0023] | +1.3138, +1.0200, +0.0235 |
| mean | +0.6398 [+0.4617, +0.8126] | -0.0122 [-0.0197, -0.0047] | +0.6750, +0.8194, +0.4249 |

### History effect: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.6104 [+0.4146, +0.8050] | -0.0102 [-0.0164, -0.0037] | +0.6744, +0.7882, +0.3687 |
| 0.5 | +0.6359 [+0.4171, +0.8616] | -0.0105 [-0.0193, -0.0017] | +0.6884, +0.6897, +0.5296 |
| 0.75 | +0.6275 [+0.3922, +0.8524] | -0.0093 [-0.0197, +0.0009] | +0.7288, +0.6712, +0.4825 |
| 1.0 | +0.7261 [+0.5109, +0.9343] | -0.0093 [-0.0214, +0.0016] | +0.8741, +0.8328, +0.4714 |
| mean | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |

### History effect: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.6652 [+0.4513, +0.8701] | -0.0084 [-0.0157, -0.0011] | +0.9740, +0.5981, +0.4235 |
| 0.5 | +0.5045 [+0.2775, +0.7450] | -0.0193 [-0.0289, -0.0097] | +0.5577, +0.6506, +0.3053 |
| 0.75 | +0.6036 [+0.3580, +0.8447] | -0.0144 [-0.0253, -0.0034] | +0.6289, +0.6513, +0.5307 |
| 1.0 | +0.7626 [+0.5278, +0.9924] | -0.0036 [-0.0160, +0.0087] | +0.7997, +1.0512, +0.4369 |
| mean | +0.6340 [+0.4562, +0.8067] | -0.0115 [-0.0192, -0.0036] | +0.7401, +0.7378, +0.4241 |

### History effect: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.6452 [+0.4358, +0.8509] | -0.0101 [-0.0172, -0.0027] | +0.8578, +0.6760, +0.4019 |
| 0.5 | +0.5024 [+0.2766, +0.7406] | -0.0212 [-0.0307, -0.0116] | +0.5751, +0.6624, +0.2696 |
| 0.75 | +0.6497 [+0.4084, +0.8894] | -0.0096 [-0.0204, +0.0015] | +0.8258, +0.6515, +0.4719 |
| 1.0 | +0.7741 [+0.5471, +0.9948] | -0.0051 [-0.0177, +0.0074] | +0.8982, +0.9493, +0.4749 |
| mean | +0.6429 [+0.4632, +0.8148] | -0.0115 [-0.0192, -0.0036] | +0.7892, +0.7348, +0.4045 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_leagueews-minus-timely_current_only: baron | +1.4646 [+0.7576, +2.1575] | +0.0021 [-0.0158, +0.0192] | +1.7360, +1.5494, +1.1086 |
| europe: timely_leagueews-minus-timely_current_only: dragon | +0.0884 [-0.1754, +0.3210] | -0.0039 [-0.0155, +0.0077] | -0.0373, +0.3789, -0.0764 |
| europe: timely_leagueews-minus-timely_current_only: teamfight | +0.2678 [+0.0921, +0.4354] | -0.0380 [-0.0662, -0.0093] | +0.2927, +0.3417, +0.1692 |
| europe: timely_leagueews-minus-timely_current_only: macro | +0.6070 [+0.3423, +0.8661] | -0.0133 [-0.0246, -0.0015] | +0.6638, +0.7566, +0.4005 |
| europe: timely_leagueews-minus-timely_clock_only: baron | +7.3065 [+6.0189, +8.6617] | +0.0098 [-0.0255, +0.0448] | +7.5327, +7.2279, +7.1588 |
| europe: timely_leagueews-minus-timely_clock_only: dragon | +1.1938 [+0.7858, +1.5996] | +0.0129 [-0.0076, +0.0312] | +1.0121, +1.5351, +1.0343 |
| europe: timely_leagueews-minus-timely_clock_only: teamfight | +1.2656 [+1.0271, +1.5239] | -0.0284 [-0.0605, +0.0042] | +1.2495, +1.3146, +1.2326 |
| europe: timely_leagueews-minus-timely_clock_only: macro | +3.2553 [+2.8114, +3.7124] | -0.0019 [-0.0205, +0.0155] | +3.2648, +3.3592, +3.1419 |
| europe: history_effect_difference_timely_minus_cumulative: baron | -0.1585 [-0.5658, +0.2431] | -0.0032 [-0.0135, +0.0072] | -0.0911, -0.1037, -0.2806 |
| europe: history_effect_difference_timely_minus_cumulative: dragon | -0.0165 [-0.2904, +0.2448] | +0.0075 [-0.0057, +0.0207] | -0.0192, +0.1519, -0.1821 |
| europe: history_effect_difference_timely_minus_cumulative: teamfight | +0.0259 [-0.1190, +0.1780] | +0.0005 [-0.0226, +0.0226] | -0.0408, +0.1508, -0.0322 |
| europe: history_effect_difference_timely_minus_cumulative: macro | -0.0497 [-0.2184, +0.1299] | +0.0016 [-0.0079, +0.0111] | -0.0504, +0.0663, -0.1649 |
| americas: timely_leagueews-minus-timely_current_only: baron | +1.5984 [+0.9719, +2.2381] | -0.0085 [-0.0269, +0.0106] | +1.9295, +1.8940, +0.9716 |
| americas: timely_leagueews-minus-timely_current_only: dragon | +0.2788 [+0.0471, +0.5062] | +0.0096 [-0.0029, +0.0218] | +0.1996, +0.2068, +0.4302 |
| americas: timely_leagueews-minus-timely_current_only: teamfight | +0.1975 [+0.0133, +0.3812] | -0.0203 [-0.0457, +0.0058] | +0.3236, +0.1006, +0.1684 |
| americas: timely_leagueews-minus-timely_current_only: macro | +0.6916 [+0.4665, +0.9219] | -0.0064 [-0.0173, +0.0052] | +0.8175, +0.7338, +0.5234 |
| americas: timely_leagueews-minus-timely_clock_only: baron | +5.7812 [+4.5397, +7.0412] | -0.0032 [-0.0435, +0.0357] | +6.6507, +5.6099, +5.0829 |
| americas: timely_leagueews-minus-timely_clock_only: dragon | +0.9468 [+0.5539, +1.3528] | -0.0161 [-0.0376, +0.0063] | +0.8427, +0.8769, +1.1208 |
| americas: timely_leagueews-minus-timely_clock_only: teamfight | +1.1191 [+0.8781, +1.3570] | -0.0309 [-0.0683, +0.0049] | +1.1830, +0.9639, +1.2105 |
| americas: timely_leagueews-minus-timely_clock_only: macro | +2.6157 [+2.1647, +3.0769] | -0.0167 [-0.0367, +0.0026] | +2.8921, +2.4836, +2.4714 |
| americas: history_effect_difference_timely_minus_cumulative: baron | -0.5079 [-0.8932, -0.1458] | +0.0006 [-0.0110, +0.0118] | -0.7270, -0.4301, -0.3666 |
| americas: history_effect_difference_timely_minus_cumulative: dragon | +0.2130 [-0.0530, +0.4629] | +0.0050 [-0.0078, +0.0190] | +0.2888, +0.1168, +0.2333 |
| americas: history_effect_difference_timely_minus_cumulative: teamfight | +0.0402 [-0.1055, +0.1893] | -0.0087 [-0.0318, +0.0147] | +0.0878, +0.0407, -0.0079 |
| americas: history_effect_difference_timely_minus_cumulative: macro | -0.0849 [-0.2397, +0.0700] | -0.0010 [-0.0108, +0.0092] | -0.1168, -0.0909, -0.0471 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_current_only: baron | +1.6764 [+1.0707, +2.2915] | -0.0059 [-0.0267, +0.0141] | +2.0981, +2.0673, +0.8639 |
| timely_leagueews-minus-timely_current_only: dragon | +0.2207 [-0.0294, +0.4686] | -0.0082 [-0.0220, +0.0058] | -0.1942, +0.6973, +0.1589 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.3907 [+0.1989, +0.5811] | +0.0032 [-0.0260, +0.0321] | +0.4951, +0.3890, +0.2880 |
| timely_leagueews-minus-timely_current_only: macro | +0.7626 [+0.5278, +0.9924] | -0.0036 [-0.0160, +0.0087] | +0.7997, +1.0512, +0.4369 |
| timely_leagueews-minus-timely_clock_only: baron | +8.3616 [+7.2404, +9.4908] | +0.0903 [+0.0535, +0.1257] | +9.6267, +7.8062, +7.6520 |
| timely_leagueews-minus-timely_clock_only: dragon | +1.3123 [+0.9339, +1.6958] | -0.0146 [-0.0359, +0.0068] | +0.7679, +1.7389, +1.4300 |
| timely_leagueews-minus-timely_clock_only: teamfight | +1.6671 [+1.4216, +1.9009] | -0.0103 [-0.0448, +0.0258] | +1.7934, +1.5206, +1.6873 |
| timely_leagueews-minus-timely_clock_only: macro | +3.7803 [+3.3943, +4.1797] | +0.0218 [+0.0041, +0.0394] | +4.0627, +3.6886, +3.5897 |
| history_effect_difference_timely_minus_cumulative: baron | -0.2468 [-0.6869, +0.2060] | -0.0106 [-0.0260, +0.0049] | -0.5245, +0.0617, -0.2777 |
| history_effect_difference_timely_minus_cumulative: dragon | +0.0559 [-0.2463, +0.3442] | -0.0006 [-0.0163, +0.0155] | -0.1677, +0.1942, +0.1412 |
| history_effect_difference_timely_minus_cumulative: teamfight | +0.0690 [-0.1145, +0.2423] | +0.0679 [+0.0424, +0.0930] | +0.0253, +0.1465, +0.0354 |
| history_effect_difference_timely_minus_cumulative: macro | -0.0406 [-0.2293, +0.1376] | +0.0189 [+0.0071, +0.0307] | -0.2223, +0.1341, -0.0337 |

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

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | +0.0103 [-0.1558, +0.1801] | +0.0089 [+0.0014, +0.0170] | +0.0379, -0.0906, +0.0837 |
| leagueews-minus-current_only | +0.0791 [-0.1184, +0.2619] | -0.0053 [-0.0124, +0.0017] | +0.2043, +0.1901, -0.1572 |
| leagueews-minus-gru | +0.6296 [+0.2694, +0.9920] | +0.0034 [-0.0108, +0.0173] | +0.0340, +0.1626, +1.6921 |
| leagueews-minus-independent | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | +0.1335, -0.3347, -0.1036 |
| leagueews-minus-snapshot | +0.4238 [+0.2114, +0.6347] | -0.0066 [-0.0144, +0.0013] | +0.2788, +0.4714, +0.5213 |
| leagueews-minus-tcn | +0.2977 [+0.1526, +0.4329] | -0.0033 [-0.0077, +0.0007] | +0.0664, +0.4455, +0.3811 |
| timely_current_only-minus-current_only | +3.9853 [+3.7507, +4.2310] | -0.0131 [-0.0222, -0.0030] | +4.1749, +3.9879, +3.7932 |
| timely_leagueews-minus-leagueews | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |
| timely_leagueews-minus-timely_clock_only | +2.1385 [+1.8057, +2.4602] | +0.0065 [-0.0058, +0.0187] | +2.4487, +1.8945, +2.0722 |
| timely_leagueews-minus-timely_current_only | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |
| timely_leagueews-minus-timely_tcn | +0.5375 [+0.3787, +0.6945] | -0.0006 [-0.0059, +0.0044] | +0.7025, +0.4249, +0.4851 |

### Input effects and target interaction by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_current_only: baron | -0.0962 [-0.6883, +0.4761] | +0.0029 [-0.0090, +0.0142] | +0.2799, +0.0203, -0.5888 |
| timely_leagueews-minus-timely_current_only: dragon | +0.0707 [-0.0817, +0.2316] | -0.0015 [-0.0087, +0.0053] | +0.1042, +0.0294, +0.0785 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.2937 [+0.1365, +0.4407] | +0.0095 [-0.0058, +0.0256] | +0.3425, +0.2488, +0.2899 |
| timely_leagueews-minus-timely_current_only: macro | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |
| timely_leagueews-minus-timely_clock_only: baron | +3.5886 [+2.6750, +4.4897] | +0.0069 [-0.0151, +0.0294] | +4.4707, +2.8782, +3.4169 |
| timely_leagueews-minus-timely_clock_only: dragon | +1.1219 [+0.8575, +1.3891] | -0.0056 [-0.0169, +0.0059] | +1.0686, +1.1560, +1.1412 |
| timely_leagueews-minus-timely_clock_only: teamfight | +1.7049 [+1.4583, +1.9517] | +0.0182 [-0.0081, +0.0452] | +1.8068, +1.6492, +1.6586 |
| timely_leagueews-minus-timely_clock_only: macro | +2.1385 [+1.8057, +2.4602] | +0.0065 [-0.0058, +0.0187] | +2.4487, +1.8945, +2.0722 |
| history_effect_difference_timely_minus_cumulative: baron | -0.2024 [-0.6387, +0.2429] | +0.0009 [-0.0093, +0.0116] | -0.0322, -0.3560, -0.2191 |
| history_effect_difference_timely_minus_cumulative: dragon | -0.0685 [-0.2284, +0.0989] | +0.0008 [-0.0066, +0.0076] | -0.1201, -0.1644, +0.0791 |
| history_effect_difference_timely_minus_cumulative: teamfight | +0.3019 [+0.1425, +0.4685] | +0.0251 [+0.0064, +0.0448] | +0.2661, +0.2484, +0.3912 |
| history_effect_difference_timely_minus_cumulative: macro | +0.0103 [-0.1558, +0.1801] | +0.0089 [+0.0014, +0.0170] | +0.0379, -0.0906, +0.0837 |

### History effect: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.4296 [-0.5829, -0.2680] | -0.0144 [-0.0184, -0.0101] | +0.6301, -1.3950, -0.5238 |
| 0.5 | -0.9302 [-1.1932, -0.6527] | -0.0228 [-0.0301, -0.0154] | -2.4638, +1.0997, -1.4265 |
| 0.75 | -0.2317 [-0.5200, +0.0690] | -0.0023 [-0.0103, +0.0057] | -1.2571, +0.6041, -0.0422 |
| 1.0 | +0.6760 [+0.3584, +0.9839] | +0.0298 [+0.0197, +0.0392] | -0.4104, +0.5916, +1.8468 |
| mean | -0.2289 [-0.4112, -0.0454] | -0.0024 [-0.0077, +0.0030] | -0.8753, +0.2251, -0.0365 |

### History effect: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.0318 [-0.1387, +0.2041] | -0.0007 [-0.0050, +0.0037] | +1.7314, -1.3950, -0.2409 |
| 0.5 | -0.5222 [-0.7913, -0.2464] | -0.0093 [-0.0166, -0.0020] | -1.2398, +1.0997, -1.4265 |
| 0.75 | -0.3305 [-0.6203, -0.0311] | -0.0228 [-0.0317, -0.0138] | -0.5278, +0.0872, -0.5508 |
| 1.0 | +0.3925 [+0.0690, +0.7102] | +0.0145 [+0.0043, +0.0242] | -1.2608, +0.5916, +1.8468 |
| mean | -0.1071 [-0.3029, +0.0831] | -0.0046 [-0.0101, +0.0012] | -0.3243, +0.0959, -0.0929 |

### History effect: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.0032 [-0.2052, +0.2310] | +0.0029 [-0.0024, +0.0087] | +0.1638, +0.1089, -0.2630 |
| 0.5 | -0.0497 [-0.2955, +0.2048] | +0.0057 [-0.0015, +0.0131] | +0.2003, -0.1117, -0.2375 |
| 0.75 | +0.2224 [-0.0551, +0.5028] | +0.0072 [-0.0019, +0.0160] | +0.4200, +0.1192, +0.1279 |
| 1.0 | +0.1817 [-0.1114, +0.4580] | -0.0013 [-0.0110, +0.0083] | +0.1848, +0.2816, +0.0787 |
| mean | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |

### History effect: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.0629 [-0.3072, +0.1842] | -0.0079 [-0.0143, -0.0014] | +0.1264, +0.0536, -0.3687 |
| 0.5 | +0.0042 [-0.2751, +0.2935] | +0.0053 [-0.0023, +0.0134] | +0.0214, +0.1773, -0.1862 |
| 0.75 | +0.4253 [+0.1182, +0.7322] | +0.0187 [+0.0090, +0.0280] | +1.0250, +0.0707, +0.1800 |
| 1.0 | +0.2710 [-0.0556, +0.5736] | -0.0045 [-0.0155, +0.0064] | +0.5650, +0.1950, +0.0532 |
| mean | +0.1594 [-0.0677, +0.3767] | +0.0029 [-0.0036, +0.0095] | +0.4344, +0.1242, -0.0804 |

### History effect: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2332 [-0.0136, +0.4774] | +0.0030 [-0.0035, +0.0097] | +0.5185, +0.3136, -0.1323 |
| 0.5 | -0.1594 [-0.4414, +0.1310] | -0.0034 [-0.0114, +0.0049] | +0.0140, -0.1192, -0.3730 |
| 0.75 | +0.3320 [+0.0265, +0.6437] | +0.0114 [+0.0018, +0.0208] | +0.7825, +0.0271, +0.1862 |
| 1.0 | +0.2241 [-0.0777, +0.5302] | -0.0111 [-0.0221, -0.0001] | +0.3539, +0.2877, +0.0308 |
| mean | +0.1575 [-0.0665, +0.3770] | +0.0000 [-0.0068, +0.0068] | +0.4172, +0.1273, -0.0721 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_leagueews-minus-timely_current_only: baron | -0.0530 [-0.8412, +0.7657] | +0.0102 [-0.0051, +0.0255] | +0.7027, +0.0391, -0.9008 |
| europe: timely_leagueews-minus-timely_current_only: dragon | +0.1764 [-0.0443, +0.4006] | -0.0038 [-0.0130, +0.0052] | +0.3867, -0.0071, +0.1494 |
| europe: timely_leagueews-minus-timely_current_only: teamfight | +0.2910 [+0.0872, +0.4939] | +0.0162 [-0.0061, +0.0397] | +0.2685, +0.2426, +0.3618 |
| europe: timely_leagueews-minus-timely_current_only: macro | +0.1381 [-0.1474, +0.4398] | +0.0076 [-0.0020, +0.0169] | +0.4527, +0.0915, -0.1299 |
| europe: timely_leagueews-minus-timely_clock_only: baron | +3.8787 [+2.5956, +5.2387] | +0.0085 [-0.0234, +0.0397] | +5.0404, +3.2013, +3.3946 |
| europe: timely_leagueews-minus-timely_clock_only: dragon | +1.0636 [+0.7119, +1.4373] | +0.0017 [-0.0131, +0.0173] | +1.0954, +1.0353, +1.0600 |
| europe: timely_leagueews-minus-timely_clock_only: teamfight | +1.8892 [+1.5576, +2.2323] | +0.0315 [-0.0031, +0.0667] | +1.9761, +1.7962, +1.8952 |
| europe: timely_leagueews-minus-timely_clock_only: macro | +2.2772 [+1.8077, +2.7526] | +0.0139 [-0.0038, +0.0300] | +2.7039, +2.0109, +2.1166 |
| europe: history_effect_difference_timely_minus_cumulative: baron | -0.1558 [-0.7852, +0.5104] | +0.0006 [-0.0146, +0.0147] | +0.4194, +0.0204, -0.9073 |
| europe: history_effect_difference_timely_minus_cumulative: dragon | +0.0376 [-0.1895, +0.2626] | -0.0001 [-0.0101, +0.0104] | +0.2459, -0.2452, +0.1122 |
| europe: history_effect_difference_timely_minus_cumulative: teamfight | +0.1390 [-0.0951, +0.3587] | +0.0237 [-0.0019, +0.0492] | -0.0818, +0.2400, +0.2589 |
| europe: history_effect_difference_timely_minus_cumulative: macro | +0.0069 [-0.2325, +0.2655] | +0.0081 [-0.0027, +0.0185] | +0.1945, +0.0051, -0.1787 |
| americas: timely_leagueews-minus-timely_current_only: baron | -0.1388 [-0.9632, +0.7093] | -0.0044 [-0.0215, +0.0124] | -0.1375, +0.0017, -0.2808 |
| americas: timely_leagueews-minus-timely_current_only: dragon | -0.0318 [-0.2470, +0.1832] | +0.0008 [-0.0089, +0.0097] | -0.1697, +0.0647, +0.0097 |
| americas: timely_leagueews-minus-timely_current_only: teamfight | +0.2965 [+0.0674, +0.5250] | +0.0028 [-0.0186, +0.0239] | +0.4178, +0.2550, +0.2168 |
| americas: timely_leagueews-minus-timely_current_only: macro | +0.0420 [-0.2648, +0.3384] | -0.0003 [-0.0095, +0.0085] | +0.0369, +0.1072, -0.0181 |
| americas: timely_leagueews-minus-timely_clock_only: baron | +3.3022 [+1.9815, +4.5420] | +0.0053 [-0.0276, +0.0380] | +3.9084, +2.5594, +3.4390 |
| americas: timely_leagueews-minus-timely_clock_only: dragon | +1.1786 [+0.7943, +1.5542] | -0.0130 [-0.0280, +0.0040] | +1.0427, +1.2731, +1.2199 |
| americas: timely_leagueews-minus-timely_clock_only: teamfight | +1.5175 [+1.1896, +1.8762] | +0.0050 [-0.0334, +0.0439] | +1.6347, +1.4998, +1.4180 |
| americas: timely_leagueews-minus-timely_clock_only: macro | +1.9994 [+1.5386, +2.4298] | -0.0009 [-0.0187, +0.0173] | +2.1953, +1.7774, +2.0256 |
| americas: history_effect_difference_timely_minus_cumulative: baron | -0.2484 [-0.9158, +0.4021] | +0.0012 [-0.0136, +0.0154] | -0.4780, -0.7276, +0.4603 |
| americas: history_effect_difference_timely_minus_cumulative: dragon | -0.1714 [-0.3880, +0.0491] | +0.0016 [-0.0090, +0.0115] | -0.4751, -0.0860, +0.0469 |
| americas: history_effect_difference_timely_minus_cumulative: teamfight | +0.4675 [+0.2379, +0.7177] | +0.0266 [-0.0003, +0.0531] | +0.6198, +0.2570, +0.5257 |
| americas: history_effect_difference_timely_minus_cumulative: macro | +0.0159 [-0.2362, +0.2567] | +0.0098 [-0.0012, +0.0206] | -0.1111, -0.1855, +0.3443 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_leagueews-minus-timely_current_only: baron | +0.0309 [-0.8338, +0.8779] | -0.0282 [-0.0468, -0.0110] | +0.4320, +0.0926, -0.4320 |
| timely_leagueews-minus-timely_current_only: dragon | +0.4825 [+0.2201, +0.7609] | +0.0110 [-0.0014, +0.0239] | +0.8386, +0.1236, +0.4855 |
| timely_leagueews-minus-timely_current_only: teamfight | +0.2997 [+0.0667, +0.5218] | +0.0037 [-0.0210, +0.0291] | +0.4243, +0.3688, +0.1061 |
| timely_leagueews-minus-timely_current_only: macro | +0.2710 [-0.0556, +0.5736] | -0.0045 [-0.0155, +0.0064] | +0.5650, +0.1950, +0.0532 |
| timely_leagueews-minus-timely_clock_only: baron | +6.7572 [+5.5589, +8.0037] | +0.0773 [+0.0468, +0.1098] | +7.1891, +6.6029, +6.4795 |
| timely_leagueews-minus-timely_clock_only: dragon | +1.3329 [+0.8999, +1.7645] | +0.0063 [-0.0137, +0.0255] | +1.6242, +1.0416, +1.3329 |
| timely_leagueews-minus-timely_clock_only: teamfight | +2.2396 [+1.8932, +2.5946] | +0.0186 [-0.0192, +0.0570] | +2.5663, +2.1470, +2.0056 |
| timely_leagueews-minus-timely_clock_only: macro | +3.4432 [+2.9920, +3.8997] | +0.0341 [+0.0155, +0.0527] | +3.7932, +3.2638, +3.2726 |
| history_effect_difference_timely_minus_cumulative: baron | +0.5965 [-0.1849, +1.4021] | +0.0062 [-0.0119, +0.0240] | +0.7405, +0.6479, +0.4011 |
| history_effect_difference_timely_minus_cumulative: dragon | +0.8886 [+0.5166, +1.2878] | +0.0204 [+0.0039, +0.0371] | +1.6948, -0.3178, +1.2887 |
| history_effect_difference_timely_minus_cumulative: teamfight | +0.4580 [+0.1882, +0.7439] | +0.0226 [-0.0115, +0.0561] | +0.2930, +0.6315, +0.4496 |
| history_effect_difference_timely_minus_cumulative: macro | +0.6477 [+0.3426, +0.9657] | +0.0164 [+0.0024, +0.0301] | +0.9094, +0.3206, +0.7131 |

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
| beyond_timing_support | True |
| history_event_nonharm | True |
| history_no_extra_burden | True |
| history_support | True |
| practical_promotion | not established; diagnostic study cannot erase prior failed budget gates |
| primary_full_input_regional_hard_one_violations | 12 |
| regional_history_consistency | True |

All model/event/region/seed results and paired intervals are retained in `analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`. Neither a diagnostic pass nor input exclusion establishes novelty or a causal effect of game actions. Previously failed regional gates remain failed.
