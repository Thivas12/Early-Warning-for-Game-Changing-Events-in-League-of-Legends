# Capped warning-risk evidence

Recall is percent; recall differences are percentage points. Burden is false-plus-late warnings per match per event. Intervals are pointwise conditional 95% paired whole-match bootstrap intervals, with fixed seed order 20260930, 20261001, 20261002. Four-budget means average operating points. Repeated calibration inspection prevents a fresh confirmation or certification claim. All study rules and failures remain visible.

## 10-30-second warnings

### uncapped_empirical, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 16.867 / 0.6127 | 10.618 / 0.6132 | 2.589 / 0.5852 | 10.025 / 0.6037 |
| timely_equal_tcn | 16.530 / 0.6136 | 10.230 / 0.6139 | 2.477 / 0.5774 | 9.746 / 0.6016 |
| timely_equal_gru | 11.586 / 0.5829 | 2.383 / 0.5560 | 1.871 / 0.5473 | 5.280 / 0.5621 |
| timely_independent | 16.438 / 0.6041 | 10.105 / 0.6156 | 2.544 / 0.5707 | 9.696 / 0.5968 |
| timely_leagueews | 16.116 / 0.6149 | 10.480 / 0.6074 | 2.607 / 0.5878 | 9.734 / 0.6034 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +5.2813 [+4.5465, +6.0437] | +0.0297 [+0.0096, +0.0477] | +5.0987, +4.4585, +6.2866 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +8.2355 [+7.8052, +8.6958] | +0.0573 [+0.0302, +0.0840] | +8.2134, +8.2289, +8.2642 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.7178 [+0.5497, +0.8759] | +0.0379 [+0.0166, +0.0601] | +0.6618, +0.5961, +0.8954 |
| timely_equal_sum-minus-timely_equal_gru: macro | +4.7449 [+4.4576, +5.0487] | +0.0416 [+0.0278, +0.0554] | +4.6580, +4.4278, +5.1488 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +0.3368 [+0.0452, +0.6213] | -0.0010 [-0.0097, +0.0078] | +0.3471, +0.3163, +0.3471 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3876 [+0.2108, +0.5603] | -0.0006 [-0.0098, +0.0078] | +0.3134, +0.4193, +0.4303 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1116 [+0.0388, +0.1821] | +0.0078 [-0.0029, +0.0179] | +0.0871, +0.1200, +0.1276 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.2787 [+0.1653, +0.3967] | +0.0021 [-0.0031, +0.0074] | +0.2492, +0.2852, +0.3017 |
| timely_equal_sum-minus-timely_independent: baron | +0.4294 [+0.0411, +0.8364] | +0.0086 [-0.0026, +0.0194] | +0.6788, +0.4474, +0.1620 |
| timely_equal_sum-minus-timely_independent: dragon | +0.5127 [+0.3018, +0.7203] | -0.0024 [-0.0125, +0.0077] | +0.5649, +0.4458, +0.5274 |
| timely_equal_sum-minus-timely_independent: teamfight | +0.0450 [-0.0513, +0.1432] | +0.0145 [+0.0014, +0.0278] | +0.0215, +0.1010, +0.0126 |
| timely_equal_sum-minus-timely_independent: macro | +0.3290 [+0.1788, +0.4855] | +0.0069 [+0.0003, +0.0133] | +0.4217, +0.3314, +0.2340 |
| timely_equal_sum-minus-timely_leagueews: baron | +0.7508 [+0.4894, +1.0036] | -0.0022 [-0.0096, +0.0049] | +0.4397, +0.8408, +0.9719 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.1383 [+0.0404, +0.2464] | +0.0058 [+0.0006, +0.0111] | +0.1898, -0.0375, +0.2626 |
| timely_equal_sum-minus-timely_leagueews: teamfight | -0.0181 [-0.0637, +0.0302] | -0.0026 [-0.0094, +0.0038] | -0.0985, +0.0177, +0.0265 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.2903 [+0.1928, +0.3824] | +0.0003 [-0.0034, +0.0041] | +0.1770, +0.2737, +0.4203 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +4.9445 [+4.1833, +5.7265] | +0.0307 [+0.0106, +0.0504] | +4.7516, +4.1422, +5.9395 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +7.8479 [+7.4223, +8.2766] | +0.0579 [+0.0315, +0.0852] | +7.9001, +7.8096, +7.8339 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.6062 [+0.4386, +0.7626] | +0.0301 [+0.0079, +0.0522] | +0.5746, +0.4761, +0.7679 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +4.4662 [+4.1876, +4.7622] | +0.0396 [+0.0256, +0.0537] | +4.4088, +4.1427, +4.8471 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1962 [+0.0208, +0.3723] | -0.0014 [-0.0068, +0.0038] | +0.3547, +0.1968, +0.0371 |
| 0.5 | +0.3609 [+0.1879, +0.5352] | +0.0123 [+0.0047, +0.0192] | +0.3186, +0.2470, +0.5173 |
| 0.75 | +0.2600 [+0.0943, +0.4345] | -0.0052 [-0.0133, +0.0031] | +0.1412, +0.2138, +0.4250 |
| 1.0 | +0.2975 [+0.1350, +0.4613] | +0.0025 [-0.0060, +0.0113] | +0.1823, +0.4830, +0.2272 |
### capped_empirical, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 16.716 / 0.6122 | 10.588 / 0.6100 | 2.590 / 0.5830 | 9.965 / 0.6017 |
| timely_equal_tcn | 16.376 / 0.6111 | 10.198 / 0.6116 | 2.491 / 0.5857 | 9.689 / 0.6028 |
| timely_equal_gru | 11.491 / 0.5846 | 2.383 / 0.5559 | 1.858 / 0.5449 | 5.244 / 0.5618 |
| timely_independent | 16.296 / 0.6022 | 10.122 / 0.6160 | 2.563 / 0.5799 | 9.660 / 0.5994 |
| timely_leagueews | 15.985 / 0.6114 | 10.449 / 0.6048 | 2.590 / 0.5898 | 9.675 / 0.6020 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +5.2247 [+4.5205, +5.9950] | +0.0276 [+0.0092, +0.0448] | +4.9676, +4.4971, +6.2095 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +8.2053 [+7.7739, +8.6604] | +0.0541 [+0.0273, +0.0804] | +8.1847, +8.1980, +8.2333 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.7325 [+0.5666, +0.8882] | +0.0382 [+0.0175, +0.0596] | +0.6694, +0.6226, +0.9055 |
| timely_equal_sum-minus-timely_equal_gru: macro | +4.7209 [+4.4446, +5.0201] | +0.0400 [+0.0266, +0.0530] | +4.6072, +4.4392, +5.1161 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +0.3394 [+0.0556, +0.6240] | +0.0011 [-0.0066, +0.0086] | +0.3548, +0.2623, +0.4011 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3899 [+0.2160, +0.5652] | -0.0016 [-0.0104, +0.0070] | +0.3089, +0.4259, +0.4347 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.0989 [+0.0264, +0.1695] | -0.0027 [-0.0125, +0.0069] | +0.0619, +0.1351, +0.0998 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.2761 [+0.1648, +0.3933] | -0.0011 [-0.0061, +0.0041] | +0.2419, +0.2744, +0.3119 |
| timely_equal_sum-minus-timely_independent: baron | +0.4191 [+0.0428, +0.8227] | +0.0100 [-0.0006, +0.0202] | +0.6634, +0.4705, +0.1234 |
| timely_equal_sum-minus-timely_independent: dragon | +0.4664 [+0.2589, +0.6716] | -0.0060 [-0.0161, +0.0040] | +0.4215, +0.4524, +0.5252 |
| timely_equal_sum-minus-timely_independent: teamfight | +0.0274 [-0.0676, +0.1252] | +0.0031 [-0.0094, +0.0156] | -0.0392, +0.0543, +0.0669 |
| timely_equal_sum-minus-timely_independent: macro | +0.3043 [+0.1564, +0.4575] | +0.0024 [-0.0039, +0.0086] | +0.3486, +0.3257, +0.2385 |
| timely_equal_sum-minus-timely_leagueews: baron | +0.7302 [+0.4711, +0.9750] | +0.0008 [-0.0059, +0.0071] | +0.4474, +0.8948, +0.8485 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.1390 [+0.0386, +0.2472] | +0.0052 [+0.0000, +0.0104] | +0.1832, -0.0375, +0.2714 |
| timely_equal_sum-minus-timely_leagueews: teamfight | +0.0004 [-0.0463, +0.0457] | -0.0067 [-0.0132, -0.0006] | -0.0290, +0.0088, +0.0215 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.2899 [+0.1938, +0.3815] | -0.0003 [-0.0037, +0.0032] | +0.2005, +0.2887, +0.3805 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +4.8853 [+4.1600, +5.6550] | +0.0266 [+0.0084, +0.0449] | +4.6128, +4.2348, +5.8084 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +7.8155 [+7.3911, +8.2504] | +0.0557 [+0.0292, +0.0831] | +7.8758, +7.7721, +7.7986 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.6336 [+0.4656, +0.7877] | +0.0408 [+0.0193, +0.0629] | +0.6075, +0.4875, +0.8058 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +4.4448 [+4.1711, +4.7366] | +0.0410 [+0.0275, +0.0545] | +4.3654, +4.1648, +4.8042 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1991 [+0.0241, +0.3784] | -0.0013 [-0.0069, +0.0039] | +0.3427, +0.2071, +0.0474 |
| 0.5 | +0.3323 [+0.1616, +0.5093] | +0.0059 [-0.0016, +0.0129] | +0.2815, +0.2281, +0.4871 |
| 0.75 | +0.3001 [+0.1311, +0.4724] | -0.0024 [-0.0102, +0.0055] | +0.2277, +0.3133, +0.3594 |
| 1.0 | +0.2728 [+0.1052, +0.4394] | -0.0065 [-0.0146, +0.0016] | +0.1156, +0.3492, +0.3535 |
### capped_sequence, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 16.716 / 0.6122 | 10.588 / 0.6100 | 2.590 / 0.5830 | 9.965 / 0.6017 |
| timely_equal_tcn | 16.376 / 0.6111 | 10.198 / 0.6116 | 2.491 / 0.5857 | 9.689 / 0.6028 |
| timely_equal_gru | 11.491 / 0.5846 | 2.383 / 0.5559 | 1.858 / 0.5449 | 5.244 / 0.5618 |
| timely_independent | 16.296 / 0.6022 | 10.122 / 0.6160 | 2.563 / 0.5799 | 9.660 / 0.5994 |
| timely_leagueews | 15.985 / 0.6114 | 10.449 / 0.6048 | 2.590 / 0.5898 | 9.675 / 0.6020 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +5.2247 [+4.5205, +5.9950] | +0.0276 [+0.0092, +0.0448] | +4.9676, +4.4971, +6.2095 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +8.2053 [+7.7739, +8.6604] | +0.0541 [+0.0273, +0.0804] | +8.1847, +8.1980, +8.2333 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.7325 [+0.5666, +0.8882] | +0.0382 [+0.0175, +0.0596] | +0.6694, +0.6226, +0.9055 |
| timely_equal_sum-minus-timely_equal_gru: macro | +4.7209 [+4.4446, +5.0201] | +0.0400 [+0.0266, +0.0530] | +4.6072, +4.4392, +5.1161 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +0.3394 [+0.0556, +0.6240] | +0.0011 [-0.0066, +0.0086] | +0.3548, +0.2623, +0.4011 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3899 [+0.2160, +0.5652] | -0.0016 [-0.0104, +0.0070] | +0.3089, +0.4259, +0.4347 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.0989 [+0.0264, +0.1695] | -0.0027 [-0.0125, +0.0069] | +0.0619, +0.1351, +0.0998 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.2761 [+0.1648, +0.3933] | -0.0011 [-0.0061, +0.0041] | +0.2419, +0.2744, +0.3119 |
| timely_equal_sum-minus-timely_independent: baron | +0.4191 [+0.0428, +0.8227] | +0.0100 [-0.0006, +0.0202] | +0.6634, +0.4705, +0.1234 |
| timely_equal_sum-minus-timely_independent: dragon | +0.4664 [+0.2589, +0.6716] | -0.0060 [-0.0161, +0.0040] | +0.4215, +0.4524, +0.5252 |
| timely_equal_sum-minus-timely_independent: teamfight | +0.0274 [-0.0676, +0.1252] | +0.0031 [-0.0094, +0.0156] | -0.0392, +0.0543, +0.0669 |
| timely_equal_sum-minus-timely_independent: macro | +0.3043 [+0.1564, +0.4575] | +0.0024 [-0.0039, +0.0086] | +0.3486, +0.3257, +0.2385 |
| timely_equal_sum-minus-timely_leagueews: baron | +0.7302 [+0.4711, +0.9750] | +0.0008 [-0.0059, +0.0071] | +0.4474, +0.8948, +0.8485 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.1390 [+0.0386, +0.2472] | +0.0052 [+0.0000, +0.0104] | +0.1832, -0.0375, +0.2714 |
| timely_equal_sum-minus-timely_leagueews: teamfight | +0.0004 [-0.0463, +0.0457] | -0.0067 [-0.0132, -0.0006] | -0.0290, +0.0088, +0.0215 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.2899 [+0.1938, +0.3815] | -0.0003 [-0.0037, +0.0032] | +0.2005, +0.2887, +0.3805 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +4.8853 [+4.1600, +5.6550] | +0.0266 [+0.0084, +0.0449] | +4.6128, +4.2348, +5.8084 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +7.8155 [+7.3911, +8.2504] | +0.0557 [+0.0292, +0.0831] | +7.8758, +7.7721, +7.7986 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.6336 [+0.4656, +0.7877] | +0.0408 [+0.0193, +0.0629] | +0.6075, +0.4875, +0.8058 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +4.4448 [+4.1711, +4.7366] | +0.0410 [+0.0275, +0.0545] | +4.3654, +4.1648, +4.8042 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.1991 [+0.0241, +0.3784] | -0.0013 [-0.0069, +0.0039] | +0.3427, +0.2071, +0.0474 |
| 0.5 | +0.3323 [+0.1616, +0.5093] | +0.0059 [-0.0016, +0.0129] | +0.2815, +0.2281, +0.4871 |
| 0.75 | +0.3001 [+0.1311, +0.4724] | -0.0024 [-0.0102, +0.0055] | +0.2277, +0.3133, +0.3594 |
| 1.0 | +0.2728 [+0.1052, +0.4394] | -0.0065 [-0.0146, +0.0016] | +0.1156, +0.3492, +0.3535 |
### capped_kl_sequence, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 14.098 / 0.4583 | 8.486 / 0.4622 | 2.035 / 0.4433 | 8.206 / 0.4546 |
| timely_equal_tcn | 13.954 / 0.4695 | 8.031 / 0.4594 | 1.958 / 0.4340 | 7.981 / 0.4543 |
| timely_equal_gru | 9.413 / 0.4396 | 1.562 / 0.4112 | 1.466 / 0.4104 | 4.147 / 0.4204 |
| timely_independent | 13.643 / 0.4503 | 7.957 / 0.4619 | 2.036 / 0.4371 | 7.878 / 0.4498 |
| timely_leagueews | 13.499 / 0.4664 | 8.410 / 0.4624 | 2.054 / 0.4447 | 7.987 / 0.4579 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +4.6848 [+4.0497, +5.3796] | +0.0186 [+0.0027, +0.0340] | +4.5511, +4.0342, +5.4690 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +6.9240 [+6.5340, +7.3304] | +0.0510 [+0.0276, +0.0744] | +6.8100, +6.9953, +6.9666 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.5696 [+0.4221, +0.7120] | +0.0328 [+0.0143, +0.0509] | +0.5027, +0.4521, +0.7540 |
| timely_equal_sum-minus-timely_equal_gru: macro | +4.0594 [+3.8117, +4.3408] | +0.0342 [+0.0222, +0.0459] | +3.9546, +3.8272, +4.3965 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +0.1440 [-0.1207, +0.4252] | -0.0112 [-0.0180, -0.0044] | +0.2391, +0.0849, +0.1080 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.4546 [+0.2784, +0.6263] | +0.0028 [-0.0059, +0.0115] | +0.0993, +0.6841, +0.5804 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.0770 [+0.0131, +0.1438] | +0.0093 [+0.0004, +0.0181] | +0.0455, +0.0606, +0.1250 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.2252 [+0.1184, +0.3395] | +0.0003 [-0.0044, +0.0048] | +0.1280, +0.2765, +0.2711 |
| timely_equal_sum-minus-timely_independent: baron | +0.4551 [+0.0795, +0.8400] | +0.0080 [-0.0016, +0.0167] | +0.6634, +0.3934, +0.3085 |
| timely_equal_sum-minus-timely_independent: dragon | +0.5289 [+0.3229, +0.7325] | +0.0003 [-0.0096, +0.0102] | +0.4612, +0.6554, +0.4700 |
| timely_equal_sum-minus-timely_independent: teamfight | -0.0004 [-0.0890, +0.0923] | +0.0062 [-0.0051, +0.0179] | -0.0177, +0.0417, -0.0253 |
| timely_equal_sum-minus-timely_independent: macro | +0.3279 [+0.1817, +0.4733] | +0.0048 [-0.0009, +0.0105] | +0.3690, +0.3635, +0.2511 |
| timely_equal_sum-minus-timely_leagueews: baron | +0.5991 [+0.3577, +0.8336] | -0.0082 [-0.0142, -0.0026] | +0.4551, +0.6942, +0.6479 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.0758 [-0.0155, +0.1784] | -0.0002 [-0.0050, +0.0048] | -0.0154, +0.0618, +0.1810 |
| timely_equal_sum-minus-timely_leagueews: teamfight | -0.0181 [-0.0577, +0.0219] | -0.0015 [-0.0071, +0.0042] | -0.0871, +0.0152, +0.0177 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.2189 [+0.1325, +0.3061] | -0.0033 [-0.0064, +0.0000] | +0.1175, +0.2571, +0.2822 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +4.5408 [+3.8970, +5.2473] | +0.0298 [+0.0135, +0.0456] | +4.3119, +3.9494, +5.3610 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +6.4694 [+6.1002, +6.8491] | +0.0482 [+0.0249, +0.0716] | +6.7107, +6.3112, +6.3863 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.4925 [+0.3426, +0.6318] | +0.0235 [+0.0047, +0.0424] | +0.4572, +0.3915, +0.6289 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +3.8342 [+3.5824, +4.1031] | +0.0339 [+0.0221, +0.0457] | +3.8266, +3.5507, +4.1254 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2033 [+0.0594, +0.3590] | +0.0031 [-0.0015, +0.0080] | +0.2265, +0.0809, +0.3025 |
| 0.5 | +0.2768 [+0.0991, +0.4559] | +0.0022 [-0.0040, +0.0083] | +0.2222, +0.5047, +0.1035 |
| 0.75 | +0.1848 [+0.0151, +0.3590] | -0.0054 [-0.0131, +0.0018] | +0.0704, +0.1865, +0.2976 |
| 1.0 | +0.2359 [+0.0739, +0.4020] | +0.0013 [-0.0067, +0.0092] | -0.0072, +0.3340, +0.3810 |
### overall: every within-model policy effect, four-budget mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: baron | -0.1517 [-0.2985, -0.0153] | -0.0005 [-0.0051, +0.0036] | -0.1928, -0.1466, -0.1157 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: dragon | -0.0302 [-0.0471, -0.0160] | -0.0032 [-0.0045, -0.0021] | -0.0287, -0.0309, -0.0309 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: teamfight | +0.0013 [-0.0184, +0.0178] | -0.0022 [-0.0064, +0.0014] | -0.0013, +0.0038, +0.0013 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: macro | -0.0602 [-0.1102, -0.0134] | -0.0020 [-0.0041, +0.0000] | -0.0743, -0.0579, -0.0484 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: baron | -2.6175 [-2.8293, -2.4154] | -0.1539 [-0.1606, -0.1476] | -2.5378, -2.6844, -2.6304 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: dragon | -2.1023 [-2.1998, -2.0059] | -0.1478 [-0.1538, -0.1424] | -2.1957, -2.0147, -2.0964 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5549 [-0.5951, -0.5113] | -0.1398 [-0.1457, -0.1342] | -0.5506, -0.5696, -0.5443 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: macro | -1.7582 [-1.8368, -1.6828] | -0.1471 [-0.1514, -0.1431] | -1.7614, -1.7562, -1.7570 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: baron | -2.7692 [-3.0054, -2.5473] | -0.1544 [-0.1631, -0.1464] | -2.7306, -2.8309, -2.7461 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1324 [-2.2306, -2.0341] | -0.1510 [-0.1574, -0.1453] | -2.2244, -2.0456, -2.1273 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5536 [-0.5948, -0.5111] | -0.1419 [-0.1491, -0.1351] | -0.5519, -0.5658, -0.5431 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: macro | -1.8184 [-1.9076, -1.7338] | -0.1491 [-0.1542, -0.1445] | -1.8356, -1.8141, -1.8055 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: baron | -0.1543 [-0.3024, -0.0307] | -0.0025 [-0.0078, +0.0022] | -0.2006, -0.0926, -0.1697 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: dragon | -0.0324 [-0.0530, -0.0155] | -0.0023 [-0.0031, -0.0015] | -0.0243, -0.0375, -0.0353 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: teamfight | +0.0139 [-0.0046, +0.0303] | +0.0083 [+0.0050, +0.0114] | +0.0240, -0.0114, +0.0290 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: macro | -0.0576 [-0.1060, -0.0155] | +0.0012 [-0.0011, +0.0031] | -0.0669, -0.0471, -0.0587 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: baron | -2.4221 [-2.6269, -2.2282] | -0.1416 [-0.1480, -0.1356] | -2.4221, -2.5069, -2.3372 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: dragon | -2.1670 [-2.2657, -2.0705] | -0.1522 [-0.1579, -0.1466] | -1.9861, -2.2729, -2.2420 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5330 [-0.5753, -0.4926] | -0.1517 [-0.1581, -0.1457] | -0.5342, -0.4951, -0.5696 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: macro | -1.7074 [-1.7912, -1.6317] | -0.1485 [-0.1528, -0.1446] | -1.6475, -1.7583, -1.7163 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: baron | -2.5764 [-2.8042, -2.3576] | -0.1442 [-0.1531, -0.1359] | -2.6226, -2.5995, -2.5069 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1994 [-2.2995, -2.0997] | -0.1545 [-0.1605, -0.1486] | -2.0103, -2.3104, -2.2773 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5191 [-0.5606, -0.4783] | -0.1434 [-0.1505, -0.1372] | -0.5102, -0.5064, -0.5405 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: macro | -1.7649 [-1.8528, -1.6837] | -0.1474 [-0.1523, -0.1428] | -1.7144, -1.8055, -1.7749 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: baron | -0.0951 [-0.1948, +0.0027] | +0.0016 [-0.0022, +0.0048] | -0.0617, -0.1851, -0.0386 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | -0.0001 [-0.0001, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: teamfight | -0.0135 [-0.0210, -0.0073] | -0.0024 [-0.0036, -0.0015] | -0.0088, -0.0227, -0.0088 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: macro | -0.0362 [-0.0693, -0.0037] | -0.0003 [-0.0016, +0.0008] | -0.0235, -0.0693, -0.0158 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: baron | -2.0775 [-2.2633, -1.8971] | -0.1449 [-0.1512, -0.1389] | -2.1213, -2.2215, -1.8898 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: dragon | -0.8209 [-0.8831, -0.7592] | -0.1447 [-0.1494, -0.1401] | -0.8209, -0.8121, -0.8297 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: teamfight | -0.3919 [-0.4245, -0.3580] | -0.1344 [-0.1397, -0.1291] | -0.3839, -0.3991, -0.3928 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: macro | -1.0968 [-1.1615, -1.0323] | -0.1413 [-0.1453, -0.1377] | -1.1087, -1.1442, -1.0375 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: baron | -2.1727 [-2.3708, -1.9928] | -0.1433 [-0.1510, -0.1362] | -2.1830, -2.4067, -1.9284 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: dragon | -0.8209 [-0.8831, -0.7592] | -0.1448 [-0.1494, -0.1402] | -0.8209, -0.8121, -0.8297 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.4054 [-0.4398, -0.3707] | -0.1369 [-0.1424, -0.1314] | -0.3928, -0.4218, -0.4016 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: macro | -1.1330 [-1.2001, -1.0703] | -0.1416 [-0.1460, -0.1376] | -1.1322, -1.2135, -1.0533 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_empirical-minus-uncapped_empirical: baron | -0.1414 [-0.2749, -0.0282] | -0.0019 [-0.0064, +0.0018] | -0.1774, -0.1697, -0.0771 |
| timely_independent: capped_empirical-minus-uncapped_empirical: dragon | +0.0162 [-0.0059, +0.0359] | +0.0004 [-0.0014, +0.0018] | +0.1147, -0.0375, -0.0287 |
| timely_independent: capped_empirical-minus-uncapped_empirical: teamfight | +0.0189 [-0.0051, +0.0416] | +0.0093 [+0.0040, +0.0140] | +0.0594, +0.0505, -0.0530 |
| timely_independent: capped_empirical-minus-uncapped_empirical: macro | -0.0354 [-0.0814, +0.0038] | +0.0026 [+0.0003, +0.0048] | -0.0011, -0.0522, -0.0530 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: baron | -2.6535 [-2.8701, -2.4456] | -0.1519 [-0.1585, -0.1456] | -2.5378, -2.6072, -2.8155 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: dragon | -2.1648 [-2.2669, -2.0657] | -0.1541 [-0.1602, -0.1480] | -2.2354, -2.2178, -2.0412 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5271 [-0.5701, -0.4855] | -0.1429 [-0.1487, -0.1372] | -0.5721, -0.5570, -0.4521 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: macro | -1.7818 [-1.8642, -1.7036] | -0.1496 [-0.1539, -0.1456] | -1.7818, -1.7940, -1.7696 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: baron | -2.7949 [-3.0264, -2.5804] | -0.1538 [-0.1621, -0.1460] | -2.7152, -2.7769, -2.8926 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1486 [-2.2496, -2.0545] | -0.1537 [-0.1603, -0.1474] | -2.1207, -2.2553, -2.0699 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5081 [-0.5512, -0.4654] | -0.1336 [-0.1412, -0.1266] | -0.5128, -0.5064, -0.5052 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: macro | -1.8172 [-1.9058, -1.7315] | -0.1470 [-0.1521, -0.1424] | -1.7829, -1.8462, -1.8226 |
| timely_independent: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: baron | -0.1311 [-0.2915, +0.0129] | -0.0035 [-0.0093, +0.0015] | -0.2006, -0.2006, +0.0077 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: dragon | -0.0309 [-0.0508, -0.0152] | -0.0026 [-0.0037, -0.0017] | -0.0221, -0.0309, -0.0397 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: teamfight | -0.0173 [-0.0405, +0.0038] | +0.0020 [-0.0023, +0.0059] | -0.0707, +0.0126, +0.0063 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: macro | -0.0598 [-0.1136, -0.0104] | -0.0014 [-0.0039, +0.0010] | -0.0978, -0.0729, -0.0086 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: baron | -2.4864 [-2.7104, -2.2828] | -0.1450 [-0.1515, -0.1389] | -2.5455, -2.4838, -2.4298 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: dragon | -2.0390 [-2.1362, -1.9464] | -0.1424 [-0.1482, -0.1369] | -1.9971, -2.1140, -2.0059 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5363 [-0.5779, -0.4942] | -0.1450 [-0.1512, -0.1393] | -0.4925, -0.5759, -0.5405 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: macro | -1.6872 [-1.7688, -1.6093] | -0.1441 [-0.1483, -0.1403] | -1.6784, -1.7246, -1.6588 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: baron | -2.6175 [-2.8554, -2.3956] | -0.1484 [-0.1576, -0.1401] | -2.7461, -2.6844, -2.4221 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.0699 [-2.1685, -1.9788] | -0.1450 [-0.1508, -0.1394] | -2.0192, -2.1449, -2.0456 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5536 [-0.5958, -0.5093] | -0.1430 [-0.1507, -0.1361] | -0.5633, -0.5633, -0.5342 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: macro | -1.7470 [-1.8344, -1.6653] | -0.1455 [-0.1506, -0.1408] | -1.7762, -1.7975, -1.6673 |
| timely_leagueews: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
### europe: every within-model policy effect, four-budget mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: baron | -0.0259 [-0.2037, +0.1219] | +0.0009 [-0.0049, +0.0057] | -0.0932, -0.0155, +0.0311 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: dragon | -0.0254 [-0.0470, -0.0089] | -0.0013 [-0.0021, -0.0007] | -0.0269, -0.0179, -0.0314 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: teamfight | +0.0175 [-0.0050, +0.0373] | +0.0009 [-0.0044, +0.0050] | +0.0000, +0.0251, +0.0276 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: macro | -0.0112 [-0.0719, +0.0388] | +0.0001 [-0.0025, +0.0024] | -0.0400, -0.0028, +0.0091 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: baron | -2.6449 [-2.9400, -2.3592] | -0.1457 [-0.1549, -0.1366] | -2.5932, -2.6087, -2.7329 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: dragon | -2.1468 [-2.2914, -2.0082] | -0.1538 [-0.1623, -0.1458] | -2.2499, -2.0930, -2.0975 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5763 [-0.6356, -0.5190] | -0.1371 [-0.1453, -0.1290] | -0.5838, -0.5788, -0.5662 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: macro | -1.7893 [-1.9030, -1.6758] | -0.1455 [-0.1512, -0.1398] | -1.8090, -1.7602, -1.7989 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: baron | -2.6708 [-2.9859, -2.3617] | -0.1448 [-0.1564, -0.1340] | -2.6863, -2.6242, -2.7019 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1722 [-2.3166, -2.0287] | -0.1552 [-0.1638, -0.1472] | -2.2768, -2.1110, -2.1289 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5587 [-0.6166, -0.5019] | -0.1362 [-0.1462, -0.1270] | -0.5838, -0.5537, -0.5387 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: macro | -1.8006 [-1.9214, -1.6814] | -0.1454 [-0.1520, -0.1388] | -1.8490, -1.7630, -1.7898 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: baron | -0.0776 [-0.2510, +0.0681] | -0.0003 [-0.0063, +0.0051] | -0.1087, -0.0311, -0.0932 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: dragon | -0.0239 [-0.0432, -0.0074] | -0.0013 [-0.0023, -0.0004] | -0.0224, -0.0224, -0.0269 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: teamfight | +0.0084 [-0.0145, +0.0310] | +0.0101 [+0.0054, +0.0140] | +0.0050, -0.0050, +0.0251 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: macro | -0.0311 [-0.0902, +0.0177] | +0.0028 [+0.0001, +0.0051] | -0.0420, -0.0195, -0.0317 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: baron | -2.4017 [-2.6850, -2.1150] | -0.1338 [-0.1426, -0.1249] | -2.3913, -2.5466, -2.2671 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: dragon | -2.2155 [-2.3567, -2.0758] | -0.1523 [-0.1604, -0.1443] | -2.0437, -2.2858, -2.3171 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5220 [-0.5811, -0.4674] | -0.1539 [-0.1628, -0.1452] | -0.5487, -0.4786, -0.5387 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: macro | -1.7131 [-1.8218, -1.6032] | -0.1467 [-0.1527, -0.1406] | -1.6613, -1.7703, -1.7076 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: baron | -2.4793 [-2.7878, -2.1719] | -0.1341 [-0.1453, -0.1232] | -2.5000, -2.5776, -2.3602 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.2395 [-2.3833, -2.0981] | -0.1536 [-0.1619, -0.1455] | -2.0662, -2.3082, -2.3440 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5136 [-0.5751, -0.4613] | -0.1439 [-0.1536, -0.1344] | -0.5437, -0.4836, -0.5136 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: macro | -1.7441 [-1.8591, -1.6251] | -0.1439 [-0.1504, -0.1373] | -1.7033, -1.7898, -1.7393 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: baron | -0.0725 [-0.2197, +0.0622] | +0.0029 [-0.0009, +0.0062] | -0.0466, -0.2174, +0.0466 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: teamfight | -0.0134 [-0.0243, -0.0050] | -0.0023 [-0.0037, -0.0011] | -0.0100, -0.0251, -0.0050 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: macro | -0.0286 [-0.0774, +0.0155] | +0.0002 [-0.0012, +0.0014] | -0.0189, -0.0808, +0.0139 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: baron | -2.0290 [-2.2869, -1.7883] | -0.1348 [-0.1441, -0.1263] | -2.1584, -2.0963, -1.8323 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: dragon | -0.8067 [-0.8954, -0.7197] | -0.1454 [-0.1522, -0.1387] | -0.7978, -0.8112, -0.8112 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: teamfight | -0.3900 [-0.4395, -0.3468] | -0.1322 [-0.1398, -0.1248] | -0.4009, -0.3884, -0.3808 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: macro | -1.0753 [-1.1670, -0.9902] | -0.1375 [-0.1430, -0.1322] | -1.1190, -1.0986, -1.0081 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: baron | -2.1014 [-2.3752, -1.8460] | -0.1318 [-0.1419, -0.1223] | -2.2050, -2.3137, -1.7857 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: dragon | -0.8067 [-0.8954, -0.7197] | -0.1454 [-0.1522, -0.1387] | -0.7978, -0.8112, -0.8112 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.4034 [-0.4531, -0.3583] | -0.1345 [-0.1423, -0.1269] | -0.4109, -0.4134, -0.3858 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: macro | -1.1039 [-1.2013, -1.0151] | -0.1373 [-0.1432, -0.1315] | -1.1379, -1.1794, -0.9943 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_empirical-minus-uncapped_empirical: baron | -0.0828 [-0.2410, +0.0457] | -0.0017 [-0.0077, +0.0035] | -0.1398, -0.0932, -0.0155 |
| timely_independent: capped_empirical-minus-uncapped_empirical: dragon | +0.0224 [-0.0061, +0.0488] | +0.0022 [+0.0007, +0.0036] | +0.1300, -0.0403, -0.0224 |
| timely_independent: capped_empirical-minus-uncapped_empirical: teamfight | +0.0376 [+0.0089, +0.0647] | +0.0101 [+0.0029, +0.0162] | +0.0702, +0.0777, -0.0351 |
| timely_independent: capped_empirical-minus-uncapped_empirical: macro | -0.0076 [-0.0616, +0.0365] | +0.0035 [+0.0002, +0.0065] | +0.0201, -0.0186, -0.0243 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: baron | -2.7743 [-3.0891, -2.4765] | -0.1473 [-0.1562, -0.1383] | -2.6708, -2.7484, -2.9037 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: dragon | -2.2051 [-2.3557, -2.0635] | -0.1558 [-0.1643, -0.1473] | -2.3127, -2.3306, -1.9720 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5412 [-0.5994, -0.4847] | -0.1429 [-0.1508, -0.1347] | -0.5988, -0.5813, -0.4435 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: macro | -1.8402 [-1.9639, -1.7232] | -0.1487 [-0.1546, -0.1427] | -1.8608, -1.8868, -1.7731 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: baron | -2.8571 [-3.1913, -2.5453] | -0.1491 [-0.1609, -0.1382] | -2.8106, -2.8416, -2.9193 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1827 [-2.3333, -2.0452] | -0.1536 [-0.1625, -0.1452] | -2.1827, -2.3709, -1.9944 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5036 [-0.5639, -0.4462] | -0.1328 [-0.1436, -0.1229] | -0.5287, -0.5036, -0.4786 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: macro | -1.8478 [-1.9729, -1.7270] | -0.1452 [-0.1523, -0.1383] | -1.8406, -1.9054, -1.7974 |
| timely_independent: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: baron | -0.0466 [-0.2150, +0.1041] | -0.0009 [-0.0082, +0.0051] | -0.1087, -0.1087, +0.0776 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: dragon | -0.0179 [-0.0370, -0.0030] | -0.0012 [-0.0021, -0.0006] | -0.0224, -0.0090, -0.0224 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: teamfight | -0.0000 [-0.0244, +0.0206] | +0.0036 [-0.0016, +0.0079] | -0.0651, +0.0376, +0.0276 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: macro | -0.0215 [-0.0792, +0.0294] | +0.0005 [-0.0025, +0.0031] | -0.0654, -0.0267, +0.0276 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: baron | -2.5052 [-2.8248, -2.2120] | -0.1381 [-0.1468, -0.1293] | -2.6087, -2.4068, -2.5000 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: dragon | -2.1020 [-2.2425, -1.9635] | -0.1424 [-0.1499, -0.1347] | -2.0482, -2.2051, -2.0527 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5111 [-0.5673, -0.4598] | -0.1408 [-0.1493, -0.1323] | -0.4435, -0.5988, -0.4911 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: macro | -1.7061 [-1.8174, -1.5902] | -0.1404 [-0.1461, -0.1345] | -1.7001, -1.7369, -1.6813 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: baron | -2.5518 [-2.8576, -2.2449] | -0.1391 [-0.1512, -0.1272] | -2.7174, -2.5155, -2.4224 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1199 [-2.2613, -1.9791] | -0.1437 [-0.1513, -0.1357] | -2.0706, -2.2141, -2.0751 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5111 [-0.5679, -0.4598] | -0.1372 [-0.1472, -0.1279] | -0.5086, -0.5612, -0.4635 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: macro | -1.7276 [-1.8431, -1.6110] | -0.1400 [-0.1466, -0.1330] | -1.7655, -1.7636, -1.6537 |
| timely_leagueews: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
### americas: every within-model policy effect, four-budget mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: baron | -0.2759 [-0.5249, -0.0602] | -0.0019 [-0.0092, +0.0044] | -0.2912, -0.2759, -0.2606 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: dragon | -0.0348 [-0.0614, -0.0131] | -0.0051 [-0.0074, -0.0029] | -0.0304, -0.0435, -0.0304 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: teamfight | -0.0153 [-0.0465, +0.0118] | -0.0052 [-0.0116, +0.0003] | -0.0025, -0.0178, -0.0255 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: macro | -0.1087 [-0.1914, -0.0376] | -0.0041 [-0.0077, -0.0010] | -0.1081, -0.1124, -0.1055 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: baron | -2.5904 [-2.9122, -2.2950] | -0.1621 [-0.1716, -0.1523] | -2.4831, -2.7590, -2.5291 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: dragon | -2.0591 [-2.1934, -1.9188] | -0.1418 [-0.1497, -0.1341] | -2.1431, -1.9388, -2.0953 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5331 [-0.5930, -0.4735] | -0.1424 [-0.1510, -0.1339] | -0.5170, -0.5603, -0.5221 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: macro | -1.7275 [-1.8449, -1.6140] | -0.1488 [-0.1549, -0.1429] | -1.7144, -1.7527, -1.7155 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: baron | -2.8663 [-3.2262, -2.5269] | -0.1640 [-0.1767, -0.1516] | -2.7744, -3.0349, -2.7897 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.0938 [-2.2321, -1.9562] | -0.1469 [-0.1554, -0.1383] | -2.1735, -1.9823, -2.1257 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5484 [-0.6108, -0.4881] | -0.1476 [-0.1583, -0.1376] | -0.5195, -0.5781, -0.5475 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: macro | -1.8362 [-1.9698, -1.7093] | -0.1528 [-0.1603, -0.1456] | -1.8225, -1.8651, -1.8210 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: baron | -0.2299 [-0.4650, -0.0320] | -0.0048 [-0.0138, +0.0024] | -0.2912, -0.1533, -0.2452 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: dragon | -0.0406 [-0.0759, -0.0130] | -0.0032 [-0.0046, -0.0018] | -0.0261, -0.0522, -0.0435 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: teamfight | +0.0195 [-0.0086, +0.0458] | +0.0065 [+0.0015, +0.0108] | +0.0433, -0.0178, +0.0331 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: macro | -0.0837 [-0.1641, -0.0180] | -0.0005 [-0.0040, +0.0025] | -0.0913, -0.0744, -0.0852 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: baron | -2.4423 [-2.7243, -2.1499] | -0.1495 [-0.1591, -0.1404] | -2.4525, -2.4678, -2.4065 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: dragon | -2.1199 [-2.2607, -1.9814] | -0.1522 [-0.1604, -0.1442] | -1.9301, -2.2605, -2.1692 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5441 [-0.6066, -0.4847] | -0.1495 [-0.1586, -0.1407] | -0.5195, -0.5119, -0.6010 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: macro | -1.7021 [-1.8107, -1.5895] | -0.1504 [-0.1564, -0.1445] | -1.6340, -1.7467, -1.7256 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: baron | -2.6722 [-3.0114, -2.3408] | -0.1543 [-0.1682, -0.1417] | -2.7437, -2.6211, -2.6517 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1605 [-2.3105, -2.0222] | -0.1553 [-0.1639, -0.1468] | -1.9562, -2.3126, -2.2127 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5246 [-0.5846, -0.4660] | -0.1430 [-0.1527, -0.1337] | -0.4762, -0.5297, -0.5679 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: macro | -1.7858 [-1.9116, -1.6628] | -0.1509 [-0.1583, -0.1438] | -1.7254, -1.8211, -1.8108 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: baron | -0.1175 [-0.2678, +0.0104] | +0.0003 [-0.0059, +0.0058] | -0.0766, -0.1533, -0.1226 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | -0.0001 [-0.0003, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: teamfight | -0.0136 [-0.0246, -0.0050] | -0.0026 [-0.0046, -0.0012] | -0.0076, -0.0204, -0.0127 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: macro | -0.0437 [-0.0944, -0.0006] | -0.0008 [-0.0030, +0.0011] | -0.0281, -0.0579, -0.0451 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: baron | -2.1255 [-2.3949, -1.8658] | -0.1551 [-0.1647, -0.1457] | -2.0846, -2.3452, -1.9467 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: dragon | -0.8346 [-0.9311, -0.7446] | -0.1439 [-0.1507, -0.1371] | -0.8433, -0.8129, -0.8477 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: teamfight | -0.3939 [-0.4403, -0.3484] | -0.1366 [-0.1438, -0.1294] | -0.3667, -0.4100, -0.4049 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: macro | -1.1180 [-1.2119, -1.0245] | -0.1452 [-0.1508, -0.1397] | -1.0982, -1.1894, -1.0664 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: baron | -2.2430 [-2.5237, -1.9887] | -0.1548 [-0.1672, -0.1431] | -2.1613, -2.4985, -2.0693 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: dragon | -0.8346 [-0.9311, -0.7446] | -0.1441 [-0.1508, -0.1371] | -0.8433, -0.8129, -0.8477 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.4075 [-0.4542, -0.3591] | -0.1392 [-0.1468, -0.1317] | -0.3744, -0.4304, -0.4176 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: macro | -1.1617 [-1.2612, -1.0648] | -0.1460 [-0.1523, -0.1399] | -1.1263, -1.2472, -1.1115 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_empirical-minus-uncapped_empirical: baron | -0.1993 [-0.4367, -0.0254] | -0.0021 [-0.0088, +0.0031] | -0.2146, -0.2452, -0.1380 |
| timely_independent: capped_empirical-minus-uncapped_empirical: dragon | +0.0101 [-0.0217, +0.0376] | -0.0014 [-0.0044, +0.0011] | +0.1000, -0.0348, -0.0348 |
| timely_independent: capped_empirical-minus-uncapped_empirical: teamfight | +0.0000 [-0.0382, +0.0337] | +0.0084 [+0.0012, +0.0147] | +0.0484, +0.0229, -0.0713 |
| timely_independent: capped_empirical-minus-uncapped_empirical: macro | -0.0630 [-0.1438, -0.0035] | +0.0016 [-0.0017, +0.0047] | -0.0221, -0.0857, -0.0813 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: baron | -2.5342 [-2.8422, -2.2473] | -0.1565 [-0.1659, -0.1474] | -2.4065, -2.4678, -2.7284 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: dragon | -2.1257 [-2.2714, -1.9866] | -0.1523 [-0.1604, -0.1440] | -2.1605, -2.1083, -2.1083 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5127 [-0.5700, -0.4520] | -0.1428 [-0.1517, -0.1346] | -0.5450, -0.5322, -0.4609 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: macro | -1.7242 [-1.8408, -1.6115] | -0.1505 [-0.1567, -0.1444] | -1.7040, -1.7028, -1.7659 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: baron | -2.7335 [-3.0789, -2.4143] | -0.1586 [-0.1712, -0.1480] | -2.6211, -2.7131, -2.8663 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.1156 [-2.2559, -1.9737] | -0.1538 [-0.1628, -0.1443] | -2.0605, -2.1431, -2.1431 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5127 [-0.5700, -0.4522] | -0.1344 [-0.1449, -0.1249] | -0.4966, -0.5093, -0.5322 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: macro | -1.7873 [-1.9188, -1.6670] | -0.1489 [-0.1563, -0.1419] | -1.7261, -1.7885, -1.8472 |
| timely_independent: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: baron | -0.2146 [-0.4964, +0.0202] | -0.0060 [-0.0155, +0.0016] | -0.2912, -0.2912, -0.0613 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: dragon | -0.0435 [-0.0759, -0.0172] | -0.0040 [-0.0059, -0.0023] | -0.0217, -0.0522, -0.0565 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: teamfight | -0.0348 [-0.0747, +0.0000] | +0.0004 [-0.0061, +0.0063] | -0.0764, -0.0127, -0.0153 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: macro | -0.0976 [-0.1926, -0.0176] | -0.0032 [-0.0073, +0.0001] | -0.1298, -0.1187, -0.0444 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: baron | -2.4678 [-2.7626, -2.1688] | -0.1518 [-0.1611, -0.1429] | -2.4831, -2.5598, -2.3605 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: dragon | -1.9779 [-2.1124, -1.8462] | -0.1424 [-0.1504, -0.1348] | -1.9475, -2.0257, -1.9605 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: teamfight | -0.5620 [-0.6238, -0.5010] | -0.1493 [-0.1584, -0.1407] | -0.5424, -0.5526, -0.5908 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: macro | -1.6692 [-1.7787, -1.5599] | -0.1478 [-0.1538, -0.1421] | -1.6577, -1.7127, -1.6373 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: baron | -2.6824 [-3.0613, -2.3472] | -0.1578 [-0.1719, -0.1452] | -2.7744, -2.8510, -2.4218 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: dragon | -2.0214 [-2.1557, -1.8866] | -0.1464 [-0.1549, -0.1381] | -1.9692, -2.0779, -2.0170 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.5968 [-0.6651, -0.5314] | -0.1489 [-0.1601, -0.1386] | -0.6188, -0.5653, -0.6061 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: macro | -1.7668 [-1.9022, -1.6434] | -0.1510 [-0.1586, -0.1439] | -1.7875, -1.8314, -1.6817 |
| timely_leagueews: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |

### Regional primary architecture results

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: uncapped_empirical: 1.0: baron | +0.1863 [-0.4298, +0.7726] | +0.0189 [-0.0007, +0.0396] | +0.0621, +0.0621, +0.4348 |
| europe: uncapped_empirical: 1.0: dragon | +0.2331 [-0.1301, +0.5811] | +0.0056 [-0.0111, +0.0229] | +0.0717, +0.4840, +0.1434 |
| europe: uncapped_empirical: 1.0: macro | +0.1910 [-0.0542, +0.4322] | +0.0059 [-0.0052, +0.0178] | +0.0747, +0.2756, +0.2228 |
| europe: uncapped_empirical: 1.0: teamfight | +0.1537 [-0.0133, +0.3175] | -0.0069 [-0.0300, +0.0165] | +0.0902, +0.2806, +0.0902 |
| europe: uncapped_empirical: mean: baron | +0.1087 [-0.3052, +0.5097] | +0.0063 [-0.0053, +0.0184] | +0.1708, -0.1863, +0.3416 |
| europe: uncapped_empirical: mean: dragon | +0.3197 [+0.0622, +0.5695] | -0.0049 [-0.0171, +0.0076] | +0.2958, +0.3451, +0.3182 |
| europe: uncapped_empirical: mean: macro | +0.1534 [-0.0078, +0.3110] | +0.0017 [-0.0056, +0.0091] | +0.1480, +0.0680, +0.2442 |
| europe: uncapped_empirical: mean: teamfight | +0.0317 [-0.0677, +0.1347] | +0.0039 [-0.0108, +0.0191] | -0.0225, +0.0451, +0.0727 |
| europe: capped_empirical: 1.0: baron | +0.2692 [-0.3363, +0.8325] | +0.0153 [-0.0022, +0.0338] | +0.0000, -0.1863, +0.9938 |
| europe: capped_empirical: 1.0: dragon | +0.2390 [-0.1198, +0.5856] | +0.0044 [-0.0120, +0.0211] | +0.0717, +0.5020, +0.1434 |
| europe: capped_empirical: 1.0: macro | +0.2184 [-0.0258, +0.4513] | -0.0045 [-0.0150, +0.0064] | +0.0239, +0.1620, +0.4693 |
| europe: capped_empirical: 1.0: teamfight | +0.1470 [-0.0268, +0.3143] | -0.0333 [-0.0556, -0.0113] | +0.0000, +0.1704, +0.2706 |
| europe: capped_empirical: mean: baron | +0.1605 [-0.2395, +0.5535] | +0.0074 [-0.0032, +0.0184] | +0.1863, -0.1708, +0.4658 |
| europe: capped_empirical: mean: dragon | +0.3182 [+0.0599, +0.5723] | -0.0049 [-0.0169, +0.0076] | +0.2913, +0.3496, +0.3137 |
| europe: capped_empirical: mean: macro | +0.1732 [+0.0177, +0.3299] | -0.0009 [-0.0079, +0.0061] | +0.1500, +0.0846, +0.2849 |
| europe: capped_empirical: mean: teamfight | +0.0409 [-0.0602, +0.1405] | -0.0053 [-0.0198, +0.0096] | -0.0276, +0.0752, +0.0752 |
| europe: capped_sequence: 1.0: baron | +0.2692 [-0.3363, +0.8325] | +0.0153 [-0.0022, +0.0338] | +0.0000, -0.1863, +0.9938 |
| europe: capped_sequence: 1.0: dragon | +0.2390 [-0.1198, +0.5856] | +0.0044 [-0.0120, +0.0211] | +0.0717, +0.5020, +0.1434 |
| europe: capped_sequence: 1.0: macro | +0.2184 [-0.0258, +0.4513] | -0.0045 [-0.0150, +0.0064] | +0.0239, +0.1620, +0.4693 |
| europe: capped_sequence: 1.0: teamfight | +0.1470 [-0.0268, +0.3143] | -0.0333 [-0.0556, -0.0113] | +0.0000, +0.1704, +0.2706 |
| europe: capped_sequence: mean: baron | +0.1605 [-0.2395, +0.5535] | +0.0074 [-0.0032, +0.0184] | +0.1863, -0.1708, +0.4658 |
| europe: capped_sequence: mean: dragon | +0.3182 [+0.0599, +0.5723] | -0.0049 [-0.0169, +0.0076] | +0.2913, +0.3496, +0.3137 |
| europe: capped_sequence: mean: macro | +0.1732 [+0.0177, +0.3299] | -0.0009 [-0.0079, +0.0061] | +0.1500, +0.0846, +0.2849 |
| europe: capped_sequence: mean: teamfight | +0.0409 [-0.0602, +0.1405] | -0.0053 [-0.0198, +0.0096] | -0.0276, +0.0752, +0.0752 |
| europe: capped_kl_sequence: 1.0: baron | -0.1656 [-0.7247, +0.3739] | -0.0044 [-0.0220, +0.0133] | -0.3727, -0.3727, +0.2484 |
| europe: capped_kl_sequence: 1.0: dragon | +0.2928 [-0.0909, +0.6665] | -0.0198 [-0.0382, -0.0016] | -0.1793, +0.4303, +0.6275 |
| europe: capped_kl_sequence: 1.0: macro | +0.0558 [-0.1690, +0.2795] | +0.0001 [-0.0110, +0.0112] | -0.1907, +0.0192, +0.3387 |
| europe: capped_kl_sequence: 1.0: teamfight | +0.0401 [-0.1137, +0.1901] | +0.0247 [+0.0033, +0.0469] | -0.0200, +0.0000, +0.1403 |
| europe: capped_kl_sequence: mean: baron | -0.0828 [-0.4764, +0.2998] | -0.0044 [-0.0142, +0.0050] | -0.0155, -0.2329, +0.0000 |
| europe: capped_kl_sequence: mean: dragon | +0.3869 [+0.1352, +0.6267] | -0.0065 [-0.0186, +0.0059] | +0.0852, +0.5423, +0.5333 |
| europe: capped_kl_sequence: mean: macro | +0.0969 [-0.0615, +0.2548] | +0.0002 [-0.0063, +0.0069] | +0.0023, +0.0948, +0.1937 |
| europe: capped_kl_sequence: mean: teamfight | -0.0134 [-0.1017, +0.0730] | +0.0116 [-0.0011, +0.0243] | -0.0626, -0.0251, +0.0476 |
| americas: uncapped_empirical: 1.0: baron | +0.8584 [+0.2449, +1.4572] | +0.0078 [-0.0133, +0.0282] | +0.7971, +1.3489, +0.4292 |
| americas: uncapped_empirical: 1.0: dragon | +0.1507 [-0.1711, +0.4654] | -0.0200 [-0.0380, -0.0020] | -0.1217, +0.3304, +0.2434 |
| americas: uncapped_empirical: 1.0: macro | +0.4031 [+0.1705, +0.6391] | -0.0009 [-0.0130, +0.0109] | +0.2896, +0.6888, +0.2310 |
| americas: uncapped_empirical: 1.0: teamfight | +0.2003 [+0.0437, +0.3566] | +0.0096 [-0.0138, +0.0353] | +0.1935, +0.3871, +0.0204 |
| americas: uncapped_empirical: mean: baron | +0.5620 [+0.1535, +0.9636] | -0.0082 [-0.0206, +0.0036] | +0.5212, +0.8124, +0.3525 |
| americas: uncapped_empirical: mean: dragon | +0.4535 [+0.2066, +0.7075] | +0.0037 [-0.0091, +0.0157] | +0.3304, +0.4912, +0.5390 |
| americas: uncapped_empirical: mean: macro | +0.4028 [+0.2378, +0.5542] | +0.0024 [-0.0049, +0.0097] | +0.3501, +0.4999, +0.3583 |
| americas: uncapped_empirical: mean: teamfight | +0.1927 [+0.0936, +0.2940] | +0.0117 [-0.0034, +0.0273] | +0.1986, +0.1961, +0.1834 |
| americas: capped_empirical: 1.0: baron | +0.7153 [+0.0820, +1.3528] | +0.0138 [-0.0053, +0.0324] | +0.7971, +1.0423, +0.3066 |
| americas: capped_empirical: 1.0: dragon | +0.1623 [-0.1552, +0.4693] | -0.0249 [-0.0429, -0.0076] | -0.1565, +0.3478, +0.2956 |
| americas: capped_empirical: 1.0: macro | +0.3265 [+0.0911, +0.5735] | -0.0084 [-0.0204, +0.0033] | +0.2067, +0.5347, +0.2381 |
| americas: capped_empirical: 1.0: teamfight | +0.1019 [-0.0544, +0.2550] | -0.0142 [-0.0373, +0.0100] | -0.0204, +0.2139, +0.1121 |
| americas: capped_empirical: mean: baron | +0.5160 [+0.1132, +0.9168] | -0.0053 [-0.0168, +0.0056] | +0.5212, +0.6898, +0.3372 |
| americas: capped_empirical: mean: dragon | +0.4593 [+0.2208, +0.7118] | +0.0017 [-0.0109, +0.0136] | +0.3260, +0.4999, +0.5521 |
| americas: capped_empirical: mean: macro | +0.3778 [+0.2118, +0.5318] | -0.0012 [-0.0083, +0.0059] | +0.3333, +0.4619, +0.3380 |
| americas: capped_empirical: mean: teamfight | +0.1579 [+0.0601, +0.2571] | -0.0001 [-0.0143, +0.0143] | +0.1528, +0.1961, +0.1248 |
| americas: capped_sequence: 1.0: baron | +0.7153 [+0.0820, +1.3528] | +0.0138 [-0.0053, +0.0324] | +0.7971, +1.0423, +0.3066 |
| americas: capped_sequence: 1.0: dragon | +0.1623 [-0.1552, +0.4693] | -0.0249 [-0.0429, -0.0076] | -0.1565, +0.3478, +0.2956 |
| americas: capped_sequence: 1.0: macro | +0.3265 [+0.0911, +0.5735] | -0.0084 [-0.0204, +0.0033] | +0.2067, +0.5347, +0.2381 |
| americas: capped_sequence: 1.0: teamfight | +0.1019 [-0.0544, +0.2550] | -0.0142 [-0.0373, +0.0100] | -0.0204, +0.2139, +0.1121 |
| americas: capped_sequence: mean: baron | +0.5160 [+0.1132, +0.9168] | -0.0053 [-0.0168, +0.0056] | +0.5212, +0.6898, +0.3372 |
| americas: capped_sequence: mean: dragon | +0.4593 [+0.2208, +0.7118] | +0.0017 [-0.0109, +0.0136] | +0.3260, +0.4999, +0.5521 |
| americas: capped_sequence: mean: macro | +0.3778 [+0.2118, +0.5318] | -0.0012 [-0.0083, +0.0059] | +0.3333, +0.4619, +0.3380 |
| americas: capped_sequence: mean: teamfight | +0.1579 [+0.0601, +0.2571] | -0.0001 [-0.0143, +0.0143] | +0.1528, +0.1961, +0.1248 |
| americas: capped_kl_sequence: 1.0: baron | +0.6540 [+0.0203, +1.2736] | -0.0024 [-0.0220, +0.0171] | +0.8584, +0.6744, +0.4292 |
| americas: capped_kl_sequence: 1.0: dragon | +0.3420 [-0.0058, +0.6933] | -0.0098 [-0.0280, +0.0089] | -0.5738, +0.9737, +0.6260 |
| americas: capped_kl_sequence: 1.0: macro | +0.4146 [+0.1646, +0.6519] | +0.0025 [-0.0083, +0.0136] | +0.1763, +0.6445, +0.4230 |
| americas: capped_kl_sequence: 1.0: teamfight | +0.2479 [+0.0989, +0.3946] | +0.0198 [-0.0013, +0.0411] | +0.2445, +0.2852, +0.2139 |
| americas: capped_kl_sequence: mean: baron | +0.3679 [-0.0104, +0.7566] | -0.0179 [-0.0282, -0.0080] | +0.4905, +0.3985, +0.2146 |
| americas: capped_kl_sequence: mean: dragon | +0.5202 [+0.2818, +0.7778] | +0.0121 [-0.0001, +0.0233] | +0.1130, +0.8216, +0.6260 |
| americas: capped_kl_sequence: mean: macro | +0.3523 [+0.1983, +0.5036] | +0.0004 [-0.0061, +0.0067] | +0.2530, +0.4559, +0.3481 |
| americas: capped_kl_sequence: mean: teamfight | +0.1689 [+0.0771, +0.2596] | +0.0071 [-0.0054, +0.0198] | +0.1553, +0.1477, +0.2037 |
## 20-60-second warnings

### uncapped_empirical, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 20.063 / 0.6173 | 21.469 / 0.5881 | 4.933 / 0.5751 | 15.488 / 0.5935 |
| timely_equal_tcn | 18.320 / 0.6106 | 21.083 / 0.5856 | 4.683 / 0.5617 | 14.695 / 0.5860 |
| timely_equal_gru | 14.947 / 0.5874 | 4.543 / 0.5940 | 3.999 / 0.5755 | 7.829 / 0.5856 |
| timely_independent | 20.714 / 0.5942 | 21.293 / 0.5915 | 4.764 / 0.5707 | 15.590 / 0.5855 |
| timely_leagueews | 18.731 / 0.6118 | 21.477 / 0.5923 | 4.901 / 0.5730 | 15.037 / 0.5923 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +5.1167 [+4.2425, +6.0380] | +0.0298 [+0.0061, +0.0517] | +4.7208, +4.1422, +6.4872 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +16.9263 [+16.3394, +17.5255] | -0.0059 [-0.0339, +0.0224] | +17.2279, +17.1639, +16.3871 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.9337 [+0.7081, +1.1464] | -0.0004 [-0.0223, +0.0225] | +0.8424, +0.7957, +1.1632 |
| timely_equal_sum-minus-timely_equal_gru: macro | +7.6589 [+7.2788, +8.0450] | +0.0079 [-0.0081, +0.0240] | +7.5970, +7.3673, +8.0125 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +1.7433 [+1.2429, +2.2517] | +0.0067 [-0.0037, +0.0164] | +1.5196, +1.5890, +2.1213 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.3862 [+0.2302, +0.5529] | +0.0025 [-0.0043, +0.0090] | +0.5649, +0.4480, +0.1456 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.2501 [+0.1476, +0.3536] | +0.0133 [+0.0030, +0.0239] | +0.2892, +0.1465, +0.3145 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.7932 [+0.6181, +0.9871] | +0.0075 [+0.0020, +0.0126] | +0.7912, +0.7278, +0.8605 |
| timely_equal_sum-minus-timely_independent: baron | -0.6505 [-1.3357, +0.0559] | +0.0231 [+0.0101, +0.0353] | +0.0849, -1.2110, -0.8254 |
| timely_equal_sum-minus-timely_independent: dragon | +0.1758 [+0.0052, +0.3338] | -0.0034 [-0.0098, +0.0033] | +0.3111, -0.0221, +0.2383 |
| timely_equal_sum-minus-timely_independent: teamfight | +0.1684 [+0.0282, +0.3064] | +0.0043 [-0.0086, +0.0176] | +0.1313, +0.1478, +0.2261 |
| timely_equal_sum-minus-timely_independent: macro | -0.1021 [-0.3381, +0.1427] | +0.0080 [+0.0016, +0.0138] | +0.1758, -0.3618, -0.1203 |
| timely_equal_sum-minus-timely_leagueews: baron | +1.3319 [+0.9630, +1.6913] | +0.0055 [-0.0018, +0.0124] | +1.1031, +1.5350, +1.3576 |
| timely_equal_sum-minus-timely_leagueews: dragon | -0.0081 [-0.1082, +0.1001] | -0.0041 [-0.0080, +0.0000] | +0.0066, -0.0397, +0.0088 |
| timely_equal_sum-minus-timely_leagueews: teamfight | +0.0316 [-0.0306, +0.0934] | +0.0021 [-0.0043, +0.0086] | -0.0669, +0.0316, +0.1301 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.4518 [+0.3235, +0.5814] | +0.0011 [-0.0026, +0.0047] | +0.3476, +0.5090, +0.4988 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +3.3734 [+2.5294, +4.2145] | +0.0231 [-0.0005, +0.0451] | +3.2012, +2.5532, +4.3659 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +16.5401 [+15.9537, +17.1452] | -0.0083 [-0.0353, +0.0199] | +16.6630, +16.7160, +16.2415 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.6837 [+0.4584, +0.9019] | -0.0138 [-0.0347, +0.0065] | +0.5532, +0.6492, +0.8487 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +6.8658 [+6.5057, +7.2195] | +0.0004 [-0.0144, +0.0161] | +6.8058, +6.6394, +7.1520 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.4226 [+0.1865, +0.6645] | -0.0030 [-0.0088, +0.0029] | +0.0831, +0.6631, +0.5215 |
| 0.5 | +0.7309 [+0.4703, +0.9855] | +0.0033 [-0.0036, +0.0104] | +0.6484, +0.9780, +0.5662 |
| 0.75 | +0.8858 [+0.6458, +1.1458] | +0.0090 [+0.0010, +0.0169] | +1.1932, +0.2118, +1.2524 |
| 1.0 | +1.1335 [+0.8685, +1.4119] | +0.0207 [+0.0115, +0.0293] | +1.2403, +1.0585, +1.1017 |
### capped_empirical, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 19.994 / 0.6192 | 21.327 / 0.5843 | 4.914 / 0.5739 | 15.411 / 0.5925 |
| timely_equal_tcn | 18.245 / 0.6079 | 21.120 / 0.5896 | 4.768 / 0.5730 | 14.711 / 0.5902 |
| timely_equal_gru | 14.952 / 0.5886 | 4.543 / 0.5940 | 4.018 / 0.5781 | 7.837 / 0.5869 |
| timely_independent | 20.631 / 0.5998 | 21.240 / 0.5908 | 4.798 / 0.5787 | 15.557 / 0.5898 |
| timely_leagueews | 18.662 / 0.6173 | 21.386 / 0.5915 | 4.883 / 0.5696 | 14.977 / 0.5928 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +5.0422 [+4.1985, +5.9433] | +0.0306 [+0.0090, +0.0506] | +4.5125, +4.2811, +6.3329 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +16.7836 [+16.1850, +17.3863] | -0.0096 [-0.0375, +0.0183] | +17.1110, +17.0050, +16.2349 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.8958 [+0.6802, +1.1005] | -0.0041 [-0.0255, +0.0170] | +0.8045, +0.7565, +1.1265 |
| timely_equal_sum-minus-timely_equal_gru: macro | +7.5739 [+7.2107, +7.9386] | +0.0056 [-0.0093, +0.0208] | +7.4760, +7.3475, +7.8981 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +1.7484 [+1.2595, +2.2601] | +0.0114 [+0.0022, +0.0201] | +1.5042, +1.8050, +1.9361 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.2067 [+0.0550, +0.3698] | -0.0053 [-0.0119, +0.0009] | +0.4038, +0.2935, -0.0772 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1461 [+0.0526, +0.2441] | +0.0009 [-0.0087, +0.0108] | +0.2084, +0.0720, +0.1579 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.7004 [+0.5334, +0.8912] | +0.0023 [-0.0026, +0.0070] | +0.7055, +0.7235, +0.6723 |
| timely_equal_sum-minus-timely_independent: baron | -0.6377 [-1.3207, +0.0661] | +0.0194 [+0.0076, +0.0308] | -0.0386, -0.9642, -0.9102 |
| timely_equal_sum-minus-timely_independent: dragon | +0.0861 [-0.0861, +0.2483] | -0.0064 [-0.0129, +0.0001] | +0.2692, -0.1920, +0.1810 |
| timely_equal_sum-minus-timely_independent: teamfight | +0.1153 [-0.0138, +0.2386] | -0.0048 [-0.0170, +0.0074] | +0.1945, -0.0467, +0.1983 |
| timely_equal_sum-minus-timely_independent: macro | -0.1454 [-0.3824, +0.1004] | +0.0027 [-0.0032, +0.0082] | +0.1417, -0.4010, -0.1770 |
| timely_equal_sum-minus-timely_leagueews: baron | +1.3319 [+0.9699, +1.6951] | +0.0019 [-0.0049, +0.0082] | +1.2882, +1.3268, +1.3807 |
| timely_equal_sum-minus-timely_leagueews: dragon | -0.0596 [-0.1605, +0.0482] | -0.0072 [-0.0111, -0.0031] | +0.0132, -0.1743, -0.0177 |
| timely_equal_sum-minus-timely_leagueews: teamfight | +0.0303 [-0.0281, +0.0923] | +0.0044 [-0.0018, +0.0106] | +0.0417, -0.0530, +0.1023 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.4342 [+0.3082, +0.5596] | -0.0003 [-0.0038, +0.0032] | +0.4477, +0.3665, +0.4885 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +3.2937 [+2.4850, +4.1181] | +0.0192 [-0.0018, +0.0394] | +3.0083, +2.4761, +4.3968 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +16.5769 [+15.9951, +17.1812] | -0.0043 [-0.0310, +0.0240] | +16.7071, +16.7115, +16.3121 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.7498 [+0.5311, +0.9713] | -0.0051 [-0.0258, +0.0152] | +0.5961, +0.6845, +0.9687 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +6.8735 [+6.5276, +7.2210] | +0.0033 [-0.0112, +0.0179] | +6.7705, +6.6240, +7.2259 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.4147 [+0.1767, +0.6579] | -0.0029 [-0.0086, +0.0030] | +0.0695, +0.6546, +0.5199 |
| 0.5 | +0.6878 [+0.4362, +0.9380] | +0.0010 [-0.0059, +0.0077] | +0.7199, +0.9276, +0.4160 |
| 0.75 | +0.6647 [+0.4208, +0.9277] | -0.0027 [-0.0103, +0.0047] | +0.9106, +0.4283, +0.6552 |
| 1.0 | +1.0344 [+0.7710, +1.3051] | +0.0139 [+0.0055, +0.0220] | +1.1218, +0.8835, +1.0979 |
### capped_sequence, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 19.994 / 0.6192 | 21.327 / 0.5843 | 4.914 / 0.5739 | 15.411 / 0.5925 |
| timely_equal_tcn | 18.245 / 0.6079 | 21.120 / 0.5896 | 4.768 / 0.5730 | 14.711 / 0.5902 |
| timely_equal_gru | 14.952 / 0.5886 | 4.543 / 0.5940 | 4.018 / 0.5781 | 7.837 / 0.5869 |
| timely_independent | 20.631 / 0.5998 | 21.240 / 0.5908 | 4.798 / 0.5787 | 15.557 / 0.5898 |
| timely_leagueews | 18.662 / 0.6173 | 21.386 / 0.5915 | 4.883 / 0.5696 | 14.977 / 0.5928 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +5.0422 [+4.1985, +5.9433] | +0.0306 [+0.0090, +0.0506] | +4.5125, +4.2811, +6.3329 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +16.7836 [+16.1850, +17.3863] | -0.0096 [-0.0375, +0.0183] | +17.1110, +17.0050, +16.2349 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.8958 [+0.6802, +1.1005] | -0.0041 [-0.0255, +0.0170] | +0.8045, +0.7565, +1.1265 |
| timely_equal_sum-minus-timely_equal_gru: macro | +7.5739 [+7.2107, +7.9386] | +0.0056 [-0.0093, +0.0208] | +7.4760, +7.3475, +7.8981 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +1.7484 [+1.2595, +2.2601] | +0.0114 [+0.0022, +0.0201] | +1.5042, +1.8050, +1.9361 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.2067 [+0.0550, +0.3698] | -0.0053 [-0.0119, +0.0009] | +0.4038, +0.2935, -0.0772 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.1461 [+0.0526, +0.2441] | +0.0009 [-0.0087, +0.0108] | +0.2084, +0.0720, +0.1579 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.7004 [+0.5334, +0.8912] | +0.0023 [-0.0026, +0.0070] | +0.7055, +0.7235, +0.6723 |
| timely_equal_sum-minus-timely_independent: baron | -0.6377 [-1.3207, +0.0661] | +0.0194 [+0.0076, +0.0308] | -0.0386, -0.9642, -0.9102 |
| timely_equal_sum-minus-timely_independent: dragon | +0.0861 [-0.0861, +0.2483] | -0.0064 [-0.0129, +0.0001] | +0.2692, -0.1920, +0.1810 |
| timely_equal_sum-minus-timely_independent: teamfight | +0.1153 [-0.0138, +0.2386] | -0.0048 [-0.0170, +0.0074] | +0.1945, -0.0467, +0.1983 |
| timely_equal_sum-minus-timely_independent: macro | -0.1454 [-0.3824, +0.1004] | +0.0027 [-0.0032, +0.0082] | +0.1417, -0.4010, -0.1770 |
| timely_equal_sum-minus-timely_leagueews: baron | +1.3319 [+0.9699, +1.6951] | +0.0019 [-0.0049, +0.0082] | +1.2882, +1.3268, +1.3807 |
| timely_equal_sum-minus-timely_leagueews: dragon | -0.0596 [-0.1605, +0.0482] | -0.0072 [-0.0111, -0.0031] | +0.0132, -0.1743, -0.0177 |
| timely_equal_sum-minus-timely_leagueews: teamfight | +0.0303 [-0.0281, +0.0923] | +0.0044 [-0.0018, +0.0106] | +0.0417, -0.0530, +0.1023 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.4342 [+0.3082, +0.5596] | -0.0003 [-0.0038, +0.0032] | +0.4477, +0.3665, +0.4885 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +3.2937 [+2.4850, +4.1181] | +0.0192 [-0.0018, +0.0394] | +3.0083, +2.4761, +4.3968 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +16.5769 [+15.9951, +17.1812] | -0.0043 [-0.0310, +0.0240] | +16.7071, +16.7115, +16.3121 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.7498 [+0.5311, +0.9713] | -0.0051 [-0.0258, +0.0152] | +0.5961, +0.6845, +0.9687 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +6.8735 [+6.5276, +7.2210] | +0.0033 [-0.0112, +0.0179] | +6.7705, +6.6240, +7.2259 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.4147 [+0.1767, +0.6579] | -0.0029 [-0.0086, +0.0030] | +0.0695, +0.6546, +0.5199 |
| 0.5 | +0.6878 [+0.4362, +0.9380] | +0.0010 [-0.0059, +0.0077] | +0.7199, +0.9276, +0.4160 |
| 0.75 | +0.6647 [+0.4208, +0.9277] | -0.0027 [-0.0103, +0.0047] | +0.9106, +0.4283, +0.6552 |
| 1.0 | +1.0344 [+0.7710, +1.3051] | +0.0139 [+0.0055, +0.0220] | +1.1218, +0.8835, +1.0979 |
### capped_kl_sequence, four-budget mean

| Model | Baron recall / burden | Dragon recall / burden | Teamfight recall / burden | Macro recall / burden |
|---|---:|---:|---:|---:|
| timely_equal_sum | 15.661 / 0.4683 | 17.615 / 0.4439 | 3.847 / 0.4309 | 12.374 / 0.4477 |
| timely_equal_tcn | 14.422 / 0.4704 | 17.316 / 0.4435 | 3.755 / 0.4331 | 11.831 / 0.4490 |
| timely_equal_gru | 11.321 / 0.4416 | 3.362 / 0.4529 | 3.099 / 0.4352 | 5.928 / 0.4432 |
| timely_independent | 16.435 / 0.4487 | 17.529 / 0.4465 | 3.665 / 0.4258 | 12.543 / 0.4403 |
| timely_leagueews | 14.635 / 0.4716 | 17.504 / 0.4419 | 3.871 / 0.4311 | 12.003 / 0.4482 |

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum-minus-timely_equal_gru: baron | +4.3402 [+3.5450, +5.1758] | +0.0266 [+0.0068, +0.0457] | +4.0882, +3.8954, +5.0370 |
| timely_equal_sum-minus-timely_equal_gru: dragon | +14.2525 [+13.7044, +14.7959] | -0.0090 [-0.0335, +0.0158] | +14.4496, +14.6284, +13.6795 |
| timely_equal_sum-minus-timely_equal_gru: teamfight | +0.7472 [+0.5504, +0.9415] | -0.0043 [-0.0229, +0.0144] | +0.7262, +0.6504, +0.8651 |
| timely_equal_sum-minus-timely_equal_gru: macro | +6.4467 [+6.1062, +6.7974] | +0.0044 [-0.0089, +0.0181] | +6.4214, +6.3914, +6.5272 |
| timely_equal_sum-minus-timely_equal_tcn: baron | +1.2393 [+0.7708, +1.7287] | -0.0021 [-0.0113, +0.0064] | +1.2265, +1.3730, +1.1185 |
| timely_equal_sum-minus-timely_equal_tcn: dragon | +0.2986 [+0.1519, +0.4588] | +0.0004 [-0.0052, +0.0061] | +0.5693, +0.3884, -0.0618 |
| timely_equal_sum-minus-timely_equal_tcn: teamfight | +0.0918 [+0.0000, +0.1789] | -0.0022 [-0.0106, +0.0062] | +0.1591, -0.0669, +0.1831 |
| timely_equal_sum-minus-timely_equal_tcn: macro | +0.5432 [+0.3795, +0.7193] | -0.0013 [-0.0059, +0.0031] | +0.6516, +0.5648, +0.4133 |
| timely_equal_sum-minus-timely_independent: baron | -0.7739 [-1.3986, -0.1320] | +0.0196 [+0.0081, +0.0304] | -0.1388, -0.9565, -1.2265 |
| timely_equal_sum-minus-timely_independent: dragon | +0.0861 [-0.0562, +0.2315] | -0.0026 [-0.0084, +0.0031] | +0.2714, -0.0265, +0.0132 |
| timely_equal_sum-minus-timely_independent: teamfight | +0.1819 [+0.0636, +0.3011] | +0.0051 [-0.0061, +0.0161] | +0.1516, +0.0644, +0.3296 |
| timely_equal_sum-minus-timely_independent: macro | -0.1687 [-0.3936, +0.0617] | +0.0074 [+0.0019, +0.0127] | +0.0947, -0.3062, -0.2945 |
| timely_equal_sum-minus-timely_leagueews: baron | +1.0259 [+0.6912, +1.3593] | -0.0033 [-0.0096, +0.0028] | +1.2573, +1.1108, +0.7097 |
| timely_equal_sum-minus-timely_leagueews: dragon | +0.1111 [+0.0139, +0.2072] | +0.0020 [-0.0016, +0.0057] | +0.0971, +0.0971, +0.1390 |
| timely_equal_sum-minus-timely_leagueews: teamfight | -0.0240 [-0.0782, +0.0340] | -0.0002 [-0.0056, +0.0050] | -0.1288, -0.0202, +0.0770 |
| timely_equal_sum-minus-timely_leagueews: macro | +0.3710 [+0.2545, +0.4904] | -0.0005 [-0.0035, +0.0024] | +0.4085, +0.3959, +0.3086 |
| timely_equal_tcn-minus-timely_equal_gru: baron | +3.1009 [+2.3215, +3.8599] | +0.0288 [+0.0099, +0.0477] | +2.8618, +2.5224, +3.9185 |
| timely_equal_tcn-minus-timely_equal_gru: dragon | +13.9539 [+13.4119, +14.5139] | -0.0094 [-0.0329, +0.0157] | +13.8803, +14.2400, +13.7413 |
| timely_equal_tcn-minus-timely_equal_gru: teamfight | +0.6555 [+0.4547, +0.8599] | -0.0021 [-0.0198, +0.0158] | +0.5671, +0.7174, +0.6820 |
| timely_equal_tcn-minus-timely_equal_gru: macro | +5.9034 [+5.5690, +6.2266] | +0.0058 [-0.0068, +0.0184] | +5.7697, +5.8266, +6.1139 |

Primary architecture contrast by budget:

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| 0.25 | +0.2488 [+0.0325, +0.4690] | +0.0020 [-0.0031, +0.0071] | +0.2029, +0.5791, -0.0356 |
| 0.5 | +0.6291 [+0.3979, +0.8662] | -0.0019 [-0.0085, +0.0042] | +0.6315, +0.7651, +0.4906 |
| 0.75 | +0.5783 [+0.3377, +0.8424] | -0.0056 [-0.0126, +0.0013] | +0.9928, +0.3512, +0.3909 |
| 1.0 | +0.7168 [+0.4546, +0.9837] | +0.0002 [-0.0076, +0.0076] | +0.7794, +0.5639, +0.8072 |
### overall: every within-model policy effect, four-budget mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: baron | -0.0694 [-0.2823, +0.1144] | +0.0019 [-0.0034, +0.0069] | -0.0617, +0.0309, -0.1774 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: dragon | -0.1427 [-0.1803, -0.1100] | -0.0038 [-0.0051, -0.0027] | -0.1170, -0.1589, -0.1523 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: teamfight | -0.0189 [-0.0765, +0.0309] | -0.0011 [-0.0072, +0.0042] | +0.0139, -0.0985, +0.0278 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: macro | -0.0770 [-0.1496, -0.0108] | -0.0010 [-0.0038, +0.0017] | -0.0549, -0.0755, -0.1006 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: baron | -4.3325 [-4.6014, -4.0711] | -0.1509 [-0.1573, -0.1449] | -4.1962, -4.0651, -4.7362 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: dragon | -3.7117 [-3.8492, -3.5866] | -0.1404 [-0.1456, -0.1354] | -3.7956, -3.5308, -3.8088 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0672 [-1.1248, -1.0117] | -0.1431 [-0.1491, -0.1370] | -1.0861, -1.0268, -1.0887 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: macro | -3.0371 [-3.1374, -2.9360] | -0.1448 [-0.1488, -0.1411] | -3.0260, -2.8742, -3.2112 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: baron | -4.4019 [-4.6861, -4.1276] | -0.1490 [-0.1572, -0.1410] | -4.2579, -4.0342, -4.9136 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.8544 [-3.9898, -3.7305] | -0.1442 [-0.1497, -0.1389] | -3.9125, -3.6896, -3.9611 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0861 [-1.1590, -1.0190] | -0.1442 [-0.1527, -0.1364] | -1.0722, -1.1253, -1.0609 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: macro | -3.1142 [-3.2226, -3.0101] | -0.1458 [-0.1510, -0.1410] | -3.0809, -2.9497, -3.3119 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: baron | -0.0746 [-0.2737, +0.0993] | -0.0027 [-0.0087, +0.0025] | -0.0463, -0.1851, +0.0077 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: dragon | +0.0368 [+0.0044, +0.0680] | +0.0040 [+0.0028, +0.0051] | +0.0441, -0.0044, +0.0706 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: teamfight | +0.0850 [+0.0478, +0.1204] | +0.0113 [+0.0071, +0.0152] | +0.0947, -0.0240, +0.1844 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: macro | +0.0158 [-0.0523, +0.0774] | +0.0042 [+0.0016, +0.0065] | +0.0309, -0.0712, +0.0876 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: baron | -3.8234 [-4.0631, -3.5842] | -0.1375 [-0.1437, -0.1316] | -3.9185, -3.6331, -3.9185 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: dragon | -3.8037 [-3.9360, -3.6765] | -0.1461 [-0.1513, -0.1411] | -3.9611, -3.6257, -3.8243 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0129 [-1.0673, -0.9597] | -0.1399 [-0.1456, -0.1341] | -1.0369, -0.8879, -1.1139 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: macro | -2.8800 [-2.9763, -2.7860] | -0.1412 [-0.1451, -0.1376] | -2.9722, -2.7155, -2.9522 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: baron | -3.8980 [-4.1744, -3.6422] | -0.1402 [-0.1485, -0.1325] | -3.9648, -3.8183, -3.9108 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.7669 [-3.8976, -3.6406] | -0.1421 [-0.1474, -0.1371] | -3.9169, -3.6301, -3.7536 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.9278 [-0.9848, -0.8737] | -0.1286 [-0.1353, -0.1219] | -0.9422, -0.9118, -0.9295 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: macro | -2.8642 [-2.9657, -2.7646] | -0.1370 [-0.1416, -0.1326] | -2.9413, -2.7867, -2.8647 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: baron | +0.0051 [-0.1200, +0.1250] | +0.0012 [-0.0024, +0.0044] | +0.1466, -0.1080, -0.0231 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: teamfight | +0.0189 [-0.0021, +0.0373] | +0.0026 [-0.0003, +0.0051] | +0.0518, -0.0594, +0.0644 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: macro | +0.0080 [-0.0364, +0.0474] | +0.0013 [-0.0003, +0.0026] | +0.0661, -0.0558, +0.0138 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: baron | -3.6306 [-3.8721, -3.3764] | -0.1470 [-0.1537, -0.1408] | -3.7720, -3.6794, -3.4403 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: dragon | -1.1806 [-1.2547, -1.1098] | -0.1410 [-0.1452, -0.1370] | -1.1343, -1.1541, -1.2534 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: teamfight | -0.9186 [-0.9742, -0.8671] | -0.1429 [-0.1487, -0.1373] | -1.0078, -0.9207, -0.8272 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: macro | -1.9099 [-1.9959, -1.8192] | -0.1436 [-0.1474, -0.1400] | -1.9714, -1.9181, -1.8403 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: baron | -3.6254 [-3.8882, -3.3632] | -0.1458 [-0.1535, -0.1386] | -3.6254, -3.7874, -3.4634 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: dragon | -1.1806 [-1.2547, -1.1098] | -0.1410 [-0.1452, -0.1370] | -1.1343, -1.1541, -1.2534 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.8996 [-0.9550, -0.8482] | -0.1403 [-0.1466, -0.1341] | -0.9560, -0.9800, -0.7628 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: macro | -1.9019 [-1.9916, -1.8085] | -0.1424 [-0.1464, -0.1385] | -1.9052, -1.9739, -1.8266 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_empirical-minus-uncapped_empirical: baron | -0.0823 [-0.2886, +0.1127] | +0.0056 [+0.0003, +0.0104] | +0.0617, -0.2160, -0.0926 |
| timely_independent: capped_empirical-minus-uncapped_empirical: dragon | -0.0530 [-0.0862, -0.0228] | -0.0008 [-0.0018, +0.0002] | -0.0750, +0.0110, -0.0949 |
| timely_independent: capped_empirical-minus-uncapped_empirical: teamfight | +0.0341 [-0.0320, +0.0928] | +0.0080 [+0.0006, +0.0149] | -0.0493, +0.0960, +0.0556 |
| timely_independent: capped_empirical-minus-uncapped_empirical: macro | -0.0337 [-0.1093, +0.0357] | +0.0043 [+0.0012, +0.0071] | -0.0209, -0.0363, -0.0440 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: baron | -4.1962 [-4.4464, -3.9420] | -0.1511 [-0.1577, -0.1443] | -4.0960, -4.0728, -4.4199 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: dragon | -3.7117 [-3.8521, -3.5830] | -0.1443 [-0.1494, -0.1389] | -3.7978, -3.6963, -3.6411 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: teamfight | -1.1337 [-1.1898, -1.0758] | -0.1529 [-0.1593, -0.1468] | -1.0432, -1.1379, -1.2200 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: macro | -3.0139 [-3.1085, -2.9190] | -0.1494 [-0.1537, -0.1454] | -2.9790, -2.9690, -3.0937 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: baron | -4.2785 [-4.5606, -4.0061] | -0.1455 [-0.1539, -0.1374] | -4.0342, -4.2888, -4.5125 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.7647 [-3.9049, -3.6345] | -0.1450 [-0.1503, -0.1395] | -3.8728, -3.6852, -3.7360 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0996 [-1.1746, -1.0264] | -0.1450 [-0.1543, -0.1362] | -1.0924, -1.0419, -1.1644 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: macro | -3.0476 [-3.1554, -2.9486] | -0.1452 [-0.1504, -0.1402] | -2.9998, -3.0053, -3.1376 |
| timely_independent: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: baron | -0.0694 [-0.2882, +0.1310] | +0.0056 [+0.0001, +0.0106] | -0.2468, +0.2391, -0.2006 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: dragon | -0.0912 [-0.1301, -0.0580] | -0.0007 [-0.0021, +0.0005] | -0.1236, -0.0243, -0.1258 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: teamfight | -0.0177 [-0.0732, +0.0296] | -0.0034 [-0.0100, +0.0024] | -0.0947, -0.0139, +0.0556 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: macro | -0.0594 [-0.1369, +0.0107] | +0.0005 [-0.0027, +0.0032] | -0.1550, +0.0670, -0.0903 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: baron | -4.0265 [-4.2754, -3.7793] | -0.1458 [-0.1521, -0.1396] | -4.1654, -3.8491, -4.0651 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: dragon | -3.8824 [-4.0165, -3.7537] | -0.1496 [-0.1549, -0.1441] | -3.8794, -3.8022, -3.9655 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0129 [-1.0685, -0.9596] | -0.1385 [-0.1445, -0.1324] | -0.9156, -1.0596, -1.0634 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: macro | -2.9739 [-3.0722, -2.8739] | -0.1446 [-0.1487, -0.1407] | -2.9868, -2.9036, -3.0313 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: baron | -4.0960 [-4.3878, -3.8221] | -0.1402 [-0.1487, -0.1318] | -4.4122, -3.6100, -4.2657 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.9736 [-4.1102, -3.8446] | -0.1503 [-0.1559, -0.1447] | -4.0030, -3.8265, -4.0913 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0306 [-1.1003, -0.9653] | -0.1419 [-0.1507, -0.1336] | -1.0104, -1.0735, -1.0078 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: macro | -3.0334 [-3.1456, -2.9292] | -0.1441 [-0.1492, -0.1391] | -3.1419, -2.8367, -3.1216 |
| timely_leagueews: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
### europe: every within-model policy effect, four-budget mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: baron | -0.0414 [-0.2785, +0.1833] | +0.0035 [-0.0035, +0.0097] | +0.0776, +0.0621, -0.2640 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: dragon | -0.1270 [-0.1788, -0.0807] | -0.0028 [-0.0041, -0.0016] | -0.1210, -0.1389, -0.1210 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: teamfight | +0.0150 [-0.0377, +0.0654] | +0.0063 [-0.0003, +0.0123] | +0.0276, -0.0551, +0.0727 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: macro | -0.0511 [-0.1393, +0.0306] | +0.0023 [-0.0011, +0.0054] | -0.0053, -0.0440, -0.1041 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: baron | -4.1046 [-4.4876, -3.7587] | -0.1462 [-0.1554, -0.1371] | -3.8820, -3.8509, -4.5807 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: dragon | -3.6871 [-3.8623, -3.5186] | -0.1438 [-0.1513, -0.1366] | -3.7424, -3.5272, -3.7917 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: teamfight | -1.1024 [-1.1825, -1.0200] | -0.1424 [-0.1509, -0.1342] | -1.1200, -1.0673, -1.1200 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: macro | -2.9647 [-3.0998, -2.8308] | -0.1441 [-0.1498, -0.1387] | -2.9148, -2.8152, -3.1641 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: baron | -4.1460 [-4.5207, -3.7690] | -0.1427 [-0.1544, -0.1313] | -3.8043, -3.7888, -4.8447 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.8141 [-3.9969, -3.6388] | -0.1466 [-0.1545, -0.1388] | -3.8634, -3.6662, -3.9127 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0874 [-1.1756, -0.9988] | -0.1362 [-0.1463, -0.1261] | -1.0924, -1.1225, -1.0473 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: macro | -3.0158 [-3.1626, -2.8739] | -0.1418 [-0.1486, -0.1347] | -2.9200, -2.8592, -3.2682 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: baron | -0.0104 [-0.2409, +0.2106] | -0.0008 [-0.0073, +0.0048] | +0.0776, -0.2174, +0.1087 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: dragon | +0.0508 [+0.0000, +0.0981] | +0.0039 [+0.0024, +0.0053] | +0.0672, -0.0090, +0.0941 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: teamfight | +0.0927 [+0.0460, +0.1362] | +0.0157 [+0.0112, +0.0199] | +0.1052, +0.0025, +0.1704 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: macro | +0.0444 [-0.0397, +0.1232] | +0.0063 [+0.0034, +0.0090] | +0.0834, -0.0746, +0.1244 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: baron | -3.7733 [-4.1332, -3.4316] | -0.1279 [-0.1362, -0.1197] | -3.8820, -3.6025, -3.8354 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: dragon | -3.8096 [-3.9852, -3.6401] | -0.1452 [-0.1526, -0.1384] | -3.9441, -3.6169, -3.8679 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0197 [-1.0939, -0.9466] | -0.1379 [-0.1466, -0.1298] | -1.0448, -0.8895, -1.1250 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: macro | -2.8675 [-3.0030, -2.7385] | -0.1370 [-0.1424, -0.1316] | -2.9570, -2.7029, -2.9428 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: baron | -3.7836 [-4.1588, -3.4149] | -0.1287 [-0.1394, -0.1184] | -3.8043, -3.8199, -3.7267 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.7588 [-3.9329, -3.5912] | -0.1413 [-0.1488, -0.1343] | -3.8768, -3.6259, -3.7738 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.9270 [-1.0066, -0.8526] | -0.1222 [-0.1307, -0.1136] | -0.9396, -0.8870, -0.9546 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: macro | -2.8232 [-2.9640, -2.6830] | -0.1308 [-0.1369, -0.1245] | -2.8736, -2.7776, -2.8184 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: baron | -0.0000 [-0.1702, +0.1571] | +0.0024 [-0.0017, +0.0062] | +0.0311, -0.0311, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: teamfight | +0.0251 [-0.0074, +0.0531] | +0.0051 [+0.0021, +0.0077] | +0.0752, -0.0551, +0.0551 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: macro | +0.0084 [-0.0498, +0.0600] | +0.0025 [+0.0008, +0.0040] | +0.0354, -0.0287, +0.0184 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: baron | -3.6180 [-3.9585, -3.2764] | -0.1390 [-0.1483, -0.1301] | -3.7112, -3.6180, -3.5248 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: dragon | -1.1817 [-1.2898, -1.0739] | -0.1412 [-0.1472, -0.1351] | -1.1743, -1.1429, -1.2280 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: teamfight | -0.9095 [-0.9820, -0.8368] | -0.1403 [-0.1484, -0.1322] | -1.0147, -0.8945, -0.8193 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: macro | -1.9031 [-2.0233, -1.7791] | -0.1401 [-0.1456, -0.1351] | -1.9667, -1.8851, -1.8574 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: baron | -3.6180 [-3.9601, -3.2662] | -0.1366 [-0.1469, -0.1265] | -3.6801, -3.6491, -3.5248 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: dragon | -1.1817 [-1.2898, -1.0739] | -0.1412 [-0.1472, -0.1351] | -1.1743, -1.1429, -1.2280 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.8844 [-0.9578, -0.8158] | -0.1352 [-0.1434, -0.1270] | -0.9396, -0.9496, -0.7642 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: macro | -1.8947 [-2.0193, -1.7714] | -0.1376 [-0.1432, -0.1323] | -1.9313, -1.9138, -1.8390 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_empirical-minus-uncapped_empirical: baron | +0.0052 [-0.2625, +0.2391] | +0.0056 [-0.0009, +0.0115] | +0.2795, -0.2329, -0.0311 |
| timely_independent: capped_empirical-minus-uncapped_empirical: dragon | -0.0284 [-0.0683, +0.0045] | -0.0002 [-0.0013, +0.0009] | -0.0627, +0.0403, -0.0627 |
| timely_independent: capped_empirical-minus-uncapped_empirical: teamfight | +0.0526 [-0.0217, +0.1240] | +0.0187 [+0.0109, +0.0259] | -0.0276, +0.1153, +0.0702 |
| timely_independent: capped_empirical-minus-uncapped_empirical: macro | +0.0098 [-0.0862, +0.0978] | +0.0080 [+0.0044, +0.0113] | +0.0631, -0.0258, -0.0079 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: baron | -4.3116 [-4.6773, -3.9588] | -0.1453 [-0.1548, -0.1360] | -4.2702, -4.0839, -4.5807 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: dragon | -3.6557 [-3.8345, -3.4739] | -0.1430 [-0.1507, -0.1358] | -3.6886, -3.7603, -3.5183 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0782 [-1.1560, -1.0011] | -0.1494 [-0.1583, -0.1410] | -0.9671, -1.1099, -1.1575 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: macro | -3.0152 [-3.1559, -2.8877] | -0.1459 [-0.1518, -0.1403] | -2.9753, -2.9847, -3.0855 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: baron | -4.3064 [-4.6978, -3.9395] | -0.1398 [-0.1514, -0.1285] | -3.9907, -4.3168, -4.6118 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.6841 [-3.8652, -3.4977] | -0.1432 [-0.1511, -0.1360] | -3.7513, -3.7200, -3.5810 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0256 [-1.1257, -0.9267] | -0.1307 [-0.1418, -0.1206] | -0.9947, -0.9947, -1.0874 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: macro | -3.0054 [-3.1539, -2.8661] | -0.1379 [-0.1447, -0.1309] | -2.9122, -3.0105, -3.0934 |
| timely_independent: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: baron | -0.0725 [-0.3135, +0.1716] | +0.0058 [-0.0014, +0.0122] | -0.2329, +0.0776, -0.0621 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: dragon | -0.0538 [-0.1028, -0.0104] | +0.0002 [-0.0012, +0.0015] | -0.0896, +0.0269, -0.0986 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: teamfight | +0.0150 [-0.0391, +0.0667] | +0.0031 [-0.0038, +0.0093] | -0.0376, +0.0200, +0.0626 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: macro | -0.0371 [-0.1289, +0.0532] | +0.0030 [-0.0006, +0.0063] | -0.1200, +0.0415, -0.0327 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: baron | -3.8406 [-4.1744, -3.5104] | -0.1390 [-0.1478, -0.1305] | -3.9130, -3.6957, -3.9130 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: dragon | -3.8933 [-4.0674, -3.7125] | -0.1520 [-0.1597, -0.1445] | -3.8455, -3.8589, -3.9754 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0164 [-1.0927, -0.9383] | -0.1353 [-0.1436, -0.1271] | -0.8970, -1.0724, -1.0799 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: macro | -2.9168 [-3.0482, -2.7866] | -0.1421 [-0.1474, -0.1366] | -2.8852, -2.8756, -2.9895 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: baron | -3.9130 [-4.2742, -3.5440] | -0.1332 [-0.1442, -0.1226] | -4.1460, -3.6180, -3.9752 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.9471 [-4.1261, -3.7637] | -0.1518 [-0.1598, -0.1442] | -3.9351, -3.8320, -4.0740 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0014 [-1.0840, -0.9171] | -0.1322 [-0.1428, -0.1217] | -0.9346, -1.0523, -1.0172 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: macro | -2.9538 [-3.0970, -2.8069] | -0.1391 [-0.1462, -0.1321] | -3.0052, -2.8341, -3.0221 |
| timely_leagueews: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
### americas: every within-model policy effect, four-budget mean

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: baron | -0.0971 [-0.4284, +0.1882] | +0.0004 [-0.0080, +0.0074] | -0.1993, +0.0000, -0.0920 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: dragon | -0.1579 [-0.2142, -0.1083] | -0.0048 [-0.0071, -0.0030] | -0.1130, -0.1782, -0.1826 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: teamfight | -0.0535 [-0.1571, +0.0314] | -0.0085 [-0.0183, +0.0001] | +0.0000, -0.1426, -0.0178 |
| timely_equal_sum: capped_empirical-minus-uncapped_empirical: macro | -0.1028 [-0.2197, +0.0003] | -0.0043 [-0.0090, -0.0003] | -0.1041, -0.1069, -0.0975 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: baron | -4.5575 [-4.9387, -4.1938] | -0.1557 [-0.1648, -0.1471] | -4.5064, -4.2765, -4.8896 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: dragon | -3.7356 [-3.9232, -3.5560] | -0.1371 [-0.1442, -0.1298] | -3.8472, -3.5342, -3.8254 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0314 [-1.1100, -0.9556] | -0.1437 [-0.1523, -0.1354] | -1.0517, -0.9855, -1.0568 |
| timely_equal_sum: capped_kl_sequence-minus-capped_sequence: macro | -3.1082 [-3.2568, -2.9756] | -0.1455 [-0.1512, -0.1400] | -3.1351, -2.9321, -3.2573 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: baron | -4.6546 [-5.0704, -4.2480] | -0.1553 [-0.1674, -0.1434] | -4.7057, -4.2765, -4.9816 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.8935 [-4.0876, -3.7067] | -0.1418 [-0.1499, -0.1341] | -3.9602, -3.7124, -4.0080 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0849 [-1.1938, -0.9826] | -0.1522 [-0.1653, -0.1399] | -1.0517, -1.1281, -1.0747 |
| timely_equal_sum: capped_kl_sequence-minus-uncapped_empirical: macro | -3.2110 [-3.3710, -3.0593] | -0.1498 [-0.1573, -0.1427] | -3.2392, -3.0390, -3.3548 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_sum: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: baron | -0.1380 [-0.4658, +0.1300] | -0.0046 [-0.0152, +0.0038] | -0.1686, -0.1533, -0.0920 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: dragon | +0.0232 [-0.0186, +0.0651] | +0.0041 [+0.0023, +0.0058] | +0.0217, +0.0000, +0.0478 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: teamfight | +0.0772 [+0.0171, +0.1328] | +0.0069 [-0.0002, +0.0129] | +0.0840, -0.0509, +0.1986 |
| timely_equal_tcn: capped_empirical-minus-uncapped_empirical: macro | -0.0125 [-0.1236, +0.0802] | +0.0021 [-0.0022, +0.0058] | -0.0209, -0.0681, +0.0515 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: baron | -3.8729 [-4.2097, -3.5329] | -0.1471 [-0.1555, -0.1386] | -3.9546, -3.6634, -4.0006 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: dragon | -3.7979 [-3.9853, -3.6199] | -0.1471 [-0.1543, -0.1393] | -3.9776, -3.6342, -3.7820 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0059 [-1.0818, -0.9341] | -0.1419 [-0.1502, -0.1341] | -1.0288, -0.8862, -1.1027 |
| timely_equal_tcn: capped_kl_sequence-minus-capped_sequence: macro | -2.8922 [-3.0290, -2.7614] | -0.1453 [-0.1508, -0.1396] | -2.9870, -2.7279, -2.9617 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: baron | -4.0108 [-4.4021, -3.6308] | -0.1517 [-0.1651, -0.1392] | -4.1232, -3.8167, -4.0926 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.7747 [-3.9616, -3.6059] | -0.1429 [-0.1507, -0.1352] | -3.9558, -3.6342, -3.7341 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.9287 [-1.0048, -0.8531] | -0.1350 [-0.1454, -0.1257] | -0.9448, -0.9371, -0.9040 |
| timely_equal_tcn: capped_kl_sequence-minus-uncapped_empirical: macro | -2.9047 [-3.0492, -2.7647] | -0.1432 [-0.1503, -0.1361] | -3.0080, -2.7960, -2.9103 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_tcn: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: baron | +0.0102 [-0.1773, +0.1972] | +0.0000 [-0.0058, +0.0052] | +0.2606, -0.1839, -0.0460 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: teamfight | +0.0127 [-0.0155, +0.0380] | +0.0001 [-0.0051, +0.0042] | +0.0280, -0.0637, +0.0739 |
| timely_equal_gru: capped_empirical-minus-uncapped_empirical: macro | +0.0077 [-0.0576, +0.0686] | +0.0000 [-0.0025, +0.0023] | +0.0962, -0.0825, +0.0093 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: baron | -3.6430 [-4.0000, -3.3018] | -0.1550 [-0.1637, -0.1461] | -3.8320, -3.7400, -3.3568 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: dragon | -1.1795 [-1.2844, -1.0814] | -0.1409 [-0.1475, -0.1349] | -1.0955, -1.1650, -1.2780 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: teamfight | -0.9278 [-1.0009, -0.8554] | -0.1456 [-0.1538, -0.1375] | -1.0008, -0.9473, -0.8353 |
| timely_equal_gru: capped_kl_sequence-minus-capped_sequence: macro | -1.9168 [-2.0413, -1.7975] | -0.1471 [-0.1522, -0.1419] | -1.9761, -1.9508, -1.8234 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: baron | -3.6327 [-4.0097, -3.2847] | -0.1550 [-0.1662, -0.1446] | -3.5714, -3.9240, -3.4028 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: dragon | -1.1795 [-1.2844, -1.0814] | -0.1409 [-0.1475, -0.1349] | -1.0955, -1.1650, -1.2780 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: teamfight | -0.9151 [-0.9903, -0.8409] | -0.1454 [-0.1550, -0.1366] | -0.9728, -1.0110, -0.7614 |
| timely_equal_gru: capped_kl_sequence-minus-uncapped_empirical: macro | -1.9091 [-2.0454, -1.7825] | -0.1471 [-0.1530, -0.1414] | -1.8799, -2.0333, -1.8141 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_equal_gru: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_empirical-minus-uncapped_empirical: baron | -0.1686 [-0.5111, +0.1282] | +0.0056 [-0.0028, +0.0126] | -0.1533, -0.1993, -0.1533 |
| timely_independent: capped_empirical-minus-uncapped_empirical: dragon | -0.0768 [-0.1331, -0.0288] | -0.0013 [-0.0032, +0.0001] | -0.0869, -0.0174, -0.1261 |
| timely_independent: capped_empirical-minus-uncapped_empirical: teamfight | +0.0153 [-0.0945, +0.1073] | -0.0028 [-0.0151, +0.0081] | -0.0713, +0.0764, +0.0407 |
| timely_independent: capped_empirical-minus-uncapped_empirical: macro | -0.0767 [-0.1985, +0.0342] | +0.0005 [-0.0045, +0.0051] | -0.1038, -0.0468, -0.0795 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: baron | -4.0824 [-4.4329, -3.7418] | -0.1568 [-0.1658, -0.1477] | -3.9240, -4.0619, -4.2612 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: dragon | -3.7660 [-3.9605, -3.5775] | -0.1456 [-0.1528, -0.1379] | -3.9037, -3.6342, -3.7602 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: teamfight | -1.1901 [-1.2749, -1.1087] | -0.1565 [-0.1661, -0.1473] | -1.1205, -1.1663, -1.2835 |
| timely_independent: capped_kl_sequence-minus-capped_sequence: macro | -3.0128 [-3.1510, -2.8777] | -0.1529 [-0.1589, -0.1472] | -2.9827, -2.9541, -3.1016 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: baron | -4.2510 [-4.6628, -3.8670] | -0.1512 [-0.1632, -0.1392] | -4.0773, -4.2612, -4.4145 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.8428 [-4.0432, -3.6485] | -0.1469 [-0.1543, -0.1391] | -3.9906, -3.6515, -3.8863 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.1748 [-1.2918, -1.0658] | -0.1593 [-0.1746, -0.1455] | -1.1918, -1.0899, -1.2427 |
| timely_independent: capped_kl_sequence-minus-uncapped_empirical: macro | -3.0895 [-3.2508, -2.9455] | -0.1524 [-0.1605, -0.1451] | -3.0866, -3.0009, -3.1812 |
| timely_independent: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_independent: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: baron | -0.0664 [-0.4198, +0.2358] | +0.0053 [-0.0037, +0.0124] | -0.2606, +0.3985, -0.3372 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: dragon | -0.1275 [-0.1874, -0.0734] | -0.0017 [-0.0040, +0.0002] | -0.1565, -0.0739, -0.1521 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: teamfight | -0.0509 [-0.1454, +0.0274] | -0.0098 [-0.0201, -0.0004] | -0.1528, -0.0484, +0.0484 |
| timely_leagueews: capped_empirical-minus-uncapped_empirical: macro | -0.0816 [-0.2013, +0.0253] | -0.0021 [-0.0069, +0.0022] | -0.1900, +0.0921, -0.1470 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: baron | -4.2101 [-4.5887, -3.8492] | -0.1526 [-0.1614, -0.1435] | -4.4145, -4.0006, -4.2152 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: dragon | -3.8718 [-4.0550, -3.6805] | -0.1472 [-0.1544, -0.1395] | -3.9124, -3.7472, -3.9558 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: teamfight | -1.0093 [-1.0889, -0.9343] | -0.1417 [-0.1501, -0.1337] | -0.9346, -1.0467, -1.0467 |
| timely_leagueews: capped_kl_sequence-minus-capped_sequence: macro | -3.0304 [-3.1801, -2.8913] | -0.1471 [-0.1529, -0.1415] | -3.0871, -2.9315, -3.0726 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: baron | -4.2765 [-4.7062, -3.8685] | -0.1472 [-0.1593, -0.1348] | -4.6750, -3.6021, -4.5524 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: dragon | -3.9993 [-4.1928, -3.8132] | -0.1489 [-0.1568, -0.1408] | -4.0689, -3.8211, -4.1080 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: teamfight | -1.0602 [-1.1675, -0.9624] | -0.1515 [-0.1649, -0.1391] | -1.0874, -1.0950, -0.9983 |
| timely_leagueews: capped_kl_sequence-minus-uncapped_empirical: macro | -3.1120 [-3.2730, -2.9609] | -0.1492 [-0.1568, -0.1417] | -3.2771, -2.8394, -3.2196 |
| timely_leagueews: capped_sequence-minus-capped_empirical: baron | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: dragon | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: teamfight | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |
| timely_leagueews: capped_sequence-minus-capped_empirical: macro | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | +0.0000, +0.0000, +0.0000 |

### Regional primary architecture results

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Recall difference by seed, pp |
|---|---:|---:|---|
| europe: uncapped_empirical: 1.0: baron | +2.2360 [+1.2586, +3.2378] | +0.0289 [+0.0087, +0.0491] | +2.5466, +1.4286, +2.7329 |
| europe: uncapped_empirical: 1.0: dragon | +0.8964 [+0.5153, +1.3003] | +0.0349 [+0.0164, +0.0540] | +1.0757, +1.2549, +0.3586 |
| europe: uncapped_empirical: 1.0: macro | +1.1076 [+0.7291, +1.4880] | +0.0314 [+0.0184, +0.0445] | +1.3277, +0.8711, +1.1240 |
| europe: uncapped_empirical: 1.0: teamfight | +0.1904 [-0.0524, +0.4306] | +0.0304 [+0.0062, +0.0560] | +0.3608, -0.0702, +0.2806 |
| europe: uncapped_empirical: mean: baron | +1.7391 [+1.0522, +2.4308] | +0.0135 [-0.0003, +0.0278] | +1.7236, +1.1180, +2.3758 |
| europe: uncapped_empirical: mean: dragon | +0.2316 [-0.0030, +0.4752] | +0.0071 [-0.0018, +0.0163] | +0.3541, +0.3003, +0.0403 |
| europe: uncapped_empirical: mean: macro | +0.7379 [+0.4900, +0.9846] | +0.0122 [+0.0048, +0.0199] | +0.7894, +0.5087, +0.9156 |
| europe: uncapped_empirical: mean: teamfight | +0.2430 [+0.0994, +0.3909] | +0.0159 [+0.0012, +0.0313] | +0.2906, +0.1077, +0.3307 |
| europe: capped_empirical: 1.0: baron | +2.2567 [+1.2496, +3.2292] | +0.0478 [+0.0298, +0.0671] | +2.6087, +1.8012, +2.3602 |
| europe: capped_empirical: 1.0: dragon | +0.4542 [+0.0724, +0.8644] | +0.0160 [-0.0013, +0.0347] | +0.3586, +0.7530, +0.2510 |
| europe: capped_empirical: 1.0: macro | +0.9526 [+0.5653, +1.3168] | +0.0287 [+0.0169, +0.0412] | +1.1127, +0.7913, +0.9539 |
| europe: capped_empirical: 1.0: teamfight | +0.1470 [-0.0900, +0.3833] | +0.0222 [-0.0004, +0.0451] | +0.3708, -0.1804, +0.2506 |
| europe: capped_empirical: mean: baron | +1.7081 [+1.0370, +2.3962] | +0.0178 [+0.0051, +0.0311] | +1.7236, +1.3975, +2.0031 |
| europe: capped_empirical: mean: dragon | +0.0538 [-0.1797, +0.2955] | +0.0004 [-0.0083, +0.0095] | +0.1658, +0.1703, -0.1748 |
| europe: capped_empirical: mean: macro | +0.6424 [+0.3981, +0.8906] | +0.0083 [+0.0014, +0.0151] | +0.7008, +0.5393, +0.6871 |
| europe: capped_empirical: mean: teamfight | +0.1654 [+0.0239, +0.3054] | +0.0065 [-0.0069, +0.0201] | +0.2130, +0.0501, +0.2330 |
| europe: capped_sequence: 1.0: baron | +2.2567 [+1.2496, +3.2292] | +0.0478 [+0.0298, +0.0671] | +2.6087, +1.8012, +2.3602 |
| europe: capped_sequence: 1.0: dragon | +0.4542 [+0.0724, +0.8644] | +0.0160 [-0.0013, +0.0347] | +0.3586, +0.7530, +0.2510 |
| europe: capped_sequence: 1.0: macro | +0.9526 [+0.5653, +1.3168] | +0.0287 [+0.0169, +0.0412] | +1.1127, +0.7913, +0.9539 |
| europe: capped_sequence: 1.0: teamfight | +0.1470 [-0.0900, +0.3833] | +0.0222 [-0.0004, +0.0451] | +0.3708, -0.1804, +0.2506 |
| europe: capped_sequence: mean: baron | +1.7081 [+1.0370, +2.3962] | +0.0178 [+0.0051, +0.0311] | +1.7236, +1.3975, +2.0031 |
| europe: capped_sequence: mean: dragon | +0.0538 [-0.1797, +0.2955] | +0.0004 [-0.0083, +0.0095] | +0.1658, +0.1703, -0.1748 |
| europe: capped_sequence: mean: macro | +0.6424 [+0.3981, +0.8906] | +0.0083 [+0.0014, +0.0151] | +0.7008, +0.5393, +0.6871 |
| europe: capped_sequence: mean: teamfight | +0.1654 [+0.0239, +0.3054] | +0.0065 [-0.0069, +0.0201] | +0.2130, +0.0501, +0.2330 |
| europe: capped_kl_sequence: 1.0: baron | +1.9462 [+0.9682, +2.9150] | +0.0029 [-0.0162, +0.0218] | +1.7391, +1.2422, +2.8571 |
| europe: capped_kl_sequence: 1.0: dragon | +0.7649 [+0.4244, +1.1479] | +0.0222 [+0.0064, +0.0384] | +1.0398, +0.5378, +0.7171 |
| europe: capped_kl_sequence: 1.0: macro | +0.8369 [+0.4786, +1.1932] | +0.0049 [-0.0057, +0.0157] | +0.8628, +0.4029, +1.2449 |
| europe: capped_kl_sequence: 1.0: teamfight | -0.2004 [-0.4162, +0.0134] | -0.0104 [-0.0318, +0.0107] | -0.1904, -0.5713, +0.1604 |
| europe: capped_kl_sequence: mean: baron | +1.3768 [+0.7294, +2.0287] | -0.0004 [-0.0128, +0.0123] | +1.7236, +1.1491, +1.2578 |
| europe: capped_kl_sequence: mean: dragon | +0.1763 [-0.0317, +0.3980] | +0.0019 [-0.0060, +0.0101] | +0.3675, +0.2599, -0.0986 |
| europe: capped_kl_sequence: mean: macro | +0.5453 [+0.3076, +0.7720] | +0.0011 [-0.0052, +0.0074] | +0.7430, +0.4271, +0.4657 |
| europe: capped_kl_sequence: mean: teamfight | +0.0827 [-0.0451, +0.2103] | +0.0020 [-0.0108, +0.0141] | +0.1378, -0.1278, +0.2380 |
| americas: uncapped_empirical: 1.0: baron | +1.9415 [+0.8951, +2.9906] | +0.0036 [-0.0164, +0.0247] | +1.7167, +2.1459, +1.9620 |
| americas: uncapped_empirical: 1.0: dragon | +1.2520 [+0.8464, +1.6461] | +0.0078 [-0.0100, +0.0251] | +1.3563, +1.4432, +0.9564 |
| americas: uncapped_empirical: 1.0: macro | +1.1584 [+0.7741, +1.5398] | +0.0099 [-0.0019, +0.0222] | +1.1534, +1.2439, +1.0780 |
| americas: uncapped_empirical: 1.0: teamfight | +0.2818 [+0.0547, +0.5183] | +0.0184 [-0.0067, +0.0438] | +0.3871, +0.1426, +0.3158 |
| americas: uncapped_empirical: mean: baron | +1.7474 [+1.0033, +2.5043] | -0.0001 [-0.0146, +0.0139] | +1.3182, +2.0540, +1.8700 |
| americas: uncapped_empirical: mean: dragon | +0.5361 [+0.3061, +0.7716] | -0.0022 [-0.0114, +0.0071] | +0.7694, +0.5912, +0.2478 |
| americas: uncapped_empirical: mean: macro | +0.8469 [+0.5862, +1.1137] | +0.0028 [-0.0049, +0.0110] | +0.7918, +0.9437, +0.8053 |
| americas: uncapped_empirical: mean: teamfight | +0.2572 [+0.1054, +0.4165] | +0.0107 [-0.0044, +0.0266] | +0.2878, +0.1859, +0.2980 |
| americas: capped_empirical: 1.0: baron | +2.3707 [+1.2937, +3.4449] | +0.0178 [-0.0016, +0.0369] | +2.2072, +2.0233, +2.8817 |
| americas: capped_empirical: 1.0: dragon | +0.8288 [+0.4308, +1.2164] | -0.0178 [-0.0356, -0.0016] | +0.9042, +0.8520, +0.7303 |
| americas: capped_empirical: 1.0: macro | +1.1141 [+0.7480, +1.4991] | -0.0008 [-0.0121, +0.0105] | +1.1288, +0.9754, +1.2379 |
| americas: capped_empirical: 1.0: teamfight | +0.1426 [-0.0910, +0.3836] | -0.0024 [-0.0242, +0.0213] | +0.2750, +0.0509, +0.1019 |
| americas: capped_empirical: mean: baron | +1.7883 [+1.0494, +2.5348] | +0.0049 [-0.0080, +0.0178] | +1.2876, +2.2072, +1.8700 |
| americas: capped_empirical: mean: dragon | +0.3550 [+0.1298, +0.5790] | -0.0111 [-0.0200, -0.0020] | +0.6347, +0.4130, +0.0174 |
| americas: capped_empirical: mean: macro | +0.7566 [+0.4985, +1.0166] | -0.0036 [-0.0106, +0.0036] | +0.7087, +0.9048, +0.6563 |
| americas: capped_empirical: mean: teamfight | +0.1265 [-0.0122, +0.2698] | -0.0047 [-0.0180, +0.0096] | +0.2037, +0.0942, +0.0815 |
| americas: capped_sequence: 1.0: baron | +2.3707 [+1.2937, +3.4449] | +0.0178 [-0.0016, +0.0369] | +2.2072, +2.0233, +2.8817 |
| americas: capped_sequence: 1.0: dragon | +0.8288 [+0.4308, +1.2164] | -0.0178 [-0.0356, -0.0016] | +0.9042, +0.8520, +0.7303 |
| americas: capped_sequence: 1.0: macro | +1.1141 [+0.7480, +1.4991] | -0.0008 [-0.0121, +0.0105] | +1.1288, +0.9754, +1.2379 |
| americas: capped_sequence: 1.0: teamfight | +0.1426 [-0.0910, +0.3836] | -0.0024 [-0.0242, +0.0213] | +0.2750, +0.0509, +0.1019 |
| americas: capped_sequence: mean: baron | +1.7883 [+1.0494, +2.5348] | +0.0049 [-0.0080, +0.0178] | +1.2876, +2.2072, +1.8700 |
| americas: capped_sequence: mean: dragon | +0.3550 [+0.1298, +0.5790] | -0.0111 [-0.0200, -0.0020] | +0.6347, +0.4130, +0.0174 |
| americas: capped_sequence: mean: macro | +0.7566 [+0.4985, +1.0166] | -0.0036 [-0.0106, +0.0036] | +0.7087, +0.9048, +0.6563 |
| americas: capped_sequence: mean: teamfight | +0.1265 [-0.0122, +0.2698] | -0.0047 [-0.0180, +0.0096] | +0.2037, +0.0942, +0.0815 |
| americas: capped_kl_sequence: 1.0: baron | +1.1036 [+0.0204, +2.1211] | -0.0036 [-0.0229, +0.0164] | +0.7971, +1.7781, +0.7357 |
| americas: capped_kl_sequence: 1.0: dragon | +0.6781 [+0.2980, +1.0356] | +0.0156 [-0.0004, +0.0309] | +1.1650, +0.6086, +0.2608 |
| americas: capped_kl_sequence: 1.0: macro | +0.5996 [+0.2263, +0.9673] | -0.0045 [-0.0157, +0.0060] | +0.6982, +0.7242, +0.3763 |
| americas: capped_kl_sequence: 1.0: teamfight | +0.0170 [-0.2085, +0.2469] | -0.0256 [-0.0462, -0.0042] | +0.1324, -0.2139, +0.1324 |
| americas: capped_kl_sequence: mean: baron | +1.1036 [+0.3971, +1.7953] | -0.0038 [-0.0163, +0.0092] | +0.7357, +1.5941, +0.9810 |
| americas: capped_kl_sequence: mean: dragon | +0.4173 [+0.1964, +0.6354] | -0.0011 [-0.0094, +0.0066] | +0.7651, +0.5130, -0.0261 |
| americas: capped_kl_sequence: mean: macro | +0.5407 [+0.2960, +0.7884] | -0.0038 [-0.0104, +0.0029] | +0.5605, +0.7007, +0.3607 |
| americas: capped_kl_sequence: mean: teamfight | +0.1010 [-0.0307, +0.2341] | -0.0064 [-0.0184, +0.0068] | +0.1808, -0.0051, +0.1273 |

## Prespecified descriptive rules

| Rule | Result |
|---|---|
| architecture_support | True |
| equal_leagueews_hard_one_budget_one | {'30': True, '60': True} |
| event_point_nonharm | True |
| gru_support | True |
| no_extra_burden | False |
| practical_promotion | not established by adaptively reused calibration; previous failures remain and patch 16.17 stays sealed |
| regional_architecture_consistency | False |

## Regional violations

Each row counts event/region/seed/budget cells out of 72. The full CSV lists every nominal-budget violation, including those below the hard-one level.

| Family / window / policy | Nominal budget violations | Hard-one violations |
|---|---:|---:|
| timely_equal_sum / 30 / uncapped_empirical | 13 | 4 |
| timely_equal_sum / 30 / capped_empirical | 13 | 3 |
| timely_equal_sum / 30 / capped_sequence | 13 | 3 |
| timely_equal_sum / 30 / capped_kl_sequence | 0 | 0 |
| timely_equal_sum / 60 / uncapped_empirical | 10 | 3 |
| timely_equal_sum / 60 / capped_empirical | 10 | 3 |
| timely_equal_sum / 60 / capped_sequence | 10 | 3 |
| timely_equal_sum / 60 / capped_kl_sequence | 0 | 0 |
| timely_equal_tcn / 30 / uncapped_empirical | 17 | 5 |
| timely_equal_tcn / 30 / capped_empirical | 17 | 5 |
| timely_equal_tcn / 30 / capped_sequence | 17 | 5 |
| timely_equal_tcn / 30 / capped_kl_sequence | 0 | 0 |
| timely_equal_tcn / 60 / uncapped_empirical | 10 | 3 |
| timely_equal_tcn / 60 / capped_empirical | 10 | 2 |
| timely_equal_tcn / 60 / capped_sequence | 10 | 2 |
| timely_equal_tcn / 60 / capped_kl_sequence | 0 | 0 |
| timely_equal_gru / 30 / uncapped_empirical | 7 | 3 |
| timely_equal_gru / 30 / capped_empirical | 5 | 3 |
| timely_equal_gru / 30 / capped_sequence | 5 | 3 |
| timely_equal_gru / 30 / capped_kl_sequence | 0 | 0 |
| timely_equal_gru / 60 / uncapped_empirical | 11 | 2 |
| timely_equal_gru / 60 / capped_empirical | 11 | 2 |
| timely_equal_gru / 60 / capped_sequence | 11 | 2 |
| timely_equal_gru / 60 / capped_kl_sequence | 0 | 0 |
| timely_independent / 30 / uncapped_empirical | 14 | 4 |
| timely_independent / 30 / capped_empirical | 11 | 1 |
| timely_independent / 30 / capped_sequence | 11 | 1 |
| timely_independent / 30 / capped_kl_sequence | 0 | 0 |
| timely_independent / 60 / uncapped_empirical | 6 | 2 |
| timely_independent / 60 / capped_empirical | 4 | 2 |
| timely_independent / 60 / capped_sequence | 4 | 2 |
| timely_independent / 60 / capped_kl_sequence | 0 | 0 |
| timely_leagueews / 30 / uncapped_empirical | 17 | 5 |
| timely_leagueews / 30 / capped_empirical | 14 | 2 |
| timely_leagueews / 30 / capped_sequence | 14 | 2 |
| timely_leagueews / 30 / capped_kl_sequence | 0 | 0 |
| timely_leagueews / 60 / uncapped_empirical | 9 | 0 |
| timely_leagueews / 60 / capped_empirical | 10 | 3 |
| timely_leagueews / 60 / capped_sequence | 10 | 3 |
| timely_leagueews / 60 / capped_kl_sequence | 0 | 0 |

## Silent policies

| Policy | Silent head/budget cells out of 360 |
|---|---:|
| uncapped_empirical | 0 |
| capped_empirical | 0 |
| capped_sequence | 0 |
| capped_kl_sequence | 0 |

Precision and cap activity are descriptive points. The aggregate counts retain every warning, timely hit and event denominator; `analysis.json` retains cap activity per head, region, policy and budget. A match at the cap is not necessarily truncated: activity counts matches where the same threshold would emit more than four warnings.

## Budget-one event precision for the primary architectures

Precision pools timely hits and alerts over the three fixed seeds within each event; it is descriptive and does not treat seeds as independent matches. A dash means zero alerts.

| Window / policy / model | Baron timely precision | Dragon timely precision | Teamfight timely precision |
|---|---:|---:|---:|
| 30 / uncapped_empirical / timely_equal_sum | 19.396% | 37.427% | 21.573% |
| 30 / uncapped_empirical / timely_equal_tcn | 19.232% | 36.967% | 20.822% |
| 30 / capped_empirical / timely_equal_sum | 19.210% | 37.530% | 21.631% |
| 30 / capped_empirical / timely_equal_tcn | 19.085% | 36.982% | 20.655% |
| 30 / capped_sequence / timely_equal_sum | 19.210% | 37.530% | 21.631% |
| 30 / capped_sequence / timely_equal_tcn | 19.085% | 36.982% | 20.655% |
| 30 / capped_kl_sequence / timely_equal_sum | 21.235% | 38.856% | 22.084% |
| 30 / capped_kl_sequence / timely_equal_tcn | 20.956% | 37.831% | 21.826% |
| 60 / uncapped_empirical / timely_equal_sum | 24.825% | 54.259% | 34.455% |
| 60 / uncapped_empirical / timely_equal_tcn | 23.804% | 53.915% | 34.328% |
| 60 / capped_empirical / timely_equal_sum | 24.599% | 54.201% | 34.443% |
| 60 / capped_empirical / timely_equal_tcn | 23.745% | 53.635% | 34.242% |
| 60 / capped_sequence / timely_equal_sum | 24.599% | 54.201% | 34.443% |
| 60 / capped_sequence / timely_equal_tcn | 23.745% | 53.635% | 34.242% |
| 60 / capped_kl_sequence / timely_equal_sum | 25.343% | 56.045% | 35.435% |
| 60 / capped_kl_sequence / timely_equal_tcn | 24.170% | 55.965% | 35.229% |
