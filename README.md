# final_folder - technical-debt pair dataset, bugs, vectors and the ML input

Question the data is built for: **given a project pair (the project, and the same project with technical debt induced), which of 5 kinds of technical debt was induced?**
`complexity`, `concurrency`, `coupling_cohesion`, `dependency_structure`, `security`. Next step (yours): one model with the time feature, one without.

```
final_folder/
  project_dataset/            61 pairs of real open-source projects: P#_clean and P#_TD (Python 41, C/C++ 20)
                              + project_details/<project>/ : git history, SonarQube results, properties of every project
  project_with_bugs_dataset/  the same pairs with 3 injected bugs - the SAME bugs in the clean and in the TD project
  pipeline/                   the code: project folder -> feature vector -> dataset.csv (+ bug injection, fix times, adding projects)
  out_dataset/                the machine-learning input: dataset_with_time.csv / dataset_without_time.csv, target = td_type
  ml_model/                   the models: with-time vs without-time, cross-validation results, trained models, predict.py
  results/                    every experiment with its numbers, the comparison current vs previous, controls (start with results/00_executive_summary.md)
```
**Start with `GUIDE.md`** (what is where, what needs what, how to do each task). Read in this order: this file -> `project_dataset/README.md` -> `project_with_bugs_dataset/README.md` -> `pipeline/README.md` -> `out_dataset/README.md` -> `ml_model/README.md` -> `results/00_executive_summary.md`.

## The five TD types in the data
concurrency 26, security 16, dependency_structure 7, coupling_cohesion 6, complexity 6 (61 pairs). The classes are unbalanced and the small ones have 6 pairs.

## What to know before modelling (read this)
1. **The time column.** `time_diff_min` comes from the ground-truth time model in `pipeline/bug_injection/sample_times.py`: each TD type has its own slow-down factor for fixing a bug, so the time is informative about the type (alone it identifies the type for about 93% of the pairs) and the model with the time feature is expected to do better than the one without. Measured times can replace the model values at any time (`make_dataset.py times`).
2. **Project leakage.** Pairs of one project often share their TD type (all 24 boltons pairs are concurrency). With a random split a model can learn the project instead of the debt. Use `fold_by_project` for an honest comparison; `fold` is the stratified split.
3. **Sample size.** 61 datapoints, up to 400 features: use the `delta_only` layout (134 features) or select features.
4. The 3 bugs per pair were checked to be valid code (Python parses, C compiles syntactically) but were **not** validated with the projects' test suites.
5. Tests folders were removed from all projects (they are not used by the technical-debt analysis); the test results measured before the removal are in each `P#_prop/properties.txt`.

Models and results: `ml_model/README.md` (with time vs without time, four splits, 7 classifiers).

## Licences
`project_dataset/` and `project_with_bugs_dataset/` contain copies of open-source projects (boltons, click, jinja, werkzeug, C-Thread-Pool, cJSON, jansson, libpng, libyaml, zlib), each under its own licence (see the `LICENSE` file inside each project folder); the technical-debt changes and bugs are modifications of those files. The code in `pipeline/`, `ml_model/` and `results/scripts/` and the generated tables were written for this study; no licence has been chosen for them yet. Git author e-mails in `project_dataset/project_details/` are stored as hashes.
