# 7. The earlier experiments of the study and how they compare

These experiments tried other tasks before the TD-type classification. They are listed with their numbers and with an honest verdict on how valid and how comparable they are.

## 7.1 The first prediction model (target = COCOMO effort of the injected patch)

Files: `data/earlier_all_projects_predictions.csv`, `earlier_model_comparison_predictions.csv`.

| evaluation | result | comment |
|---|---|---|
| reported in the earlier analysis (random forest, 80/20 split) | R2 0.8986, MSE 0.002075 | single split on a target that is a formula of the patch size |
| same model, 5-fold cross-validation (this study, recomputed) | R2 0.533, MSE 0.0259 | rows of one project sit in several folds |
| same model, leave-one-project-out (this study, recomputed) | R2 -0.428, MSE 0.0791 | projects not seen in training |

Problems found in this model: (1) the target `Target_PM` is an exact function of `Lines_Added` (confirmed), i.e. it predicts the size of the injected patch, not an effort caused by debt; (2) the join key was the pair name only, which repeats in `Python/` and `C_C++/`: 20 of 61 rows carry another pair's project and 18 another pair's TD type, and no C/C++ project is actually in the data; (3) 'historical interest' summed all added lines of every commit that touched the file, before the injected smell existed.

**Verdict:** the 0.90 R2 does not measure what it was meant to; with a project-held-out evaluation the same model has R2 < 0. Not comparable with the classification task, and superseded.

## 7.2 Interest paid by technical debt, predicted from git history (2025 method)

### (a) function-level smells followed through 700 commits per repository (9 repositories, 6153 snapshots)

Task: will a smell function absorb any interest in the next 100 commits (AUC; 0.5 = chance).

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

### (b) release-by-release instances (SonarQube issues for Python, structural smells for C/C++; 20,582 instance-transitions, 7.8% pay interest in the next version)

| protocol | model | AUC | PR_AUC | Spearman | MAE_lines |
|---|---|---|---|---|---|
| leave-one-repo-out | all_features | 0.594 | 0.169 | 0.099 | 0.606 |
| leave-one-repo-out | history_only | 0.494 | 0.141 | 0.016 | 0.561 |
| leave-one-repo-out | prior | 0.500 | 0.122 |  | 0.526 |
| leave-one-repo-out | size_only | 0.556 | 0.148 | 0.085 | 0.642 |
| temporal | all_features | 0.713 | 0.224 | 0.207 | 0.349 |
| temporal | history_only | 0.519 | 0.119 | 0.088 | 0.353 |
| temporal | prior | 0.500 | 0.090 |  | 0.329 |
| temporal | size_only | 0.613 | 0.152 | 0.150 | 0.308 |

### (c) the interest model applied to the dataset pairs (predicted interest lines of the touched functions, TD minus clean)

| td_type | pairs | touched_function_is_a_smell | mean_delta_lines | share_delta_positive |
|---|---|---|---|---|
| complexity | 6 | 5 | 3.088 | 0.833 |
| concurrency | 26 | 2 | -0.001 | 0 |
| coupling_cohesion | 6 | 3 | 0.017 | 0.333 |
| dependency_structure | 7 | 4 | 1.591 | 0.286 |
| security | 16 | 5 | -0.204 | 0.062 |

40 of 61 pairs touch no function that is a smell on either side, so a smell-based interest model gives them no score.

**Verdict:** the signal is weak but real for a task with a real target (AUC 0.57-0.59 for held-out projects, 0.63-0.71 for later versions, chance = 0.5; the history features alone are at chance); it does not apply to security and concurrency debt, which add no size or complexity. Different task from the classification; not comparable by metric.

## 7.3 Predicting the time to remove bugs from the project vector (bug lifetime from git history, SZZ)

Label: median age at removal (days) of the bugs fixed in the year after a release snapshot (119 snapshots of 9 repositories). A first label, 'days until the last open bug is fixed', saturated at its 365-day cap for every repository and could not be learned.

| features | n_features | model | R2 | spearman | MAE_days |
|---|---|---|---|---|---|
| size_only | 3 | ridge | -0.123 | -0.196 | 572.935 |
| size_only | 3 | rf | -0.537 | -0.171 | 635.165 |
| history | 29 | ridge | -0.269 | 0.132 | 571.721 |
| history | 29 | rf | -0.246 | 0.111 | 565.122 |
| structure | 47 | ridge | -2.075 | -0.160 | 605.140 |
| structure | 47 | rf | -0.304 | -0.168 | 596.866 |
| code | 51 | ridge | -0.305 | -0.144 | 586.109 |
| code | 51 | rf | -0.276 | -0.218 | 592.730 |
| td | 38 | ridge | -1.120 | 0.200 | 6543.116 |
| td | 38 | rf | -0.128 | 0.099 | 568.033 |
| static (s+c+td) | 134 | ridge | -0.283 | 0.261 | 652.578 |
| static (s+c+td) | 134 | rf | -0.303 | -0.165 | 588.809 |
| static w/o td | 97 | ridge | -1.112 | -0.066 | 596.823 |
| static w/o td | 97 | rf | -0.397 | -0.247 | 605.425 |
| embeddings only | 97 | ridge | -1.998 | -0.406 | 14408.770 |
| embeddings only | 97 | rf | -0.127 | -0.102 | 562.416 |
| all | 258 | ridge | -1.971 | -0.169 | 7205.751 |
| all | 258 | rf | -0.206 | -0.014 | 579.479 |
| all w/o td | 221 | ridge | -2.502 | -0.208 | 8612.139 |
| all w/o td | 221 | rf | -0.237 | -0.104 | 585.398 |

Best R2 across all feature sets and models (leave one repository out): -0.123; best Spearman 0.261.

**Verdict:** no out-of-sample skill (R2 < 0 everywhere): 119 points from 9 projects cannot support a 258-dimensional vector. Dropped; the time label was then defined per bug and pair (section 4).
