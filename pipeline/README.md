# pipeline - from a project pair to the machine-learning input

Input: the pairs in `../project_dataset`. Output: `../out_dataset/{full,delta_only}/dataset_with_time.csv` and `dataset_without_time.csv` (target = TD type).
Python 3.10+ with `requirements.txt` (numpy, pandas, networkx, lizard, bandit, flawfinder; `git` must be installed; for the C/C++ bug check `gcc`).
```
python -m venv .venv && .venv/bin/pip install -r requirements.txt && export PATH=$PWD/.venv/bin:$PATH     # bandit and flawfinder must be on the PATH
```

## The steps
```
project_dataset/<lang>/P#/P#_clean, P#_TD
      |  1. bug_injection/inject_bugs.py      3 bugs per pair, same patches on both sides   -> project_with_bugs_dataset/<lang>/P#/{P#_clean_bug, P#_TD_bug, P#_bugs}
      |  2. extract.py                        133-feature vector of each bugged project (structure, code shape, technical debt)
      |  3. bug_injection/sample_times.py     fix time of every bug in the clean and in the TD project (ground-truth time model), summed per pair
      |  4. make_dataset.py build             vectors + time + label + folds  ->  out_dataset/
      v
out_dataset/full/{dataset_with_time.csv, dataset_without_time.csv}      out_dataset/delta_only/{...}      bugs.csv, feature_dictionary.csv, feature_groups.json, label_map.json
```
## Commands (run from this folder)
| command | what it does |
|---|---|
| `python make_dataset.py build [--workers 3]` | vectorises all bugged projects and writes `../out_dataset` (about 1.5 minutes for 61 pairs) |
| `python make_dataset.py inject` | injects the bugs into every pair that has no bugged project yet |
| `python make_dataset.py add --lang Python --clean DIR --td DIR --td-type security [--td-subtype S --project NAME --repository URL --base-commit SHA] [--no-build]` | adds a NEW pair: copies it into `../project_dataset` as the next `P#`, writes `td.patch`, injects 3 bugs, samples the times, rebuilds the dataset |
| `python make_dataset.py times FILLED.csv` | merges MEASURED times (columns `id,bug,clean_min,td_min`, one row per bug); `time_source` becomes `measured`, the pair's `time_diff_min` is recomputed |
| `python extract.py DIR` | prints the 133 features of one project folder |
| `python bug_injection/inject_bugs.py ../project_dataset ../project_with_bugs_dataset [--only Python/P1]` | the injection alone |

## Files
| file | role |
|---|---|
| `extract.py` | `extract(folder)` -> the 133 named features. Calls the three feature files below. |
| `f_structure.py` | directory layout and the file dependency graph (imports for Python, `#include` for C): size, cycles, fan-in/out, instability, clustering, modularity, PageRank, graph spectrum |
| `f_code.py` | lines, comments, per-function size / cyclomatic complexity / parameters (lizard), Python and C idioms |
| `f_td.py` | technical debt: smells and their COCOMO II principal, god classes, LCOM4 cohesion, SATD comments, duplication, security (bandit / flawfinder), validation guards, concurrency idioms |
| `common.py` | finds the production source files (tests, docs, examples, vendored and build folders are skipped) |
| `make_dataset.py` | the orchestration above, the 5-fold splits and the CSV writing |
| `bug_injection/mutate.py` | lists candidate bugs for Python (through the syntax tree) and C (conditions and expressions) |
| `bug_injection/inject_bugs.py` | selects 3 bugs per pair and writes the bugged projects |
| `bug_injection/sample_times.py` | the ground-truth time model for the fix times (documented, replaceable) |
| `tools/export_sonarqube_server.py` | exports everything the SonarQube server holds (projects, measures, issues, rules) into `../project_dataset/sonarqube_server`; needs the server and `SONAR_TOKEN` in the environment |
| `tools/export_project_details.py` | one-time script that assembled `project_dataset` and `project_with_bugs_dataset` from the working folders (not needed to use the pipeline) |
The meaning of every feature is in `../out_dataset/FEATURES.md`.

## The label, the folds and the time
* **target**: `td_type` from `../project_dataset/properties_all_pairs.csv` (5 classes; `label_map.json` gives the integer).
* **folds**: `fold` = 5-fold stratified by TD type; `fold_by_project` = 5 folds with whole projects. They are recomputed on every `build`, so they change when pairs are added.
* **time**: `time_diff_min` = (minutes to fix the 3 bugs in the TD project) - (minutes in the clean project). Today these come from the time model in `sample_times.py`: per bug the clean time is log-normal around 25 minutes and the TD time is that multiplied by a factor that depends on the TD type (concurrency 3.4, security 2.4, complexity 1.8, coupling_cohesion 1.4, dependency_structure 1.05), a little less for bugs outside the file the TD touched, plus small noise. Each TD type has its own factor, so the time is informative about the type; change `FACTOR` etc. at the top of the file to change that, or replace the model values with measured times.

## Checked
* the injection reproduces the same bug patches when run again; adding a new pair (a small C library with its TD twin) works end to end; merging measured times replaces the model values of that pair only (all tested on a copy).
