# 9. Limits and threats to validity

| threat | detail | what would address it |
|---|---|---|
| time feature from a model | `time_diff_min` is produced by the ground-truth time model, not measured. The with-time gain depends on its assumed per-type factors; the shuffled control shows the gain is not a leak of the other features, and the noise controls show how it shrinks with noisy times. | replace with measured times (`make_dataset.py times`) and re-run `ml_model/run_experiments.py` |
| time model calibrated after seeing the classifiers | four settings were tried; the weakest gave no gain and was replaced (section 4.3). The reported gain is for the chosen setting. | fix the time model before running a confirmatory experiment |
| small data | 61 pairs; class sizes 26/16/7/6/6; one pair moves accuracy by 1.6 points; accuracy intervals of +-0.10 | more pairs; report intervals |
| project leakage | pairs of one project share a TD type (24 boltons pairs are all concurrency) | `fold_by_project`, leave-one-project-out |
| injected technical debt | 60 of 61 TD changes are injected (LLM refactorings or small scripted changes); only libpng P20 is natural | natural pairs (e.g. fix commits of the C security-debt dataset) |
| bugs not validated by tests | valid code, but not shown to fail a test | run the projects' test suites on the bugged projects (`td_vector/bugs/validate.py`) |
| metric proxies | the audit metrics cannot see feature envy, god classes, memory-safety fixes | class-level metrics |
| multiple comparisons | 7 classifiers x 2 layouts x 4 protocols were compared; the final model was chosen because the pair with/without time was clearly separated, not from a held-out set | fix the model before a confirmatory run |
| SonarQube coverage | Python only, TD folder only, 36 of 61 pairs; scans included tests folders | scan clean and bugged folders; a C/C++ analyzer |
| fixed hyper-parameters | no tuning on the test folds; no nested cross-validation | nested cross-validation with more data |
| COCOMO II constants | nominal COCOMO II.2000 values; the constants of the 2025 paper could not be checked | check the paper |
