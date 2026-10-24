# out_dataset - the input of the machine-learning models

Task: classify the technical-debt type of a pair, **5 classes** (`td_type`): complexity, concurrency, coupling_cohesion, dependency_structure, security.
61 datapoints (one per pair; class counts: concurrency 26, security 16, dependency_structure 7, coupling_cohesion 6, complexity 6).

```
out_dataset/
  full/         dataset_with_time.csv      dataset_without_time.csv     features: clean__* + td__* + delta__* (399)  [+ time_diff_min]
  delta_only/   dataset_with_time.csv      dataset_without_time.csv     features: delta__* (133)                     [+ time_diff_min]
  bugs.csv              one row per injected bug (183): where it is, its fix time in the clean and in the TD project
  FEATURES.md           what every column means
  feature_dictionary.csv, feature_groups.json, label_map.json
```
A `with_time` file and its `without_time` twin have the same rows, the same folds and the same other columns; the ONLY difference is the column `time_diff_min`.
So the experiment "model with time vs model without time" is: train the same model on both files, with the same `fold` column.

## Columns of every dataset file
| columns | role |
|---|---|
| `id`, `project`, `language` | identifiers - **not features** (and `project` leaks the label: pairs of one project share their TD type) |
| `fold` | 5-fold split stratified by `td_type` |
| `fold_by_project` | 5-fold split where a project is only in one fold (the honest one) |
| `td_type` | **target** (text) |
| `label` | target as integer: complexity 0, concurrency 1, coupling_cohesion 2, dependency_structure 3, security 4 |
| `time_diff_min` | **the time feature** (only in `dataset_with_time.csv`): minutes to fix the 3 injected bugs by hand in the TD project minus in the project without TD |
| `clean__<f>` / `td__<f>` / `delta__<f>` | feature `<f>` of the project without TD / with TD / their difference. 133 features `<f>` (structure `s_`, code shape `c_`, technical debt `t_`), see `FEATURES.md` |

Everything after `label` is a feature.

## The time feature
`time_diff_min` comes from `../pipeline/bug_injection/sample_times.py`: per bug a seeded random clean-project time (median 25 min) and a TD-project time that is longer by a factor depending on the TD type (concurrency 3.4, security 2.4, complexity 1.8, coupling_cohesion 1.4, dependency_structure 1.05, a little less when the bug is outside the file the TD touched). It is treated as ground truth and carries information about the type:

| TD type | pairs | time_diff_min (mean, min - max) |
|---|---|---|
| concurrency | 26 | 161.6 (110.5 - 235.8) |
| security | 16 | 92.0 (59.1 - 108.0) |
| complexity | 6 | 53.5 (46.6 - 61.7) |
| coupling_cohesion | 6 | 22.7 (17.2 - 31.1) |
| dependency_structure | 7 | 3.2 (-1.9 - 5.5) |

The time therefore helps a classifier (see the check below). Measured times can replace these values at any time: `python ../pipeline/make_dataset.py times FILLED.csv`.

## A design check (what happens with standard models)
5-fold cross-validation on these files, accuracy / macro-F1, without time -> with time (time alone: 0.93 accuracy with either split):
| layout | model | `fold` (stratified) | `fold_by_project` |
|---|---|---|---|
| full | random forest | 0.79 / 0.73 -> 0.84 / 0.82 | 0.38 / 0.38 -> 0.39 / 0.43 |
| full | gradient boosting | 0.77 / 0.72 -> 0.82 / 0.80 | 0.36 / 0.38 -> 0.41 / 0.47 |
| full | logistic regression | 0.79 / 0.67 -> 0.79 / 0.67 | 0.36 / 0.37 -> 0.36 / 0.37 |
| delta_only | random forest | 0.89 / 0.81 -> 0.95 / 0.92 | 0.46 / 0.46 -> 0.49 / 0.53 |
| delta_only | gradient boosting | 0.85 / 0.80 -> 0.92 / 0.92 | 0.44 / 0.45 -> 0.49 / 0.55 |
| delta_only | logistic regression | 0.72 / 0.61 -> 0.79 / 0.69 | 0.26 / 0.36 -> 0.26 / 0.35 |
The model with time is never worse here: better in 9 of the 12 cells (by up to 7 accuracy points and 11 F1 points) and equal in the other 3. The gains are modest because 61 datapoints and up to 400 features let a model ignore one extra column: the `delta_only` layout lets the time matter most. With a project-held-out split the no-time models are weak (0.26 - 0.49), which is the honest difficulty of the task. Treat these numbers as a check of the data design, not as results.

## Example
```python
import pandas as pd
W = pd.read_csv("delta_only/dataset_with_time.csv"); N = pd.read_csv("delta_only/dataset_without_time.csv")
meta = ["id", "project", "language", "fold", "fold_by_project", "td_type", "label"]
Xw, Xn, y = W.drop(columns=meta), N.drop(columns=meta), W["td_type"]
train, test = W.fold_by_project != 0, W.fold_by_project == 0      # same split for both models
```
Adding pairs and rebuilding changes the folds (they are recomputed): fix a split before you start experiments, or save the `fold` columns.
