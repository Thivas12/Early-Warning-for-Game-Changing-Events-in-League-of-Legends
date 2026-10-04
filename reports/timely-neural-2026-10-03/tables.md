# Timely-target neural evidence

Recall is percent, differences percentage points. Burden is expected false-plus-late warnings per match per event. Intervals are paired whole-match conditional 95% intervals, pointwise and unadjusted. Early cost equality does not imply later equality. The four-budget mean averages fixed policies, not independent matches. Seed order: 20260930, 20261001, 20261002.

## 10-30 seconds, four-budget matched-early mean

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

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| leagueews-minus-current_only | +0.7171 [+0.5431, +0.8813] | -0.0101 [-0.0178, -0.0026] | +0.8251, +0.7580, +0.5681 |
| leagueews-minus-gru | +3.3809 [+3.0613, +3.7204] | +0.0064 [-0.0085, +0.0205] | +2.9995, +3.0401, +4.1030 |
| leagueews-minus-independent | -0.0187 [-0.1613, +0.1309] | +0.0012 [-0.0045, +0.0071] | +0.1200, -0.0894, -0.0868 |
| leagueews-minus-snapshot | +0.9479 [+0.7639, +1.1342] | -0.0084 [-0.0172, +0.0005] | +0.9041, +1.0516, +0.8879 |
| leagueews-minus-tcn | +0.0476 [-0.0630, +0.1608] | -0.0030 [-0.0074, +0.0017] | +0.0106, +0.0769, +0.0554 |
| target_effect_difference_leagueews_minus_tcn | +0.1280 [+0.0177, +0.2414] | -0.0017 [-0.0071, +0.0038] | +0.2678, +0.1208, -0.0045 |
| timely_leagueews-minus-independent | +0.4318 [+0.2570, +0.6267] | -0.0039 [-0.0134, +0.0062] | +0.6611, +0.3561, +0.2780 |
| timely_leagueews-minus-leagueews | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |
| timely_leagueews-minus-pcgrad | +0.4233 [+0.2821, +0.5604] | -0.0016 [-0.0095, +0.0069] | +0.4504, +0.4787, +0.3409 |
| timely_leagueews-minus-timely_tcn | +0.1757 [+0.0613, +0.2903] | -0.0047 [-0.0097, +0.0005] | +0.2784, +0.1977, +0.0509 |
| timely_tcn-minus-tcn | +0.3225 [+0.1987, +0.4507] | -0.0033 [-0.0109, +0.0049] | +0.2733, +0.3248, +0.3694 |

### Target effects by event

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| timely_leagueews-minus-leagueews: baron | -0.0444 [-0.2433, +0.1671] | +0.0019 [-0.0041, +0.0080] | +0.2028, -0.2086, -0.1274 |
| timely_leagueews-minus-leagueews: dragon | +1.1633 [+0.8518, +1.4827] | -0.0062 [-0.0199, +0.0083] | +1.1980, +1.2640, +1.0280 |
| timely_leagueews-minus-leagueews: teamfight | +0.2326 [+0.0987, +0.3572] | -0.0108 [-0.0285, +0.0069] | +0.2226, +0.2813, +0.1940 |
| timely_tcn-minus-tcn: baron | +0.0555 [-0.1605, +0.2670] | -0.0016 [-0.0080, +0.0050] | -0.1118, +0.0671, +0.2113 |
| timely_tcn-minus-tcn: dragon | +0.6899 [+0.4110, +0.9757] | -0.0066 [-0.0195, +0.0081] | +0.7451, +0.6913, +0.6332 |
| timely_tcn-minus-tcn: teamfight | +0.2220 [+0.1053, +0.3409] | -0.0018 [-0.0186, +0.0152] | +0.1866, +0.2158, +0.2636 |
| timely_leagueews-minus-timely_tcn: baron | +0.0938 [-0.1925, +0.3774] | -0.0109 [-0.0198, -0.0021] | +0.4591, +0.1364, -0.3140 |
| timely_leagueews-minus-timely_tcn: dragon | +0.3446 [+0.1721, +0.5049] | +0.0004 [-0.0078, +0.0083] | +0.2406, +0.3984, +0.3946 |
| timely_leagueews-minus-timely_tcn: teamfight | +0.0886 [+0.0206, +0.1540] | -0.0034 [-0.0125, +0.0059] | +0.1355, +0.0582, +0.0721 |
| target_effect_difference_leagueews_minus_tcn: baron | -0.0999 [-0.3595, +0.1766] | +0.0035 [-0.0043, +0.0114] | +0.3146, -0.2757, -0.3387 |
| target_effect_difference_leagueews_minus_tcn: dragon | +0.4735 [+0.2924, +0.6531] | +0.0004 [-0.0087, +0.0091] | +0.4529, +0.5727, +0.3948 |
| target_effect_difference_leagueews_minus_tcn: teamfight | +0.0106 [-0.0777, +0.0868] | -0.0090 [-0.0196, +0.0017] | +0.0360, +0.0654, -0.0696 |

### LeagueEWS target effect: deterministic

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +0.3630 [+0.1921, +0.5361] | -0.0024 [-0.0101, +0.0056] | +0.1989, +0.6664, +0.2237 |
| 0.5 | +0.8190 [+0.6167, +1.0170] | +0.0406 [+0.0311, +0.0506] | +0.7439, +0.6903, +1.0228 |
| 0.75 | -0.0266 [-0.2203, +0.1702] | -0.0130 [-0.0236, -0.0020] | -1.2767, +1.0514, +0.1455 |
| 1.0 | -0.1014 [-0.2911, +0.0935] | -0.0548 [-0.0658, -0.0429] | -0.3666, -0.2745, +0.3369 |
| mean | +0.2635 [+0.1188, +0.4041] | -0.0074 [-0.0154, +0.0007] | -0.1751, +0.5334, +0.4322 |

### LeagueEWS target effect: regional_deterministic

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +0.2910 [+0.1171, +0.4674] | -0.0052 [-0.0129, +0.0029] | +0.1989, +0.4505, +0.2237 |
| 0.5 | +0.6461 [+0.4446, +0.8415] | +0.0141 [+0.0044, +0.0240] | +0.4744, +0.5640, +0.8999 |
| 0.75 | +0.1782 [-0.0200, +0.3727] | -0.0083 [-0.0187, +0.0030] | -0.2311, +0.7634, +0.0023 |
| 1.0 | -0.1768 [-0.3691, +0.0130] | -0.0620 [-0.0729, -0.0499] | -0.5517, -0.0688, +0.0900 |
| mean | +0.2346 [+0.0932, +0.3755] | -0.0154 [-0.0233, -0.0072] | -0.0274, +0.4273, +0.3040 |

### LeagueEWS target effect: matched_early_mixture

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +0.5449 [+0.3922, +0.7054] | -0.0021 [-0.0093, +0.0046] | +0.6762, +0.5419, +0.4166 |
| 0.5 | +0.4717 [+0.2846, +0.6493] | -0.0042 [-0.0136, +0.0046] | +0.5234, +0.4005, +0.4912 |
| 0.75 | +0.3568 [+0.1834, +0.5366] | -0.0062 [-0.0164, +0.0040] | +0.4334, +0.3659, +0.2710 |
| 1.0 | +0.4287 [+0.2623, +0.5962] | -0.0077 [-0.0185, +0.0037] | +0.5315, +0.4739, +0.2806 |
| mean | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |

### Regional target effects, four-budget matched-early mean

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| europe: timely_leagueews-minus-leagueews: baron | +0.0481 [-0.2371, +0.3566] | -0.0010 [-0.0090, +0.0075] | +0.2339, -0.0262, -0.0633 |
| europe: timely_leagueews-minus-leagueews: dragon | +1.1740 [+0.7382, +1.6382] | -0.0001 [-0.0201, +0.0203] | +1.1517, +1.4282, +0.9422 |
| europe: timely_leagueews-minus-leagueews: teamfight | +0.2055 [+0.0171, +0.3954] | +0.0020 [-0.0230, +0.0267] | +0.1580, +0.3227, +0.1356 |
| europe: timely_leagueews-minus-leagueews: macro | +0.4759 [+0.2933, +0.6729] | +0.0003 [-0.0108, +0.0116] | +0.5145, +0.5749, +0.3382 |
| europe: timely_tcn-minus-tcn: baron | +0.1920 [-0.1350, +0.5117] | +0.0019 [-0.0073, +0.0108] | +0.0157, +0.3573, +0.2029 |
| europe: timely_tcn-minus-tcn: dragon | +0.6781 [+0.2896, +1.1110] | -0.0071 [-0.0252, +0.0117] | +0.5898, +0.6983, +0.7462 |
| europe: timely_tcn-minus-tcn: teamfight | +0.2187 [+0.0570, +0.3872] | +0.0113 [-0.0123, +0.0354] | +0.2214, +0.1922, +0.2425 |
| europe: timely_tcn-minus-tcn: macro | +0.3629 [+0.1837, +0.5502] | +0.0020 [-0.0082, +0.0133] | +0.2756, +0.4159, +0.3972 |
| europe: timely_leagueews-minus-timely_tcn: baron | -0.0379 [-0.4479, +0.3653] | -0.0140 [-0.0263, -0.0019] | +0.3122, -0.0862, -0.3398 |
| europe: timely_leagueews-minus-timely_tcn: dragon | +0.4354 [+0.1972, +0.6601] | +0.0083 [-0.0041, +0.0194] | +0.3152, +0.7245, +0.2664 |
| europe: timely_leagueews-minus-timely_tcn: teamfight | +0.1109 [+0.0132, +0.2109] | -0.0054 [-0.0183, +0.0077] | +0.1054, +0.1557, +0.0714 |
| europe: timely_leagueews-minus-timely_tcn: macro | +0.1694 [+0.0056, +0.3301] | -0.0037 [-0.0106, +0.0033] | +0.2443, +0.2647, -0.0006 |
| americas: timely_leagueews-minus-leagueews: baron | -0.1358 [-0.4264, +0.1635] | +0.0048 [-0.0036, +0.0134] | +0.1721, -0.3886, -0.1908 |
| americas: timely_leagueews-minus-leagueews: dragon | +1.1529 [+0.7207, +1.5951] | -0.0124 [-0.0319, +0.0078] | +1.2429, +1.1047, +1.1112 |
| americas: timely_leagueews-minus-leagueews: teamfight | +0.2602 [+0.0850, +0.4346] | -0.0237 [-0.0472, +0.0014] | +0.2882, +0.2391, +0.2534 |
| americas: timely_leagueews-minus-leagueews: macro | +0.4258 [+0.2417, +0.6091] | -0.0104 [-0.0219, +0.0013] | +0.5677, +0.3184, +0.3913 |
| americas: timely_tcn-minus-tcn: baron | -0.0791 [-0.3478, +0.1908] | -0.0051 [-0.0143, +0.0038] | -0.2375, -0.2193, +0.2195 |
| americas: timely_tcn-minus-tcn: dragon | +0.7013 [+0.3045, +1.0881] | -0.0061 [-0.0245, +0.0135] | +0.8958, +0.6845, +0.5236 |
| americas: timely_tcn-minus-tcn: teamfight | +0.2254 [+0.0577, +0.4067] | -0.0149 [-0.0405, +0.0096] | +0.1513, +0.2399, +0.2851 |
| americas: timely_tcn-minus-tcn: macro | +0.2825 [+0.1139, +0.4575] | -0.0087 [-0.0200, +0.0026] | +0.2698, +0.2350, +0.3427 |
| americas: timely_leagueews-minus-timely_tcn: baron | +0.2239 [-0.1611, +0.6062] | -0.0079 [-0.0200, +0.0040] | +0.6041, +0.3561, -0.2887 |
| americas: timely_leagueews-minus-timely_tcn: dragon | +0.2565 [+0.0164, +0.4971] | -0.0076 [-0.0193, +0.0037] | +0.1683, +0.0821, +0.5189 |
| americas: timely_leagueews-minus-timely_tcn: teamfight | +0.0660 [-0.0326, +0.1589] | -0.0015 [-0.0147, +0.0118] | +0.1660, -0.0409, +0.0728 |
| americas: timely_leagueews-minus-timely_tcn: macro | +0.1821 [+0.0285, +0.3364] | -0.0057 [-0.0131, +0.0015] | +0.3128, +0.1324, +0.1010 |

### Policy changes, four-budget mean

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| current_only: matched_early_mixture-minus-regional_deterministic | +0.8250 [+0.7789, +0.8753] | +0.0966 [+0.0936, +0.0997] | +0.5056, +0.6577, +1.3116 |
| current_only: regional_deterministic-minus-deterministic | +0.1610 [+0.1435, +0.1805] | +0.0179 [+0.0169, +0.0190] | +0.1408, +0.2422, +0.1001 |
| gru: matched_early_mixture-minus-regional_deterministic | +1.0502 [+0.9985, +1.1011] | +0.1491 [+0.1456, +0.1529] | +1.1531, +0.9825, +1.0151 |
| gru: regional_deterministic-minus-deterministic | +0.1087 [+0.0924, +0.1251] | +0.0094 [+0.0088, +0.0101] | +0.1440, +0.1125, +0.0694 |
| independent: matched_early_mixture-minus-regional_deterministic | +0.7510 [+0.7069, +0.7973] | +0.0812 [+0.0782, +0.0843] | +0.5644, +0.9476, +0.7412 |
| independent: regional_deterministic-minus-deterministic | +0.2997 [+0.2740, +0.3258] | +0.0197 [+0.0186, +0.0208] | +0.2904, +0.1028, +0.5058 |
| leagueews: matched_early_mixture-minus-regional_deterministic | +0.8856 [+0.8436, +0.9275] | +0.1074 [+0.1039, +0.1111] | +0.6414, +0.9822, +1.0332 |
| leagueews: regional_deterministic-minus-deterministic | +0.1529 [+0.1350, +0.1728] | +0.0164 [+0.0155, +0.0173] | +0.1728, +0.1576, +0.1282 |
| pcgrad: matched_early_mixture-minus-regional_deterministic | +0.7787 [+0.7370, +0.8207] | +0.0865 [+0.0833, +0.0897] | +0.6991, +0.7603, +0.8766 |
| pcgrad: regional_deterministic-minus-deterministic | +0.1110 [+0.0925, +0.1302] | +0.0111 [+0.0104, +0.0118] | +0.1850, +0.0489, +0.0991 |
| snapshot: matched_early_mixture-minus-regional_deterministic | +1.3111 [+1.2580, +1.3656] | +0.1322 [+0.1285, +0.1363] | +1.1440, +1.4317, +1.3576 |
| snapshot: regional_deterministic-minus-deterministic | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| tcn: matched_early_mixture-minus-regional_deterministic | +0.7848 [+0.7416, +0.8270] | +0.0873 [+0.0843, +0.0904] | +1.0750, +0.7355, +0.5440 |
| tcn: regional_deterministic-minus-deterministic | +0.0916 [+0.0764, +0.1081] | +0.0119 [+0.0112, +0.0127] | +0.1194, +0.1080, +0.0476 |
| timely_leagueews: matched_early_mixture-minus-regional_deterministic | +1.1015 [+1.0544, +1.1474] | +0.1177 [+0.1144, +0.1213] | +1.2099, +1.0005, +1.0941 |
| timely_leagueews: regional_deterministic-minus-deterministic | +0.1240 [+0.1074, +0.1409] | +0.0085 [+0.0079, +0.0090] | +0.3206, +0.0514, +0.0000 |
| timely_tcn: matched_early_mixture-minus-regional_deterministic | +1.1969 [+1.1525, +1.2425] | +0.1290 [+0.1255, +0.1329] | +1.1111, +1.3915, +1.0882 |
| timely_tcn: regional_deterministic-minus-deterministic | +0.0810 [+0.0656, +0.0996] | +0.0078 [+0.0072, +0.0085] | +0.0489, +0.1080, +0.0860 |
## 20-60 seconds, four-budget matched-early mean

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

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| leagueews-minus-current_only | +0.0791 [-0.1184, +0.2619] | -0.0053 [-0.0124, +0.0017] | +0.2043, +0.1901, -0.1572 |
| leagueews-minus-gru | +0.6296 [+0.2694, +0.9920] | +0.0034 [-0.0108, +0.0173] | +0.0340, +0.1626, +1.6921 |
| leagueews-minus-independent | -0.1016 [-0.2997, +0.0783] | +0.0024 [-0.0023, +0.0075] | +0.1335, -0.3347, -0.1036 |
| leagueews-minus-snapshot | +0.4238 [+0.2114, +0.6347] | -0.0066 [-0.0144, +0.0013] | +0.2788, +0.4714, +0.5213 |
| leagueews-minus-tcn | +0.2977 [+0.1526, +0.4329] | -0.0033 [-0.0077, +0.0007] | +0.0664, +0.4455, +0.3811 |
| target_effect_difference_leagueews_minus_tcn | +0.2399 [+0.0644, +0.4296] | +0.0027 [-0.0034, +0.0087] | +0.6361, -0.0205, +0.1040 |
| timely_leagueews-minus-independent | +3.8941 [+3.6053, +4.1894] | -0.0017 [-0.0126, +0.0092] | +4.3464, +3.5626, +3.7734 |
| timely_leagueews-minus-leagueews | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |
| timely_leagueews-minus-pcgrad | +4.1969 [+3.9550, +4.4466] | -0.0039 [-0.0142, +0.0065] | +4.3296, +4.1025, +4.1587 |
| timely_leagueews-minus-timely_tcn | +0.5375 [+0.3787, +0.6945] | -0.0006 [-0.0059, +0.0044] | +0.7025, +0.4249, +0.4851 |
| timely_tcn-minus-tcn | +3.7558 [+3.5143, +4.0052] | -0.0068 [-0.0166, +0.0026] | +3.5767, +3.9178, +3.7729 |

### Target effects by event

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| timely_leagueews-minus-leagueews: baron | +2.1962 [+1.6774, +2.7356] | +0.0040 [-0.0092, +0.0169] | +2.6719, +1.8781, +2.0386 |
| timely_leagueews-minus-leagueews: dragon | +8.1871 [+7.7508, +8.6396] | -0.0171 [-0.0333, -0.0019] | +8.3512, +8.1352, +8.0750 |
| timely_leagueews-minus-leagueews: teamfight | +1.6037 [+1.3918, +1.8139] | +0.0007 [-0.0192, +0.0208] | +1.6154, +1.6784, +1.5173 |
| timely_tcn-minus-tcn: baron | +1.3029 [+0.7652, +1.8389] | -0.0024 [-0.0143, +0.0098] | +1.0053, +1.7342, +1.1694 |
| timely_tcn-minus-tcn: dragon | +8.3467 [+7.9011, +8.7728] | -0.0188 [-0.0345, -0.0033] | +8.1826, +8.3410, +8.5165 |
| timely_tcn-minus-tcn: teamfight | +1.6178 [+1.4086, +1.8432] | +0.0008 [-0.0201, +0.0213] | +1.5422, +1.6782, +1.6329 |
| timely_leagueews-minus-timely_tcn: baron | +1.3866 [+0.9288, +1.8160] | -0.0024 [-0.0123, +0.0068] | +1.7780, +0.9488, +1.4330 |
| timely_leagueews-minus-timely_tcn: dragon | +0.1267 [-0.0132, +0.2749] | -0.0014 [-0.0074, +0.0046] | +0.1391, +0.2719, -0.0310 |
| timely_leagueews-minus-timely_tcn: teamfight | +0.0993 [-0.0010, +0.1966] | +0.0020 [-0.0086, +0.0123] | +0.1904, +0.0541, +0.0534 |
| target_effect_difference_leagueews_minus_tcn: baron | +0.8933 [+0.4263, +1.4185] | +0.0064 [-0.0044, +0.0174] | +1.6666, +0.1439, +0.8692 |
| target_effect_difference_leagueews_minus_tcn: dragon | -0.1596 [-0.3072, -0.0002] | +0.0017 [-0.0049, +0.0084] | +0.1686, -0.2058, -0.4415 |
| target_effect_difference_leagueews_minus_tcn: teamfight | -0.0140 [-0.1329, +0.1047] | -0.0001 [-0.0122, +0.0121] | +0.0732, +0.0002, -0.1156 |

### LeagueEWS target effect: deterministic

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +0.9950 [+0.7354, +1.2609] | -0.0775 [-0.0868, -0.0685] | +0.9711, +0.8952, +1.1186 |
| 0.5 | +5.0316 [+4.7128, +5.3784] | +0.0385 [+0.0266, +0.0503] | +4.4684, +7.1130, +3.5135 |
| 0.75 | +4.5316 [+4.1510, +4.9158] | -0.1062 [-0.1210, -0.0917] | +3.3292, +5.1661, +5.0995 |
| 1.0 | +7.4629 [+7.0862, +7.8579] | +0.0552 [+0.0395, +0.0708] | +6.9860, +7.5137, +7.8892 |
| mean | +4.5053 [+4.2409, +4.7816] | -0.0225 [-0.0339, -0.0117] | +3.9387, +5.1720, +4.4052 |

### LeagueEWS target effect: regional_deterministic

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +1.5350 [+1.2764, +1.8044] | -0.0558 [-0.0652, -0.0467] | +2.3081, +0.8952, +1.4015 |
| 0.5 | +5.1424 [+4.8187, +5.4867] | +0.0280 [+0.0158, +0.0401] | +5.6923, +6.2214, +3.5135 |
| 0.75 | +5.0826 [+4.6944, +5.4705] | -0.0683 [-0.0836, -0.0536] | +4.9823, +5.1661, +5.0995 |
| 1.0 | +7.4629 [+7.0862, +7.8579] | +0.0552 [+0.0395, +0.0708] | +6.9860, +7.5137, +7.8892 |
| mean | +4.8057 [+4.5362, +5.0876] | -0.0102 [-0.0218, +0.0007] | +4.9922, +4.9491, +4.4759 |

### LeagueEWS target effect: matched_early_mixture

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| 0.25 | +3.0509 [+2.8332, +3.2902] | +0.0005 [-0.0070, +0.0078] | +3.2849, +3.0472, +2.8206 |
| 0.5 | +4.2550 [+3.9812, +4.5546] | -0.0016 [-0.0120, +0.0085] | +4.4514, +4.2421, +4.0716 |
| 0.75 | +4.4871 [+4.1919, +4.7979] | -0.0051 [-0.0178, +0.0076] | +4.7465, +4.2353, +4.4793 |
| 1.0 | +4.1898 [+3.8926, +4.5039] | -0.0103 [-0.0239, +0.0033] | +4.3685, +4.0643, +4.1365 |
| mean | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |

### Regional target effects, four-budget matched-early mean

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| europe: timely_leagueews-minus-leagueews: baron | +2.2733 [+1.5466, +3.0233] | +0.0098 [-0.0097, +0.0291] | +2.8112, +2.2825, +1.7261 |
| europe: timely_leagueews-minus-leagueews: dragon | +7.6887 [+7.0685, +8.3297] | -0.0179 [-0.0411, +0.0055] | +8.0790, +7.5208, +7.4662 |
| europe: timely_leagueews-minus-leagueews: teamfight | +1.6303 [+1.3313, +1.9179] | +0.0210 [-0.0069, +0.0492] | +1.6699, +1.6843, +1.5367 |
| europe: timely_leagueews-minus-leagueews: macro | +3.8641 [+3.5251, +4.1941] | +0.0043 [-0.0097, +0.0185] | +4.1867, +3.8292, +3.5764 |
| europe: timely_tcn-minus-tcn: baron | +1.4544 [+0.7319, +2.1743] | -0.0066 [-0.0230, +0.0107] | +1.5420, +1.8723, +0.9489 |
| europe: timely_tcn-minus-tcn: dragon | +8.1220 [+7.5143, +8.7505] | -0.0124 [-0.0347, +0.0103] | +8.0471, +8.1223, +8.1966 |
| europe: timely_tcn-minus-tcn: teamfight | +1.6124 [+1.3211, +1.8902] | +0.0171 [-0.0079, +0.0445] | +1.3644, +1.7328, +1.7398 |
| europe: timely_tcn-minus-tcn: macro | +3.7296 [+3.4122, +4.0597] | -0.0007 [-0.0133, +0.0126] | +3.6512, +3.9091, +3.6284 |
| europe: timely_leagueews-minus-timely_tcn: baron | +1.0984 [+0.4927, +1.7114] | +0.0065 [-0.0072, +0.0193] | +1.8279, +0.4874, +0.9797 |
| europe: timely_leagueews-minus-timely_tcn: dragon | -0.0437 [-0.2329, +0.1661] | -0.0069 [-0.0152, +0.0016] | +0.1030, -0.0806, -0.1535 |
| europe: timely_leagueews-minus-timely_tcn: teamfight | +0.1650 [+0.0275, +0.3088] | +0.0122 [-0.0025, +0.0266] | +0.3359, +0.0869, +0.0724 |
| europe: timely_leagueews-minus-timely_tcn: macro | +0.4066 [+0.1919, +0.6236] | +0.0040 [-0.0035, +0.0111] | +0.7556, +0.1645, +0.2995 |
| americas: timely_leagueews-minus-leagueews: baron | +2.1201 [+1.3420, +2.8989] | -0.0018 [-0.0194, +0.0160] | +2.5345, +1.4789, +2.3470 |
| americas: timely_leagueews-minus-leagueews: dragon | +8.6706 [+8.0296, +9.3211] | -0.0163 [-0.0388, +0.0054] | +8.6152, +8.7312, +8.6655 |
| americas: timely_leagueews-minus-leagueews: teamfight | +1.5767 [+1.2955, +1.8687] | -0.0195 [-0.0468, +0.0094] | +1.5600, +1.6724, +1.4976 |
| americas: timely_leagueews-minus-leagueews: macro | +4.1225 [+3.7623, +4.4911] | -0.0125 [-0.0269, +0.0008] | +4.2365, +3.9608, +4.1701 |
| americas: timely_tcn-minus-tcn: baron | +1.1534 [+0.3840, +1.8990] | +0.0019 [-0.0161, +0.0191] | +0.4756, +1.5978, +1.3870 |
| americas: timely_tcn-minus-tcn: dragon | +8.5647 [+7.9363, +9.2208] | -0.0253 [-0.0471, -0.0041] | +8.3140, +8.5532, +8.8269 |
| americas: timely_tcn-minus-tcn: teamfight | +1.6232 [+1.3174, +1.9510] | -0.0155 [-0.0450, +0.0158] | +1.7229, +1.6226, +1.5242 |
| americas: timely_tcn-minus-tcn: macro | +3.7805 [+3.4450, +4.1281] | -0.0129 [-0.0274, +0.0007] | +3.5041, +3.9245, +3.9127 |
| americas: timely_leagueews-minus-timely_tcn: baron | +1.6711 [+1.0235, +2.3417] | -0.0114 [-0.0248, +0.0021] | +1.7288, +1.4042, +1.8804 |
| americas: timely_leagueews-minus-timely_tcn: dragon | +0.2919 [+0.0789, +0.5011] | +0.0041 [-0.0045, +0.0129] | +0.1741, +0.6138, +0.0879 |
| americas: timely_leagueews-minus-timely_tcn: teamfight | +0.0325 [-0.1090, +0.1712] | -0.0081 [-0.0220, +0.0066] | +0.0425, +0.0208, +0.0342 |
| americas: timely_leagueews-minus-timely_tcn: macro | +0.6652 [+0.4400, +0.8984] | -0.0051 [-0.0123, +0.0018] | +0.6485, +0.6796, +0.6675 |

### Policy changes, four-budget mean

| Contrast / event | Recall difference [95%] | Burden difference [95%] | Recall differences by seed |
|---|---:|---:|---|
| current_only: matched_early_mixture-minus-regional_deterministic | +4.0811 [+3.9517, +4.2034] | +0.1953 [+0.1883, +0.2028] | +3.6488, +3.7709, +4.8235 |
| current_only: regional_deterministic-minus-deterministic | +0.3074 [+0.2887, +0.3273] | +0.0152 [+0.0143, +0.0161] | +0.4406, +0.4817, +0.0000 |
| gru: matched_early_mixture-minus-regional_deterministic | +2.6317 [+2.5396, +2.7252] | +0.1849 [+0.1804, +0.1901] | +3.7257, +2.0200, +2.1494 |
| gru: regional_deterministic-minus-deterministic | +0.2304 [+0.2130, +0.2490] | +0.0131 [+0.0123, +0.0139] | +0.5292, +0.0000, +0.1620 |
| independent: matched_early_mixture-minus-regional_deterministic | +3.8371 [+3.7080, +3.9630] | +0.1620 [+0.1545, +0.1700] | +3.8045, +3.8917, +3.8152 |
| independent: regional_deterministic-minus-deterministic | +0.3226 [+0.2971, +0.3491] | +0.0170 [+0.0161, +0.0179] | +0.2631, +0.2648, +0.4399 |
| leagueews: matched_early_mixture-minus-regional_deterministic | +3.9535 [+3.8227, +4.0808] | +0.1576 [+0.1504, +0.1651] | +4.0352, +3.8930, +3.9325 |
| leagueews: regional_deterministic-minus-deterministic | +0.0743 [+0.0614, +0.0881] | +0.0060 [+0.0055, +0.0065] | +0.0000, +0.2229, +0.0000 |
| pcgrad: matched_early_mixture-minus-regional_deterministic | +3.8015 [+3.6606, +3.9415] | +0.1720 [+0.1644, +0.1798] | +3.9512, +3.7052, +3.7481 |
| pcgrad: regional_deterministic-minus-deterministic | +0.1457 [+0.1236, +0.1697] | +0.0050 [+0.0045, +0.0056] | +0.1980, +0.2391, +0.0000 |
| snapshot: matched_early_mixture-minus-regional_deterministic | +3.6035 [+3.4529, +3.7538] | +0.1883 [+0.1807, +0.1963] | +4.2352, +3.7502, +2.8251 |
| snapshot: regional_deterministic-minus-deterministic | +0.3198 [+0.3054, +0.3353] | +0.0204 [+0.0195, +0.0213] | +0.0000, +0.3671, +0.5923 |
| tcn: matched_early_mixture-minus-regional_deterministic | +3.5826 [+3.4460, +3.7191] | +0.1651 [+0.1579, +0.1724] | +3.6306, +3.5707, +3.5466 |
| tcn: regional_deterministic-minus-deterministic | +0.5601 [+0.5196, +0.5993] | +0.0252 [+0.0240, +0.0265] | +0.1928, +0.7895, +0.6979 |
| timely_leagueews: matched_early_mixture-minus-regional_deterministic | +3.1435 [+3.0628, +3.2275] | +0.1637 [+0.1593, +0.1684] | +3.2558, +2.8411, +3.3335 |
| timely_leagueews: regional_deterministic-minus-deterministic | +0.3748 [+0.3459, +0.4044] | +0.0183 [+0.0172, +0.0194] | +1.0535, +0.0000, +0.0707 |
| timely_tcn: matched_early_mixture-minus-regional_deterministic | +2.3263 [+2.2560, +2.4010] | +0.1367 [+0.1329, +0.1409] | +2.7091, +1.8855, +2.3843 |
| timely_tcn: regional_deterministic-minus-deterministic | +0.1604 [+0.1412, +0.1801] | +0.0106 [+0.0099, +0.0113] | +0.0000, +0.1419, +0.3394 |

## Frozen gates

| Gate | Pass |
|---|---|
| no_extra_burden | False |
| no_mean_event_harm | False |
| objective_alignment_effect | True |
| practical_promotion | False |
| regional_hard_budget | False |
| strong_control_gain | True |

All regional failures are in `budget-violations.csv`. `aggregate-counts.csv` contains denominators and expected counts, `by-seed.csv` every seed point, and `analysis.json` all paired intervals, seed ranges/SD, policy effects and gates.
