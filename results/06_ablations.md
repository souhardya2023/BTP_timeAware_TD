# 6. Ablations: what matters in the setup

## 6.1 Earlier dataset vs current dataset vs current dataset with time

v1 = the earlier dataset (vectors of the projects **without** the injected bugs, no time); v2 = the current vectors (projects with the 3 bugs), no time; v3 = v2 plus `time_diff_min`. Same classifiers and folds. Accuracy (mean over the 20 splits for the repeated protocol).

| layout | model | protocol | v1_bug_free | v2_bugs | v3_bugs_and_time | v2_minus_v1 | v3_minus_v2 |
|---|---|---|---|---|---|---|---|
| delta_only | kbest10_random_forest | given_stratified | 0.787 | 0.787 | 0.918 | 0 | 0.131 |
| delta_only | kbest10_random_forest | repeated_stratified | 0.840 | 0.840 | 0.938 | 0 | 0.098 |
| delta_only | kbest10_random_forest | given_by_project | 0.311 | 0.311 | 0.508 | 0 | 0.197 |
| delta_only | kbest10_random_forest | leave_one_project_out | 0.426 | 0.426 | 0.508 | 0 | 0.082 |
| delta_only | random_forest | given_stratified | 0.869 | 0.885 | 0.885 | 0.016 | 0 |
| delta_only | random_forest | repeated_stratified | 0.892 | 0.893 | 0.919 | 0.002 | 0.025 |
| delta_only | random_forest | given_by_project | 0.459 | 0.459 | 0.459 | 0 | 0 |
| delta_only | random_forest | leave_one_project_out | 0.459 | 0.459 | 0.459 | 0 | 0 |
| delta_only | gradient_boosting | given_stratified | 0.836 | 0.836 | 0.918 | 0 | 0.082 |
| delta_only | gradient_boosting | repeated_stratified | 0.883 | 0.883 | 0.968 | 0 | 0.085 |
| delta_only | gradient_boosting | given_by_project | 0.443 | 0.443 | 0.475 | 0 | 0.033 |
| delta_only | gradient_boosting | leave_one_project_out | 0.426 | 0.426 | 0.459 | 0 | 0.033 |
| delta_only | logistic_regression | given_stratified | 0.721 | 0.721 | 0.787 | 0 | 0.066 |
| delta_only | logistic_regression | repeated_stratified | 0.785 | 0.792 | 0.814 | 0.007 | 0.022 |
| delta_only | logistic_regression | given_by_project | 0.262 | 0.262 | 0.262 | 0 | 0 |
| delta_only | logistic_regression | leave_one_project_out | 0.311 | 0.311 | 0.328 | 0 | 0.016 |
| full | kbest10_random_forest | given_stratified | 0.705 | 0.705 | 0.820 | 0 | 0.115 |
| full | kbest10_random_forest | repeated_stratified | 0.781 | 0.781 | 0.927 | 0 | 0.146 |
| full | kbest10_random_forest | given_by_project | 0.115 | 0.115 | 0.279 | 0 | 0.164 |
| full | kbest10_random_forest | leave_one_project_out | 0.246 | 0.246 | 0.377 | 0 | 0.131 |
| full | random_forest | given_stratified | 0.787 | 0.787 | 0.803 | 0 | 0.016 |
| full | random_forest | repeated_stratified | 0.854 | 0.853 | 0.876 | -0.001 | 0.023 |
| full | random_forest | given_by_project | 0.377 | 0.377 | 0.393 | 0 | 0.016 |
| full | random_forest | leave_one_project_out | 0.410 | 0.410 | 0.393 | 0 | -0.016 |
| full | gradient_boosting | given_stratified | 0.787 | 0.787 | 0.803 | 0 | 0.016 |
| full | gradient_boosting | repeated_stratified | 0.856 | 0.857 | 0.929 | 0.001 | 0.072 |
| full | gradient_boosting | given_by_project | 0.361 | 0.361 | 0.410 | 0 | 0.049 |
| full | gradient_boosting | leave_one_project_out | 0.328 | 0.328 | 0.393 | 0 | 0.066 |
| full | logistic_regression | given_stratified | 0.803 | 0.787 | 0.787 | -0.016 | 0 |
| full | logistic_regression | repeated_stratified | 0.814 | 0.811 | 0.811 | -0.003 | 0.001 |
| full | logistic_regression | given_by_project | 0.361 | 0.361 | 0.361 | 0 | 0 |
| full | logistic_regression | leave_one_project_out | 0.410 | 0.410 | 0.410 | 0 | 0 |

* averaged over all rows above: v2 - v1 = +0.000, v3 - v2 = +0.052; v2 equals v1 exactly in 25 of 32 rows.
* how much the bugs change the vectors: 92.8% of all 24339 feature values (61 pairs x 399 columns) are identical to the bug-free vectors; for the others the change is 0.064 standard deviations of that feature on average (median 0.007, largest 12.36).

| block | share_of_values_identical | mean_change_in_std_units |
|---|---|---|
| code | 0.92109 | 0.00644 |
| structure | 0.95818 | 0.00001 |
| technical debt | 0.90090 | 0.00780 |

The bugs are a few changed operators per project, so the vectors hardly move and the accuracy without time is unchanged (v2 - v1 is zero for most rows); the time feature is what moves the accuracy.

## 6.2 Which feature group carries the information (delta layout; accuracy)

| model | features | n | random splits: without time | random splits: with time | project folds: without time | project folds: with time | leave one project out: without time | leave one project out: with time |
|---|---|---|---|---|---|---|---|---|
| kbest10_random_forest | structure | 46 | 0.616 | 0.949 | 0.213 | 0.541 | 0.230 | 0.541 |
| kbest10_random_forest | code | 50 | 0.834 | 0.918 | 0.393 | 0.459 | 0.393 | 0.443 |
| kbest10_random_forest | technical_debt | 37 | 0.795 | 0.949 | 0.246 | 0.492 | 0.230 | 0.475 |
| kbest10_random_forest | structure+code | 96 | 0.834 | 0.946 | 0.393 | 0.525 | 0.393 | 0.492 |
| kbest10_random_forest | structure+td | 83 | 0.821 | 0.943 | 0.279 | 0.426 | 0.279 | 0.492 |
| kbest10_random_forest | code+td | 87 | 0.825 | 0.939 | 0.295 | 0.492 | 0.344 | 0.492 |
| kbest10_random_forest | all_133 | 133 | 0.839 | 0.951 | 0.311 | 0.541 | 0.426 | 0.508 |
| random_forest | structure | 46 | 0.687 | 0.903 | 0.279 | 0.492 | 0.295 | 0.492 |
| random_forest | code | 50 | 0.839 | 0.913 | 0.426 | 0.459 | 0.426 | 0.459 |
| random_forest | technical_debt | 37 | 0.830 | 0.920 | 0.262 | 0.344 | 0.311 | 0.393 |
| random_forest | structure+code | 96 | 0.864 | 0.916 | 0.426 | 0.459 | 0.426 | 0.459 |
| random_forest | structure+td | 83 | 0.869 | 0.918 | 0.393 | 0.459 | 0.426 | 0.475 |
| random_forest | code+td | 87 | 0.861 | 0.900 | 0.426 | 0.459 | 0.459 | 0.443 |
| random_forest | all_133 | 133 | 0.890 | 0.926 | 0.459 | 0.492 | 0.459 | 0.475 |

With the final model: without time the best single block on random splits is `all_133` (0.839) and the worst `structure` (0.616); with time every block reaches 0.918 to 0.951, so on random splits the choice of block matters little once the time is available. On project folds the best block without time is `code` (0.393), with time `structure` (0.541).


Random splits = mean of 10 splits. Blocks are the difference columns `delta__s_*` (structure), `delta__c_*` (code shape), `delta__t_*` (technical debt). The time-only accuracy is in `ml_metrics.csv` (model `time_only`).

## 6.3 Layouts and classifiers

### full vs delta_only (final model, change when time is added in brackets)

| protocol | delta_only without | delta_only with | full without | full with |
|---|---|---|---|---|
| given_stratified | 0.787 | 0.918 | 0.705 | 0.820 |
| repeated_stratified | 0.840 | 0.938 | 0.781 | 0.927 |
| given_by_project | 0.311 | 0.508 | 0.115 | 0.279 |
| leave_one_project_out | 0.426 | 0.508 | 0.246 | 0.377 |

### plain classifiers vs the same classifier behind the ten-best selector (with time; accuracy)

| layout | protocol | random_forest | kbest10_random_forest | logistic_regression | kbest10_logistic_regression |
|---|---|---|---|---|---|
| delta_only | given_stratified | 0.885 | 0.918 | 0.787 | 0.803 |
| delta_only | repeated_stratified | 0.919 | 0.938 | 0.814 | 0.854 |
| delta_only | given_by_project | 0.459 | 0.508 | 0.262 | 0.246 |
| delta_only | leave_one_project_out | 0.459 | 0.508 | 0.328 | 0.328 |
| full | given_stratified | 0.803 | 0.820 | 0.787 | 0.820 |
| full | repeated_stratified | 0.876 | 0.927 | 0.811 | 0.863 |
| full | given_by_project | 0.393 | 0.279 | 0.361 | 0.262 |
| full | leave_one_project_out | 0.393 | 0.377 | 0.410 | 0.197 |

The selector matters most for the models that get the time: with hundreds of columns, a plain model uses one extra column only a little (change in accuracy from adding the time for the plain classifiers: -0.016 to +0.085; behind the selector: +0.066 to +0.279).
