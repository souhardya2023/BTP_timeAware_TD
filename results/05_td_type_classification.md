# 5. TD-type classification: model with the time feature vs model without it

Task: from the features of a pair predict `td_type` (5 classes). 61 datapoints (concurrency 26, security 16, dependency_structure 7, coupling_cohesion 6, complexity 6). Everything except `time_diff_min` is identical between the two models of a pair of runs (rows, features, folds, classifier and settings).

## 5.1 Setup

| item | setting |
|---|---|
| layouts | `full`: clean__ + td__ + delta__ features (399, +1 with time); `delta_only`: delta__ features (133, +1 with time) |
| classifiers (fixed settings, nothing tuned on a test fold) | random_forest (300 trees, balanced class weights); gradient_boosting (100 trees, depth 2); logistic_regression (standardised, C=1, balanced); svm_rbf (standardised, C=3, balanced); knn (k=3, standardised); kbest10_random_forest and kbest10_logistic_regression (the 10 features with the highest ANOVA F against td_type, selected inside every training fold, then the classifier) |
| protocols | given_stratified (5 folds, stratified by TD type); repeated_stratified (20 random stratified 5-fold splits); given_by_project (5 folds, a project in one fold only); leave_one_project_out (10 folds, one project each) |
| baselines | majority = the most frequent class of the training folds (the largest class, concurrency, is 26 of 61 = 0.426 of the data; when whole projects are held out the training majority can be a class that is rare in the test project, which gives very low values); time_diff_min alone (random forest) |
| metrics | accuracy; macro-F1 (mean of the 5 class F1); balanced accuracy |
| runs | 656 runs in `data/ml_metrics.csv` |

## 5.2 Complete results, all classifiers (accuracy / macro-F1, without time -> with time)

### layout `delta_only`

**given stratified folds (`fold`)**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.836 / 0.766 | 0.918 / 0.919 | +0.082 | +0.153 |
| kbest10_logistic_regression | 0.525 / 0.550 | 0.803 / 0.687 | +0.279 | +0.137 |
| kbest10_random_forest | 0.787 / 0.674 | 0.918 / 0.863 | +0.131 | +0.190 |
| knn | 0.639 / 0.447 | 0.639 / 0.442 | +0.000 | -0.005 |
| logistic_regression | 0.721 / 0.611 | 0.787 / 0.688 | +0.066 | +0.077 |
| random_forest | 0.885 / 0.811 | 0.885 / 0.820 | +0.000 | +0.008 |
| svm_rbf | 0.705 / 0.604 | 0.705 / 0.596 | +0.000 | -0.008 |

baselines: majority 0.426 / 0.120; time_only 0.934 / 0.918

**20 random stratified 5-fold splits (mean)**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.883 / 0.795 | 0.968 / 0.953 | +0.085 | +0.158 |
| kbest10_logistic_regression | 0.659 / 0.626 | 0.854 / 0.782 | +0.195 | +0.155 |
| kbest10_random_forest | 0.840 / 0.757 | 0.938 / 0.900 | +0.098 | +0.143 |
| knn | 0.677 / 0.515 | 0.679 / 0.516 | +0.002 | +0.001 |
| logistic_regression | 0.792 / 0.674 | 0.814 / 0.707 | +0.022 | +0.033 |
| random_forest | 0.893 / 0.819 | 0.919 / 0.860 | +0.025 | +0.040 |
| svm_rbf | 0.730 / 0.608 | 0.745 / 0.625 | +0.016 | +0.016 |

**given project folds (`fold_by_project`)**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.443 / 0.449 | 0.475 / 0.515 | +0.033 | +0.066 |
| kbest10_logistic_regression | 0.098 / 0.112 | 0.246 / 0.257 | +0.148 | +0.145 |
| kbest10_random_forest | 0.311 / 0.339 | 0.508 / 0.600 | +0.197 | +0.261 |
| knn | 0.148 / 0.177 | 0.148 / 0.177 | +0.000 | +0.000 |
| logistic_regression | 0.262 / 0.357 | 0.262 / 0.350 | +0.000 | -0.007 |
| random_forest | 0.459 / 0.462 | 0.459 / 0.463 | +0.000 | +0.001 |
| svm_rbf | 0.098 / 0.065 | 0.098 / 0.065 | +0.000 | +0.000 |

baselines: majority 0.033 / 0.013; time_only 0.934 / 0.949

**leave one project out**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.426 / 0.408 | 0.459 / 0.489 | +0.033 | +0.080 |
| kbest10_logistic_regression | 0.148 / 0.180 | 0.328 / 0.297 | +0.180 | +0.117 |
| kbest10_random_forest | 0.426 / 0.376 | 0.508 / 0.565 | +0.082 | +0.189 |
| knn | 0.197 / 0.200 | 0.197 / 0.200 | +0.000 | +0.000 |
| logistic_regression | 0.311 / 0.390 | 0.328 / 0.392 | +0.016 | +0.002 |
| random_forest | 0.459 / 0.475 | 0.459 / 0.472 | +0.000 | -0.003 |
| svm_rbf | 0.115 / 0.071 | 0.115 / 0.070 | +0.000 | -0.001 |

baselines: majority 0.033 / 0.013; time_only 0.934 / 0.949

### layout `full`

**given stratified folds (`fold`)**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.787 / 0.744 | 0.803 / 0.785 | +0.016 | +0.041 |
| kbest10_logistic_regression | 0.672 / 0.422 | 0.820 / 0.724 | +0.148 | +0.302 |
| kbest10_random_forest | 0.705 / 0.544 | 0.820 / 0.785 | +0.115 | +0.241 |
| knn | 0.738 / 0.594 | 0.738 / 0.594 | +0.000 | +0.000 |
| logistic_regression | 0.787 / 0.668 | 0.787 / 0.668 | +0.000 | +0.000 |
| random_forest | 0.787 / 0.726 | 0.803 / 0.749 | +0.016 | +0.023 |
| svm_rbf | 0.738 / 0.621 | 0.738 / 0.621 | +0.000 | +0.000 |

baselines: majority 0.426 / 0.120; time_only 0.934 / 0.918

**20 random stratified 5-fold splits (mean)**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.857 / 0.781 | 0.929 / 0.911 | +0.072 | +0.130 |
| kbest10_logistic_regression | 0.703 / 0.469 | 0.863 / 0.813 | +0.160 | +0.343 |
| kbest10_random_forest | 0.781 / 0.659 | 0.927 / 0.914 | +0.146 | +0.255 |
| knn | 0.722 / 0.548 | 0.722 / 0.548 | +0.000 | +0.000 |
| logistic_regression | 0.811 / 0.683 | 0.811 / 0.683 | +0.001 | +0.001 |
| random_forest | 0.853 / 0.795 | 0.876 / 0.838 | +0.023 | +0.043 |
| svm_rbf | 0.784 / 0.668 | 0.785 / 0.669 | +0.001 | +0.001 |

**given project folds (`fold_by_project`)**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.361 / 0.381 | 0.410 / 0.466 | +0.049 | +0.085 |
| kbest10_logistic_regression | 0.180 / 0.161 | 0.262 / 0.218 | +0.082 | +0.057 |
| kbest10_random_forest | 0.115 / 0.190 | 0.279 / 0.326 | +0.164 | +0.136 |
| knn | 0.311 / 0.273 | 0.311 / 0.273 | +0.000 | +0.000 |
| logistic_regression | 0.361 / 0.372 | 0.361 / 0.372 | +0.000 | +0.000 |
| random_forest | 0.377 / 0.384 | 0.393 / 0.426 | +0.016 | +0.042 |
| svm_rbf | 0.082 / 0.044 | 0.082 / 0.044 | +0.000 | +0.000 |

baselines: majority 0.033 / 0.013; time_only 0.934 / 0.949

**leave one project out**

| model | without_time | with_time | change_accuracy | change_f1 |
|---|---|---|---|---|
| gradient_boosting | 0.328 / 0.331 | 0.393 / 0.449 | +0.066 | +0.117 |
| kbest10_logistic_regression | 0.131 / 0.065 | 0.197 / 0.148 | +0.066 | +0.083 |
| kbest10_random_forest | 0.246 / 0.147 | 0.377 / 0.355 | +0.131 | +0.207 |
| knn | 0.328 / 0.278 | 0.328 / 0.278 | +0.000 | +0.000 |
| logistic_regression | 0.410 / 0.434 | 0.410 / 0.426 | +0.000 | -0.008 |
| random_forest | 0.410 / 0.422 | 0.393 / 0.431 | -0.016 | +0.008 |
| svm_rbf | 0.164 / 0.162 | 0.164 / 0.162 | +0.000 | +0.000 |

baselines: majority 0.033 / 0.013; time_only 0.934 / 0.949

## 5.3 Is the difference with / without time real? (the final model `kbest10_random_forest`)

| layout | protocol | acc_without | ci95_without | acc_with | ci95_with | difference | ci95_difference | fixed_by_time | broken_by_time | mcnemar_p |
|---|---|---|---|---|---|---|---|---|---|---|
| delta_only | given_by_project | 0.311 | 0.21-0.44 | 0.508 | 0.39-0.63 | +0.197 | +0.10 to +0.30 | 12 | 0 | 0.000 |
| delta_only | given_stratified | 0.787 | 0.67-0.87 | 0.918 | 0.82-0.96 | +0.131 | +0.05 to +0.23 | 8 | 0 | 0.008 |
| delta_only | leave_one_project_out | 0.426 | 0.31-0.55 | 0.508 | 0.39-0.63 | +0.082 | +0.02 to +0.16 | 5 | 0 | 0.062 |
| full | given_by_project | 0.115 | 0.06-0.22 | 0.279 | 0.18-0.40 | +0.164 | +0.08 to +0.26 | 10 | 0 | 0.002 |
| full | given_stratified | 0.705 | 0.58-0.80 | 0.820 | 0.71-0.90 | +0.115 | +0.03 to +0.20 | 7 | 0 | 0.016 |
| full | leave_one_project_out | 0.246 | 0.16-0.37 | 0.377 | 0.27-0.50 | +0.131 | +0.05 to +0.21 | 8 | 0 | 0.008 |

Wilson 95% intervals of a single accuracy are about +-0.10 with 61 pairs. 'fixed_by_time' = pairs predicted right with the time but wrong without it; 'broken_by_time' = the reverse. The difference interval is a paired bootstrap over the 61 pairs (2000 resamples); the McNemar test is exact.

### over 20 random splits (kbest10_random_forest)

| layout | repeats | acc_without_mean | acc_without_sd | acc_with_mean | acc_with_sd | diff_mean | diff_min | diff_max | splits_with_better | splits_equal | splits_worse |
|---|---|---|---|---|---|---|---|---|---|---|---|
| delta_only | 20 | 0.840 | 0.029 | 0.938 | 0.017 | 0.098 | 0.049 | 0.148 | 20 | 0 | 0 |
| full | 20 | 0.781 | 0.028 | 0.927 | 0.023 | 0.146 | 0.082 | 0.197 | 20 | 0 | 0 |

The 20 splits reuse the same 61 pairs, so a p-value over them would be optimistic and none is quoted; the useful information is that the with-time model was better in every split and the range of the difference.

### all classifiers, deterministic splits (paired comparison)

| layout | protocol | model | acc_without | acc_with | diff | pairs_fixed_by_time | pairs_broken_by_time | mcnemar_p |
|---|---|---|---|---|---|---|---|---|
| delta_only | given_by_project | gradient_boosting | 0.443 | 0.475 | +0.033 | 2 | 0 | 0.500 |
| delta_only | given_by_project | kbest10_logistic_regression | 0.098 | 0.246 | +0.148 | 9 | 0 | 0.004 |
| delta_only | given_by_project | kbest10_random_forest | 0.311 | 0.508 | +0.197 | 12 | 0 | 0.000 |
| delta_only | given_by_project | knn | 0.148 | 0.148 | +0.000 | 0 | 0 | 1.000 |
| delta_only | given_by_project | logistic_regression | 0.262 | 0.262 | +0.000 | 0 | 0 | 1.000 |
| delta_only | given_by_project | random_forest | 0.459 | 0.459 | +0.000 | 1 | 1 | 1.000 |
| delta_only | given_by_project | svm_rbf | 0.098 | 0.098 | +0.000 | 0 | 0 | 1.000 |
| delta_only | given_stratified | gradient_boosting | 0.836 | 0.918 | +0.082 | 5 | 0 | 0.062 |
| delta_only | given_stratified | kbest10_logistic_regression | 0.525 | 0.803 | +0.279 | 21 | 4 | 0.001 |
| delta_only | given_stratified | kbest10_random_forest | 0.787 | 0.918 | +0.131 | 8 | 0 | 0.008 |
| delta_only | given_stratified | knn | 0.639 | 0.639 | +0.000 | 0 | 0 | 1.000 |
| delta_only | given_stratified | logistic_regression | 0.721 | 0.787 | +0.066 | 4 | 0 | 0.125 |
| delta_only | given_stratified | random_forest | 0.885 | 0.885 | +0.000 | 2 | 2 | 1.000 |
| delta_only | given_stratified | svm_rbf | 0.705 | 0.705 | +0.000 | 0 | 0 | 1.000 |
| delta_only | leave_one_project_out | gradient_boosting | 0.426 | 0.459 | +0.033 | 3 | 1 | 0.625 |
| delta_only | leave_one_project_out | kbest10_logistic_regression | 0.148 | 0.328 | +0.180 | 11 | 0 | 0.001 |
| delta_only | leave_one_project_out | kbest10_random_forest | 0.426 | 0.508 | +0.082 | 5 | 0 | 0.062 |
| delta_only | leave_one_project_out | knn | 0.197 | 0.197 | +0.000 | 0 | 0 | 1.000 |
| delta_only | leave_one_project_out | logistic_regression | 0.311 | 0.328 | +0.016 | 1 | 0 | 1.000 |
| delta_only | leave_one_project_out | random_forest | 0.459 | 0.459 | +0.000 | 1 | 1 | 1.000 |
| delta_only | leave_one_project_out | svm_rbf | 0.115 | 0.115 | +0.000 | 0 | 0 | 1.000 |
| full | given_by_project | gradient_boosting | 0.361 | 0.410 | +0.049 | 4 | 1 | 0.375 |
| full | given_by_project | kbest10_logistic_regression | 0.180 | 0.262 | +0.082 | 5 | 0 | 0.062 |
| full | given_by_project | kbest10_random_forest | 0.115 | 0.279 | +0.164 | 10 | 0 | 0.002 |
| full | given_by_project | knn | 0.311 | 0.311 | +0.000 | 0 | 0 | 1.000 |
| full | given_by_project | logistic_regression | 0.361 | 0.361 | +0.000 | 0 | 0 | 1.000 |
| full | given_by_project | random_forest | 0.377 | 0.393 | +0.016 | 1 | 0 | 1.000 |
| full | given_by_project | svm_rbf | 0.082 | 0.082 | +0.000 | 0 | 0 | 1.000 |
| full | given_stratified | gradient_boosting | 0.787 | 0.803 | +0.016 | 1 | 0 | 1.000 |
| full | given_stratified | kbest10_logistic_regression | 0.672 | 0.820 | +0.148 | 9 | 0 | 0.004 |
| full | given_stratified | kbest10_random_forest | 0.705 | 0.820 | +0.115 | 7 | 0 | 0.016 |
| full | given_stratified | knn | 0.738 | 0.738 | +0.000 | 0 | 0 | 1.000 |
| full | given_stratified | logistic_regression | 0.787 | 0.787 | +0.000 | 0 | 0 | 1.000 |
| full | given_stratified | random_forest | 0.787 | 0.803 | +0.016 | 2 | 1 | 1.000 |
| full | given_stratified | svm_rbf | 0.738 | 0.738 | +0.000 | 0 | 0 | 1.000 |
| full | leave_one_project_out | gradient_boosting | 0.328 | 0.393 | +0.066 | 5 | 1 | 0.219 |
| full | leave_one_project_out | kbest10_logistic_regression | 0.131 | 0.197 | +0.066 | 4 | 0 | 0.125 |
| full | leave_one_project_out | kbest10_random_forest | 0.246 | 0.377 | +0.131 | 8 | 0 | 0.008 |
| full | leave_one_project_out | knn | 0.328 | 0.328 | +0.000 | 0 | 0 | 1.000 |
| full | leave_one_project_out | logistic_regression | 0.410 | 0.410 | +0.000 | 0 | 0 | 1.000 |
| full | leave_one_project_out | random_forest | 0.410 | 0.393 | -0.016 | 0 | 1 | 1.000 |
| full | leave_one_project_out | svm_rbf | 0.164 | 0.164 | +0.000 | 0 | 0 | 1.000 |

## 5.4 Per class (final model, delta layout; precision / recall / F1)

**given stratified folds (`fold`)**

| td_type | pairs | without time P/R/F1 | with time P/R/F1 |
|---|---|---|---|
| complexity | 6 | 1.00 / 0.67 / 0.80 | 1.00 / 0.67 / 0.80 |
| concurrency | 26 | 0.96 / 0.92 / 0.94 | 1.00 / 1.00 / 1.00 |
| coupling_cohesion | 6 | 0.43 / 0.50 / 0.46 | 0.83 / 0.83 / 0.83 |
| dependency_structure | 7 | 0.33 / 0.29 / 0.31 | 0.83 / 0.71 / 0.77 |
| security | 16 | 0.79 / 0.94 / 0.86 | 0.84 / 1.00 / 0.91 |

**given project folds (`fold_by_project`)**

| td_type | pairs | without time P/R/F1 | with time P/R/F1 |
|---|---|---|---|
| complexity | 6 | 0.50 / 1.00 / 0.67 | 1.00 / 1.00 / 1.00 |
| concurrency | 26 | 0.20 / 0.08 / 0.11 | 0.50 / 0.08 / 0.13 |
| coupling_cohesion | 6 | 0.40 / 0.33 / 0.36 | 0.60 / 1.00 / 0.75 |
| dependency_structure | 7 | 0.50 / 0.14 / 0.22 | 1.00 / 0.43 / 0.60 |
| security | 16 | 0.25 / 0.50 / 0.33 | 0.37 / 0.88 / 0.52 |

**leave one project out**

| td_type | pairs | without time P/R/F1 | with time P/R/F1 |
|---|---|---|---|
| complexity | 6 | 0.45 / 0.83 / 0.59 | 1.00 / 0.83 / 0.91 |
| concurrency | 26 | 1.00 / 0.08 / 0.14 | 1.00 / 0.08 / 0.14 |
| coupling_cohesion | 6 | 0.33 / 0.17 / 0.22 | 0.56 / 0.83 / 0.67 |
| dependency_structure | 7 | 0.50 / 0.29 / 0.36 | 0.75 / 0.43 / 0.55 |
| security | 16 | 0.39 / 1.00 / 0.56 | 0.39 / 1.00 / 0.56 |

The concurrency class is the weak point under the project-held-out protocols: 24 of its 26 pairs come from one project (boltons), so when boltons is held out only 2 concurrency pairs (C-Thread-Pool) remain for training. This is a property of the data, not of the time feature.

## 5.5 Per held-out project (leave one project out; accuracy; final model, delta layout)

| project | pairs | TD types of the project | without time | with time |
|---|---|---|---|---|
| C-Thread-Pool | 4 | concurrency,security | 1 | 1 |
| boltons | 24 | concurrency | 0 | 0 |
| cJSON | 1 | dependency_structure | 0 | 1 |
| click | 10 | complexity,coupling_cohesion,dependency_structure | 0.300 | 0.600 |
| jansson | 6 | complexity,dependency_structure,security | 0.833 | 0.833 |
| jinja | 5 | complexity,coupling_cohesion | 0.600 | 0.800 |
| libpng | 1 | security | 1 | 1 |
| libyaml | 5 | security | 1 | 1 |
| werkzeug | 2 | security | 1 | 1 |
| zlib | 3 | dependency_structure,security | 1 | 1 |

## 5.6 Confusion matrices (random forest, pooled predictions, rows = true type)

**delta_only, given project folds (`fold_by_project`), random forest without time**

| index | complexity | concurrency | coupling_cohesion | dependency_structure | security |
|---|---|---|---|---|---|
| complexity | 5 | 0 | 1 | 0 | 0 |
| concurrency | 0 | 2 | 0 | 0 | 24 |
| coupling_cohesion | 1 | 0 | 3 | 2 | 0 |
| dependency_structure | 0 | 0 | 5 | 2 | 0 |
| security | 0 | 0 | 0 | 0 | 16 |

**delta_only, given project folds (`fold_by_project`), random forest with time**

| index | complexity | concurrency | coupling_cohesion | dependency_structure | security |
|---|---|---|---|---|---|
| complexity | 5 | 0 | 1 | 0 | 0 |
| concurrency | 0 | 2 | 0 | 0 | 24 |
| coupling_cohesion | 1 | 0 | 2 | 3 | 0 |
| dependency_structure | 0 | 0 | 4 | 3 | 0 |
| security | 0 | 0 | 0 | 0 | 16 |

**delta_only, leave one project out, random forest without time**

| index | complexity | concurrency | coupling_cohesion | dependency_structure | security |
|---|---|---|---|---|---|
| complexity | 5 | 0 | 1 | 0 | 0 |
| concurrency | 0 | 2 | 0 | 0 | 24 |
| coupling_cohesion | 0 | 0 | 3 | 3 | 0 |
| dependency_structure | 0 | 0 | 4 | 2 | 1 |
| security | 0 | 0 | 0 | 0 | 16 |

**delta_only, leave one project out, random forest with time**

| index | complexity | concurrency | coupling_cohesion | dependency_structure | security |
|---|---|---|---|---|---|
| complexity | 5 | 0 | 1 | 0 | 0 |
| concurrency | 0 | 2 | 0 | 0 | 24 |
| coupling_cohesion | 0 | 0 | 2 | 4 | 0 |
| dependency_structure | 0 | 0 | 4 | 3 | 0 |
| security | 0 | 0 | 0 | 0 | 16 |

## 5.7 What the models use

Top features of a random forest with time on all 61 pairs, layout `delta_only`:

| rank | feature | importance |
|---|---|---|
| 1 | time_diff_min | 0.0834 |
| 2 | delta__t_conc_lock_per_kloc | 0.0415 |
| 3 | delta__c_fn_nloc_mean | 0.0320 |
| 4 | delta__c_funcs_per_kloc | 0.0320 |
| 5 | delta__t_satd_requirement | 0.0320 |
| 6 | delta__c_loc | 0.0307 |
| 7 | delta__c_file_sloc_log_mean | 0.0301 |
| 8 | delta__t_satd_defect | 0.0283 |
| 9 | delta__c_fn_nloc_std | 0.0230 |
| 10 | delta__s_fan_in_mean | 0.0223 |
| 11 | delta__c_sloc | 0.0222 |
| 12 | delta__c_blank_ratio | 0.0218 |

Top features of a random forest with time on all 61 pairs, layout `full`:

| rank | feature | importance |
|---|---|---|
| 1 | time_diff_min | 0.0437 |
| 2 | delta__c_fn_nloc_mean | 0.0274 |
| 3 | delta__c_loc | 0.0189 |
| 4 | td__s_graph_edges_per_node | 0.0186 |
| 5 | delta__s_file_bytes_log_mean | 0.0185 |
| 6 | delta__c_blank_ratio | 0.0176 |
| 7 | delta__s_fan_out_mean | 0.0168 |
| 8 | delta__t_satd_defect | 0.0167 |
| 9 | delta__s_fan_in_mean | 0.0159 |
| 10 | delta__c_sloc | 0.0154 |
| 11 | td__s_fan_in_mean | 0.0144 |
| 12 | delta__c_file_sloc_log_mean | 0.0138 |

* selected by the ten-best step (delta_only, with time): `time_diff_min`, `delta__s_graph_edges_per_node`, `delta__s_fan_in_mean`, `delta__s_fan_out_mean`, `delta__c_loc`, `delta__c_sloc`, `delta__c_fn_nloc_std`, `delta__c_py_raise_per_kloc`, `delta__t_principal_pm`, `delta__t_very_complex`
* selected by the ten-best step (delta_only, without time): `delta__s_graph_edges_per_node`, `delta__s_fan_in_mean`, `delta__s_fan_out_mean`, `delta__c_loc`, `delta__c_sloc`, `delta__c_fn_nloc_std`, `delta__c_py_raise_per_kloc`, `delta__t_principal_pm`, `delta__t_very_complex`, `delta__t_satd_doc`
* selected by the ten-best step (full, with time): `time_diff_min`, `clean__s_fan_out_p50`, `clean__s_isolated_share`, `clean__s_weak_components`, `clean__t_satd_requirement`, `td__s_cyc_largest`, `td__s_fan_out_p50`, `td__s_isolated_share`, `td__s_weak_components`, `td__t_satd_requirement`
* selected by the ten-best step (full, without time): `clean__s_fan_out_p50`, `clean__s_isolated_share`, `clean__s_weak_components`, `clean__t_satd_requirement`, `td__s_cyc_largest`, `td__s_fan_in_p90`, `td__s_fan_out_p50`, `td__s_isolated_share`, `td__s_weak_components`, `td__t_satd_requirement`

The time feature is selected in both layouts and ranks first by random-forest importance.
