# final_folder - technical-debt prioritisation: pair dataset, models, interest and the evaluation of the ranking

B.Tech project 2026-27, IIT Kharagpur: **Characterising AI-Induced Technical Debt and Its Impact on Software Maintenance**.

When a team has more technical debt (TD) than it can repay, what should it fix first, and how can the answer be tested? This folder holds everything built to study that question:

1. **A dataset** of 61 pairs of real open-source projects: the project as it is, and the same project with one technical-debt change of one of 5 types induced. Three small bugs are injected into both copies, and a fix-time value is attached to every pair.
2. **A pipeline** that turns each pair into 133 numbers (structure, code shape, technical debt).
3. **Level 1, debt-type classification**: which of the 5 kinds of debt was induced, with and without the fix-time feature, seven classifiers, four evaluation protocols.
4. **Level 2, interest and ranking**: the interest of debt in person-months from the git history of 9 projects (2025 method of Wiriyakul and Senivongse with COCOMO II), models that predict it, and an evaluation of the ranking of debt instances (capture@k, lift, NDCG, baselines, bootstrap intervals).
5. **The presentation** of all of this, its script, and the code that draws every figure and table.

The 5 TD types: `complexity`, `concurrency`, `coupling_cohesion`, `dependency_structure`, `security`.

```
final_folder/
  project_dataset/            61 pairs of real open-source projects: P#_clean and P#_TD (Python 41, C/C++ 20)
                              + project_details/<project>/ : git history, SonarQube results, properties of every project
  project_with_bugs_dataset/  the same pairs with 3 injected bugs - the SAME bugs in the clean and in the TD project
  pipeline/                   the code: project folder -> feature vector -> dataset.csv (+ bug injection, fix times, adding projects)
  out_dataset/                the machine-learning input: dataset_with_time.csv / dataset_without_time.csv, target = td_type
  ml_model/                   Level 1 models: with-time vs without-time, cross-validation results, trained models, predict.py
  interest_exp/               Level 2: interest in person-months (calculation, prediction), code, data, results
  results/                    every Level 1 experiment with its numbers (start with results/00_executive_summary.md)
  synthetic_dataset/          150 generated projects with git histories, debt of known type and known interest (README.md first)
  insights/                   out-of-the-box analyses: what the data says beyond the numbers (INSIGHTS.md first), code, results, figures
  presentation/               the final talk (TD-presentation.pptx), its script and Q&A, and the Python that draws the figures and tables
  GUIDE.md                    what needs what, how to do each task
```

**Reading order:** this file -> `GUIDE.md` -> `project_dataset/README.md` -> `project_with_bugs_dataset/README.md` -> `pipeline/README.md` -> `out_dataset/README.md` -> `ml_model/README.md` -> `results/00_executive_summary.md` -> `interest_exp/README.md` -> `insights/INSIGHTS.md` -> `synthetic_dataset/README.md` -> `INSIGHTS_ALL.txt` (all insights in one file) -> `insights/new/INSIGHTS_NEW.md` -> `presentation/README.md`.

## 1. The data

| item | value |
|---|---|
| pairs | 61 (Python 41, C/C++ 20) from 10 open-source projects |
| Python projects | boltons, click, jinja, werkzeug |
| C/C++ projects | C-Thread-Pool, cJSON, jansson, libpng, libyaml, zlib |
| classes | concurrency 26, security 16, dependency_structure 7, coupling_cohesion 6, complexity 6 |
| origin of the TD change | 60 injected (45 scripted or hand-written, 15 LLM refactorings in the SmellBench style) and 1 natural (libpng, a real fix commit) |
| bugs | 3 per pair, 183 in total, the same patch on the clean and the TD copy; 70 in a file the TD change touched |
| features | 133: structure 46, code shape 50, technical debt 37 (`out_dataset/FEATURES.md`) |
| layouts | `delta_only` (133 columns: TD copy minus clean copy) and `full` (399: clean, TD, delta) |
| time feature | `time_diff_min`: minutes to fix the 3 bugs in the TD project minus in the clean project |

How the 61 pairs were made: 102 candidate pairs, a **metric audit** keeps a pair only if a metric of its own type moved (52 kept, 50 dropped as "not visible to these metrics"), then 9 pairs from two more projects (C-Thread-Pool 4, libyaml 5) were added: 61. Details: `results/01_dataset.md`, `results/02_audit_and_features.md`.

## 2. What to know before modelling (read this)

1. **The time column.** `time_diff_min` comes from the ground-truth time model in `pipeline/bug_injection/sample_times.py`: each TD type has its own slow-down factor for fixing a bug (concurrency 3.4, security 2.4, complexity 1.8, coupling 1.4, dependency 1.05; 0.85 of the effect when the bug is in a file the TD change did not touch). The time is therefore informative about the type (alone it identifies the type for about 93 % of the pairs), and a model with the time feature is expected to do better. The factors were calibrated after the classifiers had been seen (four settings; one weak setting was replaced), so the gain from time is **conditional on this model**; it is not evidence about real developers. Measured times can replace the model values at any time (`make_dataset.py times`); `time_source` is `sample` until then.
2. **Project leakage.** Pairs of one project often share their TD type (all 24 boltons pairs are concurrency). With a random split a model can learn the project instead of the debt. Use `fold_by_project` for an honest comparison; `fold` is the stratified split.
3. **Sample size.** 61 datapoints, up to 400 features: use the `delta_only` layout (134 columns with time) or select features. The 95 % interval of one accuracy is about plus or minus 0.10.
4. The 3 bugs per pair were checked to be valid code (Python parses, C compiles syntactically) but were **not** validated with the projects' test suites.
5. Tests folders were removed from all projects; the test results measured before the removal are in each `P#_prop/properties.txt`.

## 3. Results

### Level 1: debt type, with and without the fix-time feature
Final model: ten-best-feature selector (ANOVA F, inside the folds) + random forest (300 trees, balanced), delta layout. Accuracy; the majority class is 0.426.

| protocol | without time | with time |
|---|---|---|
| given stratified folds | 0.787 | 0.918 |
| 20 repeated stratified splits | 0.840 | 0.938 |
| given by-project folds | 0.311 | 0.508 |
| leave one project out | 0.426 | 0.508 |

* The stratified gain is +0.131 (bootstrap interval +0.05 to +0.23, McNemar p = 0.008); the plain random forest stays at 0.885 with or without time; time alone gives 0.93.
* The shuffled-time control removes the gain (0.840 against 0.839); noise shrinks it (gone at log-noise 1.0).
* With whole projects held out, accuracy is at the majority baseline: the model does not generalise to new projects yet. The change a TD makes in the features is tiny (mean 0.008 standard deviations) against the differences between projects, and 24 of the 26 concurrency pairs come from boltons.
* Everything: `results/05_td_type_classification.md`; 656 runs (7 classifiers x 2 layouts x 4 protocols x with/without time).

### Level 2: interest in person-months and the ranking of instances
Method and numbers: `interest_exp/README.md`, `interest_exp/results/00_summary.md`.

| | |
|---|---|
| interest paid, 9 projects x 20 releases | **10.52 person-months** (1,607 events), about 6 % of the effort of rewriting all debt once |
| instance-releases / instances | 20,853 / 1,557; about 92 % of instance-releases have zero interest |
| any interest in the next release (AUC) | 0.59 for unseen repositories, 0.71 for later releases (chance 0.5) |
| how many person-months per instance | not predictable: no model beats "predict zero" |
| total of a project | two-part model: predicted / actual = 1.14 |

Ranking of the instances of a release (123 repo-release groups, leave-one-repo-out); share of next-release interest in the top k % of the ranking:

| model | top 10 % | top 20 % | top 30 % | top 50 % |
|---|---|---|---|---|
| random | 10.0 | 20.0 | 30.0 | 50.0 |
| persistence (rank by interest already paid) | 21.7 | 38.8 | 46.9 | 67.0 |
| RF regression | 17.2 | 35.0 | 48.9 | 70.5 |
| two-part (hurdle) model | 20.0 | 38.5 (CI 32-44) | 51.5 | 73.5 |
| oracle | 89.9 | 95.8 | 98.1 | 99.4 |

* The learned ranking captures about 1.9 times what chance does and **ties the persistence rule** in the top 20 %. Two-part minus persistence: -2.0, -2.2, +3.3 and +5.6 points at 10, 20, 30 and 50 % (the last one has the interval +0.4 to +10.7: marginal, several budgets were examined).
* NDCG@20 is 0.21 (two-part) against 0.23 (persistence); the rank correlation is about 0.14, so the order inside the top group is weak.
* Temporal protocol (57 groups): two-part 28.2 and 41.9 % at top 10 and 20 %; persistence 23.4 and 39.1 %.
* Code and tables: `presentation/prioritization_eval.py`, `presentation/capture_curve.py`, `presentation/data/`.

### Honest summary
A working, reproducible way to **build** a debt dataset and to **evaluate** a prioritisation. The ranking beats chance and is not yet better than a simple history rule; the amount of interest cannot be predicted per instance; the time-feature gain depends on the time model; the type classifier does not generalise to unseen projects.

## 4. How to reproduce

Environment: Python 3.10+ (tested with 3.13), `git`, optionally `gcc` (syntax check of the C bugs), Node.js for the deck.
```
python -m venv .venv && . .venv/bin/activate
pip install -r pipeline/requirements.txt -r ml_model/requirements.txt -r interest_exp/requirements.txt
```
| to do | command |
|---|---|
| rebuild `out_dataset` (about 1.5 min) | `cd pipeline && python make_dataset.py build` |
| Level 1 experiments (about 10 min) | `cd ml_model && python run_experiments.py`, then `python train_models.py` |
| the extra experiments and the result documents | `python results/scripts/extra_experiments.py` (about 25 min), then `python results/scripts/build_results.py` |
| interest calculation and models | `cd interest_exp/code && sh clone_repos.sh && python run_all.py` (see `interest_exp/code/README.md`; the SonarQube data needs a running server and `SONAR_TOKEN` in the environment, never in a file) |
| ranking evaluation | `cd presentation && python prioritization_eval.py && python capture_curve.py` |
| figures, tables and deck | `cd presentation && ./build_all.sh` (see `presentation/README.md`) |
| predict a pair | `cd ml_model && python predict.py --layout delta_only --with-time --id C_C++/P3` |
| add a pair | `cd pipeline && python make_dataset.py add --lang Python --clean CLEAN_DIR --td TD_DIR --td-type security` (see `GUIDE.md`) |
| replace the time values by measured ones | fill `clean_min`, `td_min` per bug in a CSV `id,bug,clean_min,td_min`, then `cd pipeline && python make_dataset.py times FILE.csv` |

## 5. The synthetic benchmark
`synthetic_dataset/` holds 150 generated Python projects (150 domains, 5 to 34 files, 5 to 30 releases each) with real git histories, 1,321 injected debt instances (5-10 of one major type and one each of two others per project), the interest of every instance in every release computed from git, 1,321 clean/debt commit pairs and the 133 features of every pair and release. It is synthetic (assembled from templates, simulated histories): it is for testing methods with known truth and for the regimes in which the patterns of the real data are absent; it is not evidence about developers. See `synthetic_dataset/README.md`, `VALIDATION.md` and `insight_check.md`.

## 6. The presentation
`new_presentation/` holds only the insights that are new relative to the current talk, organised like `presentation/` (README, slide outline, the insight file, 36 figures, reports, data); `python new_presentation/build_new_presentation.py` rebuilds it.

`presentation/new_figures/` holds every graph, plot and dataset-creation picture of the project as matplotlib PNGs, with an index (`presentation/new_figures/README.md`).

`presentation/TD-presentation.pptx` is the final deck (21 slides), and `presentation/script_TD-presentation.md` is its script: about 14 minutes of spoken text, the results explained in depth, the architecture and what was done, 70 questions an examiner can ask with answers, and the numbers to remember. Every figure, table and diagram of the generated deck is drawn by Python (`presentation/make_figures.py`, `make_tables.py`, `make_architecture.py`).

## 7. Limits
* 61 datapoints; 60 of them injected, 1 natural. The audit uses metrics related to the features, so Level 1 may look easier than it is.
* The fix times are a model, not measurements; the gain from them is conditional on it.
* The bugs are not validated with tests.
* The type classifier does not generalise across projects (majority-baseline accuracy); concurrency comes almost only from boltons.
* Interest is the effort implied by the size of changes inside debt-carrying code (COCOMO II with nominal constants and multipliers 1), not measured developer time; it depends on the smell detector.
* The learned ranking ties the persistence baseline in the top 20 %; the +5.6 points at 50 % is marginal.
* The motivation statistics in the slides come from secondary sources and have not been re-checked; the citation of Wiriyakul and Senivongse (2025) is incomplete.
Full list: `results/09_limits_and_threats.md`.

## 8. Licences
`project_dataset/` and `project_with_bugs_dataset/` contain copies of open-source projects (boltons, click, jinja, werkzeug, C-Thread-Pool, cJSON, jansson, libpng, libyaml, zlib), each under its own licence (see the `LICENSE` file inside each project folder); the technical-debt changes and bugs are modifications of those files. The code in `pipeline/`, `ml_model/`, `interest_exp/code/`, `presentation/` and `results/scripts/` and the generated tables were written for this study; no licence has been chosen for them yet. The IIT Kharagpur logo in `presentation/kgp_logo.png` belongs to the institute. Git author e-mails in `project_dataset/project_details/` are stored as hashes.

## 9. Later work: 33 real repositories, scenarios, code text, and how to regenerate everything

| folder | what |
|---|---|
| `real_project_analysis/` | the same release pipeline on 33 real repositories (16 Python, 17 C/C++): patterns of real debt, 20 insights, the design spec of a dataset that obeys them, natural pairs mined from commits |
| `synthetic_dataset_v2/` | a second synthetic benchmark built to those measured properties (27 acceptance tests; v1 passes 9, v2 passes 25) |
| `scenario_analysis/` | which patterns repeat across Python and C/C++ and which are noise; rule discovery by decision tree |
| `code_insights/` | what the code text shows: traits (calls, repeated lines, pointer use), clones and their co-change, code examples |
| `embedding_generalisation/` | embeddings from several code models (unfinished) |
| `reproduce/` | **every figure and score, the manifest that maps them to scripts, and `regenerate.sh`** (start with `reproduce/README.md`) |
