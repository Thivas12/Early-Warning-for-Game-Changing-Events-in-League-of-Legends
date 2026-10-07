# Matched useful-lead architecture evidence

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
| timely_equal_tcn | 16.873 / 0.6411 | 10.460 / 0.6353 | 2.571 / 0.6053 | 9.968 / 0.6272 |
| timely_original_gru | 7.757 / 0.6129 | 4.585 / 0.6319 | 1.873 / 0.6075 | 4.738 / 0.6175 |
| timely_equal_gru | 11.847 / 0.6107 | 4.647 / 0.6371 | 1.971 / 0.6010 | 6.155 / 0.6163 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | -0.0671 [-0.1766, +0.0509] | +0.0003 [-0.0063, +0.0073] | -0.0837, -0.0126, -0.1051 |
| leagueews-minus-current_only | +0.7171 [+0.5431, +0.8813] | -0.0101 [-0.0178, -0.0026] | +0.8251, +0.7580, +0.5681 |
| leagueews-minus-gru | +3.3809 [+3.0613, +3.7204] | +0.0064 [-0.0085, +0.0205] | +2.9995, +3.0401, +4.1030 |
| leagueews-minus-independent | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | +0.1200, -0.0894, -0.0868 |
| leagueews-minus-snapshot | +0.9479 [+0.7639, +1.1342] | -0.0084 [-0.0172, +0.0005] | +0.9041, +1.0516, +0.8879 |
| leagueews-minus-tcn | +0.0476 [-0.0630, +0.1608] | -0.0030 [-0.0074, +0.0017] | +0.0106, +0.0769, +0.0554 |
| leagueews_gru_by_weighting_interaction | -1.0918 [-1.3524, -0.8394] | +0.0021 [-0.0079, +0.0119] | -0.9286, -1.5384, -0.8083 |
| leagueews_tcn_by_weighting_interaction | +0.0663 [-0.0412, +0.1741] | +0.0046 [-0.0003, +0.0093] | -0.0790, +0.0694, +0.2085 |
| projection_by_weighting_interaction | -0.0903 [-0.1820, +0.0047] | +0.0008 [-0.0036, +0.0054] | -0.0909, -0.0302, -0.1498 |
| sharing_effect_difference_timely_minus_cumulative | -0.0422 [-0.1652, +0.0800] | -0.0018 [-0.0075, +0.0040] | -0.0085, +0.0584, -0.1765 |
| timely_clock_history-minus-timely_current_only | +0.1170 [+0.0140, +0.2186] | +0.0018 [-0.0025, +0.0061] | +0.0184, +0.1838, +0.1488 |
| timely_current_only-minus-current_only | +0.5176 [+0.3858, +0.6438] | -0.0053 [-0.0133, +0.0030] | +0.6248, +0.4581, +0.4699 |
| timely_equal_gru-minus-timely_independent | -3.7912 [-4.0844, -3.5150] | -0.0106 [-0.0238, +0.0028] | -3.6397, -3.4379, -4.2959 |
| timely_equal_gru-minus-timely_original_gru | +1.4166 [+1.1845, +1.6611] | -0.0012 [-0.0104, +0.0077] | +1.1289, +1.9183, +1.2028 |
| timely_equal_pcgrad-minus-timely_equal_sum | -0.0392 [-0.1034, +0.0239] | -0.0002 [-0.0030, +0.0030] | -0.0192, -0.0473, -0.0511 |
| timely_equal_pcgrad-minus-timely_independent | +0.2247 [+0.0764, +0.3776] | +0.0001 [-0.0066, +0.0065] | +0.2926, +0.3016, +0.0800 |
| timely_equal_pcgrad-minus-timely_leagueews | +0.2857 [+0.1918, +0.3765] | +0.0007 [-0.0030, +0.0047] | +0.1811, +0.3326, +0.3434 |
| timely_equal_pcgrad-minus-timely_original_pcgrad | +0.2346 [+0.1521, +0.3161] | +0.0017 [-0.0020, +0.0054] | +0.1094, +0.3496, +0.2447 |
| timely_equal_pcgrad-minus-timely_tcn | +0.4613 [+0.3370, +0.5879] | -0.0040 [-0.0093, +0.0014] | +0.4595, +0.5303, +0.3943 |
| timely_equal_sum-minus-timely_equal_gru | +4.0551 [+3.7861, +4.3436] | +0.0109 [-0.0016, +0.0232] | +3.9515, +3.7868, +4.4270 |
| timely_equal_sum-minus-timely_equal_tcn | +0.2420 [+0.1305, +0.3543] | -0.0001 [-0.0053, +0.0052] | +0.1995, +0.2670, +0.2594 |
| timely_equal_sum-minus-timely_independent | +0.2639 [+0.1185, +0.4166] | +0.0003 [-0.0063, +0.0066] | +0.3118, +0.3489, +0.1311 |
| timely_equal_sum-minus-timely_leagueews | +0.3249 [+0.2308, +0.4181] | +0.0009 [-0.0030, +0.0045] | +0.2003, +0.3799, +0.3945 |
| timely_equal_sum-minus-timely_tcn | +0.5005 [+0.3709, +0.6342] | -0.0038 [-0.0091, +0.0019] | +0.4787, +0.5775, +0.4454 |
| timely_equal_tcn-minus-timely_equal_gru | +3.8131 [+3.5467, +4.1040] | +0.0109 [-0.0016, +0.0237] | +3.7520, +3.5198, +4.1676 |
| timely_equal_tcn-minus-timely_independent | +0.0220 [-0.1317, +0.1773] | +0.0004 [-0.0065, +0.0071] | +0.1124, +0.0818, -0.1283 |
| timely_equal_tcn-minus-timely_tcn | +0.2586 [+0.1692, +0.3440] | -0.0037 [-0.0078, +0.0003] | +0.2793, +0.3105, +0.1860 |
| timely_independent-minus-independent | +0.4927 [+0.3512, +0.6462] | -0.0033 [-0.0115, +0.0053] | +0.5497, +0.3871, +0.5414 |
| timely_leagueews-minus-leagueews | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |
| timely_leagueews-minus-timely_clock_history | +0.5330 [+0.3739, +0.6958] | -0.0117 [-0.0193, -0.0038] | +0.7230, +0.5616, +0.3142 |
| timely_leagueews-minus-timely_clock_only | +2.9334 [+2.6308, +3.2524] | -0.0093 [-0.0214, +0.0033] | +3.0772, +2.9184, +2.8047 |
| timely_leagueews-minus-timely_current_only | +0.6500 [+0.4779, +0.8206] | -0.0098 [-0.0176, -0.0022] | +0.7414, +0.7455, +0.4631 |
| timely_leagueews-minus-timely_independent | -0.0610 [-0.2192, +0.0992] | -0.0006 [-0.0070, +0.0061] | +0.1115, -0.0310, -0.2634 |
| timely_leagueews-minus-timely_original_gru | +5.1468 [+4.8088, +5.5019] | +0.0088 [-0.0074, +0.0245] | +4.8800, +5.3252, +5.2353 |
| timely_leagueews-minus-timely_tcn | +0.1757 [+0.0613, +0.2903] | -0.0047 [-0.0097, +0.0005] | +0.2784, +0.1977, +0.0509 |
| timely_original_gru-minus-gru | -1.3154 [-1.4414, -1.1854] | -0.0075 [-0.0149, -0.0001] | -1.3394, -1.8395, -0.7674 |
| timely_original_pcgrad-minus-timely_independent | -0.0099 [-0.1662, +0.1454] | -0.0015 [-0.0085, +0.0052] | +0.1831, -0.0481, -0.1646 |
| timely_original_pcgrad-minus-timely_leagueews | +0.0511 [-0.0151, +0.1150] | -0.0010 [-0.0040, +0.0020] | +0.0716, -0.0171, +0.0987 |
| timely_original_pcgrad-minus-timely_tcn | +0.2268 [+0.1138, +0.3409] | -0.0056 [-0.0109, -0.0001] | +0.3501, +0.1806, +0.1496 |
| timely_tcn-minus-timely_original_gru | +4.9712 [+4.6318, +5.3351] | +0.0135 [-0.0030, +0.0296] | +4.6016, +5.1275, +5.1844 |

### Matched architecture effects and weighting interactions by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_tcn: baron | +0.3022 [+0.0178, +0.5702] | -0.0057 [-0.0141, +0.0024] | +0.3681, +0.3575, +0.1810 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3343 [+0.1593, +0.5082] | -0.0011 [-0.0099, +0.0073] | +0.1542, +0.3706, +0.4780 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.0894 [+0.0157, +0.1618] | +0.0066 [-0.0040, +0.0166] | +0.0761, +0.0730, +0.1191 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.2420 [+0.1305, +0.3543] | -0.0001 [-0.0053, +0.0052] | +0.1995, +0.2670, +0.2594 |
| timely_equal_sum-minus-timely_equal_gru: baron | +5.3286 [+4.6008, +6.1038] | +0.0247 [+0.0050, +0.0433] | +5.1934, +4.5920, +6.2005 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +6.1473 [+5.8075, +6.5222] | -0.0029 [-0.0229, +0.0178] | +6.0433, +6.2114, +6.1872 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.6894 [+0.5312, +0.8387] | +0.0109 [-0.0098, +0.0326] | +0.6177, +0.5571, +0.8934 |
| timely_equal_sum-minus-timely_equal_gru: macro | +4.0551 [+3.7861, +4.3436] | +0.0109 [-0.0016, +0.0232] | +3.9515, +3.7868, +4.4270 |
| timely_leagueews-minus-timely_tcn: baron | +0.0938 [-0.1925, +0.3774] | -0.0109 [-0.0198, -0.0021] | +0.4591, +0.1364, -0.3140 |
| timely_leagueews-minus-timely_tcn: dragon | +0.3446 [+0.1721, +0.5049] | +0.0004 [-0.0078, +0.0083] | +0.2406, +0.3984, +0.3946 |
| timely_leagueews-minus-timely_tcn: teamfight | +0.0886 [+0.0206, +0.1540] | -0.0034 [-0.0125, +0.0059] | +0.1355, +0.0582, +0.0721 |
| timely_leagueews-minus-timely_tcn: macro | +0.1757 [+0.0613, +0.2903] | -0.0047 [-0.0097, +0.0005] | +0.2784, +0.1977, +0.0509 |
| timely_leagueews-minus-timely_original_gru: baron | +8.5192 [+7.5936, +9.5034] | +0.0251 [-0.0036, +0.0532] | +7.8929, +8.8301, +8.8345 |
| timely_leagueews-minus-timely_original_gru: dragon | +6.1380 [+5.7721, +6.5227] | +0.0037 [-0.0167, +0.0248] | +6.0554, +6.4540, +5.9048 |
| timely_leagueews-minus-timely_original_gru: teamfight | +0.7834 [+0.6036, +0.9645] | -0.0024 [-0.0273, +0.0231] | +0.6919, +0.6916, +0.9666 |
| timely_leagueews-minus-timely_original_gru: macro | +5.1468 [+4.8088, +5.5019] | +0.0088 [-0.0074, +0.0245] | +4.8800, +5.3252, +5.2353 |
| leagueews_tcn_by_weighting_interaction: baron | +0.2084 [-0.0712, +0.4768] | +0.0052 [-0.0030, +0.0128] | -0.0911, +0.2211, +0.4951 |
| leagueews_tcn_by_weighting_interaction: dragon | -0.0103 [-0.1486, +0.1344] | -0.0014 [-0.0088, +0.0057] | -0.0864, -0.0278, +0.0834 |
| leagueews_tcn_by_weighting_interaction: teamfight | +0.0008 [-0.0635, +0.0700] | +0.0101 [-0.0000, +0.0197] | -0.0594, +0.0148, +0.0470 |
| leagueews_tcn_by_weighting_interaction: macro | +0.0663 [-0.0412, +0.1741] | +0.0046 [-0.0003, +0.0093] | -0.0790, +0.0694, +0.2085 |
| leagueews_gru_by_weighting_interaction: baron | -3.1905 [-3.9643, -2.4631] | -0.0004 [-0.0230, +0.0224] | -2.6994, -4.2381, -2.6340 |
| leagueews_gru_by_weighting_interaction: dragon | +0.0092 [-0.1229, +0.1414] | -0.0066 [-0.0144, +0.0012] | -0.0121, -0.2426, +0.2824 |
| leagueews_gru_by_weighting_interaction: teamfight | -0.0940 [-0.2001, +0.0192] | +0.0133 [-0.0036, +0.0294] | -0.0741, -0.1345, -0.0732 |
| leagueews_gru_by_weighting_interaction: macro | -1.0918 [-1.3524, -0.8394] | +0.0021 [-0.0079, +0.0119] | -0.9286, -1.5384, -0.8083 |

### Primary equal-weight LeagueEWS minus TCN: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1877 [+0.0296, +0.3520] | -0.0129 [-0.0176, -0.0079] | +0.3611, +0.7194, -0.5172 |
| 0.5 | -0.2490 [-0.4242, -0.0776] | -0.0509 [-0.0579, -0.0439] | -0.4128, +0.5112, -0.8455 |
| 0.75 | +1.0462 [+0.8723, +1.2167] | +0.1030 [+0.0949, +0.1112] | +0.4941, +1.1571, +1.4874 |
| 1.0 | -0.5346 [-0.7129, -0.3640] | -0.0972 [-0.1063, -0.0886] | -0.1533, -0.6110, -0.8393 |
| mean | +0.1126 [-0.0040, +0.2261] | -0.0145 [-0.0194, -0.0095] | +0.0723, +0.4442, -0.1787 |

### Primary equal-weight LeagueEWS minus TCN: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | -0.0351 [-0.1930, +0.1260] | -0.0176 [-0.0227, -0.0127] | +0.0628, +0.3697, -0.5378 |
| 0.5 | -0.1736 [-0.3485, -0.0043] | -0.0464 [-0.0536, -0.0394] | -0.2483, +0.5112, -0.7838 |
| 0.75 | +1.0736 [+0.8987, +1.2393] | +0.1033 [+0.0948, +0.1115] | +0.4941, +1.2394, +1.4874 |
| 1.0 | -0.3296 [-0.5050, -0.1619] | -0.0809 [-0.0899, -0.0725] | -0.1533, +0.0039, -0.8393 |
| mean | +0.1338 [+0.0169, +0.2443] | -0.0104 [-0.0153, -0.0054] | +0.0388, +0.5310, -0.1684 |

### Primary equal-weight LeagueEWS minus TCN: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2217 [+0.0732, +0.3752] | -0.0017 [-0.0066, +0.0030] | +0.3014, +0.2729, +0.0909 |
| 0.5 | +0.2111 [+0.0510, +0.3702] | -0.0032 [-0.0095, +0.0032] | +0.0846, +0.2490, +0.2995 |
| 0.75 | +0.2084 [+0.0600, +0.3610] | -0.0004 [-0.0079, +0.0067] | +0.1420, +0.2170, +0.2662 |
| 1.0 | +0.3266 [+0.1793, +0.4740] | +0.0050 [-0.0027, +0.0124] | +0.2697, +0.3291, +0.3810 |
| mean | +0.2420 [+0.1305, +0.3543] | -0.0001 [-0.0053, +0.0052] | +0.1995, +0.2670, +0.2594 |

### Primary equal-weight LeagueEWS minus TCN: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1962 [+0.0208, +0.3723] | -0.0014 [-0.0068, +0.0038] | +0.3547, +0.1968, +0.0371 |
| 0.5 | +0.3609 [+0.1879, +0.5352] | +0.0123 [+0.0047, +0.0192] | +0.3186, +0.2470, +0.5173 |
| 0.75 | +0.2600 [+0.0943, +0.4345] | -0.0052 [-0.0133, +0.0031] | +0.1412, +0.2138, +0.4250 |
| 1.0 | +0.2975 [+0.1350, +0.4613] | +0.0025 [-0.0060, +0.0113] | +0.1823, +0.4830, +0.2272 |
| mean | +0.2787 [+0.1653, +0.3967] | +0.0021 [-0.0031, +0.0074] | +0.2492, +0.2852, +0.3017 |

### Primary equal-weight LeagueEWS minus TCN: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1847 [+0.0139, +0.3543] | -0.0031 [-0.0087, +0.0024] | +0.3102, +0.2409, +0.0029 |
| 0.5 | +0.2287 [+0.0529, +0.4037] | +0.0013 [-0.0062, +0.0085] | +0.2426, +0.1253, +0.3181 |
| 0.75 | +0.2200 [+0.0587, +0.3865] | -0.0036 [-0.0120, +0.0044] | +0.0407, +0.2767, +0.3428 |
| 1.0 | +0.3487 [+0.1783, +0.5106] | +0.0025 [-0.0060, +0.0110] | +0.2132, +0.5237, +0.3092 |
| mean | +0.2455 [+0.1365, +0.3581] | -0.0007 [-0.0060, +0.0047] | +0.2017, +0.2917, +0.2432 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_equal_sum-minus-timely_equal_tcn: baron | +0.0479 [-0.3503, +0.4340] | -0.0020 [-0.0135, +0.0097] | +0.1738, -0.0793, +0.0491 |
| europe: timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3403 [+0.0854, +0.5858] | -0.0040 [-0.0159, +0.0080] | +0.2649, +0.2047, +0.5514 |
| europe: timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.0149 [-0.0898, +0.1176] | +0.0075 [-0.0074, +0.0223] | -0.0734, +0.0574, +0.0606 |
| europe: timely_equal_sum-minus-timely_equal_tcn: macro | +0.1344 [-0.0263, +0.2876] | +0.0005 [-0.0068, +0.0079] | +0.1218, +0.0609, +0.2204 |
| europe: timely_equal_sum-minus-timely_equal_gru: baron | +5.3457 [+4.3005, +6.4307] | +0.0513 [+0.0238, +0.0806] | +4.9461, +4.3063, +6.7846 |
| europe: timely_equal_sum-minus-timely_equal_gru: dragon | +5.9417 [+5.4354, +6.4465] | -0.0050 [-0.0312, +0.0203] | +5.9056, +5.9850, +5.9346 |
| europe: timely_equal_sum-minus-timely_equal_gru: teamfight | +0.4938 [+0.2728, +0.7189] | -0.0159 [-0.0451, +0.0156] | +0.3844, +0.3660, +0.7309 |
| europe: timely_equal_sum-minus-timely_equal_gru: macro | +3.9270 [+3.5251, +4.3343] | +0.0101 [-0.0077, +0.0276] | +3.7454, +3.5524, +4.4834 |
| europe: timely_leagueews-minus-timely_tcn: baron | -0.0379 [-0.4479, +0.3653] | -0.0140 [-0.0263, -0.0019] | +0.3122, -0.0862, -0.3398 |
| europe: timely_leagueews-minus-timely_tcn: dragon | +0.4354 [+0.1972, +0.6601] | +0.0083 [-0.0041, +0.0194] | +0.3152, +0.7245, +0.2664 |
| europe: timely_leagueews-minus-timely_tcn: teamfight | +0.1109 [+0.0132, +0.2109] | -0.0054 [-0.0183, +0.0077] | +0.1054, +0.1557, +0.0714 |
| europe: timely_leagueews-minus-timely_tcn: macro | +0.1694 [+0.0056, +0.3301] | -0.0037 [-0.0106, +0.0033] | +0.2443, +0.2647, -0.0006 |
| europe: timely_leagueews-minus-timely_original_gru: baron | +8.7566 [+7.3901, +10.1703] | +0.0384 [-0.0006, +0.0772] | +8.0335, +8.9891, +9.2473 |
| europe: timely_leagueews-minus-timely_original_gru: dragon | +5.8783 [+5.3516, +6.3927] | -0.0036 [-0.0302, +0.0215] | +5.7133, +6.4004, +5.5212 |
| europe: timely_leagueews-minus-timely_original_gru: teamfight | +0.6336 [+0.3959, +0.8903] | -0.0287 [-0.0644, +0.0071] | +0.5844, +0.5754, +0.7410 |
| europe: timely_leagueews-minus-timely_original_gru: macro | +5.0895 [+4.5974, +5.5776] | +0.0020 [-0.0205, +0.0237] | +4.7771, +5.3217, +5.1698 |
| europe: leagueews_tcn_by_weighting_interaction: baron | +0.0858 [-0.3491, +0.4942] | +0.0119 [+0.0014, +0.0227] | -0.1384, +0.0069, +0.3889 |
| europe: leagueews_tcn_by_weighting_interaction: dragon | -0.0951 [-0.3084, +0.1269] | -0.0123 [-0.0218, -0.0022] | -0.0503, -0.5199, +0.2850 |
| europe: leagueews_tcn_by_weighting_interaction: teamfight | -0.0960 [-0.1882, -0.0068] | +0.0128 [-0.0001, +0.0267] | -0.1788, -0.0983, -0.0108 |
| europe: leagueews_tcn_by_weighting_interaction: macro | -0.0351 [-0.1988, +0.1226] | +0.0041 [-0.0025, +0.0110] | -0.1225, -0.2038, +0.2210 |
| europe: leagueews_gru_by_weighting_interaction: baron | -3.4110 [-4.4773, -2.3432] | +0.0129 [-0.0172, +0.0430] | -3.0874, -4.6828, -2.4627 |
| europe: leagueews_gru_by_weighting_interaction: dragon | +0.0634 [-0.1231, +0.2542] | -0.0014 [-0.0119, +0.0099] | +0.1922, -0.4155, +0.4134 |
| europe: leagueews_gru_by_weighting_interaction: teamfight | -0.1398 [-0.2973, +0.0054] | +0.0129 [-0.0103, +0.0376] | -0.2000, -0.2094, -0.0100 |
| europe: leagueews_gru_by_weighting_interaction: macro | -1.1625 [-1.5372, -0.8066] | +0.0081 [-0.0060, +0.0226] | -1.0317, -1.7692, -0.6864 |
| americas: timely_equal_sum-minus-timely_equal_tcn: baron | +0.5532 [+0.1528, +0.9493] | -0.0094 [-0.0217, +0.0021] | +0.5598, +0.7886, +0.3112 |
| americas: timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3284 [+0.0911, +0.5689] | +0.0019 [-0.0104, +0.0138] | +0.0469, +0.5316, +0.4069 |
| americas: timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1652 [+0.0680, +0.2675] | +0.0057 [-0.0085, +0.0205] | +0.2280, +0.0889, +0.1786 |
| americas: timely_equal_sum-minus-timely_equal_tcn: macro | +0.3489 [+0.1881, +0.5009] | -0.0006 [-0.0078, +0.0066] | +0.2782, +0.4697, +0.2989 |
| americas: timely_equal_sum-minus-timely_equal_gru: baron | +5.3118 [+4.2875, +6.3948] | -0.0020 [-0.0297, +0.0248] | +5.4376, +4.8739, +5.6240 |
| americas: timely_equal_sum-minus-timely_equal_gru: dragon | +6.3466 [+5.8743, +6.8393] | -0.0008 [-0.0304, +0.0299] | +6.1768, +6.4309, +6.4321 |
| americas: timely_equal_sum-minus-timely_equal_gru: teamfight | +0.8882 [+0.6693, +1.1097] | +0.0377 [+0.0097, +0.0682] | +0.8549, +0.7513, +1.0585 |
| americas: timely_equal_sum-minus-timely_equal_gru: macro | +4.1822 [+3.7902, +4.5953] | +0.0116 [-0.0061, +0.0299] | +4.1564, +4.0187, +4.3715 |
| americas: timely_leagueews-minus-timely_tcn: baron | +0.2239 [-0.1611, +0.6062] | -0.0079 [-0.0200, +0.0040] | +0.6041, +0.3561, -0.2887 |
| americas: timely_leagueews-minus-timely_tcn: dragon | +0.2565 [+0.0164, +0.4971] | -0.0076 [-0.0193, +0.0037] | +0.1683, +0.0821, +0.5189 |
| americas: timely_leagueews-minus-timely_tcn: teamfight | +0.0660 [-0.0326, +0.1589] | -0.0015 [-0.0147, +0.0118] | +0.1660, -0.0409, +0.0728 |
| americas: timely_leagueews-minus-timely_tcn: macro | +0.1821 [+0.0285, +0.3364] | -0.0057 [-0.0131, +0.0015] | +0.3128, +0.1324, +0.1010 |
| americas: timely_leagueews-minus-timely_original_gru: baron | +8.2847 [+6.9081, +9.6832] | +0.0118 [-0.0300, +0.0543] | +7.7540, +8.6730, +8.4271 |
| americas: timely_leagueews-minus-timely_original_gru: dragon | +6.3899 [+5.8922, +6.9230] | +0.0110 [-0.0199, +0.0432] | +6.3871, +6.5059, +6.2769 |
| americas: timely_leagueews-minus-timely_original_gru: teamfight | +0.9356 [+0.6757, +1.2032] | +0.0240 [-0.0106, +0.0604] | +0.8011, +0.8098, +1.1959 |
| americas: timely_leagueews-minus-timely_original_gru: macro | +5.2034 [+4.7113, +5.7018] | +0.0156 [-0.0088, +0.0405] | +4.9807, +5.3296, +5.2999 |
| americas: leagueews_tcn_by_weighting_interaction: baron | +0.3294 [-0.0577, +0.6876] | -0.0016 [-0.0133, +0.0089] | -0.0443, +0.4326, +0.5998 |
| americas: leagueews_tcn_by_weighting_interaction: dragon | +0.0720 [-0.1192, +0.2630] | +0.0095 [-0.0014, +0.0201] | -0.1214, +0.4494, -0.1121 |
| americas: leagueews_tcn_by_weighting_interaction: teamfight | +0.0992 [+0.0081, +0.1944] | +0.0073 [-0.0067, +0.0216] | +0.0620, +0.1298, +0.1059 |
| americas: leagueews_tcn_by_weighting_interaction: macro | +0.1668 [+0.0196, +0.3070] | +0.0051 [-0.0026, +0.0116] | -0.0346, +0.3372, +0.1979 |
| americas: leagueews_gru_by_weighting_interaction: baron | -2.9729 [-4.0459, -1.9479] | -0.0137 [-0.0478, +0.0200] | -2.3164, -3.7991, -2.8032 |
| americas: leagueews_gru_by_weighting_interaction: dragon | -0.0433 [-0.2348, +0.1362] | -0.0118 [-0.0230, -0.0011] | -0.2103, -0.0749, +0.1553 |
| americas: leagueews_gru_by_weighting_interaction: teamfight | -0.0473 [-0.2060, +0.1066] | +0.0136 [-0.0096, +0.0374] | +0.0538, -0.0584, -0.1374 |
| americas: leagueews_gru_by_weighting_interaction: macro | -1.0212 [-1.3857, -0.6640] | -0.0040 [-0.0194, +0.0108] | -0.8243, -1.3108, -0.9284 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_tcn: baron | +0.5245 [+0.0935, +0.9337] | +0.0133 [-0.0014, +0.0277] | +0.4320, +0.7097, +0.4320 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.1912 [-0.0499, +0.4209] | -0.0072 [-0.0207, +0.0053] | -0.0265, +0.4060, +0.1942 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1768 [+0.0680, +0.2902] | +0.0013 [-0.0160, +0.0181] | +0.1414, +0.3334, +0.0556 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.2975 [+0.1350, +0.4613] | +0.0025 [-0.0060, +0.0113] | +0.1823, +0.4830, +0.2272 |
| timely_equal_sum-minus-timely_equal_gru: baron | +5.6156 [+4.6721, +6.5960] | +0.0486 [+0.0179, +0.0770] | +5.1527, +4.7516, +6.9423 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +10.9395 [+10.3679, +11.5483] | +0.0588 [+0.0222, +0.0970] | +10.8130, +11.1660, +10.8394 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.9733 [+0.7563, +1.1883] | +0.0158 [-0.0150, +0.0479] | +0.8487, +0.9447, +1.1265 |
| timely_equal_sum-minus-timely_equal_gru: macro | +5.8428 [+5.4844, +6.2279] | +0.0410 [+0.0211, +0.0606] | +5.6048, +5.6208, +6.3028 |
| timely_leagueews-minus-timely_tcn: baron | +0.0617 [-0.3461, +0.4734] | -0.0140 [-0.0289, +0.0006] | +0.7714, +0.0000, -0.5862 |
| timely_leagueews-minus-timely_tcn: dragon | +0.3472 [+0.1136, +0.5822] | +0.0006 [-0.0126, +0.0131] | -0.2030, +0.9180, +0.3266 |
| timely_leagueews-minus-timely_tcn: teamfight | +0.1128 [-0.0034, +0.2285] | +0.0002 [-0.0153, +0.0158] | +0.2122, +0.0051, +0.1212 |
| timely_leagueews-minus-timely_tcn: macro | +0.1739 [+0.0086, +0.3432] | -0.0044 [-0.0128, +0.0036] | +0.2602, +0.3077, -0.0461 |
| timely_leagueews-minus-timely_original_gru: baron | +9.8735 [+8.7592, +11.1111] | +0.0328 [-0.0097, +0.0741] | +8.7010, +10.4289, +10.4906 |
| timely_leagueews-minus-timely_original_gru: dragon | +10.0127 [+9.4441, +10.6193] | +0.0317 [-0.0053, +0.0681] | +9.6919, +10.4775, +9.8685 |
| timely_leagueews-minus-timely_original_gru: teamfight | +1.2663 [+1.0120, +1.5141] | +0.0584 [+0.0204, +0.0973] | +1.1164, +1.2175, +1.4650 |
| timely_leagueews-minus-timely_original_gru: macro | +7.0508 [+6.6229, +7.5105] | +0.0410 [+0.0158, +0.0652] | +6.5031, +7.3746, +7.2747 |
| leagueews_tcn_by_weighting_interaction: baron | +0.4628 [-0.0311, +0.9397] | +0.0273 [+0.0114, +0.0429] | -0.3394, +0.7097, +1.0182 |
| leagueews_tcn_by_weighting_interaction: dragon | -0.1559 [-0.3841, +0.0701] | -0.0078 [-0.0209, +0.0047] | +0.1765, -0.5120, -0.1324 |
| leagueews_tcn_by_weighting_interaction: teamfight | +0.0640 [-0.0576, +0.1870] | +0.0011 [-0.0172, +0.0181] | -0.0707, +0.3284, -0.0657 |
| leagueews_tcn_by_weighting_interaction: macro | +0.1236 [-0.0664, +0.3046] | +0.0069 [-0.0019, +0.0154] | -0.0779, +0.1754, +0.2734 |
| leagueews_gru_by_weighting_interaction: baron | -4.2579 [-5.2360, -3.3341] | +0.0158 [-0.0174, +0.0482] | -3.5483, -5.6773, -3.5483 |
| leagueews_gru_by_weighting_interaction: dragon | +0.9268 [+0.6348, +1.2351] | +0.0271 [+0.0079, +0.0472] | +1.1210, +0.6885, +0.9710 |
| leagueews_gru_by_weighting_interaction: teamfight | -0.2930 [-0.4611, -0.1123] | -0.0427 [-0.0689, -0.0167] | -0.2677, -0.2728, -0.3385 |
| leagueews_gru_by_weighting_interaction: macro | -1.2080 [-1.5681, -0.8786] | +0.0001 [-0.0161, +0.0166] | -0.8983, -1.7539, -0.9719 |

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
| timely_equal_tcn | 18.997 / 0.6407 | 21.503 / 0.6092 | 5.029 / 0.6169 | 15.176 / 0.6223 |
| timely_original_gru | 12.938 / 0.6185 | 8.899 / 0.6339 | 3.810 / 0.6008 | 8.549 / 0.6177 |
| timely_equal_gru | 15.635 / 0.6228 | 9.095 / 0.6254 | 4.283 / 0.6248 | 9.671 / 0.6244 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| history_effect_difference_timely_minus_cumulative | +0.0103 [-0.1558, +0.1801] | +0.0089 [+0.0014, +0.0170] | +0.0379, -0.0906, +0.0837 |
| leagueews-minus-current_only | +0.0791 [-0.1184, +0.2619] | -0.0053 [-0.0124, +0.0017] | +0.2043, +0.1901, -0.1572 |
| leagueews-minus-gru | +0.6296 [+0.2694, +0.9920] | +0.0034 [-0.0108, +0.0173] | +0.0340, +0.1626, +1.6921 |
| leagueews-minus-independent | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | +0.1335, -0.3347, -0.1036 |
| leagueews-minus-snapshot | +0.4238 [+0.2114, +0.6347] | -0.0066 [-0.0144, +0.0013] | +0.2788, +0.4714, +0.5213 |
| leagueews-minus-tcn | +0.2977 [+0.1526, +0.4329] | -0.0033 [-0.0077, +0.0007] | +0.0664, +0.4455, +0.3811 |
| leagueews_gru_by_weighting_interaction | -0.6797 [-0.9675, -0.3821] | -0.0065 [-0.0166, +0.0029] | -0.3831, -0.7687, -0.8873 |
| leagueews_tcn_by_weighting_interaction | +0.1765 [+0.0207, +0.3379] | +0.0044 [-0.0004, +0.0093] | +0.1385, +0.2950, +0.0959 |
| projection_by_weighting_interaction | -0.1411 [-0.2673, -0.0166] | -0.0003 [-0.0045, +0.0037] | -0.3396, +0.0416, -0.1252 |
| sharing_effect_difference_timely_minus_cumulative | -0.5625 [-0.7758, -0.3427] | +0.0027 [-0.0036, +0.0091] | -0.4917, -0.5293, -0.6666 |
| timely_clock_history-minus-timely_current_only | -0.0426 [-0.1855, +0.0879] | +0.0055 [+0.0014, +0.0093] | +0.0756, +0.0438, -0.2473 |
| timely_current_only-minus-current_only | +3.9853 [+3.7507, +4.2310] | -0.0131 [-0.0222, -0.0030] | +4.1749, +3.9879, +3.7932 |
| timely_equal_gru-minus-timely_independent | -6.4410 [-6.8174, -6.0753] | +0.0036 [-0.0098, +0.0179] | -6.0644, -6.3301, -6.9285 |
| timely_equal_gru-minus-timely_original_gru | +1.1221 [+0.8667, +1.3756] | +0.0066 [-0.0020, +0.0156] | +0.8636, +1.2978, +1.2049 |
| timely_equal_pcgrad-minus-timely_equal_sum | -0.0292 [-0.1092, +0.0570] | +0.0002 [-0.0027, +0.0031] | -0.1644, +0.0851, -0.0083 |
| timely_equal_pcgrad-minus-timely_independent | -0.2509 [-0.4740, -0.0091] | +0.0055 [-0.0006, +0.0115] | -0.0420, -0.2497, -0.4609 |
| timely_equal_pcgrad-minus-timely_leagueews | +0.4132 [+0.2929, +0.5393] | +0.0004 [-0.0033, +0.0040] | +0.3161, +0.6143, +0.3093 |
| timely_equal_pcgrad-minus-timely_original_pcgrad | +0.3013 [+0.1840, +0.4236] | -0.0002 [-0.0037, +0.0035] | +0.1409, +0.5707, +0.1924 |
| timely_equal_pcgrad-minus-timely_tcn | +0.9508 [+0.7625, +1.1445] | -0.0002 [-0.0058, +0.0052] | +1.0186, +1.0392, +0.7945 |
| timely_equal_sum-minus-timely_equal_gru | +6.2193 [+5.8808, +6.5671] | +0.0017 [-0.0117, +0.0149] | +6.1868, +5.9953, +6.4760 |
| timely_equal_sum-minus-timely_equal_tcn | +0.7140 [+0.5401, +0.8921] | +0.0038 [-0.0017, +0.0090] | +0.8410, +0.7199, +0.5811 |
| timely_equal_sum-minus-timely_independent | -0.2217 [-0.4428, +0.0097] | +0.0053 [-0.0011, +0.0112] | +0.1224, -0.3348, -0.4526 |
| timely_equal_sum-minus-timely_leagueews | +0.4424 [+0.3142, +0.5740] | +0.0001 [-0.0036, +0.0036] | +0.4805, +0.5291, +0.3177 |
| timely_equal_sum-minus-timely_tcn | +0.9800 [+0.7800, +1.1752] | -0.0005 [-0.0061, +0.0050] | +1.1830, +0.9541, +0.8028 |
| timely_equal_tcn-minus-timely_equal_gru | +5.5054 [+5.1720, +5.8319] | -0.0021 [-0.0150, +0.0102] | +5.3458, +5.2754, +5.8949 |
| timely_equal_tcn-minus-timely_independent | -0.9357 [-1.2149, -0.6595] | +0.0015 [-0.0060, +0.0090] | -0.7186, -1.0547, -1.0336 |
| timely_equal_tcn-minus-timely_tcn | +0.2660 [+0.1413, +0.3951] | -0.0042 [-0.0081, -0.0002] | +0.3420, +0.2342, +0.2217 |
| timely_independent-minus-independent | +4.5582 [+4.3122, +4.8259] | -0.0068 [-0.0169, +0.0038] | +4.7045, +4.4265, +4.5436 |
| timely_leagueews-minus-leagueews | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |
| timely_leagueews-minus-timely_clock_history | +0.1320 [-0.0635, +0.3245] | -0.0018 [-0.0082, +0.0047] | +0.1666, +0.0556, +0.1739 |
| timely_leagueews-minus-timely_clock_only | +2.1385 [+1.8057, +2.4602] | +0.0065 [-0.0058, +0.0187] | +2.4487, +1.8945, +2.0722 |
| timely_leagueews-minus-timely_current_only | +0.0894 [-0.1254, +0.3027] | +0.0036 [-0.0030, +0.0102] | +0.2422, +0.0995, -0.0735 |
| timely_leagueews-minus-timely_independent | -0.6641 [-0.9246, -0.3971] | +0.0051 [-0.0013, +0.0114] | -0.3581, -0.8640, -0.7702 |
| timely_leagueews-minus-timely_original_gru | +6.8990 [+6.4850, +7.3441] | +0.0081 [-0.0080, +0.0247] | +6.5699, +6.7640, +7.3632 |
| timely_leagueews-minus-timely_tcn | +0.5375 [+0.3787, +0.6945] | -0.0006 [-0.0059, +0.0044] | +0.7025, +0.4249, +0.4851 |
| timely_original_gru-minus-gru | -2.2737 [-2.4730, -2.0622] | -0.0088 [-0.0179, -0.0000] | -2.3230, -2.7041, -1.7941 |
| timely_original_pcgrad-minus-timely_independent | -0.5522 [-0.8107, -0.2892] | +0.0057 [-0.0010, +0.0120] | -0.1829, -0.8204, -0.6533 |
| timely_original_pcgrad-minus-timely_leagueews | +0.1119 [+0.0248, +0.2005] | +0.0005 [-0.0024, +0.0035] | +0.1752, +0.0435, +0.1169 |
| timely_original_pcgrad-minus-timely_tcn | +0.6494 [+0.4898, +0.8156] | -0.0001 [-0.0052, +0.0050] | +0.8777, +0.4685, +0.6021 |
| timely_tcn-minus-timely_original_gru | +6.3615 [+5.9481, +6.7741] | +0.0087 [-0.0063, +0.0246] | +5.8674, +6.3391, +6.8781 |

### Matched architecture effects and weighting interactions by event

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_tcn: baron | +1.7198 [+1.2300, +2.2030] | +0.0101 [+0.0003, +0.0192] | +1.9590, +1.5170, +1.6833 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.2478 [+0.0955, +0.4069] | -0.0017 [-0.0083, +0.0047] | +0.3594, +0.5007, -0.1169 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1744 [+0.0655, +0.2842] | +0.0029 [-0.0074, +0.0142] | +0.2045, +0.1420, +0.1768 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.7140 [+0.5401, +0.8921] | +0.0038 [-0.0017, +0.0090] | +0.8410, +0.7199, +0.5811 |
| timely_equal_sum-minus-timely_equal_gru: baron | +5.0812 [+4.2350, +5.9450] | +0.0280 [+0.0047, +0.0494] | +4.9044, +4.5754, +5.7638 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +12.6560 [+12.2043, +13.1026] | -0.0179 [-0.0361, -0.0003] | +12.7469, +12.6713, +12.5499 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.9208 [+0.6986, +1.1420] | -0.0050 [-0.0265, +0.0180] | +0.9089, +0.7392, +1.1142 |
| timely_equal_sum-minus-timely_equal_gru: macro | +6.2193 [+5.8808, +6.5671] | +0.0017 [-0.0117, +0.0149] | +6.1868, +5.9953, +6.4760 |
| timely_leagueews-minus-timely_tcn: baron | +1.3866 [+0.9288, +1.8160] | -0.0024 [-0.0123, +0.0068] | +1.7780, +0.9488, +1.4330 |
| timely_leagueews-minus-timely_tcn: dragon | +0.1267 [-0.0132, +0.2749] | -0.0014 [-0.0074, +0.0046] | +0.1391, +0.2719, -0.0310 |
| timely_leagueews-minus-timely_tcn: teamfight | +0.0993 [-0.0010, +0.1966] | +0.0020 [-0.0086, +0.0123] | +0.1904, +0.0541, +0.0534 |
| timely_leagueews-minus-timely_tcn: macro | +0.5375 [+0.3787, +0.6945] | -0.0006 [-0.0059, +0.0044] | +0.7025, +0.4249, +0.4851 |
| timely_leagueews-minus-timely_original_gru: baron | +6.4688 [+5.3611, +7.6146] | +0.0287 [-0.0012, +0.0576] | +5.7613, +5.7523, +7.8928 |
| timely_leagueews-minus-timely_original_gru: dragon | +12.8310 [+12.3636, +13.3112] | -0.0256 [-0.0454, -0.0078] | +12.6361, +13.1024, +12.7546 |
| timely_leagueews-minus-timely_original_gru: teamfight | +1.3973 [+1.1288, +1.6497] | +0.0213 [-0.0046, +0.0494] | +1.3122, +1.4373, +1.4423 |
| timely_leagueews-minus-timely_original_gru: macro | +6.8990 [+6.4850, +7.3441] | +0.0081 [-0.0080, +0.0247] | +6.5699, +6.7640, +7.3632 |
| leagueews_tcn_by_weighting_interaction: baron | +0.3332 [-0.1083, +0.7661] | +0.0125 [+0.0036, +0.0211] | +0.1810, +0.5682, +0.2503 |
| leagueews_tcn_by_weighting_interaction: dragon | +0.1211 [-0.0180, +0.2645] | -0.0003 [-0.0059, +0.0050] | +0.2203, +0.2288, -0.0859 |
| leagueews_tcn_by_weighting_interaction: teamfight | +0.0751 [-0.0218, +0.1710] | +0.0008 [-0.0086, +0.0108] | +0.0140, +0.0879, +0.1234 |
| leagueews_tcn_by_weighting_interaction: macro | +0.1765 [+0.0207, +0.3379] | +0.0044 [-0.0004, +0.0093] | +0.1385, +0.2950, +0.0959 |
| leagueews_gru_by_weighting_interaction: baron | -1.3876 [-2.2190, -0.5420] | -0.0007 [-0.0206, +0.0175] | -0.8569, -1.1769, -2.1290 |
| leagueews_gru_by_weighting_interaction: dragon | -0.1750 [-0.3234, -0.0287] | +0.0077 [+0.0013, +0.0143] | +0.1109, -0.4310, -0.2047 |
| leagueews_gru_by_weighting_interaction: teamfight | -0.4765 [-0.6453, -0.3051] | -0.0263 [-0.0441, -0.0092] | -0.4033, -0.6982, -0.3281 |
| leagueews_gru_by_weighting_interaction: macro | -0.6797 [-0.9675, -0.3821] | -0.0065 [-0.0166, +0.0029] | -0.3831, -0.7687, -0.8873 |

### Primary equal-weight LeagueEWS minus TCN: deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.4005 [+0.1883, +0.6185] | +0.0088 [+0.0038, +0.0137] | +0.4381, +0.2743, +0.4891 |
| 0.5 | +0.4057 [+0.1657, +0.6493] | +0.0024 [-0.0045, +0.0092] | +0.8773, +0.6792, -0.3394 |
| 0.75 | -0.2735 [-0.5238, -0.0097] | -0.0889 [-0.0973, -0.0807] | +0.0487, -0.3477, -0.5215 |
| 1.0 | +1.2456 [+0.9939, +1.5034] | +0.0485 [+0.0403, +0.0569] | +0.8285, +0.7116, +2.1968 |
| mean | +0.4446 [+0.2684, +0.6245] | -0.0073 [-0.0124, -0.0024] | +0.5481, +0.3293, +0.4563 |

### Primary equal-weight LeagueEWS minus TCN: regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.3068 [+0.0950, +0.5260] | -0.0010 [-0.0060, +0.0040] | +0.4381, -0.0069, +0.4891 |
| 0.5 | +0.4057 [+0.1657, +0.6493] | +0.0024 [-0.0045, +0.0092] | +0.8773, +0.6792, -0.3394 |
| 0.75 | -0.2808 [-0.5193, -0.0186] | -0.1093 [-0.1177, -0.1009] | +0.0487, -0.3477, -0.5434 |
| 1.0 | +0.8569 [+0.6008, +1.1224] | +0.0337 [+0.0255, +0.0424] | +0.8285, +0.7116, +1.0305 |
| mean | +0.3221 [+0.1573, +0.4998] | -0.0185 [-0.0236, -0.0138] | +0.5481, +0.2590, +0.1592 |

### Primary equal-weight LeagueEWS minus TCN: matched_early_mixture

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.4992 [+0.3064, +0.6790] | +0.0015 [-0.0035, +0.0063] | +0.6213, +0.6167, +0.2597 |
| 0.5 | +0.6693 [+0.4526, +0.8932] | +0.0026 [-0.0036, +0.0088] | +0.8389, +0.6564, +0.5127 |
| 0.75 | +0.8665 [+0.6466, +1.1043] | +0.0046 [-0.0029, +0.0122] | +1.0242, +0.7729, +0.8023 |
| 1.0 | +0.8209 [+0.5855, +1.0714] | +0.0064 [-0.0016, +0.0140] | +0.8795, +0.8336, +0.7495 |
| mean | +0.7140 [+0.5401, +0.8921] | +0.0038 [-0.0017, +0.0090] | +0.8410, +0.7199, +0.5811 |

### Primary equal-weight LeagueEWS minus TCN: dense_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.4226 [+0.1865, +0.6645] | -0.0030 [-0.0088, +0.0029] | +0.0831, +0.6631, +0.5215 |
| 0.5 | +0.7309 [+0.4703, +0.9855] | +0.0033 [-0.0036, +0.0104] | +0.6484, +0.9780, +0.5662 |
| 0.75 | +0.8858 [+0.6458, +1.1458] | +0.0090 [+0.0010, +0.0169] | +1.1932, +0.2118, +1.2524 |
| 1.0 | +1.1335 [+0.8685, +1.4119] | +0.0207 [+0.0115, +0.0293] | +1.2403, +1.0585, +1.1017 |
| mean | +0.7932 [+0.6181, +0.9871] | +0.0075 [+0.0020, +0.0126] | +0.7912, +0.7278, +0.8605 |

### Primary equal-weight LeagueEWS minus TCN: dense_regional_deterministic

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.5927 [+0.3611, +0.8319] | +0.0052 [-0.0010, +0.0111] | +0.5582, +0.5915, +0.6284 |
| 0.5 | +0.7635 [+0.5036, +1.0258] | +0.0034 [-0.0036, +0.0105] | +0.8629, +0.8939, +0.5336 |
| 0.75 | +0.9373 [+0.6913, +1.2021] | +0.0093 [+0.0013, +0.0175] | +1.1021, +0.5031, +1.2066 |
| 1.0 | +0.9796 [+0.7147, +1.2475] | +0.0170 [+0.0077, +0.0259] | +0.9811, +0.9717, +0.9859 |
| mean | +0.8183 [+0.6418, +1.0081] | +0.0087 [+0.0033, +0.0139] | +0.8761, +0.7401, +0.8386 |

### Regional mechanisms, four-budget matched-early mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: timely_equal_sum-minus-timely_equal_tcn: baron | +1.9066 [+1.2447, +2.5589] | +0.0241 [+0.0107, +0.0377] | +2.5964, +1.1524, +1.9709 |
| europe: timely_equal_sum-minus-timely_equal_tcn: dragon | +0.1082 [-0.1191, +0.3400] | +0.0015 [-0.0074, +0.0107] | +0.0932, +0.4476, -0.2163 |
| europe: timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1708 [+0.0208, +0.3301] | +0.0088 [-0.0073, +0.0250] | +0.1919, +0.1188, +0.2017 |
| europe: timely_equal_sum-minus-timely_equal_tcn: macro | +0.7285 [+0.4878, +0.9614] | +0.0115 [+0.0040, +0.0194] | +0.9605, +0.5730, +0.6521 |
| europe: timely_equal_sum-minus-timely_equal_gru: baron | +5.2056 [+3.9268, +6.4634] | +0.0467 [+0.0171, +0.0769] | +5.2457, +4.3538, +6.0173 |
| europe: timely_equal_sum-minus-timely_equal_gru: dragon | +12.5404 [+11.8885, +13.1997] | -0.0153 [-0.0406, +0.0109] | +12.6229, +12.6176, +12.3805 |
| europe: timely_equal_sum-minus-timely_equal_gru: teamfight | +1.0316 [+0.7173, +1.3372] | +0.0031 [-0.0275, +0.0328] | +0.9795, +0.8302, +1.2852 |
| europe: timely_equal_sum-minus-timely_equal_gru: macro | +6.2592 [+5.7448, +6.7299] | +0.0115 [-0.0069, +0.0295] | +6.2827, +5.9339, +6.5610 |
| europe: timely_leagueews-minus-timely_tcn: baron | +1.0984 [+0.4927, +1.7114] | +0.0065 [-0.0072, +0.0193] | +1.8279, +0.4874, +0.9797 |
| europe: timely_leagueews-minus-timely_tcn: dragon | -0.0437 [-0.2329, +0.1661] | -0.0069 [-0.0152, +0.0016] | +0.1030, -0.0806, -0.1535 |
| europe: timely_leagueews-minus-timely_tcn: teamfight | +0.1650 [+0.0275, +0.3088] | +0.0122 [-0.0025, +0.0266] | +0.3359, +0.0869, +0.0724 |
| europe: timely_leagueews-minus-timely_tcn: macro | +0.4066 [+0.1919, +0.6236] | +0.0040 [-0.0035, +0.0111] | +0.7556, +0.1645, +0.2995 |
| europe: timely_leagueews-minus-timely_original_gru: baron | +6.5739 [+4.9852, +8.1899] | +0.0427 [+0.0024, +0.0820] | +5.8000, +6.1339, +7.7878 |
| europe: timely_leagueews-minus-timely_original_gru: dragon | +12.6629 [+12.0009, +13.3512] | -0.0334 [-0.0601, -0.0069] | +12.6566, +12.8255, +12.5067 |
| europe: timely_leagueews-minus-timely_original_gru: teamfight | +1.6203 [+1.2660, +1.9771] | +0.0120 [-0.0242, +0.0483] | +1.4920, +1.5554, +1.8134 |
| europe: timely_leagueews-minus-timely_original_gru: macro | +6.9524 [+6.3411, +7.5932] | +0.0071 [-0.0158, +0.0291] | +6.6495, +6.8383, +7.3693 |
| europe: leagueews_tcn_by_weighting_interaction: baron | +0.8082 [+0.1616, +1.4382] | +0.0176 [+0.0052, +0.0305] | +0.7685, +0.6650, +0.9912 |
| europe: leagueews_tcn_by_weighting_interaction: dragon | +0.1519 [-0.0527, +0.3434] | +0.0084 [+0.0008, +0.0162] | -0.0097, +0.5283, -0.0628 |
| europe: leagueews_tcn_by_weighting_interaction: teamfight | +0.0057 [-0.1306, +0.1407] | -0.0034 [-0.0165, +0.0100] | -0.1440, +0.0319, +0.1293 |
| europe: leagueews_tcn_by_weighting_interaction: macro | +0.3220 [+0.0969, +0.5540] | +0.0075 [+0.0011, +0.0143] | +0.2049, +0.4084, +0.3526 |
| europe: leagueews_gru_by_weighting_interaction: baron | -1.3683 [-2.5634, -0.1694] | +0.0040 [-0.0226, +0.0312] | -0.5543, -1.7801, -1.7705 |
| europe: leagueews_gru_by_weighting_interaction: dragon | -0.1226 [-0.3533, +0.0940] | +0.0180 [+0.0091, +0.0278] | -0.0337, -0.2078, -0.1262 |
| europe: leagueews_gru_by_weighting_interaction: teamfight | -0.5887 [-0.8292, -0.3401] | -0.0089 [-0.0341, +0.0157] | -0.5125, -0.7253, -0.5282 |
| europe: leagueews_gru_by_weighting_interaction: macro | -0.6932 [-1.1111, -0.2685] | +0.0044 [-0.0085, +0.0182] | -0.3668, -0.9044, -0.8083 |
| americas: timely_equal_sum-minus-timely_equal_tcn: baron | +1.5354 [+0.7995, +2.2663] | -0.0039 [-0.0181, +0.0096] | +1.3299, +1.8769, +1.3994 |
| americas: timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3831 [+0.1523, +0.6053] | -0.0049 [-0.0145, +0.0044] | +0.6176, +0.5522, -0.0204 |
| americas: timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1781 [+0.0226, +0.3341] | -0.0030 [-0.0175, +0.0128] | +0.2172, +0.1656, +0.1515 |
| americas: timely_equal_sum-minus-timely_equal_tcn: macro | +0.6989 [+0.4432, +0.9657] | -0.0039 [-0.0115, +0.0038] | +0.7216, +0.8649, +0.5101 |
| americas: timely_equal_sum-minus-timely_equal_gru: baron | +4.9584 [+3.6400, +6.2825] | +0.0092 [-0.0229, +0.0428] | +4.5676, +4.7941, +5.5136 |
| americas: timely_equal_sum-minus-timely_equal_gru: dragon | +12.7682 [+12.1216, +13.4410] | -0.0205 [-0.0474, +0.0051] | +12.8672, +12.7234, +12.7141 |
| americas: timely_equal_sum-minus-timely_equal_gru: teamfight | +0.8081 [+0.4796, +1.1407] | -0.0132 [-0.0453, +0.0187] | +0.8372, +0.6466, +0.9404 |
| americas: timely_equal_sum-minus-timely_equal_gru: macro | +6.1782 [+5.6669, +6.7117] | -0.0081 [-0.0272, +0.0109] | +6.0907, +6.0547, +6.3894 |
| americas: timely_leagueews-minus-timely_tcn: baron | +1.6711 [+1.0235, +2.3417] | -0.0114 [-0.0248, +0.0021] | +1.7288, +1.4042, +1.8804 |
| americas: timely_leagueews-minus-timely_tcn: dragon | +0.2919 [+0.0789, +0.5011] | +0.0041 [-0.0045, +0.0129] | +0.1741, +0.6138, +0.0879 |
| americas: timely_leagueews-minus-timely_tcn: teamfight | +0.0325 [-0.1090, +0.1712] | -0.0081 [-0.0220, +0.0066] | +0.0425, +0.0208, +0.0342 |
| americas: timely_leagueews-minus-timely_tcn: macro | +0.6652 [+0.4400, +0.8984] | -0.0051 [-0.0123, +0.0018] | +0.6485, +0.6796, +0.6675 |
| americas: timely_leagueews-minus-timely_original_gru: baron | +6.3650 [+4.7729, +7.9599] | +0.0147 [-0.0278, +0.0565] | +5.7231, +5.3756, +7.9964 |
| americas: timely_leagueews-minus-timely_original_gru: dragon | +12.9940 [+12.3127, +13.7012] | -0.0178 [-0.0458, +0.0081] | +12.6162, +13.3709, +12.9951 |
| americas: timely_leagueews-minus-timely_original_gru: teamfight | +1.1706 [+0.8031, +1.5435] | +0.0306 [-0.0074, +0.0698] | +1.1296, +1.3172, +1.0650 |
| americas: timely_leagueews-minus-timely_original_gru: macro | +6.8432 [+6.2249, +7.4513] | +0.0092 [-0.0137, +0.0324] | +6.4896, +6.6879, +7.3522 |
| americas: leagueews_tcn_by_weighting_interaction: baron | -0.1358 [-0.7467, +0.4569] | +0.0075 [-0.0047, +0.0195] | -0.3989, +0.4726, -0.4810 |
| americas: leagueews_tcn_by_weighting_interaction: dragon | +0.0912 [-0.1090, +0.2907] | -0.0089 [-0.0170, -0.0009] | +0.4435, -0.0617, -0.1083 |
| americas: leagueews_tcn_by_weighting_interaction: teamfight | +0.1456 [+0.0191, +0.2726] | +0.0051 [-0.0074, +0.0190] | +0.1747, +0.1449, +0.1173 |
| americas: leagueews_tcn_by_weighting_interaction: macro | +0.0337 [-0.1883, +0.2555] | +0.0012 [-0.0054, +0.0082] | +0.0731, +0.1853, -0.1574 |
| americas: leagueews_gru_by_weighting_interaction: baron | -1.4066 [-2.4993, -0.2474] | -0.0055 [-0.0341, +0.0222] | -1.1555, -0.5815, -2.4828 |
| americas: leagueews_gru_by_weighting_interaction: dragon | -0.2258 [-0.4156, -0.0411] | -0.0027 [-0.0113, +0.0058] | +0.2510, -0.6475, -0.2809 |
| americas: leagueews_gru_by_weighting_interaction: teamfight | -0.3626 [-0.5867, -0.1457] | -0.0438 [-0.0677, -0.0201] | -0.2924, -0.6706, -0.1247 |
| americas: leagueews_gru_by_weighting_interaction: macro | -0.6650 [-1.0453, -0.2691] | -0.0173 [-0.0314, -0.0047] | -0.3990, -0.6332, -0.9628 |

### Fine common grid, budget-one mechanisms

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_tcn: baron | +2.0878 [+1.3391, +2.8332] | +0.0162 [+0.0014, +0.0301] | +2.1290, +1.7896, +2.3450 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +1.0769 [+0.8041, +1.3714] | +0.0213 [+0.0084, +0.0337] | +1.2181, +1.3505, +0.6620 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.2357 [+0.0676, +0.4017] | +0.0244 [+0.0073, +0.0421] | +0.3738, +0.0354, +0.2981 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +1.1335 [+0.8685, +1.4119] | +0.0207 [+0.0115, +0.0293] | +1.2403, +1.0585, +1.1017 |
| timely_equal_sum-minus-timely_equal_gru: baron | +6.3355 [+5.1610, +7.5099] | +0.0273 [-0.0031, +0.0557] | +5.7390, +5.7081, +7.5594 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +22.3762 [+21.6124, +23.1266] | -0.0083 [-0.0473, +0.0297] | +22.8617, +22.5704, +21.6965 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +1.3522 [+1.0506, +1.6562] | +0.0193 [-0.0130, +0.0523] | +1.1569, +1.1367, +1.7631 |
| timely_equal_sum-minus-timely_equal_gru: macro | +10.0213 [+9.5488, +10.5039] | +0.0128 [-0.0090, +0.0347] | +9.9192, +9.8051, +10.3397 |
| timely_leagueews-minus-timely_tcn: baron | +1.3885 [+0.7067, +2.0569] | -0.0260 [-0.0412, -0.0113] | +1.8513, +0.7405, +1.5736 |
| timely_leagueews-minus-timely_tcn: dragon | +0.6326 [+0.3809, +0.8850] | +0.0120 [-0.0003, +0.0239] | +0.8915, +0.5649, +0.4413 |
| timely_leagueews-minus-timely_tcn: teamfight | -0.0589 [-0.2163, +0.0932] | -0.0177 [-0.0342, -0.0001] | +0.1364, -0.2374, -0.0758 |
| timely_leagueews-minus-timely_tcn: macro | +0.6540 [+0.4068, +0.8945] | -0.0106 [-0.0190, -0.0019] | +0.9597, +0.3560, +0.6464 |
| timely_leagueews-minus-timely_original_gru: baron | +8.5879 [+7.0856, +10.1328] | +0.0200 [-0.0211, +0.0589] | +7.7137, +7.7445, +10.3055 |
| timely_leagueews-minus-timely_original_gru: dragon | +20.9551 [+20.1932, +21.7151] | -0.0083 [-0.0458, +0.0287] | +22.6763, +19.9841, +20.2048 |
| timely_leagueews-minus-timely_original_gru: teamfight | +2.0072 [+1.6545, +2.3586] | +0.0417 [+0.0032, +0.0813] | +2.0864, +2.2278, +1.7075 |
| timely_leagueews-minus-timely_original_gru: macro | +10.5167 [+9.9316, +11.1326] | +0.0178 [-0.0057, +0.0430] | +10.8255, +9.9855, +10.7392 |
| leagueews_tcn_by_weighting_interaction: baron | +0.6994 [+0.0200, +1.4466] | +0.0422 [+0.0259, +0.0572] | +0.2777, +1.0491, +0.7714 |
| leagueews_tcn_by_weighting_interaction: dragon | +0.4443 [+0.1901, +0.6943] | +0.0093 [-0.0023, +0.0217] | +0.3266, +0.7856, +0.2207 |
| leagueews_tcn_by_weighting_interaction: teamfight | +0.2947 [+0.1290, +0.4750] | +0.0421 [+0.0243, +0.0604] | +0.2374, +0.2728, +0.3738 |
| leagueews_tcn_by_weighting_interaction: macro | +0.4794 [+0.2273, +0.7410] | +0.0312 [+0.0221, +0.0400] | +0.2806, +0.7025, +0.4553 |
| leagueews_gru_by_weighting_interaction: baron | -2.2524 [-3.4807, -0.9962] | +0.0073 [-0.0222, +0.0358] | -1.9747, -2.0364, -2.7461 |
| leagueews_gru_by_weighting_interaction: dragon | +1.4211 [+1.1160, +1.7339] | +0.0000 [-0.0171, +0.0173] | +0.1854, +2.5863, +1.4917 |
| leagueews_gru_by_weighting_interaction: teamfight | -0.6550 [-0.9124, -0.3958] | -0.0223 [-0.0509, +0.0059] | -0.9295, -1.0912, +0.0556 |
| leagueews_gru_by_weighting_interaction: macro | -0.4954 [-0.9366, -0.0553] | -0.0050 [-0.0209, +0.0102] | -0.9063, -0.1804, -0.3996 |

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
| architecture_support | True |
| event_point_nonharm | True |
| gru_support | True |
| no_extra_burden | False |
| practical_promotion | not established by this exploratory architecture control; previous gates and sealed-test requirements remain in force |
| regional_architecture_consistency | False |

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
| timely_equal_gru / 10-30 | 1 | 1 | 9 | 3 | 3 |
| timely_equal_gru / 20-60 | 1 | 1 | 10 | 2 | 2 |
| timely_equal_pcgrad / 10-30 | 1 | 2 | 8 | 3 | 6 |
| timely_equal_pcgrad / 20-60 | 0 | 0 | 7 | 3 | 6 |
| timely_equal_sum / 10-30 | 3 | 3 | 12 | 4 | 7 |
| timely_equal_sum / 20-60 | 0 | 1 | 8 | 3 | 8 |
| timely_equal_tcn / 10-30 | 1 | 1 | 11 | 5 | 7 |
| timely_equal_tcn / 20-60 | 1 | 1 | 7 | 3 | 4 |
| timely_independent / 10-30 | 1 | 1 | 10 | 4 | 8 |
| timely_independent / 20-60 | 0 | 1 | 6 | 2 | 4 |
| timely_leagueews / 10-30 | 1 | 1 | 12 | 5 | 5 |
| timely_leagueews / 20-60 | 0 | 0 | 7 | 0 | 2 |
| timely_original_gru / 10-30 | 0 | 0 | 9 | 4 | 4 |
| timely_original_gru / 20-60 | 0 | 0 | 8 | 1 | 1 |
| timely_original_pcgrad / 10-30 | 0 | 0 | 10 | 3 | 6 |
| timely_original_pcgrad / 20-60 | 0 | 0 | 7 | 3 | 7 |
| timely_tcn / 10-30 | 1 | 2 | 9 | 3 | 6 |
| timely_tcn / 20-60 | 1 | 2 | 8 | 5 | 7 |

All model/event/region/seed results and paired intervals are retained in `analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`. Neither a diagnostic pass nor an optimizer change establishes novelty or a causal effect of game actions. Previously failed regional gates remain failed.
