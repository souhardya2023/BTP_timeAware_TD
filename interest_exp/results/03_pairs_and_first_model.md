# 3. The interest model applied to the dataset pairs, and the first prediction model

## 3.1 Interest model on the 61 pairs of the dataset

For every pair the functions touched by `td.patch` are located on the clean and on the TD side; a touched function that is a smell on a side gets features (its own metrics on that side + its real git history up to the base commit) and the function-level model predicts the interest it will absorb in the next 100 commits; a function that is not a smell on a side carries no debt there. Each pair is scored by a model trained **without** the project of the pair. delta = TD - clean (predicted interest lines).

| td_type | pairs | touched_function_is_a_smell | mean_delta_lines | share_delta_positive | mean_delta_p_any |
|---|---|---|---|---|---|
| complexity | 6 | 5 | 3.088 | 0.833 | 0.070 |
| concurrency | 26 | 2 | -0.001 | 0 | 0 |
| coupling_cohesion | 6 | 3 | 0.017 | 0.333 | 0.001 |
| dependency_structure | 7 | 4 | 1.591 | 0.286 | 0.082 |
| security | 16 | 5 | -0.204 | 0.062 | -0.077 |

40 of 61 pairs touch no function that is a smell on either side, so a smell-based interest model gives them no score (the TD changes of types security and concurrency add no size or complexity). Per pair: `pair_scores.csv`.

## 3.2 The first prediction model (target = effort of the injected patch size)

| evaluation | R2 | MSE |
|---|---|---|
| reported with the model (single 80/20 split, from the earlier summary) | 0.8986 | 0.0021 |
| 5-fold cross-validation (rows of one project in several folds) | 0.5332 | 0.0259 |
| leave one project out (4 projects) | -0.4278 | 0.0791 |
| column Pred_PM_Hist_Only of model_comparison_predictions.csv, as stored | 0.4713 | 0.0293 |
| column Pred_PM_Sonar_Only of model_comparison_predictions.csv, as stored | 0.7482 | 0.0140 |
| column Pred_PM_Combined of model_comparison_predictions.csv, as stored | 0.5407 | 0.0255 |

| check | result |
|---|---|
| target Target_PM is an exact function of Lines_Added (2.64 x KSLOC^0.91) | yes |
| rows whose project differs between the SonarQube side and the git-history side (pair-name join across Python/ and C_C++/) | 20 of 61 |
| rows whose TD type differs between the two sides | 18 of 61 |
| distinct projects actually present in the model data | boltons, click, jinja, werkzeug |
| distinct rows by (project, history-interest value): rows sharing identical history features | 26 duplicated feature rows |

The 0.90 R2 was computed on a target that is a formula of the patch size, on a data set in which 20 of 61 rows carry another pair's project (the join key was the pair name, which repeats in `Python/` and `C_C++/`); with whole projects held out the same model has R2 below 0. Superseded by the instance-level experiments above.
