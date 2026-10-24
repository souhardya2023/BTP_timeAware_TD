# GUIDE - what is in final_folder, what needs what, and how to use it

## 1. The idea in one page
The study asks: **given a software project and the same project with technical debt (TD) induced, which of 5 kinds of TD was induced?**
(`complexity`, `concurrency`, `coupling_cohesion`, `dependency_structure`, `security`.) One extra signal is available: how much longer it takes to fix bugs in the TD project than in the clean one.

```
 real open-source project --(a TD change is applied)-->  PAIR: P#_clean , P#_TD                  project_dataset/
 pair --(3 small bugs injected, the SAME bugs in both)--> P#_clean_bug , P#_TD_bug               project_with_bugs_dataset/
 each bugged project --(extract.py)--> 133 numbers: structure, code shape, technical debt         pipeline/
 per bug: minutes to fix in the clean / in the TD project --> per pair  time_diff_min             pipeline/bug_injection/sample_times.py
 one row per pair: label td_type + folds + time_diff_min + clean__/td__/delta__ features         out_dataset/
 models: with time_diff_min  versus  without it                                                  ml_model/
```
61 pairs from 10 open-source projects (Python 41: boltons, click, jinja, werkzeug; C/C++ 20: C-Thread-Pool, cJSON, jansson, libpng, libyaml, zlib). TD types: concurrency 26, security 16, dependency_structure 7, coupling_cohesion 6, complexity 6.

## 2. Map of the folder
| folder | size | what it is | made by |
|---|---|---|---|
| `project_dataset/` | 122 MB | **the data**: the 61 pairs (clean and TD copies of the projects, no `.git`, no tests folder), their properties, and all details of the 10 projects | `pipeline/tools/export_project_details.py`, `export_sonarqube_server.py` (one-time) |
| `project_with_bugs_dataset/` | 101 MB | the same 61 pairs with 3 injected bugs each (the same bugs in the clean and the TD project) | `pipeline/bug_injection/inject_bugs.py` |
| `pipeline/` | 128 KB | **the code** that turns the two folders above into the machine-learning input | hand-written |
| `out_dataset/` | 472 KB | **the machine-learning input**: CSV files with the label, the features and the time feature | `pipeline/make_dataset.py build` |
| `ml_model/` | 3.9 MB | the with-time vs without-time experiments, 4 trained models, `predict.py` | `ml_model/*.py` |
| `results/` | 4 MB | **all experiments and their numbers**: 10 documents (dataset, audit, features, history, time model, classification, ablations, earlier experiments, current vs previous, limits) + `data/` CSVs + the scripts that produce them | `results/scripts/` |
| `README.md`, `GUIDE.md` | | overview, this guide | |
Every folder has its own `README.md`; the guide below tells you what to read when.

## 3. What is required where (dependencies)
| to do this | you need | you do NOT need |
|---|---|---|
| **train / evaluate / use the models** | `out_dataset/` + `ml_model/` (packages: scikit-learn, pandas, numpy, joblib) | everything else |
| **rebuild `out_dataset` from the projects** | `project_dataset/` (the folders `Python/`, `C_C++/` and `properties_all_pairs.csv`), `project_with_bugs_dataset/`, `pipeline/` (packages: numpy, pandas, networkx, lizard, bandit, flawfinder; `bandit` and `flawfinder` must be on the PATH) | `project_details/`, `sonarqube_server/` |
| **add a new pair** | `pipeline/`, `project_dataset/`, `project_with_bugs_dataset/`, and `git` (used to apply the bug patches) | - |
| **change or replace the time values** | `out_dataset/bugs.csv` + `pipeline/make_dataset.py` (command `times`) | - |
| **read or re-create the experiment results** | `results/` (documents, `data/`); to regenerate: `ml_model/run_experiments.py`, then `results/scripts/extra_experiments.py` (about 25 min), then `results/scripts/build_results.py` | the pipeline |
| **study the projects' history, SonarQube issues, properties** | `project_dataset/project_details/` and `project_dataset/sonarqube_server/` | the code |
| **re-export the SonarQube data** | a running SonarQube server and `SONAR_TOKEN` in the environment; `pipeline/tools/export_sonarqube_server.py` | - |
`pipeline/tools/export_project_details.py` rebuilds `project_dataset` from the author's working folders; it cannot be run from `final_folder` alone and is kept only as a record of where the data came from.

**Environment.** Python 3.10+ (tested with 3.13), `git`, optionally `gcc` (only for the syntax check of the C bugs). Example:
```
python -m venv .venv && . .venv/bin/activate
pip install -r pipeline/requirements.txt -r ml_model/requirements.txt       # bandit and flawfinder install their commands into .venv/bin
```

## 4. Folder by folder

### 4.1 `project_dataset/` - the pairs and everything known about them
```
Python/P1..P41/   C_C++/P1..P20/      (C_C++ because "/" cannot be used in a name)
    P#_clean/   the project, unchanged            P#_TD/   the same project with one technical-debt change
    P#_prop/    properties.txt (what was induced, where, validation results)     td.patch (clean -> TD)
properties_all_pairs.csv   one row per pair: project, repository, base commit, TD type/subtype, CWE, description, files and lines changed, validation, + sonar_* columns
INDEX.md                   table of the pairs
project_details/<project>/ git history, releases, SZZ bugs, SonarQube per release, version-wise interest, pairs.csv      (10 projects)
sonarqube_server/          the whole SonarQube server: 52 projects, measures, 10,727 issues, rules
```
* **Used by:** `pipeline/make_dataset.py` reads `properties_all_pairs.csv` (the list of pairs, their `td_type` = the label) and, for `add` and `inject`, the `P#_clean`, `P#_TD` and `td.patch`.
* **The 5 TD types** come from the injected change: concurrency (a lock removed ...), security (a bounds / NULL check removed ...), dependency_structure, coupling_cohesion, complexity.
* **Where the changes come from:** 15 pairs (click, jinja) are LLM-written refactorings from the SmellBench dataset, 45 are small scripted injections, 1 (libpng P20) is a real vulnerability-fix commit (natural). So 60 of 61 are injected.
* `project_details/<project>/`: `git_history/commits.csv` (author e-mails hashed), `releases.csv`, `szz_bugs.csv` (bugs mined from the history, with lifetimes), `sonarqube/` (issues of each of the last 20 releases for the Python projects; structural-smell tracking for all). Not used by the pipeline - they are the project's documentation and background data.
* `sonarqube_server/`: SonarQube exists only for Python (Community Build has no C/C++ analyzer) and only for the TD folder of 36 pairs; `projects.csv` says which server project belongs to which pair. Not used as ML features because the coverage is partial.

### 4.2 `project_with_bugs_dataset/` - the pairs with bugs
```
Python/P#/  C_C++/P#/:   P#_clean_bug/   P#_TD_bug/     the two projects with the same 3 bugs
                         P#_bugs/        bug1.patch bug2.patch bug3.patch   (apply to P#_clean and P#_TD alike)   bugs.json (file, line, function, kind, description)
```
* A **bug** = one small semantic change in one function: a flipped comparison (`<` / `<=`, `==` / `!=`), `and` / `or` swapped, a negated condition, `+` / `-`, or an off-by-one constant (`pipeline/bug_injection/mutate.py`). 183 bugs.
* Rules: never on the lines the TD change touched; the patch applies to both projects; one bug in a file the TD touched when possible; different functions and kinds. Seeded by the pair id, so re-running gives the same bugs.
* **Used by:** `make_dataset.py build` vectorises the `*_clean_bug` and `*_TD_bug` folders (the vectors describe the projects as handed to the person who fixes the bugs).
* **Not done:** the bugs were not validated with the projects' test suites; they are valid code (Python parses, C passes a syntax compile).

### 4.3 `pipeline/` - the code (`../out_dataset` is its output)
| file | role |
|---|---|
| `make_dataset.py` | the entry point: `build`, `inject`, `add`, `times` (below) |
| `extract.py` | `extract(folder)` -> 133 named features of one project; calls `f_structure.py`, `f_code.py`, `f_td.py`; `common.py` finds the source files |
| `f_structure.py` | directory layout and the file dependency graph (imports / `#include`): cycles, fan-in/out, instability, clustering, modularity, PageRank, graph spectrum |
| `f_code.py` | lines, comments, per-function size / cyclomatic complexity / parameters, Python and C idioms |
| `f_td.py` | technical debt: smells and their COCOMO II principal, god classes, LCOM4 cohesion, debt comments (SATD), duplication, security findings (bandit / flawfinder), validation guards, concurrency idioms |
| `bug_injection/mutate.py`, `inject_bugs.py` | list candidate bugs; choose 3 per pair and write `project_with_bugs_dataset` |
| `bug_injection/sample_times.py` | the ground-truth fix-time model (per bug, in the clean and in the TD project) |
| `tools/` | one-time export scripts (project details; SonarQube server) |
The 133 features: structure `s_` (46), code shape `c_` (50), technical debt `t_` (37); meaning of each: `out_dataset/FEATURES.md`.

### 4.4 `out_dataset/` - the machine-learning input
```
full/         dataset_with_time.csv   dataset_without_time.csv     features clean__* + td__* + delta__* (399) [+ time_diff_min]     (61 x 407 / 406)
delta_only/   dataset_with_time.csv   dataset_without_time.csv     features delta__* (133)                   [+ time_diff_min]     (61 x 141 / 140)
bugs.csv (one row per bug: kind, file, clean_min, td_min, diff_min, time_source)   FEATURES.md   feature_dictionary.csv   feature_groups.json   label_map.json
```
| columns | meaning |
|---|---|
| `id`, `project`, `language` | identifiers - not features (`project` leaks the label: pairs of one project share their TD type) |
| `fold` / `fold_by_project` | ready-made 5-fold splits: stratified by TD type / whole projects per fold (the honest one) |
| `td_type`, `label` | **the target** (text, integer; `label_map.json`) |
| `time_diff_min` | **the time feature**: minutes to fix the 3 bugs in the TD project minus in the clean project (only in the `with_time` files) |
| `clean__f`, `td__f`, `delta__f` | feature `f` of the project without TD / with TD / the difference |
A `with_time` file and its `without_time` twin are identical except for `time_diff_min`. `delta_only` (134 features) suits 61 datapoints better than `full` (400).

### 4.5 `ml_model/` - the models
`run_experiments.py` (cross-validation: 7 classifiers x 2 layouts x with/without time x 4 splits -> `results/`), `train_models.py` (fits the final models on all 61 pairs -> `models/*.joblib`), `predict.py`. Results are summarised in `results/report.md` and `ml_model/README.md`.

## 5. How to ...
Run the commands from the folder named; `PY` = your Python with the packages installed.
| task | command |
|---|---|
| rebuild the datasets (about 1.5 min) | `cd pipeline && PY make_dataset.py build` |
| vectorise one project folder | `cd pipeline && PY extract.py PATH/TO/PROJECT` |
| add a new pair | `cd pipeline && PY make_dataset.py add --lang Python --clean CLEAN_DIR --td TD_DIR --td-type security [--td-subtype S --project NAME --repository URL --base-commit SHA]` - copies it in as the next `P#`, writes `td.patch`, injects 3 bugs, assigns times, rebuilds `out_dataset`. Folds are recomputed on every build, so fix your split before you start experiments. |
| replace the time values by measured ones | fill `clean_min` and `td_min` for each bug in a CSV `id,bug,clean_min,td_min`, then `cd pipeline && PY make_dataset.py times FILE.csv`; `time_source` becomes `measured` and `time_diff_min` of the pair is the sum over its 3 bugs |
| train and compare the models | `cd ml_model && PY run_experiments.py` (about 10 min), `PY train_models.py` |
| predict a pair | `cd ml_model && PY predict.py --layout delta_only --with-time --id C_C++/P3` |
| use the data in your own model | `pd.read_csv("out_dataset/delta_only/dataset_with_time.csv")`; features = every column after `label`; target = `td_type`; split with `fold_by_project` |
| re-export SonarQube | `SONAR_TOKEN=... PY pipeline/tools/export_sonarqube_server.py project_dataset/sonarqube_server project_dataset` |

## 6. What is real and what is generated
| item | origin |
|---|---|
| the projects, their git history, releases | real open-source repositories (jansson, zlib, ... at fixed commits) |
| the TD changes (60 pairs) | injected: SmellBench LLM refactorings (15) and small scripted / hand-written changes (45); libpng P20 is a real fix commit |
| the 3 bugs per pair | injected mutations (not validated with tests) |
| the 133 features | computed from the project files (and tools: lizard, bandit, flawfinder, networkx) |
| SonarQube data | produced by the SonarQube server; Python only, TD folders (36 pairs) and release scans |
| SZZ bug tables, version-wise interest | computed from the git history |
| **`time_diff_min` and the per-bug times** | **from the ground-truth time model** in `pipeline/bug_injection/sample_times.py` (assumed per-type slow-down factors, seeded random); replace with measured times when available. `time_source` in `bugs.csv` is `sample` until then |

## 7. Limits to keep in mind
* 61 datapoints (class sizes 26 / 16 / 7 / 6 / 6); one pair moves accuracy by 1.6 points. Use repeated and project-held-out evaluation.
* Pairs of one project share their TD type; with a random split a model can learn the project. `fold_by_project` removes this.
* The effect of the time feature in `ml_model/results` depends on the time model; check it again with measured times.
* Tests folders were removed from all projects; building a C/C++ project may need them back. Test results measured earlier are in each `P#_prop/properties.txt`.
* SonarQube covers Python only; no SonarQube feature is used by the models.
* Large pretrained models: possible on the diffs for small models; 7B+ models need a GPU; the data is small for fine-tuning (assessment in `ml_model/README.md`).
