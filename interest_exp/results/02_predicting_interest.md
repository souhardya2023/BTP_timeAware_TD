# 2. Predicting the interest

Three prediction tasks on the instances of section 1, all evaluated on data the model has not seen: **leave-one-repo-out** (train on 8 projects, test on the 9th) and **temporal** (train on the releases before 60% of each project's history, test on the later ones).

## 2.1 Will an instance pay any interest in the next release? (classification)

| protocol | model | AUC | PR_AUC | Spearman |
|---|---|---|---|---|
| leave-one-repo-out | all_features | 0.594 | 0.169 | 0.099 |
| leave-one-repo-out | history_only | 0.494 | 0.141 | 0.016 |
| leave-one-repo-out | prior | 0.500 | 0.122 |  |
| leave-one-repo-out | size_only | 0.556 | 0.148 | 0.085 |
| temporal | all_features | 0.713 | 0.224 | 0.207 |
| temporal | history_only | 0.519 | 0.119 | 0.088 |
| temporal | prior | 0.500 | 0.090 |  |
| temporal | size_only | 0.613 | 0.152 | 0.150 |

7.8% of the instance-releases pay interest. AUC 0.5 = chance. Per held-out project (all features):

| held-out project | n | share_with_interest | AUC | Spearman |
|---|---|---|---|---|
| boltons | 5760 | 0.033 | 0.681 | 0.118 |
| cJSON | 797 | 0.034 | 0.501 | -0.018 |
| click | 1160 | 0.134 | 0.671 | 0.215 |
| jansson | 604 | 0.281 | 0.578 | 0.103 |
| jinja | 2095 | 0.093 | 0.619 | 0.101 |
| libpng | 5362 | 0.043 | 0.561 | 0.035 |
| libyaml | 841 | 0.136 | 0.517 | 0.020 |
| werkzeug | 2665 | 0.053 | 0.593 | 0.082 |
| zlib | 1298 | 0.293 | 0.622 | 0.231 |

## 2.2 How much interest, in person-months? (regression, unit mPM = milli-person-months)

Target: effort of the interest of one instance between two releases (0 for the 92% that pay none). Models: `zero` (predict no interest), `mean`, `persistence` (average interest of that instance so far, converted with COCOMO II), `size_only_rf` (region size, complexity, principal), `rf_pm` (random forest on all features, PM scale), `gb_pm` (gradient boosting), `hurdle_rf` (P(any interest) x expected PM given interest). `skill_vs_zero` = 1 - MAE / MAE of the zero model (positive = better than predicting no interest).

### leave-one-repo-out

| model | n | MAE_mPM | RMSE_mPM | R2 | skill_vs_zero | spearman_all | spearman_positives | AUC_any_interest | actual_total_mPM | predicted_total_mPM |
|---|---|---|---|---|---|---|---|---|---|---|
| zero | 20582 | 0.511 | 3.950 | -0.017 | 0 |  |  |  | 10520.571 | 0 |
| mean | 20582 | 1.003 | 3.929 | -0.007 | -0.963 | -0.198 | -0.071 | 0.293 | 10520.571 | 11745.159 |
| persistence | 20582 | 0.905 | 4.177 | -0.137 | -0.770 | 0.168 | 0.089 | 0.651 | 10520.571 | 10590.184 |
| size_only_rf | 20582 | 1.438 | 4.320 | -0.217 | -1.813 | 0.106 | -0.003 | 0.614 | 10520.571 | 22227.669 |
| rf_pm | 20582 | 1.420 | 4.363 | -0.241 | -1.779 | 0.112 | 0.025 | 0.620 | 10520.571 | 21871.770 |
| gb_pm | 20582 | 1.253 | 4.819 | -0.514 | -1.452 | 0.110 | 0.036 | 0.618 | 10520.571 | 17946.432 |
| hurdle_rf | 20582 | 0.995 | 3.947 | -0.015 | -0.946 | 0.084 | -0.020 | 0.590 | 10520.571 | 12008.125 |

### temporal

| model | n | MAE_mPM | RMSE_mPM | R2 | skill_vs_zero | spearman_all | spearman_positives | AUC_any_interest | actual_total_mPM | predicted_total_mPM |
|---|---|---|---|---|---|---|---|---|---|---|
| zero | 8535 | 0.480 | 3.469 | -0.020 | 0 |  |  |  | 4096.012 | 0 |
| mean | 8535 | 0.918 | 3.437 | -0.000 | -0.914 |  |  | 0.500 | 4096.012 | 4551.640 |
| persistence | 8535 | 0.996 | 3.776 | -0.208 | -1.076 | 0.209 | 0.139 | 0.695 | 4096.012 | 5912.860 |
| size_only_rf | 8535 | 0.796 | 3.466 | -0.017 | -0.659 | 0.174 | 0.114 | 0.674 | 4096.012 | 3640.557 |
| rf_pm | 8535 | 1.257 | 4.448 | -0.676 | -1.619 | 0.208 | 0.095 | 0.708 | 4096.012 | 8199.158 |
| gb_pm | 8535 | 1.003 | 3.680 | -0.147 | -1.089 | 0.117 | 0.026 | 0.618 | 4096.012 | 5469.253 |
| hurdle_rf | 8535 | 1.017 | 3.483 | -0.028 | -1.120 | 0.179 | 0.172 | 0.679 | 4096.012 | 5894.531 |

**Reading:** no model has a positive skill against the zero model in MAE; the best R2 is -0.0002 (R2 = 0 means no better than predicting the mean). The amount of interest of an instance cannot be predicted from these features. What exists is a weak **ranking** signal: AUC for 'any interest' up to 0.708 (chance 0.5), Spearman correlation of the predicted and real PM among the instances that paid up to 0.172. The two-part model `hurdle_rf` predicts the **overall total** well: predicted total / actual total = 1.14 (leave-one-repo-out) and 1.44 (temporal).

Best ranking of the instances by predicted PM (AUC for 'any interest'): temporal: rf_pm 0.708; leave-one-repo-out: persistence 0.651. The simple `persistence` rule (average interest of the instance so far) ranks as well as the learned models.

### per held-out project, total interest predicted vs actual (leave-one-repo-out, mPM)

| project | actual_total_mPM | persistence predicted | rf_pm predicted | hurdle_rf predicted |
|---|---|---|---|---|
| boltons | 524.1 | 443.5 | 3077.5 | 3801.1 |
| cJSON | 93.9 | 36.6 | 235.5 | 336.5 |
| click | 1322.9 | 764.7 | 1372.9 | 772.5 |
| jansson | 1597.2 | 1596.3 | 713.1 | 223.6 |
| jinja | 2441.2 | 2829.5 | 1492.3 | 1086.1 |
| libpng | 1331.5 | 2056.4 | 9471.8 | 3081.9 |
| libyaml | 341.1 | 536.8 | 993.3 | 460.8 |
| werkzeug | 554.7 | 401.1 | 2651.3 | 1607.1 |
| zlib | 2313.9 | 1925.2 | 1864.1 | 638.4 |

### totals per repository and release pair (sum of the instance predictions vs the actual sum; points = repository x release pair)

| protocol | model | points | pearson | spearman | R2 | MAE_mPM | total_ratio_pred_over_actual |
|---|---|---|---|---|---|---|---|
| leave-one-repo-out | zero | 164 |  |  | -0.165 | 64.150 | 0 |
| leave-one-repo-out | mean | 164 | -0.055 | 0.044 | -0.227 | 93.899 | 1.116 |
| leave-one-repo-out | persistence | 164 | 0.068 | 0.235 | -0.122 | 83.771 | 1.007 |
| leave-one-repo-out | size_only_rf | 164 | 0.005 | 0.046 | -1.348 | 140.840 | 2.113 |
| leave-one-repo-out | rf_pm | 164 | -0.015 | 0.157 | -1.218 | 136.454 | 2.079 |
| leave-one-repo-out | gb_pm | 164 | -0.024 | 0.152 | -0.932 | 117.982 | 1.706 |
| leave-one-repo-out | hurdle_rf | 164 | -0.061 | 0.038 | -0.239 | 94.296 | 1.141 |
| temporal | zero | 69 |  |  | -0.270 | 59.362 | 0 |
| temporal | mean | 69 | -0.164 | -0.136 | -0.345 | 79.009 | 1.111 |
| temporal | persistence | 69 | 0.107 | 0.266 | -0.280 | 81.718 | 1.444 |
| temporal | size_only_rf | 69 | 0.048 | 0.243 | -0.048 | 61.801 | 0.889 |
| temporal | rf_pm | 69 | 0.003 | 0.165 | -1.243 | 105.965 | 2.002 |
| temporal | gb_pm | 69 | -0.099 | -0.009 | -0.430 | 83.917 | 1.335 |
| temporal | hurdle_rf | 69 | -0.094 | 0.027 | -0.347 | 84.549 | 1.439 |

### total interest of a repository in the next release, predicted directly from the state at the current release

Features: number of instances, total principal, mean age, interest so far, interest of the previous release, language. Baselines: zero, mean, `persistence` = the interest of the previous release.

| protocol | model | points | MAE_mPM | skill_vs_zero | R2 | pearson | spearman |
|---|---|---|---|---|---|---|---|
| leave-one-repo-out | mean | 155 | 82.283 | -0.242 | -0.020 | -0.269 | -0.291 |
| leave-one-repo-out | persistence | 155 | 102.127 | -0.542 | -1.067 | -0.035 | 0.116 |
| leave-one-repo-out | random_forest | 155 | 124.436 | -0.878 | -0.388 | -0.255 | -0.183 |
| leave-one-repo-out | ridge | 155 | 100.017 | -0.510 | -0.141 | -0.097 | -0.192 |
| leave-one-repo-out | zero | 155 | 66.251 | 0 | -0.167 |  |  |
| temporal | mean | 69 | 71.729 | -0.208 | -0.012 |  |  |
| temporal | persistence | 69 | 87.910 | -0.481 | -1.387 | -0.002 | 0.069 |
| temporal | random_forest | 69 | 116.929 | -0.970 | -0.496 | 0.282 | 0.258 |
| temporal | ridge | 69 | 111.711 | -0.882 | -0.581 | -0.010 | 0.134 |
| temporal | zero | 69 | 59.362 | 0 | -0.270 |  |  |

### what the random forest uses (importance, `rf_pm`)

| feature | importance |
|---|---|
| age | 0.3180 |
| ccn0 | 0.1515 |
| nloc0 | 0.1268 |
| principal_pm | 0.1162 |
| past_il | 0.1104 |
| sonar_effort_min | 0.0730 |
| past_n | 0.0469 |
| rule=complex_method | 0.0095 |
| rule=long_method | 0.0085 |
| lang_c | 0.0078 |
| rule=python:S8513 | 0.0055 |
| rule=python:S3776 | 0.0050 |

## 2.3 Function-level model on the commit history (next 100 commits)

Every 40 commits of the last 700 (all commits for smaller projects), every function that is a smell (Long Method / Complex Method / Many Parameters) is a snapshot; features come from the history before the snapshot; the target is the interest (lines and PM) the function absorbs in the next 100 commits. 6,153 snapshots from 9 projects.

| protocol | model | AUC | PR_AUC | Spearman | MAE_lines |
|---|---|---|---|---|---|
| leave-one-project-out | all_features | 0.568 | 0.534 | 0.142 | 5.648 |
| leave-one-project-out | history_only | 0.535 | 0.514 | 0.095 | 5.388 |
| leave-one-project-out | prior (mean) | 0.500 | 0.484 |  | 5.269 |
| leave-one-project-out | size_only | 0.523 | 0.498 | 0.077 | 5.790 |
| temporal | all_features | 0.625 | 0.583 | 0.221 | 3.620 |
| temporal | history_only | 0.611 | 0.551 | 0.202 | 3.664 |
| temporal | prior (mean) | 0.500 | 0.451 |  | 3.622 |
| temporal | size_only | 0.567 | 0.518 | 0.174 | 3.621 |

Per held-out project (all features, leave-one-project-out):

| fold | n | pos_rate | AUC | PR_AUC | Spearman | MAE_lines |
|---|---|---|---|---|---|---|
| boltons.git | 465 | 0.258 | 0.567 | 0.285 | 0.074 | 2.551 |
| cJSON.git | 152 | 0.612 | 0.705 | 0.741 | 0.288 | 15.485 |
| click.git | 607 | 0.560 | 0.505 | 0.578 | 0.100 | 5.150 |
| jansson.git | 187 | 0.824 | 0.575 | 0.851 | 0.300 | 9.719 |
| jinja.git | 588 | 0.354 | 0.566 | 0.401 | 0.174 | 3.283 |
| libpng.git | 2320 | 0.233 | 0.558 | 0.258 | 0.108 | 2.674 |
| libyaml.git | 135 | 0.467 | 0.671 | 0.636 | 0.157 | 4.362 |
| werkzeug.git | 1063 | 0.659 | 0.535 | 0.697 | 0.093 | 4.979 |
| zlib.git | 636 | 0.393 | 0.433 | 0.360 | -0.019 | 2.627 |
