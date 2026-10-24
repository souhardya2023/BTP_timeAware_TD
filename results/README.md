# results - every experiment, every number

All experiments of the study with their numbers, the comparison of the current setup with the previous one, and the controls. Start with `00_executive_summary.md`.

| document | content |
|---|---|
| `00_executive_summary.md` | main result, findings, how to read |
| `01_dataset.md` | construction, composition, validation, bugs |
| `02_audit_and_features.md` | metric audit, the 133 features |
| `03_history_and_sonarqube.md` | git history, SZZ, SonarQube, interest |
| `04_time_feature.md` | time model, calibration, controls |
| `05_td_type_classification.md` | main experiment |
| `06_ablations.md` | dataset versions, feature groups, layouts |
| `07_earlier_experiments.md` | earlier prediction attempts |
| `08_current_vs_previous.md` | is current better than previous |
| `09_limits_and_threats.md` | limits |

## Experiment register

| id | question | document | data files |
|---|---|---|---|
| E01 | How was the dataset built; what is in it; do the tests pass on both sides | 01 | properties_all_pairs.csv, dropped_unchanged.csv |
| E02 | Do the TD changes move a metric of their own type (102 pairs; the 50 removed) | 02 | dropped_unchanged.csv |
| E03 | Same audit on the final 61 pairs | 02 | td_audit_final_61.csv |
| E04 | Which features differ between the TD types (ANOVA) | 02 | feature_anova_by_td_type.csv |
| E05 | Git history and SZZ bug mining per project | 03 | git_history_summary.csv |
| E06 | SonarQube: server export, per-release scans | 03 | (project_dataset/sonarqube_server) |
| E07 | Version-wise interest of smell instances (2025 method) | 03, 07 | interest_transitions_*.csv |
| E08 | Re-evaluation of the first prediction model (patch-size effort) | 07 | earlier_*.csv |
| E09 | Interest from git history, function-level snapshots | 07 | interest_snapshot_model_results.csv |
| E10 | Interest, release-by-release instances | 07 | interest_version_model_results.csv |
| E11 | Interest model applied to the dataset pairs | 07 | interest_pair_scores.csv |
| E12 | Bug lifetime predicted from the project vector | 07 | bug_lifetime_model_results.csv, bug_lifetime_summary.txt |
| E13 | The time model: distributions and calibration sweep (x3) | 04 | x3_time_model_sweep.csv, time_model_sweep_summary.csv |
| E14 | Time controls: shuffled and noisy time (x2) | 04 | x2_time_controls.csv, time_controls_summary.csv |
| E15 | TD-type classification: 7 classifiers x 2 layouts x 4 protocols x with / without time (656 runs) | 05 | ml_metrics.csv, ml_summary.csv, ml_time_effect.csv, ml_predictions.csv |
| E16 | Significance: McNemar, bootstrap and Wilson intervals (x4) | 05, 08 | x4_*.csv, comparison_with_vs_without_time.csv |
| E17 | Per class, per project, confusion matrices, importances (x5) | 05 | x5_*.csv, ml_confusion_*.csv, ml_importance.csv |
| E18 | Dataset versions: bug-free vs with bugs vs with time (x0) | 06, 08 | x0_old_dataset_runs.csv, dataset_versions_summary.csv |
| E19 | Feature blocks (x1) | 06 | x1_feature_blocks.csv, feature_blocks_summary.csv |
| E20 | Layouts and selector vs plain classifiers | 06, 08 | ml_time_effect.csv |

## Glossary of the metrics

| term | meaning |
|---|---|
| accuracy | share of pairs whose TD type is predicted right |
| macro-F1 | mean over the 5 types of the F1 score (harmonic mean of precision and recall); every type counts equally, so rare types matter |
| balanced accuracy | mean recall over the 5 types |
| precision / recall (per type) | of the pairs predicted as the type, the share that is right / of the pairs of the type, the share found |
| AUC | chance that a pair that pays interest gets a higher score than one that does not; 0.5 = chance |
| R2 | regression: 1 = perfect, 0 = as good as predicting the mean, negative = worse than the mean |
| Spearman | rank correlation between predicted and true values |
| 95% CI (Wilson) | interval of one accuracy given the number of pairs |
| paired bootstrap CI | interval of the accuracy difference with / without time, resampling the 61 pairs 2000 times |
| McNemar p | exact test on the pairs where the two models disagree |

## Protocols

| name | meaning |
|---|---|
| given_stratified | given stratified folds (`fold`) |
| repeated_stratified | 20 random stratified 5-fold splits (mean) |
| given_by_project | given project folds (`fold_by_project`) |
| leave_one_project_out | leave one project out |

## How these documents were produced
`scripts/extra_experiments.py` runs the ablations and controls (about 25 minutes, seeds fixed) and writes `data/x*.csv`; `scripts/build_results.py` reads the results of all experiments (`ml_model/results`, `data/`, the earlier working folders) and writes the documents, so every number comes from a file. Library versions: numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1, scipy 1.18.1; Python 3.13.13.

## Files in data/

| file | size |
|---|---|
| `data/bug_lifetime_model_results.csv` | 4 KB |
| `data/bug_lifetime_summary.txt` | 3 KB |
| `data/comparison_with_vs_without_time.csv` | 1 KB |
| `data/dataset_versions_summary.csv` | 4 KB |
| `data/dropped_unchanged.csv` | 2 KB |
| `data/earlier_all_projects_predictions.csv` | 11 KB |
| `data/earlier_historical_analysis_all_pairs.csv` | 4 KB |
| `data/earlier_model_comparison_predictions.csv` | 14 KB |
| `data/extra_experiments.log` | 0 KB |
| `data/feature_anova_by_td_type.csv` | 5 KB |
| `data/feature_blocks_summary.csv` | 2 KB |
| `data/git_history_summary.csv` | 0 KB |
| `data/interest_pair_scores.csv` | 4 KB |
| `data/interest_snapshot_model_results.csv` | 4 KB |
| `data/interest_transitions_boltons.csv` | 944 KB |
| `data/interest_transitions_cJSON.csv` | 127 KB |
| `data/interest_transitions_click.csv` | 193 KB |
| `data/interest_transitions_jansson.csv` | 105 KB |
| `data/interest_transitions_jinja.csv` | 353 KB |
| `data/interest_transitions_libpng.csv` | 932 KB |
| `data/interest_transitions_libyaml.csv` | 166 KB |
| `data/interest_transitions_werkzeug.csv` | 466 KB |
| `data/interest_transitions_zlib.csv` | 211 KB |
| `data/interest_version_model_results.csv` | 4 KB |
| `data/ml_confusion_delta_only_given_by_project_with_time.csv` | 0 KB |
| `data/ml_confusion_delta_only_given_by_project_without_time.csv` | 0 KB |
| `data/ml_confusion_delta_only_leave_one_project_out_with_time.csv` | 0 KB |
| `data/ml_confusion_delta_only_leave_one_project_out_without_time.csv` | 0 KB |
| `data/ml_confusion_full_given_by_project_with_time.csv` | 0 KB |
| `data/ml_confusion_full_given_by_project_without_time.csv` | 0 KB |
| `data/ml_confusion_full_leave_one_project_out_with_time.csv` | 0 KB |
| `data/ml_confusion_full_leave_one_project_out_without_time.csv` | 0 KB |
| `data/ml_importance.csv` | 26 KB |
| `data/ml_metrics.csv` | 69 KB |
| `data/ml_predictions.csv` | 483 KB |
| `data/ml_summary.csv` | 8 KB |
| `data/ml_time_effect.csv` | 5 KB |
| `data/td_audit_final_61.csv` | 6 KB |
| `data/time_controls_summary.csv` | 2 KB |
| `data/time_model_sweep_summary.csv` | 1 KB |
| `data/x0_old_dataset_runs.csv` | 38 KB |
| `data/x1_feature_blocks.csv` | 38 KB |
| `data/x2_time_controls.csv` | 18 KB |
| `data/x3_time_model_sweep.csv` | 37 KB |
| `data/x4_significance_deterministic_splits.csv` | 8 KB |
| `data/x4_significance_repeated_splits.csv` | 2 KB |
| `data/x5_per_class.csv` | 18 KB |
| `data/x5_per_project.csv` | 8 KB |
