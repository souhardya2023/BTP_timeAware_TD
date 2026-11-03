# synthetic_dataset_v2 - 150 projects built to the properties measured on 33 real projects

Second version of `../synthetic_dataset`. The generator (`generator/`) is the first one with: log-normal function sizes (complexity grows with size), an edit rate that rises with size as lines^0.70 for debt and clean code alike (no avoidance), persistent heterogeneity (gamma) and frozen units, a release clock driven by the release type (patch / minor / major) with independent jitter, early-life activity, a refactoring hazard of 4.5 % per release for big functions, growth chunks that can cross thresholds, heavy-tailed event sizes, and a huge tier (H, 8 projects).

| item | value |
|---|---|
| projects / releases / commits / lines | 150 / 2,060 / 8,067 / 117,595 (tiers S 50, M 60, L 16, X 16, H 8) |
| typed debt instances | 1,313 in 23 templates (concurrency 275, security 270, complexity 266, coupling 257, dependency 245) |
| every release compiles, smoke script at the last release | 2,060 / 2,060, 0 failures (`compile_check.txt`) |
| acceptance panel (27 tests against the real corpus) | **25 pass** (first dataset: 9); fail: release interest vs commits (0.555, band 0.6-0.85), churn (2.1 %, band 1.0-2.0) |

Files: `acceptance.py` (the panel; runs the real pipeline `../real_project_analysis/code/a1_release_tables.py` on the repositories), `acceptance_v2.txt/csv`, `acceptance_v1.*` (the same for the first dataset), `make_all.sh` (build + measure + ground truth + features + compile check), `level1_eval_v2.py`, `sim2real_v2.py`, `codebert_v2_embed.py`, `codebert_eval_v2.py`, `results/`, `results_level2/` (the ranking models of Chapter 6 on this data), `figures/V1-V7`, `generator/`. The repositories (`repos/`) and the pipeline data are large and can be rebuilt with `make_all.sh`.

Results: the history matches real code (AUC of size / persistence / size+history 0.62 / 0.73 / 0.79 against 0.62 / 0.75 / 0.79 real; capture values higher because groups are smaller) but a type classifier trained on the pairs still fails on the 61 real pairs (0.148; sign of the delta 0.344; majority 0.426) because the debt change is still too visible (0.35 % of a project, real 0.09 %). Version-1 numbers and the tuning rounds are in `acceptance_v2_round*.txt` (the tuning is a fit to the panel, not an independent test). A syntax error in padded functions found by `compile_check.py` was repaired and everything rebuilt.
