# ml_model - classify the technical-debt type, with and without the time feature

Task: from the features of a pair (`../out_dataset`) predict `td_type`, one of 5 classes (complexity, concurrency, coupling_cohesion, dependency_structure, security).
Two models of every kind: one that gets `time_diff_min`, one that does not. Everything else (rows, features, split, classifier, settings) is identical.

```
ml_model/
  run_experiments.py   cross-validation of 7 classifiers x 2 layouts x with/without time x 4 splits   -> results/
  train_models.py      fits the final models on all 61 pairs                                         -> models/<layout>_{with,without}_time.joblib
  predict.py           predicts the TD type of a pair with a trained model
  results/             report.md (all tables), metrics.csv (every run), summary.csv, time_effect.csv, predictions.csv (per pair), confusion_*.csv, importance.csv
  models/              the four final models
  requirements.txt     scikit-learn, pandas, numpy, joblib
```
Run: `pip install -r requirements.txt`, then `python run_experiments.py` (about 10 minutes), `python train_models.py`, `python predict.py --layout delta_only --with-time --id C_C++/P3`.

## How the models are evaluated
61 datapoints are few, so four splits are used (all in `run_experiments.py`):
| split | meaning |
|---|---|
| `given_stratified` | the 5 folds of the `fold` column (stratified by TD type) |
| `repeated_stratified` | 20 different random stratified 5-fold splits - mean over the 20 and the paired difference with/without time |
| `given_by_project` | the `fold_by_project` column: the model is tested on projects it never saw |
| `leave_one_project_out` | each of the 10 projects is the test set once |
Classifiers (fixed settings, nothing tuned on a test fold): random forest, gradient boosting, logistic regression, SVM (RBF), kNN, and random forest / logistic regression behind a **10-best-features selector fitted inside every training fold** (`kbest10_*`). Baselines: majority class and the time feature alone. Metrics: accuracy and macro-F1.

## Results (accuracy / macro-F1, without time -> with time)
The matched pair used as the final models, `kbest10_random_forest`:
| layout | split | without time | with time | change in accuracy |
|---|---|---|---|---|
| delta_only | repeated_stratified | 0.84 / 0.76 | 0.94 / 0.90 | +0.10 |
| delta_only | given_stratified | 0.79 / 0.67 | 0.92 / 0.86 | +0.13 |
| delta_only | given_by_project | 0.31 / 0.34 | 0.51 / 0.60 | +0.20 |
| delta_only | leave_one_project_out | 0.43 / 0.38 | 0.51 / 0.56 | +0.08 |
| full | repeated_stratified | 0.78 / 0.66 | 0.93 / 0.91 | +0.15 |
| full | given_stratified | 0.70 / 0.54 | 0.82 / 0.79 | +0.12 |
| full | given_by_project | 0.12 / 0.19 | 0.28 / 0.33 | +0.16 |
| full | leave_one_project_out | 0.25 / 0.15 | 0.38 / 0.35 | +0.13 |
* Plain classifiers on all features (random forest, gradient boosting, logistic regression, SVM, kNN): the change in accuracy from adding the time is -0.02 to +0.09 (the only case with a lower value is random forest on `full` with leave-one-project-out, -0.02 = one pair; the largest gains are for gradient boosting on `delta_only`: +0.08 and +0.09). A model with hundreds of columns uses one extra column only a little.
* With the feature selector (`kbest10_*`) the time is picked as one of the 10 features and the change is +0.07 to +0.28, positive in every run of the 20 repeated splits.
* The time feature alone (random forest on `time_diff_min`) reaches accuracy 0.93 / macro-F1 0.92 to 0.95, so it carries most of the type information in this dataset; in a random forest on all features it ranks first (`results/importance.csv`).
* Without time the task is hard when whole projects are held out (best models 0.38 to 0.46 accuracy); with time the best is 0.51 (`delta_only`) and 0.41 (`full`).
All tables: `results/report.md` (headline table at the top).

## Read these numbers with care
1. **The time feature comes from a ground-truth time model** (`../pipeline/bug_injection/sample_times.py`): each TD type has its own slow-down factor for fixing a bug. The gain from the time feature is therefore a property of that model. Replace the values with measured times (`../pipeline/make_dataset.py times FILE`), run `run_experiments.py` again, and the table shows what the time is worth with real values.
2. **Small data.** 61 pairs (class sizes 26 / 16 / 7 / 6 / 6). A change of one pair moves accuracy by 1.6 points; use the repeated protocol and the project-held-out protocols, not a single split.
3. **Project leakage.** With a random split the models can learn the project (all 24 boltons pairs are concurrency). `given_by_project` and `leave_one_project_out` remove this and give much lower accuracy for the models without time.
4. The final models in `models/` are fitted on all 61 pairs: their accuracy on those pairs is not an evaluation (`predict.py` on a dataset pair is a demonstration). The honest numbers are the cross-validation results above.
5. The features selected for the final `delta_only` model with time are `time_diff_min` and nine structure/code/TD differences (graph edges per node, fan-in/fan-out, lines of code, function-size spread, raise statements per KLOC, principal, very complex functions); without time the selector takes the same nine plus `delta__t_satd_doc`.

## Predict a new pair
Add it with `python ../pipeline/make_dataset.py add --lang Python --clean DIR --td DIR --td-type TYPE` (this rebuilds `../out_dataset`; `--td-type` is only needed to store the pair, the model does not read it), then `python predict.py --layout delta_only --with-time --id Python/P42`.

## Fine-tuning large pretrained models with this dataset (assessment, nothing was run)
* Small code models (CodeBERT, UniXcoder, CodeT5; 100-250 million parameters) can be fine-tuned on the `td.patch` text to predict the TD type, slowly on a machine without GPU (the 61 patches are about 170 KB in total).
* Models with 7 billion parameters or more need a GPU with roughly 16-24 GB, even with LoRA; not possible on a 4-core / 7 GB CPU machine.
* A whole project does not fit a model's context; use the diff, the changed functions, or the diff plus the bug patches. `time_diff_min` is a number: give it as a short text field or combine it with the model output in a second-stage classifier.
* 61 examples (26 / 16 / 7 / 6 / 6) are very few: expect memorisation and unstable results; evaluate with `fold_by_project`, and consider more labelled pairs, prompting, or embeddings plus the classifiers above.
