# Executive summary

**What was done.** A dataset of 61 project pairs (a real open-source project, and the same project with technical debt of one of 5 types induced) was built; 3 bugs were injected into every pair (the same bugs on both sides); every bugged project was turned into a 133-number vector (structure, code shape, technical debt); a fix-time value per pair (`time_diff_min`) was added; and classifiers of the TD type were trained and compared with and without that time feature.

## Main result (final model: ten-best-feature selector + random forest, delta layout)

| protocol | without_time | with_time | difference | verdict |
|---|---|---|---|---|
| given_stratified | 0.787 | 0.918 | 0.131 | better, clear |
| repeated_stratified | 0.840 | 0.938 | 0.098 | better, clear |
| given_by_project | 0.311 | 0.508 | 0.197 | better, clear |
| leave_one_project_out | 0.426 | 0.508 | 0.082 | better, borderline |

Accuracy; the largest class (concurrency) is 0.43 of the data. The 95% Wilson interval of one accuracy with 61 pairs is about +-0.10. 'Clear' = bootstrap interval above 0 and McNemar p < 0.05 (section 8).

Best classifier of any kind (delta layout): given stratified folds (`fold`): without time 0.89 (random_forest), with time 0.92 (gradient_boosting); 20 random stratified 5-fold splits (mean): without time 0.89 (random_forest), with time 0.97 (gradient_boosting); given project folds (`fold_by_project`): without time 0.46 (random_forest), with time 0.51 (kbest10_random_forest); leave one project out: without time 0.46 (random_forest), with time 0.51 (kbest10_random_forest).

## Findings

1. **The time feature improves the classification** for the selector-based models in every protocol and layout (+0.07 to +0.28 accuracy over all 16 comparisons); the final model gains +0.08 to +0.20 (delta layout). For the plain classifiers the change is small (-0.02 to +0.09): one column among hundreds is hardly used.
2. **The time values come from the ground-truth time model** (assumed per-type slow-down factors). The gain is therefore conditional on that model: the shuffled-time control removes it and strong noise reduces it (section 4.4). The calibration of the time model was done after seeing how the classifiers behaved (section 4.3).
3. **Project identity is the main confounder**: with random splits accuracy is 0.84 (delta layout, without time); with whole projects held out it is 0.31 to 0.43. Use `fold_by_project`.
4. **The concurrency class cannot be learned across projects**: 24 of its 26 pairs come from boltons, so with boltons held out the model has seen only 2 concurrency pairs and predicts the other 24 as security (section 5.6).
5. **The bugs do not change the TD-type accuracy** (v2 - v1 = +0.000 on average, section 6.1); the technical-debt and code features carry the information without time, and with time every feature block works (section 6.2).
6. **Earlier experiments** (patch-size regression, interest from git history, bug lifetime) had invalid or very weak evaluations and are superseded (section 7).

## How to read the results folder

| file | content |
|---|---|
| 01_dataset.md | construction stages and counts, composition, validation, bugs |
| 02_audit_and_features.md | metric audit of the TD changes; the 133 features; which features differ between TD types |
| 03_history_and_sonarqube.md | git history, SZZ bugs, SonarQube, version-wise interest |
| 04_time_feature.md | the time model, its distributions, calibration sweep, shuffled / noisy controls |
| 05_td_type_classification.md | the main experiment: all classifiers, protocols, significance, per class, per project, confusion matrices, features used |
| 06_ablations.md | dataset versions, feature groups, layouts, selector |
| 07_earlier_experiments.md | the first prediction model, interest models, bug-lifetime model |
| 08_current_vs_previous.md | is the current setup better than the previous one |
| 09_limits_and_threats.md | what could make the results wrong or not general |
| data/ | every table as CSV, plus logs |
| scripts/ | `extra_experiments.py` (ablations and controls) and `build_results.py` (these documents) |
