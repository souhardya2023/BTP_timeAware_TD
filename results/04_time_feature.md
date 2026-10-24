# 4. The time feature: how it is generated, what it looks like, and how much depends on it

`time_diff_min` is the minutes needed to fix the 3 injected bugs of a pair in the TD project minus in the clean project (sum over the bugs). In this dataset the values come from the ground-truth time model `pipeline/bug_injection/sample_times.py`; `time_source` in `bugs.csv` says `sample` until measured times are merged.

## 4.1 The model (constants read from the code)

| td_type | slow-down factor F |
|---|---|
| concurrency | 3.400 |
| security | 2.400 |
| complexity | 1.800 |
| coupling_cohesion | 1.400 |
| dependency_structure | 1.050 |

* per bug: clean time = 25 min x LogNormal(0, 0.3); TD time = clean time x exp(ln F x w + N(0, 0.08)); w = 1 for a bug in a file the TD change touched, 0.85 otherwise; seeded by pair and bug id.
* the only inputs are the TD type and whether the bug is in a TD-touched file: the time does not depend on the project, the code or the bug kind.

## 4.2 Distribution of the generated times

### per bug (183 bugs), minutes

| td_type | clean_min_mean | clean_min_std | clean_min_min | clean_min_max | td_min_mean | td_min_std | td_min_min | td_min_max | diff_min_mean | diff_min_std | diff_min_min | diff_min_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| complexity | 24.8 | 5.4 | 17.1 | 35.8 | 42.7 | 9.7 | 29.5 | 60.7 | 17.8 | 5.6 | 10.1 | 31.9 |
| concurrency | 26.1 | 7.6 | 13.5 | 46.7 | 79.9 | 25.1 | 40.5 | 145.6 | 53.9 | 18.5 | 24.5 | 106.8 |
| coupling_cohesion | 22.8 | 6.1 | 15.7 | 40.8 | 30.3 | 8.5 | 22.4 | 56.4 | 7.6 | 2.9 | 4.3 | 15.6 |
| dependency_structure | 25.8 | 7.2 | 14.6 | 38.4 | 26.9 | 7.9 | 15.3 | 41 | 1.1 | 2.1 | -2.5 | 6.6 |
| security | 25 | 6.2 | 15 | 41.6 | 55.6 | 13.9 | 32.4 | 90.4 | 30.7 | 8.9 | 14.3 | 56.1 |

### ratio TD time / clean time per bug

| td_type | mean | std | min | max |
|---|---|---|---|---|
| complexity | 1.720 | 0.180 | 1.430 | 2.110 |
| concurrency | 3.070 | 0.400 | 2.410 | 4.120 |
| coupling_cohesion | 1.330 | 0.080 | 1.220 | 1.480 |
| dependency_structure | 1.040 | 0.080 | 0.860 | 1.190 |
| security | 2.240 | 0.250 | 1.740 | 2.730 |

### per pair: `time_diff_min` (61 pairs)

| td_type | count | mean | std | min | median | max |
|---|---|---|---|---|---|---|
| complexity | 6 | 53.5 | 6.6 | 46.6 | 51.2 | 61.7 |
| concurrency | 26 | 161.6 | 29.3 | 110.5 | 160.7 | 235.8 |
| coupling_cohesion | 6 | 22.7 | 4.6 | 17.2 | 22 | 31.1 |
| dependency_structure | 7 | 3.2 | 2.4 | -1.9 | 4 | 5.5 |
| security | 16 | 92 | 14.4 | 59.1 | 96.1 | 108 |

### neighbouring TD types ordered by mean time

| between | gap_of_means | ranges_overlap |
|---|---|---|
| dependency_structure / coupling_cohesion | 19.500 | False |
| coupling_cohesion / complexity | 30.800 | False |
| complexity / security | 38.500 | True |
| security / concurrency | 69.600 | False |

* bugs in a TD-touched file: 70 of 183; mean ratio TD/clean there 2.58, elsewhere 2.15.
* the time alone classifies the TD type with accuracy 0.93 (random forest on `time_diff_min` only, project-held-out folds); the majority class is 0.43.

## 4.3 How the time model was set (calibration sweep)

Four settings were tried on the delta layout; the models were evaluated with and without the time on the given stratified folds, the project folds and 10 random stratified splits. The setting `cfg1_selected` is the one in use. The first setting was too weak for the time to help the models; the later ones are stronger. **The setting was chosen after seeing how the models behaved**, so the with-time gains in section 6 are conditional on this choice.

| setting | F concurrency | F security | F complexity | F coupling | F dependency | base sigma | noise sigma | outside weight |
|---|---|---|---|---|---|---|---|---|
| cfg0_weak | 3 | 2.200 | 1.700 | 1.350 | 1.100 | 0.450 | 0.120 | 0.600 |
| cfg1_selected | 3.400 | 2.400 | 1.800 | 1.400 | 1.050 | 0.300 | 0.080 | 0.850 |
| cfg2_strong | 4 | 2.600 | 1.800 | 1.350 | 1.050 | 0.250 | 0.060 | 0.900 |
| cfg3_near_deterministic | 4 | 2.600 | 1.800 | 1.350 | 1.050 | 0.150 | 0.040 | 1 |

### accuracy of the time alone, and the gain in accuracy from adding the time (with - without)

| setting | protocol | time_alone_accuracy | gain from time: random forest | gain from time: logistic regression | gain from time: ten-best + random forest |
|---|---|---|---|---|---|
| cfg0_weak | given stratified folds | 0.656 | 0.016 | 0 | 0.049 |
| cfg0_weak | project folds | 0.574 | -0.049 | 0 | 0 |
| cfg0_weak | 10 random splits | 0.602 | 0.025 | 0.015 | 0.030 |
| cfg1_selected | given stratified folds | 0.934 | 0.066 | 0.066 | 0.115 |
| cfg1_selected | project folds | 0.934 | 0.033 | 0 | 0.230 |
| cfg1_selected | 10 random splits | 0.957 | 0.036 | 0.025 | 0.111 |
| cfg2_strong | given stratified folds | 0.984 | 0.066 | 0.066 | 0.131 |
| cfg2_strong | project folds | 0.967 | 0.033 | 0 | 0.230 |
| cfg2_strong | 10 random splits | 0.984 | 0.036 | 0.028 | 0.120 |
| cfg3_near_deterministic | given stratified folds | 1 | 0.066 | 0.066 | 0.131 |
| cfg3_near_deterministic | project folds | 1 | 0.033 | 0 | 0.230 |
| cfg3_near_deterministic | 10 random splits | 1 | 0.036 | 0.033 | 0.121 |

Note: the row `cfg1_selected` is the setting of the dataset, yet its gains differ a little from section 5 (ten-best + random forest on the given folds: +0.115 here, +0.131 in section 5). The values of the time column are identical; here the time column is appended after the other features, in the dataset files it is the first feature column, and the selector's tie-breaking and the trees depend on the column order. The size of this difference (about 0.02 accuracy for one split of 61 pairs) is the run-to-run noise to keep in mind when reading single-split numbers.

## 4.4 Controls: shuffled time and noisy time (delta layout)

The time column was replaced before the experiment: **shuffled** = the same values assigned to random pairs (negative control: the gain must vanish); **log-multiplicative noise** = each value times exp(N(0, s)); **additive noise** = N(0, k x std of the column) added. Real values: no change. Noise is applied to training and test rows alike.

### kbest10_random_forest

| variant | acc given_by_project | acc repeated_stratified |
|---|---|---|
| (no time at all) | 0.311 | 0.840 |
| real | 0.508 | 0.939 |
| shuffled | 0.311 | 0.839 |
| logmult:0.25 | 0.459 | 0.926 |
| logmult:0.5 | 0.328 | 0.884 |
| logmult:1.0 | 0.311 | 0.839 |
| additive:0.5 | 0.377 | 0.856 |
| additive:1.0 | 0.279 | 0.841 |
| additive:2.0 | 0.311 | 0.839 |

### gradient_boosting

| variant | acc given_by_project | acc repeated_stratified |
|---|---|---|
| (no time at all) | 0.443 | 0.883 |
| real | 0.475 | 0.969 |
| shuffled | 0.443 | 0.895 |
| logmult:0.25 | 0.475 | 0.967 |
| logmult:0.5 | 0.459 | 0.957 |
| logmult:1.0 | 0.426 | 0.910 |
| additive:0.5 | 0.443 | 0.887 |
| additive:1.0 | 0.443 | 0.890 |
| additive:2.0 | 0.443 | 0.895 |

### share of the gain that remains (10 random splits; 1 = the full gain of the real time values, 0 = no gain)

| model | variant | accuracy | gain_over_no_time | share_of_real_gain |
|---|---|---|---|---|
| kbest10_random_forest | real | 0.939 | 0.100 | 1 |
| kbest10_random_forest | shuffled | 0.839 | 0 | 0 |
| kbest10_random_forest | logmult:0.25 | 0.926 | 0.087 | 0.869 |
| kbest10_random_forest | logmult:0.5 | 0.884 | 0.044 | 0.443 |
| kbest10_random_forest | logmult:1.0 | 0.839 | 0 | 0 |
| kbest10_random_forest | additive:0.5 | 0.856 | 0.016 | 0.164 |
| kbest10_random_forest | additive:1.0 | 0.841 | 0.002 | 0.016 |
| kbest10_random_forest | additive:2.0 | 0.839 | 0 | 0 |
| gradient_boosting | real | 0.969 | 0.075 | 1 |
| gradient_boosting | shuffled | 0.895 | 0.002 | 0.022 |
| gradient_boosting | logmult:0.25 | 0.967 | 0.074 | 0.978 |
| gradient_boosting | logmult:0.5 | 0.957 | 0.064 | 0.848 |
| gradient_boosting | logmult:1.0 | 0.910 | 0.016 | 0.217 |
| gradient_boosting | additive:0.5 | 0.887 | -0.007 | -0.087 |
| gradient_boosting | additive:1.0 | 0.890 | -0.003 | -0.043 |
| gradient_boosting | additive:2.0 | 0.895 | 0.002 | 0.022 |

How to read it: the 'shuffled' rows show what the models do with a time column that carries no information about the pair; the noise rows show how much of the gain survives when the time is a noisy measurement of the effect.
