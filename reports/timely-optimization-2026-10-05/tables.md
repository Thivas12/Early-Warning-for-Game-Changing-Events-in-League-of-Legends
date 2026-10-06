# Useful-lead optimizer factorial evidence

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
| timely_equal_sum | 17.175 / 0.6354 | 10.795 / 0.6342 | 2.660 / 0.6119 | 10.210 / 0.6271 |
| timely_original_pcgrad | 16.422 / 0.6375 | 10.719 / 0.6278 | 2.668 / 0.6107 | 9.936 / 0.6253 |
| timely_equal_pcgrad | 17.062 / 0.6419 | 10.796 / 0.6277 | 2.654 / 0.6113 | 10.171 / 0.6270 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | -0.0671 [-0.1766, +0.0509] | +0.0003 [-0.0063, +0.0073] | -0.0837, -0.0126, -0.1051 |
| leagueews-minus-current_only | +0.7171 [+0.5431, +0.8813] | -0.0101 [-0.0178, -0.0026] | +0.8251, +0.7580, +0.5681 |
| leagueews-minus-gru | +3.3809 [+3.0613, +3.7204] | +0.0064 [-0.0085, +0.0205] | +2.9995, +3.0401, +4.1030 |
| leagueews-minus-independent | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | +0.1200, -0.0894, -0.0868 |
| leagueews-minus-snapshot | +0.9479 [+0.7639, +1.1342] | -0.0084 [-0.0172, +0.0005] | +0.9041, +1.0516, +0.8879 |
| leagueews-minus-tcn | +0.0476 [-0.0630, +0.1608] | -0.0030 [-0.0074, +0.0017] | +0.0106, +0.0769, +0.0554 |
| projection_by_weighting_interaction | -0.0903 [-0.1820, +0.0047] | +0.0008 [-0.0036, +0.0054] | -0.0909, -0.0302, -0.1498 |
| sharing_effect_difference_timely_minus_cumulative | -0.0422 [-0.1652, +0.0800] | -0.0018 [-0.0075, +0.0040] | -0.0085, +0.0584, -0.1765 |
| timely_clock_history-minus-timely_current_only | +0.1170 [+0.0140, +0.2186] | +0.0018 [-0.0025, +0.0061] | +0.0184, +0.1838, +0.1488 |
| timely_current_only-minus-current_only | +0.5176 [+0.3858, +0.6438] | -0.0053 [-0.0133, +0.0030] | +0.6248, +0.4581, +0.4699 |
| timely_equal_pcgrad-minus-timely_equal_sum | -0.0392 [-0.1034, +0.0239] | -0.0002 [-0.0030, +0.0030] | -0.0192, -0.0473, -0.0511 |
| timely_equal_pcgrad-minus-timely_independent | +0.2247 [+0.0764, +0.3776] | +0.0001 [-0.0066, +0.0065] | +0.2926, +0.3016, +0.0800 |
| timely_equal_pcgrad-minus-timely_leagueews | +0.2857 [+0.1918, +0.3765] | +0.0007 [-0.0030, +0.0047] | +0.1811, +0.3326, +0.3434 |
| timely_equal_pcgrad-minus-timely_original_pcgrad | +0.2346 [+0.1521, +0.3161] | +0.0017 [-0.0020, +0.0054] | +0.1094, +0.3496, +0.2447 |
| timely_equal_pcgrad-minus-timely_tcn | +0.4613 [+0.3370, +0.5879] | -0.0040 [-0.0093, +0.0014] | +0.4595, +0.5303, +0.3943 |
| timely_equal_sum-minus-timely_independent | +0.2639 [+0.1185, +0.4166] | +0.0003 [-0.0063, +0.0066] | +0.3118, +0.3489, +0.1311 |
| timely_equal_sum-minus-timely_leagueews | +0.3249 [+0.2308, +0.4181] | +0.0009 [-0.0030, +0.0045] | +0.2003, +0.3799, +0.3945 |
| timely_equal_sum-minus-timely_tcn | +0.5005 [+0.3709, +0.6342] | -0.0038 [-0.0091, +0.0019] | +0.4787, +0.5775, +0.4454 |
| timely_independent-minus-independent | +0.4927 [+0.3512, +0.6462] | -0.0033 [-0.0115, +0.0053] | +0.5497, +0.3871, +0.5414 |
| timely_leagueews-minus-leagueews | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |
| timely_leagueews-minus-timely_clock_history | +0.5330 [+0.3739, +0.6958] | -0.0117 [-0.0193, -0.0038] | +0.7230, +0.5616, +0.3142 |
| timely_leagueews-minus-timely_clock_only | +2.9334 [+2.6308, +3.2524] | -0.0093 [-0.0214, +0.0033] | +3.0772, +2.9184, +2.8047 |
| timely_leagueews-minus-timely_current_only | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |
| timely_leagueews-minus-timely_independent | -0.0610 [-0.2192, +0.0992] | -0.0006 [-0.0070, +0.0061] | +0.1115, -0.0310, -0.2634 |
| timely_leagueews-minus-timely_tcn | +0.1757 [+0.0613, +0.2903] | -0.0047 [-0.0097, +0.0005] | +0.2784, +0.1977, +0.0509 |
| timely_original_pcgrad-minus-timely_independent | -0.0099 [-0.1662, +0.1454] | -0.0015 [-0.0085, +0.0052] | +0.1831, -0.0481, -0.1646 |
| timely_original_pcgrad-minus-timely_leagueews | +0.0511 [-0.0151, +0.1150] | -0.0010 [-0.0040, +0.0020] | +0.0716, -0.0171, +0.0987 |
| timely_original_pcgrad-minus-timely_tcn | +0.2268 [+0.1138, +0.3409] | -0.0056 [-0.0109, -0.0001] | +0.3501, +0.1806, +0.1496 |

### Weight, projection and interaction effects by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_leagueews: baron | +0.8988 [+0.6503, +1.1491] | -0.0026 [-0.0096, +0.0042] | +0.6898, +1.0444, +0.9623 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.0719 [-0.0324, +0.1804] | -0.0015 [-0.0070, +0.0039] | +0.0007, +0.0202, +0.1947 |
| timely_equal_sum-minus-timely_leagueews: teamfight | +0.0040 [-0.0448, +0.0535] | +0.0067 [-0.0006, +0.0137] | -0.0895, +0.0750, +0.0265 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.3249 [+0.2308, +0.4181] | +0.0009 [-0.0030, +0.0045] | +0.2003, +0.3799, +0.3945 |
| timely_original_pcgrad-minus-timely_leagueews: baron | +0.1455 [-0.0274, +0.3188] | -0.0005 [-0.0052, +0.0042] | +0.1890, -0.0148, +0.2622 |
| timely_original_pcgrad-minus-timely_leagueews: dragon | -0.0042 [-0.0898, +0.0828] | -0.0079 [-0.0124, -0.0033] | +0.0338, -0.0600, +0.0135 |
| timely_original_pcgrad-minus-timely_leagueews: teamfight | +0.0120 [-0.0287, +0.0520] | +0.0055 [-0.0006, +0.0115] | -0.0080, +0.0235, +0.0204 |
| timely_original_pcgrad-minus-timely_leagueews: macro | +0.0511 [-0.0151, +0.1150] | -0.0010 [-0.0040, +0.0020] | +0.0716, -0.0171, +0.0987 |
| timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.1130 [-0.2741, +0.0514] | +0.0066 [+0.0021, +0.0110] | -0.1724, -0.1490, -0.0177 |
| timely_equal_pcgrad-minus-timely_equal_sum: dragon | +0.0017 [-0.0857, +0.0886] | -0.0065 [-0.0112, -0.0018] | +0.0472, +0.0483, -0.0905 |
| timely_equal_pcgrad-minus-timely_equal_sum: teamfight | -0.0063 [-0.0471, +0.0346] | -0.0006 [-0.0066, +0.0059] | +0.0674, -0.0411, -0.0451 |
| timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.0392 [-0.1034, +0.0239] | -0.0002 [-0.0030, +0.0030] | -0.0192, -0.0473, -0.0511 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +0.6403 [+0.4381, +0.8494] | +0.0044 [-0.0019, +0.0108] | +0.3284, +0.9102, +0.6824 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | +0.0777 [-0.0281, +0.1863] | -0.0000 [-0.0057, +0.0057] | +0.0141, +0.1285, +0.0907 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | -0.0143 [-0.0627, +0.0350] | +0.0006 [-0.0065, +0.0077] | -0.0141, +0.0103, -0.0391 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.2346 [+0.1521, +0.3161] | +0.0017 [-0.0020, +0.0054] | +0.1094, +0.3496, +0.2447 |
| projection_by_weighting_interaction: baron | -0.2585 [-0.4976, -0.0162] | +0.0070 [+0.0006, +0.0140] | -0.3614, -0.1342, -0.2799 |
| projection_by_weighting_interaction: dragon | +0.0059 [-0.1162, +0.1262] | +0.0014 [-0.0047, +0.0078] | +0.0134, +0.1082, -0.1041 |
| projection_by_weighting_interaction: teamfight | -0.0183 [-0.0743, +0.0388] | -0.0061 [-0.0144, +0.0028] | +0.0754, -0.0647, -0.0656 |
| projection_by_weighting_interaction: macro | -0.0903 [-0.1820, +0.0047] | +0.0008 [-0.0036, +0.0054] | -0.0909, -0.0302, -0.1498 |

### Primary equal-weight minus original-weight sum: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.1247 [-0.2484, +0.0017] | -0.0219 [-0.0255, -0.0182] | +0.3179, -0.2497, -0.4424 |
| 0.5 | -0.2861 [-0.4394, -0.1446] | -0.0481 [-0.0534, -0.0430] | +0.3262, -0.2417, -0.9428 |
| 0.75 | +0.7616 [+0.6195, +0.9149] | +0.0405 [+0.0345, +0.0466] | +0.4017, +0.4833, +1.3997 |
| 1.0 | -0.0457 [-0.1974, +0.1061] | -0.0390 [-0.0455, -0.0326] | +0.0622, +0.3355, -0.5347 |
| mean | +0.0763 [-0.0158, +0.1663] | -0.0171 [-0.0209, -0.0135] | +0.2770, +0.0818, -0.1301 |

### Primary equal-weight minus original-weight sum: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.0185 [-0.1478, +0.1112] | -0.0174 [-0.0210, -0.0136] | +0.3179, -0.2497, -0.1236 |
| 0.5 | -0.1284 [-0.2830, +0.0240] | -0.0389 [-0.0441, -0.0338] | +0.2542, -0.0566, -0.5828 |
| 0.75 | +0.5604 [+0.4150, +0.7125] | +0.0265 [+0.0205, +0.0325] | -0.4485, +0.7301, +1.3997 |
| 1.0 | +0.0907 [-0.0586, +0.2401] | -0.0289 [-0.0352, -0.0224] | +0.0622, +0.7447, -0.5347 |
| mean | +0.1261 [+0.0323, +0.2198] | -0.0146 [-0.0184, -0.0110] | +0.0464, +0.2921, +0.0396 |

### Primary equal-weight minus original-weight sum: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2328 [+0.1250, +0.3467] | +0.0023 [-0.0011, +0.0057] | +0.2504, +0.2774, +0.1707 |
| 0.5 | +0.3540 [+0.2147, +0.4891] | -0.0007 [-0.0053, +0.0039] | +0.2306, +0.3926, +0.4388 |
| 0.75 | +0.3830 [+0.2489, +0.5209] | -0.0003 [-0.0059, +0.0054] | +0.1971, +0.4327, +0.5191 |
| 1.0 | +0.3297 [+0.1968, +0.4618] | +0.0023 [-0.0039, +0.0082] | +0.1231, +0.4167, +0.4493 |
| mean | +0.3249 [+0.2308, +0.4181] | +0.0009 [-0.0030, +0.0045] | +0.2003, +0.3799, +0.3945 |

### Primary equal-weight minus original-weight sum: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1388 [+0.0115, +0.2764] | -0.0031 [-0.0073, +0.0009] | +0.0869, +0.2235, +0.1059 |
| 0.5 | +0.3226 [+0.1715, +0.4749] | +0.0034 [-0.0019, +0.0090] | +0.2560, +0.1875, +0.5244 |
| 0.75 | +0.3710 [+0.2150, +0.5265] | +0.0009 [-0.0056, +0.0073] | +0.1486, +0.3004, +0.6638 |
| 1.0 | +0.3289 [+0.1783, +0.4741] | +0.0003 [-0.0066, +0.0068] | +0.2164, +0.3831, +0.3872 |
| mean | +0.2903 [+0.1928, +0.3824] | +0.0003 [-0.0034, +0.0041] | +0.1770, +0.2737, +0.4203 |

### Primary equal-weight minus original-weight sum: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2011 [+0.0709, +0.3361] | -0.0011 [-0.0051, +0.0030] | +0.2015, +0.3161, +0.0856 |
| 0.5 | +0.3774 [+0.2252, +0.5313] | +0.0065 [+0.0010, +0.0121] | +0.3485, +0.1757, +0.6080 |
| 0.75 | +0.3661 [+0.2156, +0.5184] | +0.0019 [-0.0043, +0.0083] | +0.0026, +0.4217, +0.6741 |
| 1.0 | +0.3524 [+0.2048, +0.4954] | +0.0004 [-0.0064, +0.0070] | +0.2002, +0.3982, +0.4589 |
| mean | +0.3243 [+0.2295, +0.4188] | +0.0019 [-0.0018, +0.0056] | +0.1882, +0.3279, +0.4567 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_equal_sum-minus-timely_leagueews: baron | +0.8526 [+0.4876, +1.1792] | +0.0041 [-0.0053, +0.0135] | +0.6793, +0.8502, +1.0281 |
| europe: timely_equal_sum-minus-timely_leagueews: dragon | +0.1016 [-0.0502, +0.2533] | -0.0064 [-0.0139, +0.0009] | +0.2115, -0.2503, +0.3436 |
| europe: timely_equal_sum-minus-timely_leagueews: teamfight | -0.0436 [-0.1098, +0.0197] | +0.0076 [-0.0022, +0.0177] | -0.1159, -0.0667, +0.0518 |
| europe: timely_equal_sum-minus-timely_leagueews: macro | +0.3035 [+0.1668, +0.4329] | +0.0017 [-0.0031, +0.0069] | +0.2583, +0.1778, +0.4745 |
| europe: timely_original_pcgrad-minus-timely_leagueews: baron | +0.0495 [-0.1944, +0.2822] | -0.0038 [-0.0102, +0.0028] | +0.0177, -0.0703, +0.2012 |
| europe: timely_original_pcgrad-minus-timely_leagueews: dragon | -0.0563 [-0.1866, +0.0739] | -0.0151 [-0.0214, -0.0084] | -0.0186, -0.2591, +0.1088 |
| europe: timely_original_pcgrad-minus-timely_leagueews: teamfight | -0.0147 [-0.0706, +0.0412] | +0.0012 [-0.0068, +0.0095] | -0.0389, -0.0599, +0.0547 |
| europe: timely_original_pcgrad-minus-timely_leagueews: macro | -0.0072 [-0.1054, +0.0841] | -0.0059 [-0.0101, -0.0018] | -0.0133, -0.1298, +0.1215 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.0064 [-0.2312, +0.2303] | +0.0046 [-0.0011, +0.0103] | +0.0587, -0.0114, -0.0665 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: dragon | -0.0566 [-0.1780, +0.0705] | -0.0092 [-0.0160, -0.0026] | -0.0068, -0.0711, -0.0920 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: teamfight | -0.0264 [-0.0791, +0.0254] | +0.0015 [-0.0064, +0.0095] | +0.0736, -0.0472, -0.1055 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.0298 [-0.1193, +0.0577] | -0.0010 [-0.0052, +0.0030] | +0.0418, -0.0432, -0.0880 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +0.7966 [+0.4969, +1.1117] | +0.0125 [+0.0040, +0.0207] | +0.7203, +0.9091, +0.7605 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | +0.1013 [-0.0554, +0.2614] | -0.0006 [-0.0093, +0.0079] | +0.2233, -0.0622, +0.1427 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | -0.0552 [-0.1262, +0.0112] | +0.0078 [-0.0026, +0.0174] | -0.0034, -0.0539, -0.1084 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.2809 [+0.1662, +0.3962] | +0.0066 [+0.0012, +0.0117] | +0.3134, +0.2643, +0.2649 |
| europe: projection_by_weighting_interaction: baron | -0.0559 [-0.3838, +0.2866] | +0.0084 [-0.0005, +0.0173] | +0.0410, +0.0589, -0.2677 |
| europe: projection_by_weighting_interaction: dragon | -0.0003 [-0.1838, +0.1718] | +0.0058 [-0.0033, +0.0148] | +0.0118, +0.1880, -0.2008 |
| europe: projection_by_weighting_interaction: teamfight | -0.0116 [-0.0874, +0.0640] | +0.0003 [-0.0113, +0.0118] | +0.1125, +0.0128, -0.1602 |
| europe: projection_by_weighting_interaction: macro | -0.0226 [-0.1476, +0.1088] | +0.0048 [-0.0012, +0.0110] | +0.0551, +0.0866, -0.2096 |
| americas: timely_equal_sum-minus-timely_leagueews: baron | +0.9445 [+0.5774, +1.3030] | -0.0093 [-0.0201, +0.0003] | +0.7001, +1.2360, +0.8973 |
| americas: timely_equal_sum-minus-timely_leagueews: dragon | +0.0430 [-0.0948, +0.1838] | +0.0035 [-0.0041, +0.0109] | -0.2038, +0.2826, +0.0503 |
| americas: timely_equal_sum-minus-timely_leagueews: teamfight | +0.0523 [-0.0177, +0.1198] | +0.0059 [-0.0049, +0.0163] | -0.0627, +0.2189, +0.0007 |
| americas: timely_equal_sum-minus-timely_leagueews: macro | +0.3466 [+0.2183, +0.4815] | +0.0000 [-0.0056, +0.0052] | +0.1445, +0.5792, +0.3161 |
| americas: timely_original_pcgrad-minus-timely_leagueews: baron | +0.2402 [-0.0021, +0.4715] | +0.0028 [-0.0041, +0.0099] | +0.3581, +0.0400, +0.3225 |
| americas: timely_original_pcgrad-minus-timely_leagueews: dragon | +0.0463 [-0.0801, +0.1603] | -0.0007 [-0.0070, +0.0056] | +0.0847, +0.1332, -0.0789 |
| americas: timely_original_pcgrad-minus-timely_leagueews: teamfight | +0.0392 [-0.0198, +0.0957] | +0.0098 [+0.0012, +0.0186] | +0.0235, +0.1084, -0.0143 |
| americas: timely_original_pcgrad-minus-timely_leagueews: macro | +0.1086 [+0.0177, +0.1929] | +0.0040 [-0.0002, +0.0083] | +0.1554, +0.0939, +0.0764 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.2182 [-0.4370, +0.0031] | +0.0086 [+0.0024, +0.0148] | -0.4005, -0.2848, +0.0305 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: dragon | +0.0582 [-0.0634, +0.1823] | -0.0037 [-0.0106, +0.0032] | +0.0996, +0.1641, -0.0891 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: teamfight | +0.0141 [-0.0506, +0.0775] | -0.0027 [-0.0110, +0.0057] | +0.0612, -0.0350, +0.0162 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.0486 [-0.1373, +0.0432] | +0.0007 [-0.0034, +0.0050] | -0.0799, -0.0519, -0.0141 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +0.4860 [+0.1832, +0.7715] | -0.0036 [-0.0136, +0.0058] | -0.0585, +0.9112, +0.6053 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | +0.0549 [-0.0902, +0.2035] | +0.0005 [-0.0075, +0.0086] | -0.1888, +0.3134, +0.0401 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | +0.0273 [-0.0486, +0.0970] | -0.0065 [-0.0169, +0.0036] | -0.0251, +0.0756, +0.0313 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.1894 [+0.0722, +0.3043] | -0.0032 [-0.0091, +0.0019] | -0.0908, +0.4334, +0.2256 |
| americas: projection_by_weighting_interaction: baron | -0.4585 [-0.8061, -0.1016] | +0.0057 [-0.0043, +0.0157] | -0.7586, -0.3248, -0.2920 |
| americas: projection_by_weighting_interaction: dragon | +0.0119 [-0.1525, +0.1820] | -0.0030 [-0.0118, +0.0062] | +0.0150, +0.0308, -0.0102 |
| americas: projection_by_weighting_interaction: teamfight | -0.0250 [-0.1090, +0.0596] | -0.0124 [-0.0243, -0.0004] | +0.0376, -0.1433, +0.0306 |
| americas: projection_by_weighting_interaction: macro | -0.1572 [-0.2854, -0.0266] | -0.0032 [-0.0095, +0.0030] | -0.2353, -0.1458, -0.0905 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_leagueews: baron | +0.8742 [+0.4689, +1.2446] | +0.0089 [-0.0041, +0.0210] | +0.4011, +1.1416, +1.0799 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.1295 [-0.0351, +0.3002] | +0.0094 [-0.0004, +0.0191] | +0.3796, -0.1589, +0.1677 |
| timely_equal_sum-minus-timely_leagueews: teamfight | -0.0168 [-0.1011, +0.0707] | -0.0176 [-0.0302, -0.0052] | -0.1313, +0.1667, -0.0859 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.3289 [+0.1783, +0.4741] | +0.0003 [-0.0066, +0.0068] | +0.2164, +0.3831, +0.3872 |
| timely_original_pcgrad-minus-timely_leagueews: baron | +0.2777 [-0.0105, +0.5530] | +0.0058 [-0.0038, +0.0157] | +0.1543, +0.0309, +0.6479 |
| timely_original_pcgrad-minus-timely_leagueews: dragon | +0.0324 [-0.1128, +0.1767] | -0.0019 [-0.0100, +0.0061] | +0.3884, +0.0441, -0.3354 |
| timely_original_pcgrad-minus-timely_leagueews: teamfight | +0.0000 [-0.0761, +0.0728] | +0.0103 [+0.0001, +0.0214] | +0.0354, -0.0404, +0.0051 |
| timely_original_pcgrad-minus-timely_leagueews: macro | +0.1034 [-0.0052, +0.2132] | +0.0047 [-0.0007, +0.0102] | +0.1927, +0.0115, +0.1059 |
| timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.0103 [-0.2946, +0.2957] | +0.0061 [-0.0038, +0.0156] | +0.0617, -0.2160, +0.1234 |
| timely_equal_pcgrad-minus-timely_equal_sum: dragon | -0.2089 [-0.3617, -0.0554] | -0.0202 [-0.0288, -0.0123] | -0.1147, -0.3707, -0.1412 |
| timely_equal_pcgrad-minus-timely_equal_sum: teamfight | -0.0370 [-0.1087, +0.0413] | +0.0016 [-0.0090, +0.0131] | -0.0152, -0.1414, +0.0455 |
| timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.0854 [-0.1987, +0.0309] | -0.0042 [-0.0101, +0.0016] | -0.0227, -0.2427, +0.0092 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +0.5862 [+0.2552, +0.9545] | +0.0092 [-0.0023, +0.0210] | +0.3085, +0.8948, +0.5554 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | -0.1118 [-0.2905, +0.0620] | -0.0089 [-0.0182, +0.0002] | -0.1236, -0.5737, +0.3619 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | -0.0539 [-0.1445, +0.0401] | -0.0263 [-0.0394, -0.0134] | -0.1819, +0.0657, -0.0455 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.1402 [+0.0133, +0.2733] | -0.0087 [-0.0155, -0.0020] | +0.0010, +0.1289, +0.2906 |
| projection_by_weighting_interaction: baron | -0.2880 [-0.6881, +0.1542] | +0.0003 [-0.0131, +0.0144] | -0.0926, -0.2468, -0.5245 |
| projection_by_weighting_interaction: dragon | -0.2413 [-0.4489, -0.0469] | -0.0183 [-0.0297, -0.0066] | -0.5031, -0.4149, +0.1942 |
| projection_by_weighting_interaction: teamfight | -0.0370 [-0.1379, +0.0684] | -0.0088 [-0.0242, +0.0077] | -0.0505, -0.1010, +0.0404 |
| projection_by_weighting_interaction: macro | -0.1888 [-0.3393, -0.0243] | -0.0089 [-0.0170, -0.0007] | -0.2154, -0.2542, -0.0966 |

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
| timely_equal_sum | 20.717 / 0.6507 | 21.751 / 0.6075 | 5.204 / 0.6198 | 15.890 / 0.6260 |
| timely_original_pcgrad | 19.579 / 0.6494 | 21.889 / 0.6079 | 5.212 / 0.6219 | 15.560 / 0.6264 |
| timely_equal_pcgrad | 20.578 / 0.6531 | 21.774 / 0.6095 | 5.231 / 0.6162 | 15.861 / 0.6263 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | +0.0103 [-0.1558, +0.1801] | +0.0089 [+0.0014, +0.0170] | +0.0379, -0.0906, +0.0837 |
| leagueews-minus-current_only | +0.0791 [-0.1184, +0.2619] | -0.0053 [-0.0124, +0.0017] | +0.2043, +0.1901, -0.1572 |
| leagueews-minus-gru | +0.6296 [+0.2694, +0.9920] | +0.0034 [-0.0108, +0.0173] | +0.0340, +0.1626, +1.6921 |
| leagueews-minus-independent | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | +0.1335, -0.3347, -0.1036 |
| leagueews-minus-snapshot | +0.4238 [+0.2114, +0.6347] | -0.0066 [-0.0144, +0.0013] | +0.2788, +0.4714, +0.5213 |
| leagueews-minus-tcn | +0.2977 [+0.1526, +0.4329] | -0.0033 [-0.0077, +0.0007] | +0.0664, +0.4455, +0.3811 |
| projection_by_weighting_interaction | -0.1411 [-0.2673, -0.0166] | -0.0003 [-0.0045, +0.0037] | -0.3396, +0.0416, -0.1252 |
| sharing_effect_difference_timely_minus_cumulative | -0.5625 [-0.7758, -0.3427] | +0.0027 [-0.0036, +0.0091] | -0.4917, -0.5293, -0.6666 |
| timely_clock_history-minus-timely_current_only | -0.0426 [-0.1855, +0.0879] | +0.0055 [+0.0014, +0.0093] | +0.0756, +0.0438, -0.2473 |
| timely_current_only-minus-current_only | +3.9853 [+3.7507, +4.2310] | -0.0131 [-0.0222, -0.0030] | +4.1749, +3.9879, +3.7932 |
| timely_equal_pcgrad-minus-timely_equal_sum | -0.0292 [-0.1092, +0.0570] | +0.0002 [-0.0027, +0.0031] | -0.1644, +0.0851, -0.0083 |
| timely_equal_pcgrad-minus-timely_independent | -0.2509 [-0.4740, -0.0091] | +0.0055 [-0.0006, +0.0115] | -0.0420, -0.2497, -0.4609 |
| timely_equal_pcgrad-minus-timely_leagueews | +0.4132 [+0.2929, +0.5393] | +0.0004 [-0.0033, +0.0040] | +0.3161, +0.6143, +0.3093 |
| timely_equal_pcgrad-minus-timely_original_pcgrad | +0.3013 [+0.1840, +0.4236] | -0.0002 [-0.0037, +0.0035] | +0.1409, +0.5707, +0.1924 |
| timely_equal_pcgrad-minus-timely_tcn | +0.9508 [+0.7625, +1.1445] | -0.0002 [-0.0058, +0.0052] | +1.0186, +1.0392, +0.7945 |
| timely_equal_sum-minus-timely_independent | -0.2217 [-0.4428, +0.0097] | +0.0053 [-0.0011, +0.0112] | +0.1224, -0.3348, -0.4526 |
| timely_equal_sum-minus-timely_leagueews | +0.4424 [+0.3142, +0.5740] | +0.0001 [-0.0036, +0.0036] | +0.4805, +0.5291, +0.3177 |
| timely_equal_sum-minus-timely_tcn | +0.9800 [+0.7800, +1.1752] | -0.0005 [-0.0061, +0.0050] | +1.1830, +0.9541, +0.8028 |
| timely_independent-minus-independent | +4.5582 [+4.3122, +4.8259] | -0.0068 [-0.0169, +0.0038] | +4.7045, +4.4265, +4.5436 |
| timely_leagueews-minus-leagueews | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |
| timely_leagueews-minus-timely_clock_history | +0.1320 [-0.0635, +0.3245] | -0.0018 [-0.0082, +0.0047] | +0.1666, +0.0556, +0.1739 |
| timely_leagueews-minus-timely_clock_only | +2.1385 [+1.8057, +2.4602] | +0.0065 [-0.0058, +0.0187] | +2.4487, +1.8945, +2.0722 |
| timely_leagueews-minus-timely_current_only | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |
| timely_leagueews-minus-timely_independent | -0.6641 [-0.9246, -0.3971] | +0.0051 [-0.0013, +0.0114] | -0.3581, -0.8640, -0.7702 |
| timely_leagueews-minus-timely_tcn | +0.5375 [+0.3787, +0.6945] | -0.0006 [-0.0059, +0.0044] | +0.7025, +0.4249, +0.4851 |
| timely_original_pcgrad-minus-timely_independent | -0.5522 [-0.8107, -0.2892] | +0.0057 [-0.0010, +0.0120] | -0.1829, -0.8204, -0.6533 |
| timely_original_pcgrad-minus-timely_leagueews | +0.1119 [+0.0248, +0.2005] | +0.0005 [-0.0024, +0.0035] | +0.1752, +0.0435, +0.1169 |
| timely_original_pcgrad-minus-timely_tcn | +0.6494 [+0.4898, +0.8156] | -0.0001 [-0.0052, +0.0050] | +0.8777, +0.4685, +0.6021 |

### Weight, projection and interaction effects by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_leagueews: baron | +1.3098 [+0.9500, +1.6719] | +0.0035 [-0.0037, +0.0107] | +1.3662, +1.6029, +0.9603 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.0207 [-0.0861, +0.1317] | -0.0008 [-0.0048, +0.0034] | +0.1640, -0.0333, -0.0685 |
| timely_equal_sum-minus-timely_leagueews: teamfight | -0.0032 [-0.0756, +0.0628] | -0.0023 [-0.0094, +0.0043] | -0.0887, +0.0179, +0.0611 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.4424 [+0.3142, +0.5740] | +0.0001 [-0.0036, +0.0036] | +0.4805, +0.5291, +0.3177 |
| timely_original_pcgrad-minus-timely_leagueews: baron | +0.1720 [-0.0734, +0.4272] | +0.0022 [-0.0032, +0.0077] | +0.3940, -0.0851, +0.2070 |
| timely_original_pcgrad-minus-timely_leagueews: dragon | +0.1591 [+0.0719, +0.2412] | -0.0005 [-0.0038, +0.0030] | +0.2062, +0.2055, +0.0656 |
| timely_original_pcgrad-minus-timely_leagueews: teamfight | +0.0046 [-0.0472, +0.0621] | -0.0001 [-0.0058, +0.0057] | -0.0746, +0.0102, +0.0781 |
| timely_original_pcgrad-minus-timely_leagueews: macro | +0.1119 [+0.0248, +0.2005] | +0.0005 [-0.0024, +0.0035] | +0.1752, +0.0435, +0.1169 |
| timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.1383 [-0.3600, +0.1008] | +0.0024 [-0.0031, +0.0076] | -0.4358, +0.0782, -0.0572 |
| timely_equal_pcgrad-minus-timely_equal_sum: dragon | +0.0238 [-0.0585, +0.1102] | +0.0019 [-0.0014, +0.0054] | -0.0760, +0.1389, +0.0085 |
| timely_equal_pcgrad-minus-timely_equal_sum: teamfight | +0.0269 [-0.0259, +0.0771] | -0.0036 [-0.0094, +0.0022] | +0.0186, +0.0382, +0.0238 |
| timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.0292 [-0.1092, +0.0570] | +0.0002 [-0.0027, +0.0031] | -0.1644, +0.0851, -0.0083 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +0.9996 [+0.6542, +1.3426] | +0.0037 [-0.0033, +0.0105] | +0.5364, +1.7661, +0.6961 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | -0.1146 [-0.2143, -0.0110] | +0.0016 [-0.0024, +0.0058] | -0.1183, -0.0999, -0.1256 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | +0.0191 [-0.0498, +0.0874] | -0.0057 [-0.0128, +0.0006] | +0.0045, +0.0459, +0.0068 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.3013 [+0.1840, +0.4236] | -0.0002 [-0.0037, +0.0035] | +0.1409, +0.5707, +0.1924 |
| projection_by_weighting_interaction: baron | -0.3103 [-0.6588, +0.0419] | +0.0001 [-0.0071, +0.0077] | -0.8298, +0.1632, -0.2642 |
| projection_by_weighting_interaction: dragon | -0.1353 [-0.2553, -0.0195] | +0.0024 [-0.0021, +0.0069] | -0.2823, -0.0665, -0.0571 |
| projection_by_weighting_interaction: teamfight | +0.0223 [-0.0576, +0.0963] | -0.0035 [-0.0118, +0.0047] | +0.0932, +0.0280, -0.0543 |
| projection_by_weighting_interaction: macro | -0.1411 [-0.2673, -0.0166] | -0.0003 [-0.0045, +0.0037] | -0.3396, +0.0416, -0.1252 |

### Primary equal-weight minus original-weight sum: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +2.2335 [+2.0275, +2.4426] | +0.0595 [+0.0549, +0.0642] | +1.7779, +3.1301, +1.7924 |
| 0.5 | +1.6744 [+1.4535, +1.8935] | +0.0451 [+0.0401, +0.0506] | +1.8327, +0.5224, +2.6681 |
| 0.75 | +0.2581 [+0.0647, +0.4518] | -0.0315 [-0.0374, -0.0254] | +1.8929, +0.6831, -1.8017 |
| 1.0 | +0.5757 [+0.3698, +0.7934] | +0.0162 [+0.0102, +0.0224] | +1.6835, +0.6818, -0.6382 |
| mean | +1.1854 [+1.0556, +1.3101] | +0.0223 [+0.0190, +0.0257] | +1.7968, +1.2543, +0.5051 |

### Primary equal-weight minus original-weight sum: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +1.6935 [+1.4973, +1.8883] | +0.0378 [+0.0337, +0.0422] | +0.4409, +3.1301, +1.5095 |
| 0.5 | +1.2664 [+1.0513, +1.4802] | +0.0316 [+0.0267, +0.0369] | +0.6088, +0.5224, +2.6681 |
| 0.75 | +0.2041 [+0.0069, +0.4093] | -0.0538 [-0.0602, -0.0467] | +0.2398, +0.6831, -0.3104 |
| 1.0 | +0.8808 [+0.6700, +1.1016] | +0.0311 [+0.0250, +0.0374] | +1.6835, +0.6818, +0.2772 |
| mean | +1.0112 [+0.8840, +1.1354] | +0.0117 [+0.0082, +0.0153] | +0.7432, +1.2543, +1.0361 |

### Primary equal-weight minus original-weight sum: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2548 [+0.1011, +0.4058] | -0.0019 [-0.0054, +0.0014] | +0.2217, +0.3456, +0.1971 |
| 0.5 | +0.4079 [+0.2451, +0.5732] | +0.0003 [-0.0040, +0.0049] | +0.3785, +0.4983, +0.3470 |
| 0.75 | +0.5366 [+0.3624, +0.7141] | +0.0011 [-0.0042, +0.0063] | +0.5402, +0.6283, +0.4412 |
| 1.0 | +0.5704 [+0.3869, +0.7653] | +0.0011 [-0.0042, +0.0064] | +0.7817, +0.6443, +0.2853 |
| mean | +0.4424 [+0.3142, +0.5740] | +0.0001 [-0.0036, +0.0036] | +0.4805, +0.5291, +0.3177 |

### Primary equal-weight minus original-weight sum: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.3136 [+0.1214, +0.5020] | -0.0013 [-0.0055, +0.0027] | +0.0083, +0.2939, +0.6386 |
| 0.5 | +0.3926 [+0.1931, +0.5953] | -0.0025 [-0.0077, +0.0029] | +0.3430, +0.5553, +0.2794 |
| 0.75 | +0.4098 [+0.2186, +0.6144] | -0.0027 [-0.0084, +0.0030] | +0.4700, +0.3169, +0.4427 |
| 1.0 | +0.6911 [+0.4808, +0.9056] | +0.0112 [+0.0047, +0.0179] | +0.5689, +0.8697, +0.6347 |
| mean | +0.4518 [+0.3235, +0.5814] | +0.0011 [-0.0026, +0.0047] | +0.3476, +0.5090, +0.4988 |

### Primary equal-weight minus original-weight sum: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.3555 [+0.1689, +0.5386] | +0.0030 [-0.0013, +0.0070] | +0.0930, +0.3324, +0.6412 |
| 0.5 | +0.5610 [+0.3608, +0.7625] | +0.0054 [+0.0000, +0.0109] | +0.5462, +0.6631, +0.4736 |
| 0.75 | +0.5560 [+0.3699, +0.7641] | -0.0023 [-0.0080, +0.0037] | +0.5198, +0.5909, +0.5572 |
| 1.0 | +0.6801 [+0.4717, +0.8900] | +0.0121 [+0.0054, +0.0190] | +0.7850, +0.7236, +0.5318 |
| mean | +0.5381 [+0.4112, +0.6675] | +0.0045 [+0.0007, +0.0083] | +0.4860, +0.5775, +0.5510 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_equal_sum-minus-timely_leagueews: baron | +1.3839 [+0.8475, +1.9027] | +0.0085 [-0.0019, +0.0186] | +1.1759, +1.4950, +1.4809 |
| europe: timely_equal_sum-minus-timely_leagueews: dragon | +0.0955 [-0.0566, +0.2461] | +0.0038 [-0.0021, +0.0099] | +0.0207, +0.2753, -0.0094 |
| europe: timely_equal_sum-minus-timely_leagueews: teamfight | -0.0134 [-0.1195, +0.0937] | -0.0055 [-0.0150, +0.0037] | -0.1113, +0.0236, +0.0474 |
| europe: timely_equal_sum-minus-timely_leagueews: macro | +0.4887 [+0.2921, +0.6766] | +0.0023 [-0.0030, +0.0073] | +0.3618, +0.5980, +0.5063 |
| europe: timely_original_pcgrad-minus-timely_leagueews: baron | +0.0011 [-0.3694, +0.3819] | -0.0037 [-0.0112, +0.0039] | -0.2949, -0.2946, +0.5928 |
| europe: timely_original_pcgrad-minus-timely_leagueews: dragon | +0.2185 [+0.1057, +0.3356] | +0.0018 [-0.0030, +0.0063] | +0.1285, +0.3978, +0.1292 |
| europe: timely_original_pcgrad-minus-timely_leagueews: teamfight | -0.0257 [-0.1064, +0.0598] | +0.0058 [-0.0026, +0.0140] | -0.1623, -0.0183, +0.1037 |
| europe: timely_original_pcgrad-minus-timely_leagueews: macro | +0.0646 [-0.0725, +0.2022] | +0.0013 [-0.0026, +0.0055] | -0.1096, +0.0283, +0.2752 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.1216 [-0.4444, +0.1905] | -0.0064 [-0.0132, +0.0003] | -0.4021, +0.1064, -0.0691 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: dragon | -0.0160 [-0.1376, +0.1101] | +0.0000 [-0.0049, +0.0047] | -0.1857, +0.0669, +0.0709 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: teamfight | +0.0452 [-0.0359, +0.1246] | -0.0027 [-0.0109, +0.0055] | +0.1400, -0.0044, -0.0001 |
| europe: timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.0308 [-0.1526, +0.0900] | -0.0030 [-0.0069, +0.0008] | -0.1493, +0.0563, +0.0006 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +1.2612 [+0.7666, +1.7328] | +0.0058 [-0.0040, +0.0155] | +1.0686, +1.8960, +0.8191 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | -0.1389 [-0.2772, +0.0009] | +0.0021 [-0.0037, +0.0080] | -0.2934, -0.0556, -0.0677 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | +0.0574 [-0.0420, +0.1573] | -0.0141 [-0.0239, -0.0041] | +0.1911, +0.0376, -0.0563 |
| europe: timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.3933 [+0.2153, +0.5637] | -0.0021 [-0.0073, +0.0032] | +0.3221, +0.6260, +0.2317 |
| europe: projection_by_weighting_interaction: baron | -0.1227 [-0.6177, +0.3729] | -0.0027 [-0.0126, +0.0072] | -0.1073, +0.4010, -0.6618 |
| europe: projection_by_weighting_interaction: dragon | -0.2344 [-0.4063, -0.0678] | -0.0017 [-0.0084, +0.0048] | -0.3142, -0.3309, -0.0583 |
| europe: projection_by_weighting_interaction: teamfight | +0.0709 [-0.0473, +0.1819] | -0.0086 [-0.0197, +0.0027] | +0.3024, +0.0140, -0.1037 |
| europe: projection_by_weighting_interaction: macro | -0.0954 [-0.2818, +0.0913] | -0.0044 [-0.0097, +0.0012] | -0.0397, +0.0280, -0.2746 |
| americas: timely_equal_sum-minus-timely_leagueews: baron | +1.2367 [+0.7186, +1.7658] | -0.0015 [-0.0117, +0.0086] | +1.5541, +1.7094, +0.4464 |
| americas: timely_equal_sum-minus-timely_leagueews: dragon | -0.0519 [-0.2002, +0.0947] | -0.0054 [-0.0112, +0.0000] | +0.3029, -0.3327, -0.1258 |
| americas: timely_equal_sum-minus-timely_leagueews: teamfight | +0.0071 [-0.0774, +0.0982] | +0.0009 [-0.0082, +0.0108] | -0.0658, +0.0121, +0.0751 |
| americas: timely_equal_sum-minus-timely_leagueews: macro | +0.3973 [+0.2113, +0.5772] | -0.0020 [-0.0072, +0.0033] | +0.5971, +0.4629, +0.1319 |
| americas: timely_original_pcgrad-minus-timely_leagueews: baron | +0.3407 [+0.0144, +0.6540] | +0.0081 [+0.0001, +0.0158] | +1.0740, +0.1218, -0.1738 |
| americas: timely_original_pcgrad-minus-timely_leagueews: dragon | +0.1015 [-0.0216, +0.2197] | -0.0027 [-0.0075, +0.0020] | +0.2816, +0.0190, +0.0039 |
| americas: timely_original_pcgrad-minus-timely_leagueews: teamfight | +0.0353 [-0.0314, +0.1079] | -0.0061 [-0.0140, +0.0017] | +0.0146, +0.0392, +0.0521 |
| americas: timely_original_pcgrad-minus-timely_leagueews: macro | +0.1592 [+0.0417, +0.2751] | -0.0002 [-0.0044, +0.0039] | +0.4568, +0.0600, -0.0392 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.1547 [-0.4990, +0.1953] | +0.0111 [+0.0036, +0.0190] | -0.4691, +0.0503, -0.0455 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: dragon | +0.0624 [-0.0541, +0.1733] | +0.0039 [-0.0007, +0.0084] | +0.0304, +0.2088, -0.0521 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: teamfight | +0.0082 [-0.0671, +0.0823] | -0.0045 [-0.0130, +0.0034] | -0.1048, +0.0815, +0.0480 |
| americas: timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.0280 [-0.1545, +0.0937] | +0.0035 [-0.0008, +0.0078] | -0.1812, +0.1135, -0.0165 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +0.7412 [+0.2416, +1.2064] | +0.0016 [-0.0088, +0.0119] | +0.0111, +1.6379, +0.5747 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | -0.0910 [-0.2290, +0.0514] | +0.0011 [-0.0041, +0.0069] | +0.0516, -0.1428, -0.1819 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | -0.0199 [-0.1189, +0.0725] | +0.0026 [-0.0063, +0.0123] | -0.1852, +0.0544, +0.0710 |
| americas: timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.2101 [+0.0389, +0.3703] | +0.0018 [-0.0034, +0.0068] | -0.0408, +0.5165, +0.1546 |
| americas: projection_by_weighting_interaction: baron | -0.4954 [-0.9775, -0.0045] | +0.0030 [-0.0079, +0.0140] | -1.5430, -0.0715, +0.1283 |
| americas: projection_by_weighting_interaction: dragon | -0.0392 [-0.1979, +0.1200] | +0.0066 [+0.0003, +0.0131] | -0.2513, +0.1898, -0.0560 |
| americas: projection_by_weighting_interaction: teamfight | -0.0271 [-0.1349, +0.0734] | +0.0017 [-0.0095, +0.0131] | -0.1194, +0.0423, -0.0042 |
| americas: projection_by_weighting_interaction: macro | -0.1872 [-0.3552, -0.0159] | +0.0037 [-0.0021, +0.0096] | -0.6379, +0.0535, +0.0227 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_leagueews: baron | +1.7793 [+1.1886, +2.3690] | +0.0194 [+0.0067, +0.0316] | +1.8204, +2.1598, +1.3576 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.1442 [-0.0556, +0.3432] | -0.0037 [-0.0120, +0.0051] | -0.0530, +0.2118, +0.2736 |
| timely_equal_sum-minus-timely_leagueews: teamfight | +0.1499 [+0.0339, +0.2679] | +0.0178 [+0.0052, +0.0302] | -0.0606, +0.2374, +0.2728 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.6911 [+0.4808, +0.9056] | +0.0112 [+0.0047, +0.0179] | +0.5689, +0.8697, +0.6347 |
| timely_original_pcgrad-minus-timely_leagueews: baron | +0.6274 [+0.1744, +1.1104] | +0.0284 [+0.0189, +0.0386] | +1.0182, +0.3703, +0.4937 |
| timely_original_pcgrad-minus-timely_leagueews: dragon | -0.1442 [-0.3119, +0.0207] | -0.0106 [-0.0180, -0.0032] | -0.5208, +0.2295, -0.1412 |
| timely_original_pcgrad-minus-timely_leagueews: teamfight | +0.0977 [+0.0017, +0.1951] | +0.0028 [-0.0074, +0.0130] | -0.0152, -0.0707, +0.3789 |
| timely_original_pcgrad-minus-timely_leagueews: macro | +0.1936 [+0.0363, +0.3610] | +0.0069 [+0.0012, +0.0126] | +0.1608, +0.1763, +0.2438 |
| timely_equal_pcgrad-minus-timely_equal_sum: baron | -0.0720 [-0.4887, +0.3607] | -0.0042 [-0.0127, +0.0053] | -0.4011, -0.1543, +0.3394 |
| timely_equal_pcgrad-minus-timely_equal_sum: dragon | -0.2619 [-0.4335, -0.0909] | -0.0040 [-0.0112, +0.0034] | -0.2648, +0.2118, -0.7326 |
| timely_equal_pcgrad-minus-timely_equal_sum: teamfight | -0.0101 [-0.1075, +0.0824] | -0.0083 [-0.0191, +0.0021] | -0.0303, -0.0152, +0.0152 |
| timely_equal_pcgrad-minus-timely_equal_sum: macro | -0.1147 [-0.2672, +0.0411] | -0.0055 [-0.0107, -0.0001] | -0.2321, +0.0141, -0.1260 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: baron | +1.0799 [+0.4897, +1.6724] | -0.0132 [-0.0252, -0.0016] | +0.4011, +1.6353, +1.2033 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: dragon | +0.0265 [-0.1699, +0.2142] | +0.0029 [-0.0057, +0.0120] | +0.2030, +0.1942, -0.3178 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: teamfight | +0.0421 [-0.0800, +0.1620] | +0.0067 [-0.0059, +0.0192] | -0.0758, +0.2930, -0.0909 |
| timely_equal_pcgrad-minus-timely_original_pcgrad: macro | +0.3828 [+0.1668, +0.5932] | -0.0012 [-0.0079, +0.0050] | +0.1761, +0.7075, +0.2649 |
| projection_by_weighting_interaction: baron | -0.6994 [-1.3305, -0.0411] | -0.0327 [-0.0459, -0.0189] | -1.4193, -0.5245, -0.1543 |
| projection_by_weighting_interaction: dragon | -0.1177 [-0.3460, +0.1143] | +0.0066 [-0.0038, +0.0171] | +0.2560, -0.0177, -0.5914 |
| projection_by_weighting_interaction: teamfight | -0.1078 [-0.2534, +0.0254] | -0.0111 [-0.0267, +0.0041] | -0.0152, +0.0556, -0.3637 |
| projection_by_weighting_interaction: macro | -0.3083 [-0.5315, -0.0765] | -0.0124 [-0.0201, -0.0046] | -0.3928, -0.1622, -0.3698 |

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
| event_point_nonharm | True |
| mechanism_recovery | True |
| no_extra_burden | False |
| practical_promotion | not established by this exploratory optimizer diagnostic; previous gates and sealed-test requirements remain in force |
| regional_weighting_consistency | True |
| weighting_support | True |

## Hard-one burden violations

Counts are event/region/seed/budget cells out of 72 for each row. Every one of the four budgets is included; nominal-budget violations are retained in CSV.

| Family / window | deterministic | regional_deterministic | matched_early_mixture | dense_deterministic | dense_regional_deterministic |
|---|---:|---:|---:|---:|---:|
| current_only / 10-30 | 1 | 1 | 14 | 9 | 11 |
| current_only / 20-60 | 1 | 3 | 14 | 8 | 12 |
| gru / 10-30 | 1 | 1 | 10 | 5 | 9 |
| gru / 20-60 | 1 | 1 | 11 | 1 | 5 |
| independent / 10-30 | 1 | 4 | 13 | 5 | 11 |
| independent / 20-60 | 0 | 0 | 12 | 2 | 8 |
| leagueews / 10-30 | 1 | 3 | 15 | 6 | 12 |
| leagueews / 20-60 | 0 | 0 | 12 | 3 | 7 |
| pcgrad / 10-30 | 1 | 2 | 12 | 5 | 9 |
| pcgrad / 20-60 | 1 | 1 | 12 | 3 | 5 |
| snapshot / 10-30 | 1 | 1 | 12 | 10 | 10 |
| snapshot / 20-60 | 0 | 1 | 12 | 8 | 10 |
| tcn / 10-30 | 3 | 3 | 14 | 5 | 12 |
| tcn / 20-60 | 1 | 2 | 13 | 5 | 11 |
| timely_clock_history / 10-30 | 2 | 2 | 12 | 4 | 6 |
| timely_clock_history / 20-60 | 1 | 1 | 7 | 3 | 3 |
| timely_clock_only / 10-30 | 0 | 0 | 10 | 3 | 4 |
| timely_clock_only / 20-60 | 0 | 0 | 4 | 0 | 0 |
| timely_current_only / 10-30 | 0 | 0 | 11 | 3 | 4 |
| timely_current_only / 20-60 | 1 | 1 | 8 | 3 | 5 |
| timely_equal_pcgrad / 10-30 | 1 | 2 | 8 | 3 | 6 |
| timely_equal_pcgrad / 20-60 | 0 | 0 | 7 | 3 | 6 |
| timely_equal_sum / 10-30 | 3 | 3 | 12 | 4 | 7 |
| timely_equal_sum / 20-60 | 0 | 1 | 8 | 3 | 8 |
| timely_independent / 10-30 | 1 | 1 | 10 | 4 | 8 |
| timely_independent / 20-60 | 0 | 1 | 6 | 2 | 4 |
| timely_leagueews / 10-30 | 1 | 1 | 12 | 5 | 5 |
| timely_leagueews / 20-60 | 0 | 0 | 7 | 0 | 2 |
| timely_original_pcgrad / 10-30 | 0 | 0 | 10 | 3 | 6 |
| timely_original_pcgrad / 20-60 | 0 | 0 | 7 | 3 | 7 |
| timely_tcn / 10-30 | 1 | 2 | 9 | 3 | 6 |
| timely_tcn / 20-60 | 1 | 2 | 8 | 5 | 7 |

All model/event/region/seed results and paired intervals are retained in `analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`. Neither a diagnostic pass nor an optimizer change establishes novelty or a causal effect of game actions. Previously failed regional gates remain failed.
