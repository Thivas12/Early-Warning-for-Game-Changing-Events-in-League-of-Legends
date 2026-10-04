# Threshold-resolution results

Intervals are pointwise conditional paired whole-match 95% intervals. Burden is false-plus-late warnings per match per event. Budget means average four fixed operating points, not independent matches. Seed order: 20260930, 20261001, 20261002.

## 10-30-second warnings

### deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +0.3630 [+0.1921, +0.5361] | -0.0024 [-0.0101, +0.0056] | +0.1989, +0.6664, +0.2237 |
| 0.5 | +0.8190 [+0.6167, +1.0170] | +0.0406 [+0.0311, +0.0506] | +0.7439, +0.6903, +1.0228 |
| 0.75 | -0.0266 [-0.2203, +0.1702] | -0.0130 [-0.0236, -0.0020] | -1.2767, +1.0514, +0.1455 |
| 1.0 | -0.1014 [-0.2911, +0.0935] | -0.0548 [-0.0658, -0.0429] | -0.3666, -0.2745, +0.3369 |
| mean | +0.2635 [+0.1188, +0.4041] | -0.0074 [-0.0154, +0.0007] | -0.1751, +0.5334, +0.4322 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 20.878 / 0.9479 | 13.176 / 0.8887 | 3.082 / 0.7578 | 12.379 / 0.8648 |
| tcn | 20.734 / 0.9658 | 13.532 / 0.8991 | 2.834 / 0.7260 | 12.367 / 0.8636 |
| timely_leagueews | 20.971 / 0.9549 | 12.775 / 0.7651 | 3.085 / 0.7100 | 12.277 / 0.8100 |
| timely_tcn | 20.693 / 0.9466 | 12.649 / 0.7928 | 3.462 / 0.8489 | 12.268 / 0.8627 |

### regional_deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +0.2910 [+0.1171, +0.4674] | -0.0052 [-0.0129, +0.0029] | +0.1989, +0.4505, +0.2237 |
| 0.5 | +0.6461 [+0.4446, +0.8415] | +0.0141 [+0.0044, +0.0240] | +0.4744, +0.5640, +0.8999 |
| 0.75 | +0.1782 [-0.0200, +0.3727] | -0.0083 [-0.0187, +0.0030] | -0.2311, +0.7634, +0.0023 |
| 1.0 | -0.1768 [-0.3691, +0.0130] | -0.0620 [-0.0729, -0.0499] | -0.5517, -0.0688, +0.0900 |
| mean | +0.2346 [+0.0932, +0.3755] | -0.0154 [-0.0233, -0.0072] | -0.0274, +0.4273, +0.3040 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 21.310 / 0.9880 | 13.176 / 0.8887 | 3.082 / 0.7578 | 12.523 / 0.8781 |
| tcn | 20.930 / 0.9832 | 13.532 / 0.8991 | 3.024 / 0.7811 | 12.495 / 0.8878 |
| timely_leagueews | 21.177 / 0.9733 | 12.775 / 0.7651 | 3.085 / 0.7100 | 12.346 / 0.8161 |
| timely_tcn | 21.115 / 0.9839 | 12.649 / 0.7928 | 3.462 / 0.8489 | 12.409 / 0.8752 |

### matched_early_mixture: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +0.5449 [+0.3922, +0.7054] | -0.0021 [-0.0093, +0.0046] | +0.6762, +0.5419, +0.4166 |
| 0.5 | +0.4717 [+0.2846, +0.6493] | -0.0042 [-0.0136, +0.0046] | +0.5234, +0.4005, +0.4912 |
| 0.75 | +0.3568 [+0.1834, +0.5366] | -0.0062 [-0.0164, +0.0040] | +0.4334, +0.3659, +0.2710 |
| 1.0 | +0.4287 [+0.2623, +0.5962] | -0.0077 [-0.0185, +0.0037] | +0.5315, +0.4739, +0.2806 |
| mean | +0.4505 [+0.3236, +0.5842] | -0.0050 [-0.0132, +0.0034] | +0.5411, +0.4456, +0.3648 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 21.527 / 1.0215 | 14.748 / 1.0186 | 3.735 / 0.9880 | 13.337 / 1.0094 |
| tcn | 21.383 / 1.0352 | 15.018 / 1.0193 | 3.653 / 0.9817 | 13.351 / 1.0121 |
| timely_leagueews | 21.603 / 1.0238 | 15.717 / 1.0080 | 3.976 / 0.9734 | 13.765 / 1.0017 |
| timely_tcn | 21.515 / 1.0325 | 15.385 / 1.0092 | 3.868 / 0.9773 | 13.589 / 1.0063 |

### dense_deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +0.6592 [+0.4718, +0.8528] | +0.0067 [-0.0020, +0.0158] | +0.9246, +0.5503, +0.5028 |
| 0.5 | +0.4763 [+0.2697, +0.6806] | +0.0051 [-0.0047, +0.0155] | +0.5296, +0.6179, +0.2815 |
| 0.75 | +0.3833 [+0.1857, +0.5826] | -0.0043 [-0.0153, +0.0075] | +0.4451, +0.4493, +0.2554 |
| 1.0 | +0.4022 [+0.2173, +0.5901] | +0.0059 [-0.0057, +0.0186] | +0.4920, +0.4216, +0.2931 |
| mean | +0.4803 [+0.3369, +0.6188] | +0.0033 [-0.0049, +0.0120] | +0.5978, +0.5098, +0.3332 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 21.207 / 0.9828 | 14.632 / 0.9963 | 3.563 / 0.9144 | 13.134 / 0.9645 |
| tcn | 21.043 / 1.0047 | 14.720 / 0.9948 | 3.563 / 0.9298 | 13.109 / 0.9764 |
| timely_leagueews | 21.238 / 0.9839 | 15.456 / 0.9746 | 3.915 / 0.9527 | 13.536 / 0.9704 |
| timely_tcn | 21.177 / 0.9979 | 15.109 / 0.9740 | 3.802 / 0.9524 | 13.363 / 0.9748 |

### dense_regional_deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +0.6448 [+0.4622, +0.8398] | +0.0054 [-0.0033, +0.0144] | +0.8193, +0.6023, +0.5127 |
| 0.5 | +0.3866 [+0.1799, +0.5877] | -0.0025 [-0.0124, +0.0076] | +0.5155, +0.4285, +0.2157 |
| 0.75 | +0.3813 [+0.1918, +0.5827] | -0.0086 [-0.0200, +0.0030] | +0.4971, +0.3843, +0.2625 |
| 1.0 | +0.3189 [+0.1298, +0.5055] | -0.0073 [-0.0193, +0.0054] | +0.3620, +0.3957, +0.1991 |
| mean | +0.4329 [+0.2892, +0.5705] | -0.0033 [-0.0116, +0.0056] | +0.5485, +0.4527, +0.2975 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 21.578 / 1.0158 | 14.788 / 1.0072 | 3.664 / 0.9518 | 13.343 / 0.9916 |
| tcn | 21.290 / 1.0319 | 14.856 / 1.0049 | 3.652 / 0.9584 | 13.266 / 0.9984 |
| timely_leagueews | 21.516 / 1.0114 | 15.524 / 0.9793 | 3.947 / 0.9620 | 13.662 / 0.9843 |
| timely_tcn | 21.454 / 1.0207 | 15.109 / 0.9740 | 3.802 / 0.9524 | 13.455 / 0.9824 |

### Dense common budget-one contrasts

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| leagueews-minus-tcn: baron | +0.1646 [-0.2662, +0.5963] | -0.0219 [-0.0368, -0.0078] | +0.1234, +0.2468, +0.1234 |
| leagueews-minus-tcn: dragon | -0.0883 [-0.2832, +0.1305] | +0.0016 [-0.0094, +0.0114] | -0.3001, +0.1324, -0.0971 |
| leagueews-minus-tcn: teamfight | +0.0000 [-0.1040, +0.1023] | -0.0153 [-0.0306, -0.0012] | +0.0758, -0.0808, +0.0051 |
| leagueews-minus-tcn: macro | +0.0254 [-0.1380, +0.1925] | -0.0119 [-0.0198, -0.0048] | -0.0336, +0.0995, +0.0105 |
| target_effect_difference_leagueews_minus_tcn: baron | -0.1028 [-0.5930, +0.3829] | +0.0079 [-0.0076, +0.0233] | +0.6479, -0.2468, -0.7097 |
| target_effect_difference_leagueews_minus_tcn: dragon | +0.4355 [+0.1710, +0.7074] | -0.0010 [-0.0166, +0.0136] | +0.0971, +0.7856, +0.4237 |
| target_effect_difference_leagueews_minus_tcn: teamfight | +0.1128 [-0.0267, +0.2489] | +0.0156 [-0.0034, +0.0352] | +0.1364, +0.0859, +0.1162 |
| target_effect_difference_leagueews_minus_tcn: macro | +0.1485 [-0.0400, +0.3443] | +0.0075 [-0.0027, +0.0173] | +0.2938, +0.2082, -0.0566 |
| timely_leagueews-minus-leagueews: baron | +0.0309 [-0.3033, +0.3912] | +0.0011 [-0.0106, +0.0130] | +0.4628, -0.0926, -0.2777 |
| timely_leagueews-minus-leagueews: dragon | +0.8238 [+0.4262, +1.2198] | -0.0218 [-0.0414, -0.0013] | +0.6444, +1.0239, +0.8032 |
| timely_leagueews-minus-leagueews: teamfight | +0.3519 [+0.1777, +0.5229] | +0.0382 [+0.0136, +0.0649] | +0.3688, +0.3334, +0.3536 |
| timely_leagueews-minus-leagueews: macro | +0.4022 [+0.2173, +0.5901] | +0.0059 [-0.0057, +0.0186] | +0.4920, +0.4216, +0.2931 |
| timely_leagueews-minus-timely_tcn: baron | +0.0617 [-0.3461, +0.4734] | -0.0140 [-0.0289, +0.0006] | +0.7714, +0.0000, -0.5862 |
| timely_leagueews-minus-timely_tcn: dragon | +0.3472 [+0.1136, +0.5822] | +0.0006 [-0.0126, +0.0131] | -0.2030, +0.9180, +0.3266 |
| timely_leagueews-minus-timely_tcn: teamfight | +0.1128 [-0.0034, +0.2285] | +0.0002 [-0.0153, +0.0158] | +0.2122, +0.0051, +0.1212 |
| timely_leagueews-minus-timely_tcn: macro | +0.1739 [+0.0086, +0.3432] | -0.0044 [-0.0128, +0.0036] | +0.2602, +0.3077, -0.0461 |
| timely_tcn-minus-tcn: baron | +0.1337 [-0.2204, +0.4870] | -0.0068 [-0.0190, +0.0047] | -0.1851, +0.1543, +0.4320 |
| timely_tcn-minus-tcn: dragon | +0.3884 [+0.0411, +0.7270] | -0.0208 [-0.0393, -0.0006] | +0.5473, +0.2383, +0.3796 |
| timely_tcn-minus-tcn: teamfight | +0.2391 [+0.0721, +0.4246] | +0.0227 [-0.0029, +0.0487] | +0.2324, +0.2475, +0.2374 |
| timely_tcn-minus-tcn: macro | +0.2537 [+0.0752, +0.4293] | -0.0016 [-0.0131, +0.0106] | +0.1982, +0.2134, +0.3497 |

### Regional LeagueEWS target effect, dense common budget one

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| europe: baron | +0.2070 [-0.2625, +0.7111] | -0.0022 [-0.0189, +0.0151] | +0.7453, -0.1242, +0.0000 |
| europe: dragon | +1.0518 [+0.5196, +1.6266] | -0.0351 [-0.0651, -0.0049] | +0.7350, +1.4521, +0.9681 |
| europe: macro | +0.4964 [+0.2511, +0.7616] | -0.0038 [-0.0203, +0.0136] | +0.5636, +0.5562, +0.3695 |
| europe: teamfight | +0.2305 [-0.0202, +0.4917] | +0.0260 [-0.0093, +0.0636] | +0.2105, +0.3407, +0.1403 |
| americas: baron | -0.1431 [-0.6249, +0.3745] | +0.0044 [-0.0120, +0.0216] | +0.1839, -0.0613, -0.5518 |
| americas: dragon | +0.6028 [+0.0228, +1.1483] | -0.0084 [-0.0353, +0.0196] | +0.5564, +0.6086, +0.6434 |
| americas: macro | +0.3117 [+0.0306, +0.5810] | +0.0155 [-0.0006, +0.0328] | +0.4234, +0.2911, +0.2207 |
| americas: teamfight | +0.4754 [+0.2378, +0.7336] | +0.0504 [+0.0131, +0.0882] | +0.5297, +0.3260, +0.5704 |

### Budget-one policy effects and target interactions

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| leagueews: dense_deterministic-minus-deterministic | +0.7557 [+0.6914, +0.8216] | +0.0997 [+0.0953, +0.1044] | +0.3432, +0.9880, +0.9359 |
| leagueews: dense_regional_deterministic-minus-regional_deterministic | +0.8208 [+0.7578, +0.8857] | +0.1134 [+0.1087, +0.1187] | +0.4072, +1.1693, +0.8859 |
| leagueews: matched_early_mixture-minus-dense_regional_deterministic | -0.0066 [-0.0635, +0.0484] | +0.0178 [+0.0145, +0.0211] | +0.0044, -0.0878, +0.0635 |
| target_interaction_leagueews: dense_deterministic-minus-deterministic | +0.5036 [+0.4043, +0.6086] | +0.0606 [+0.0543, +0.0672] | +0.8586, +0.6961, -0.0438 |
| target_interaction_leagueews: dense_regional_deterministic-minus-regional_deterministic | +0.4958 [+0.3955, +0.6015] | +0.0547 [+0.0480, +0.0614] | +0.9137, +0.4645, +0.1090 |
| target_interaction_tcn: dense_deterministic-minus-deterministic | +0.3523 [+0.2565, +0.4497] | -0.0007 [-0.0068, +0.0051] | -0.1015, +0.9270, +0.2314 |
| target_interaction_tcn: dense_regional_deterministic-minus-regional_deterministic | +0.2757 [+0.1799, +0.3704] | -0.0034 [-0.0094, +0.0025] | -0.1565, +0.8144, +0.1693 |
| tcn: dense_deterministic-minus-deterministic | +0.7421 [+0.6787, +0.8041] | +0.1128 [+0.1081, +0.1177] | +1.1786, +0.5705, +0.4772 |
| tcn: dense_regional_deterministic-minus-regional_deterministic | +0.7707 [+0.7060, +0.8401] | +0.1106 [+0.1059, +0.1156] | +1.1719, +0.7346, +0.4057 |
| tcn: matched_early_mixture-minus-dense_regional_deterministic | +0.0853 [+0.0394, +0.1315] | +0.0136 [+0.0106, +0.0168] | +0.0765, +0.0737, +0.1058 |
| timely_leagueews: dense_deterministic-minus-deterministic | +1.2593 [+1.1782, +1.3435] | +0.1604 [+0.1543, +0.1671] | +1.2018, +1.6841, +0.8921 |
| timely_leagueews: dense_regional_deterministic-minus-regional_deterministic | +1.3166 [+1.2339, +1.4010] | +0.1681 [+0.1619, +0.1749] | +1.3209, +1.6338, +0.9949 |
| timely_leagueews: matched_early_mixture-minus-dense_regional_deterministic | +0.1031 [+0.0402, +0.1638] | +0.0175 [+0.0143, +0.0204] | +0.1740, -0.0097, +0.1451 |
| timely_tcn: dense_deterministic-minus-deterministic | +1.0944 [+1.0068, +1.1775] | +0.1120 [+0.1070, +0.1171] | +1.0771, +1.4976, +0.7087 |
| timely_tcn: dense_regional_deterministic-minus-regional_deterministic | +1.0464 [+0.9655, +1.1259] | +0.1072 [+0.1023, +0.1122] | +1.0154, +1.5490, +0.5750 |
| timely_tcn: matched_early_mixture-minus-dense_regional_deterministic | +0.1341 [+0.0729, +0.1965] | +0.0240 [+0.0206, +0.0273] | +0.0539, +0.2538, +0.0947 |

## 20-60-second warnings

### deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +0.9950 [+0.7354, +1.2609] | -0.0775 [-0.0868, -0.0685] | +0.9711, +0.8952, +1.1186 |
| 0.5 | +5.0316 [+4.7128, +5.3784] | +0.0385 [+0.0266, +0.0503] | +4.4684, +7.1130, +3.5135 |
| 0.75 | +4.5316 [+4.1510, +4.9158] | -0.1062 [-0.1210, -0.0917] | +3.3292, +5.1661, +5.0995 |
| 1.0 | +7.4629 [+7.0862, +7.8579] | +0.0552 [+0.0395, +0.0708] | +6.9860, +7.5137, +7.8892 |
| mean | +4.5053 [+4.2409, +4.7816] | -0.0225 [-0.0339, -0.0117] | +3.9387, +5.1720, +4.4052 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 23.542 / 0.8748 | 9.645 / 0.6689 | 4.235 / 0.7546 | 12.474 / 0.7661 |
| tcn | 23.439 / 0.9063 | 10.154 / 0.6872 | 3.487 / 0.6160 | 12.360 / 0.7365 |
| timely_leagueews | 25.928 / 0.8834 | 27.672 / 0.8303 | 6.210 / 0.7501 | 19.937 / 0.8213 |
| timely_tcn | 23.563 / 0.8582 | 28.343 / 0.8896 | 6.497 / 0.8003 | 19.467 / 0.8494 |

### regional_deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +1.5350 [+1.2764, +1.8044] | -0.0558 [-0.0652, -0.0467] | +2.3081, +0.8952, +1.4015 |
| 0.5 | +5.1424 [+4.8187, +5.4867] | +0.0280 [+0.0158, +0.0401] | +5.6923, +6.2214, +3.5135 |
| 0.75 | +5.0826 [+4.6944, +5.4705] | -0.0683 [-0.0836, -0.0536] | +4.9823, +5.1661, +5.0995 |
| 1.0 | +7.4629 [+7.0862, +7.8579] | +0.0552 [+0.0395, +0.0708] | +6.9860, +7.5137, +7.8892 |
| mean | +4.8057 [+4.5362, +5.0876] | -0.0102 [-0.0218, +0.0007] | +4.9922, +4.9491, +4.4759 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 23.542 / 0.8748 | 9.645 / 0.6689 | 4.235 / 0.7546 | 12.474 / 0.7661 |
| tcn | 25.003 / 0.9633 | 11.872 / 0.7627 | 3.487 / 0.6160 | 13.454 / 0.7807 |
| timely_leagueews | 25.928 / 0.8834 | 27.672 / 0.8303 | 6.210 / 0.7501 | 19.937 / 0.8213 |
| timely_tcn | 24.920 / 0.9130 | 28.343 / 0.8896 | 6.497 / 0.8003 | 19.920 / 0.8676 |

### matched_early_mixture: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +3.0509 [+2.8332, +3.2902] | +0.0005 [-0.0070, +0.0078] | +3.2849, +3.0472, +2.8206 |
| 0.5 | +4.2550 [+3.9812, +4.5546] | -0.0016 [-0.0120, +0.0085] | +4.4514, +4.2421, +4.0716 |
| 0.75 | +4.4871 [+4.1919, +4.7979] | -0.0051 [-0.0178, +0.0076] | +4.7465, +4.2353, +4.4793 |
| 1.0 | +4.1898 [+3.8926, +4.5039] | -0.0103 [-0.0239, +0.0033] | +4.3685, +4.0643, +4.1365 |
| mean | +3.9957 [+3.7699, +4.2484] | -0.0041 [-0.0144, +0.0059] | +4.2128, +3.8972, +3.8770 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 27.296 / 1.0312 | 21.668 / 1.0007 | 5.764 / 0.9940 | 18.243 / 1.0086 |
| tcn | 26.570 / 1.0376 | 21.210 / 1.0058 | 5.576 / 0.9908 | 17.786 / 1.0114 |
| timely_leagueews | 29.192 / 1.0214 | 30.363 / 0.9864 | 7.743 / 0.9873 | 22.433 / 0.9984 |
| timely_tcn | 27.864 / 1.0358 | 29.888 / 0.9792 | 7.675 / 0.9903 | 21.809 / 1.0017 |

### dense_deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +4.2341 [+3.9145, +4.5723] | -0.0045 [-0.0160, +0.0066] | +4.3916, +4.2404, +4.0703 |
| 0.5 | +5.8349 [+5.4678, +6.2217] | -0.0089 [-0.0233, +0.0053] | +6.0898, +5.7880, +5.6270 |
| 0.75 | +6.3341 [+5.9411, +6.7244] | -0.0010 [-0.0164, +0.0146] | +6.5468, +6.2114, +6.2440 |
| 1.0 | +5.8727 [+5.4792, +6.2926] | -0.0119 [-0.0290, +0.0046] | +6.3617, +5.7691, +5.4875 |
| mean | +5.5690 [+5.2721, +5.8814] | -0.0066 [-0.0194, +0.0056] | +5.8475, +5.5022, +5.3572 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 25.815 / 0.9639 | 16.833 / 0.9726 | 5.454 / 0.9562 | 16.034 / 0.9642 |
| tcn | 25.723 / 0.9881 | 16.656 / 0.9748 | 5.239 / 0.9183 | 15.873 / 0.9604 |
| timely_leagueews | 28.191 / 0.9610 | 30.144 / 0.9679 | 7.386 / 0.9281 | 21.907 / 0.9523 |
| timely_tcn | 26.802 / 0.9870 | 29.511 / 0.9559 | 7.445 / 0.9458 | 21.253 / 0.9629 |

### dense_regional_deterministic: LeagueEWS target effect

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| 0.25 | +4.5010 [+4.1810, +4.8468] | +0.0051 [-0.0067, +0.0166] | +4.7609, +4.4557, +4.2864 |
| 0.5 | +5.8338 [+5.4745, +6.2236] | -0.0035 [-0.0180, +0.0106] | +6.0924, +5.7914, +5.6175 |
| 0.75 | +6.1987 [+5.8253, +6.5813] | +0.0006 [-0.0149, +0.0162] | +6.4758, +6.0721, +6.0483 |
| 1.0 | +5.7097 [+5.3210, +6.1320] | -0.0105 [-0.0274, +0.0059] | +5.9765, +5.8049, +5.3476 |
| mean | +5.5608 [+5.2656, +5.8736] | -0.0021 [-0.0150, +0.0103] | +5.8264, +5.5310, +5.3250 |

Budget-one model recall percent / burden:

| Model | Baron | Dragon | Teamfight | Macro |
|---|---:|---:|---:|---:|
| leagueews | 26.772 / 1.0044 | 17.395 / 0.9947 | 5.454 / 0.9562 | 16.540 / 0.9851 |
| tcn | 26.607 / 1.0288 | 17.486 / 1.0069 | 5.370 / 0.9472 | 16.488 / 0.9943 |
| timely_leagueews | 28.962 / 1.0023 | 30.259 / 0.9734 | 7.529 / 0.9481 | 22.250 / 0.9746 |
| timely_tcn | 27.656 / 1.0149 | 29.761 / 0.9712 | 7.515 / 0.9558 | 21.644 / 0.9806 |

### Dense common budget-one contrasts

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| leagueews-minus-tcn: baron | +0.0926 [-0.5026, +0.6782] | -0.0242 [-0.0382, -0.0112] | -0.3703, +0.4320, +0.2160 |
| leagueews-minus-tcn: dragon | +0.1765 [-0.0646, +0.4218] | -0.0022 [-0.0118, +0.0077] | -0.8032, +0.0088, +1.3240 |
| leagueews-minus-tcn: teamfight | +0.2155 [+0.0855, +0.3491] | +0.0379 [+0.0227, +0.0533] | +0.4547, +0.0455, +0.1465 |
| leagueews-minus-tcn: macro | +0.1615 [-0.0503, +0.3818] | +0.0038 [-0.0037, +0.0112] | -0.2396, +0.1621, +0.5622 |
| target_effect_difference_leagueews_minus_tcn: baron | +1.2959 [+0.5560, +2.0808] | -0.0018 [-0.0187, +0.0157] | +2.2215, +0.3085, +1.3576 |
| target_effect_difference_leagueews_minus_tcn: dragon | +0.4561 [+0.1002, +0.8061] | +0.0142 [-0.0013, +0.0293] | +1.6948, +0.5561, -0.8827 |
| target_effect_difference_leagueews_minus_tcn: teamfight | -0.2745 [-0.4710, -0.0770] | -0.0556 [-0.0766, -0.0346] | -0.3183, -0.2829, -0.2223 |
| target_effect_difference_leagueews_minus_tcn: macro | +0.4925 [+0.2153, +0.7891] | -0.0144 [-0.0250, -0.0037] | +1.1993, +0.1939, +0.0842 |
| timely_leagueews-minus-leagueews: baron | +2.3758 [+1.6234, +3.1590] | -0.0029 [-0.0211, +0.0150] | +3.3323, +1.7587, +2.0364 |
| timely_leagueews-minus-leagueews: dragon | +13.3110 [+12.4919, +14.1687] | -0.0047 [-0.0368, +0.0262] | +13.7876, +13.5228, +12.6225 |
| timely_leagueews-minus-leagueews: teamfight | +1.9315 [+1.6019, +2.2881] | -0.0281 [-0.0615, +0.0049] | +1.9651, +2.0258, +1.8035 |
| timely_leagueews-minus-leagueews: macro | +5.8727 [+5.4792, +6.2926] | -0.0119 [-0.0290, +0.0046] | +6.3617, +5.7691, +5.4875 |
| timely_leagueews-minus-timely_tcn: baron | +1.3885 [+0.7067, +2.0569] | -0.0260 [-0.0412, -0.0113] | +1.8513, +0.7405, +1.5736 |
| timely_leagueews-minus-timely_tcn: dragon | +0.6326 [+0.3809, +0.8850] | +0.0120 [-0.0003, +0.0239] | +0.8915, +0.5649, +0.4413 |
| timely_leagueews-minus-timely_tcn: teamfight | -0.0589 [-0.2163, +0.0932] | -0.0177 [-0.0342, -0.0001] | +0.1364, -0.2374, -0.0758 |
| timely_leagueews-minus-timely_tcn: macro | +0.6540 [+0.4068, +0.8945] | -0.0106 [-0.0190, -0.0019] | +0.9597, +0.3560, +0.6464 |
| timely_tcn-minus-tcn: baron | +1.0799 [+0.3767, +1.7846] | -0.0011 [-0.0187, +0.0157] | +1.1108, +1.4502, +0.6788 |
| timely_tcn-minus-tcn: dragon | +12.8549 [+12.0479, +13.6949] | -0.0189 [-0.0499, +0.0109] | +12.0929, +12.9667, +13.5052 |
| timely_tcn-minus-tcn: teamfight | +2.2059 [+1.8759, +2.5445] | +0.0274 [-0.0063, +0.0612] | +2.2834, +2.3087, +2.0258 |
| timely_tcn-minus-tcn: macro | +5.3803 [+5.0226, +5.7681] | +0.0025 [-0.0137, +0.0174] | +5.1623, +5.5752, +5.4032 |

### Regional LeagueEWS target effect, dense common budget one

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| europe: baron | +1.9048 [+0.9255, +2.9215] | +0.0000 [-0.0260, +0.0256] | +3.1056, +1.3043, +1.3043 |
| europe: dragon | +12.2684 [+11.0733, +13.4268] | +0.0091 [-0.0340, +0.0516] | +12.7286, +12.4597, +11.6171 |
| europe: macro | +5.2812 [+4.7290, +5.8212] | -0.0115 [-0.0339, +0.0109] | +5.8059, +5.2094, +4.8283 |
| europe: teamfight | +1.6703 [+1.1845, +2.1380] | -0.0436 [-0.0887, +0.0024] | +1.5835, +1.8641, +1.5634 |
| americas: baron | +2.8408 [+1.6799, +3.9527] | -0.0058 [-0.0320, +0.0198] | +3.5561, +2.2072, +2.7590 |
| americas: dragon | +14.3221 [+13.1735, +15.5044] | -0.0184 [-0.0656, +0.0258] | +14.8148, +14.5540, +13.5976 |
| americas: macro | +6.4533 [+5.9424, +7.0402] | -0.0123 [-0.0367, +0.0105] | +6.9080, +6.3171, +6.1347 |
| americas: teamfight | +2.1969 [+1.7387, +2.6888] | -0.0127 [-0.0609, +0.0324] | +2.3531, +2.1901, +2.0475 |

### Budget-one policy effects and target interactions

| Comparison | Recall difference, pp [95%] | Burden difference [95%] | Seed differences, pp |
|---|---:|---:|---|
| leagueews: dense_deterministic-minus-deterministic | +3.5601 [+3.3970, +3.7329] | +0.1981 [+0.1910, +0.2060] | +3.8661, +2.9266, +3.8875 |
| leagueews: dense_regional_deterministic-minus-regional_deterministic | +4.0662 [+3.8848, +4.2627] | +0.2190 [+0.2112, +0.2272] | +4.3747, +3.3867, +4.4373 |
| leagueews: matched_early_mixture-minus-dense_regional_deterministic | +1.7027 [+1.5095, +1.8940] | +0.0235 [+0.0149, +0.0322] | +1.6964, +1.9284, +1.4832 |
| target_interaction_leagueews: dense_deterministic-minus-deterministic | -1.5902 [-1.7955, -1.3901] | -0.0671 [-0.0750, -0.0591] | -0.6243, -1.7446, -2.4017 |
| target_interaction_leagueews: dense_regional_deterministic-minus-regional_deterministic | -1.7533 [-1.9739, -1.5384] | -0.0657 [-0.0740, -0.0575] | -1.0095, -1.7088, -2.5415 |
| target_interaction_tcn: dense_deterministic-minus-deterministic | -1.7270 [-1.9257, -1.5284] | -0.1104 [-0.1186, -0.1025] | -2.2144, -3.5835, +0.6168 |
| target_interaction_tcn: dense_regional_deterministic-minus-regional_deterministic | -1.3094 [-1.4793, -1.1302] | -0.1006 [-0.1084, -0.0934] | -1.7113, -1.1521, -1.0648 |
| tcn: dense_deterministic-minus-deterministic | +3.5123 [+3.3536, +3.6754] | +0.2239 [+0.2157, +0.2323] | +3.8271, +4.7602, +1.9497 |
| tcn: dense_regional_deterministic-minus-regional_deterministic | +3.0337 [+2.8970, +3.1703] | +0.2136 [+0.2057, +0.2216] | +3.6151, +2.7814, +2.7045 |
| tcn: matched_early_mixture-minus-dense_regional_deterministic | +1.2978 [+1.1096, +1.4897] | +0.0171 [+0.0090, +0.0253] | +1.3670, +1.3494, +1.1770 |
| timely_leagueews: dense_deterministic-minus-deterministic | +1.9699 [+1.8375, +2.0986] | +0.1310 [+0.1254, +0.1368] | +3.2418, +1.1820, +1.4858 |
| timely_leagueews: dense_regional_deterministic-minus-regional_deterministic | +2.3129 [+2.1699, +2.4600] | +0.1533 [+0.1472, +0.1599] | +3.3652, +1.6779, +1.8958 |
| timely_leagueews: matched_early_mixture-minus-dense_regional_deterministic | +0.1827 [+0.0773, +0.2862] | +0.0237 [+0.0199, +0.0275] | +0.0883, +0.1878, +0.2720 |
| timely_tcn: dense_deterministic-minus-deterministic | +1.7853 [+1.6602, +1.9214] | +0.1135 [+0.1088, +0.1183] | +1.6127, +1.1766, +2.5665 |
| timely_tcn: dense_regional_deterministic-minus-regional_deterministic | +1.7242 [+1.6080, +1.8551] | +0.1130 [+0.1081, +0.1177] | +1.9037, +1.6293, +1.6397 |
| timely_tcn: matched_early_mixture-minus-dense_regional_deterministic | +0.1647 [+0.0497, +0.2726] | +0.0211 [+0.0175, +0.0249] | +0.1704, +0.1037, +0.2198 |

## Frozen gates

| Gate | Pass |
|---|---|
| no_extra_burden | False |
| no_mean_event_harm | True |
| primary_target_gain | True |
| regional_hard_budget | False |

All intervals, event/region/seed values and negative results are retained in `analysis.json`, `aggregate-counts.csv`, `by-seed.csv` and `budget-violations.csv`.
