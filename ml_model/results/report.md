# Results: model with the time feature vs model without it

Target: `td_type` (5 classes), 61 pairs. Time feature: `time_diff_min` (minutes to fix the 3 injected bugs in the TD project minus in the clean project; values from the ground-truth time model).
Accuracy / macro-F1; the repeated protocol is the mean over 20 random stratified 5-fold splits. Majority class = 0.43 accuracy.

## Headline: best model without time vs best model with time

| layout | protocol | best without time (acc) | best with time (acc) |
|---|---|---|---|
| full | given_stratified | gradient_boosting 0.79 (F1 0.74) | kbest10_logistic_regression 0.82 (F1 0.72) |
| full | repeated_stratified | gradient_boosting 0.86 (F1 0.78) | gradient_boosting 0.93 (F1 0.91) |
| full | given_by_project | random_forest 0.38 (F1 0.38) | gradient_boosting 0.41 (F1 0.47) |
| full | leave_one_project_out | logistic_regression 0.41 (F1 0.43) | logistic_regression 0.41 (F1 0.43) |
| delta_only | given_stratified | random_forest 0.89 (F1 0.81) | gradient_boosting 0.92 (F1 0.92) |
| delta_only | repeated_stratified | random_forest 0.89 (F1 0.82) | gradient_boosting 0.97 (F1 0.95) |
| delta_only | given_by_project | random_forest 0.46 (F1 0.46) | kbest10_random_forest 0.51 (F1 0.60) |
| delta_only | leave_one_project_out | random_forest 0.46 (F1 0.47) | kbest10_random_forest 0.51 (F1 0.56) |

(`majority` below = the most frequent class of the training folds; when whole projects are held out it can be a class that is rare in the test project, hence very low values.)

## Layout `full`

### given_stratified

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.79 / 0.74 | 0.80 / 0.79 | +0.02 | 100% of 1 run(s) |
| kbest10_logistic_regression | 0.67 / 0.42 | 0.82 / 0.72 | +0.15 | 100% of 1 run(s) |
| kbest10_random_forest | 0.70 / 0.54 | 0.82 / 0.79 | +0.12 | 100% of 1 run(s) |
| knn | 0.74 / 0.59 | 0.74 / 0.59 | +0.00 | 100% of 1 run(s) |
| logistic_regression | 0.79 / 0.67 | 0.79 / 0.67 | +0.00 | 100% of 1 run(s) |
| random_forest | 0.79 / 0.73 | 0.80 / 0.75 | +0.02 | 100% of 1 run(s) |
| svm_rbf | 0.74 / 0.62 | 0.74 / 0.62 | +0.00 | 100% of 1 run(s) |

baselines: majority acc 0.43 / F1 0.12; time_only acc 0.93 / F1 0.92

### repeated_stratified

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.86 / 0.78 | 0.93 / 0.91 | +0.07 (sd 0.02) | 100% of 20 run(s) |
| kbest10_logistic_regression | 0.70 / 0.47 | 0.86 / 0.81 | +0.16 (sd 0.03) | 100% of 20 run(s) |
| kbest10_random_forest | 0.78 / 0.66 | 0.93 / 0.91 | +0.15 (sd 0.03) | 100% of 20 run(s) |
| knn | 0.72 / 0.55 | 0.72 / 0.55 | +0.00 (sd 0.00) | 100% of 20 run(s) |
| logistic_regression | 0.81 / 0.68 | 0.81 / 0.68 | +0.00 (sd 0.00) | 100% of 20 run(s) |
| random_forest | 0.85 / 0.80 | 0.88 / 0.84 | +0.02 (sd 0.02) | 95% of 20 run(s) |
| svm_rbf | 0.78 / 0.67 | 0.79 / 0.67 | +0.00 (sd 0.00) | 100% of 20 run(s) |

### given_by_project

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.36 / 0.38 | 0.41 / 0.47 | +0.05 | 100% of 1 run(s) |
| kbest10_logistic_regression | 0.18 / 0.16 | 0.26 / 0.22 | +0.08 | 100% of 1 run(s) |
| kbest10_random_forest | 0.12 / 0.19 | 0.28 / 0.33 | +0.16 | 100% of 1 run(s) |
| knn | 0.31 / 0.27 | 0.31 / 0.27 | +0.00 | 100% of 1 run(s) |
| logistic_regression | 0.36 / 0.37 | 0.36 / 0.37 | +0.00 | 100% of 1 run(s) |
| random_forest | 0.38 / 0.38 | 0.39 / 0.43 | +0.02 | 100% of 1 run(s) |
| svm_rbf | 0.08 / 0.04 | 0.08 / 0.04 | +0.00 | 100% of 1 run(s) |

baselines: majority acc 0.03 / F1 0.01; time_only acc 0.93 / F1 0.95

### leave_one_project_out

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.33 / 0.33 | 0.39 / 0.45 | +0.07 | 100% of 1 run(s) |
| kbest10_logistic_regression | 0.13 / 0.07 | 0.20 / 0.15 | +0.07 | 100% of 1 run(s) |
| kbest10_random_forest | 0.25 / 0.15 | 0.38 / 0.35 | +0.13 | 100% of 1 run(s) |
| knn | 0.33 / 0.28 | 0.33 / 0.28 | +0.00 | 100% of 1 run(s) |
| logistic_regression | 0.41 / 0.43 | 0.41 / 0.43 | +0.00 | 100% of 1 run(s) |
| random_forest | 0.41 / 0.42 | 0.39 / 0.43 | -0.02 | 0% of 1 run(s) |
| svm_rbf | 0.16 / 0.16 | 0.16 / 0.16 | +0.00 | 100% of 1 run(s) |

baselines: majority acc 0.03 / F1 0.01; time_only acc 0.93 / F1 0.95

## Layout `delta_only`

### given_stratified

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.84 / 0.77 | 0.92 / 0.92 | +0.08 | 100% of 1 run(s) |
| kbest10_logistic_regression | 0.53 / 0.55 | 0.80 / 0.69 | +0.28 | 100% of 1 run(s) |
| kbest10_random_forest | 0.79 / 0.67 | 0.92 / 0.86 | +0.13 | 100% of 1 run(s) |
| knn | 0.64 / 0.45 | 0.64 / 0.44 | +0.00 | 100% of 1 run(s) |
| logistic_regression | 0.72 / 0.61 | 0.79 / 0.69 | +0.07 | 100% of 1 run(s) |
| random_forest | 0.89 / 0.81 | 0.89 / 0.82 | +0.00 | 100% of 1 run(s) |
| svm_rbf | 0.70 / 0.60 | 0.70 / 0.60 | +0.00 | 100% of 1 run(s) |

baselines: majority acc 0.43 / F1 0.12; time_only acc 0.93 / F1 0.92

### repeated_stratified

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.88 / 0.80 | 0.97 / 0.95 | +0.09 (sd 0.03) | 100% of 20 run(s) |
| kbest10_logistic_regression | 0.66 / 0.63 | 0.85 / 0.78 | +0.20 (sd 0.05) | 100% of 20 run(s) |
| kbest10_random_forest | 0.84 / 0.76 | 0.94 / 0.90 | +0.10 (sd 0.03) | 100% of 20 run(s) |
| knn | 0.68 / 0.52 | 0.68 / 0.52 | +0.00 (sd 0.01) | 95% of 20 run(s) |
| logistic_regression | 0.79 / 0.67 | 0.81 / 0.71 | +0.02 (sd 0.02) | 100% of 20 run(s) |
| random_forest | 0.89 / 0.82 | 0.92 / 0.86 | +0.03 (sd 0.02) | 100% of 20 run(s) |
| svm_rbf | 0.73 / 0.61 | 0.74 / 0.62 | +0.02 (sd 0.02) | 100% of 20 run(s) |

### given_by_project

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.44 / 0.45 | 0.47 / 0.52 | +0.03 | 100% of 1 run(s) |
| kbest10_logistic_regression | 0.10 / 0.11 | 0.25 / 0.26 | +0.15 | 100% of 1 run(s) |
| kbest10_random_forest | 0.31 / 0.34 | 0.51 / 0.60 | +0.20 | 100% of 1 run(s) |
| knn | 0.15 / 0.18 | 0.15 / 0.18 | +0.00 | 100% of 1 run(s) |
| logistic_regression | 0.26 / 0.36 | 0.26 / 0.35 | +0.00 | 100% of 1 run(s) |
| random_forest | 0.46 / 0.46 | 0.46 / 0.46 | +0.00 | 100% of 1 run(s) |
| svm_rbf | 0.10 / 0.07 | 0.10 / 0.07 | +0.00 | 100% of 1 run(s) |

baselines: majority acc 0.03 / F1 0.01; time_only acc 0.93 / F1 0.95

### leave_one_project_out

| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |
|---|---|---|---|---|
| gradient_boosting | 0.43 / 0.41 | 0.46 / 0.49 | +0.03 | 100% of 1 run(s) |
| kbest10_logistic_regression | 0.15 / 0.18 | 0.33 / 0.30 | +0.18 | 100% of 1 run(s) |
| kbest10_random_forest | 0.43 / 0.38 | 0.51 / 0.56 | +0.08 | 100% of 1 run(s) |
| knn | 0.20 / 0.20 | 0.20 / 0.20 | +0.00 | 100% of 1 run(s) |
| logistic_regression | 0.31 / 0.39 | 0.33 / 0.39 | +0.02 | 100% of 1 run(s) |
| random_forest | 0.46 / 0.47 | 0.46 / 0.47 | +0.00 | 100% of 1 run(s) |
| svm_rbf | 0.12 / 0.07 | 0.12 / 0.07 | +0.00 | 100% of 1 run(s) |

baselines: majority acc 0.03 / F1 0.01; time_only acc 0.93 / F1 0.95

## Where the time feature ranks in a random forest (all 61 pairs)

| layout | features | rank of time_diff_min | importance |
|---|---|---|---|
| full | 400 | 1 | 0.044 |
| delta_only | 134 | 1 | 0.083 |

Confusion matrices of the random forest on the two project-held-out protocols: `confusion_*.csv`. All runs: `metrics.csv`; per-pair predictions: `predictions.csv`.
