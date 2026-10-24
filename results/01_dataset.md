# 1. The dataset: how it was built, what is in it, and every number about it

Source of the numbers: `project_dataset/properties_all_pairs.csv`, `out_dataset/bugs.csv`, the working files of the study (`td_pairs/data`, `dataset/AUDIT.md`). Copies of the tables are in `data/`.

## 1.1 From candidates to the 61 pairs (the stages and their counts)

| stage | pairs | note |
|---|---|---|
| A. candidate pairs recorded for Python (validated records) | 178 | `td_pairs/data/pairs.jsonl` (SmellBench re-built projects + scripted injections) |
|    rejected candidates | 40 | `td_pairs/data/rejected.jsonl` (patch did not apply, tests failed, ...) |
|    SmellBench pairs re-built as whole projects | 42 | `smellbench_pairs.jsonl`; 105 more of large projects (numpy, pandas, scikit-learn, seaborn, xarray) in `smellbench_heavy.jsonl` were left out for size or no test run |
| B. pairs in the folder structure after removing large projects, flagged pairs (TD side fails tests) and pairs without a test run | 102 | Python 71, C/C++ 31 (20 injected + 11 natural from the C security-debt dataset: libpng 6, libxml2 4, zlib 1) |
| C. after the metric audit (a pair stays only if a metric of its own TD type moved in the debt direction) | 52 | 50 pairs removed (list: `data/dropped_unchanged.csv`); Python 41, C/C++ 11 |
| D. + C-Thread-Pool 4 pairs and libyaml 5 pairs (expat: 2 pairs passed but each pair is 260 MB, left out) | 61 | **final dataset**: Python 41, C/C++ 20 |

Later stages did not change the number of pairs: unneeded files (docs, CI, examples, changelogs) were trimmed from all projects, then the test folders were removed (dataset 208 MB -> 100 MB); the test results measured before are stored in each `properties.txt`.

## 1.2 The final 61 pairs

### by TD type and language

| td_type | C/C++ | Python | total |
|---|---|---|---|
| complexity | 1 | 5 | 6 |
| concurrency | 2 | 24 | 26 |
| coupling_cohesion | 0 | 6 | 6 |
| dependency_structure | 3 | 4 | 7 |
| security | 14 | 2 | 16 |
| total | 20 | 41 | 61 |

### by project

| project | language | complexity | concurrency | coupling_cohesion | dependency_structure | security | total |
|---|---|---|---|---|---|---|---|
| C-Thread-Pool | C/C++ | 0 | 2 | 0 | 0 | 2 | 4 |
| boltons | Python | 0 | 24 | 0 | 0 | 0 | 24 |
| cJSON | C/C++ | 0 | 0 | 0 | 1 | 0 | 1 |
| click | Python | 3 | 0 | 3 | 4 | 0 | 10 |
| jansson | C/C++ | 1 | 0 | 0 | 1 | 4 | 6 |
| jinja | Python | 2 | 0 | 3 | 0 | 0 | 5 |
| libpng | C/C++ | 0 | 0 | 0 | 0 | 1 | 1 |
| libyaml | C/C++ | 0 | 0 | 0 | 0 | 5 | 5 |
| werkzeug | Python | 0 | 0 | 0 | 0 | 2 | 2 |
| zlib | C/C++ | 0 | 0 | 0 | 1 | 2 | 3 |
| total |  | 6 | 26 | 6 | 7 | 16 | 61 |

### size of the TD change (lines added + deleted in `td.patch`, files changed)

| td_type | pairs | lines_median | lines_min | lines_max | files_median | files_max |
|---|---|---|---|---|---|---|
| complexity | 6 | 115.500 | 58 | 316 | 2 | 5 |
| concurrency | 26 | 10 | 2 | 95 | 1 | 1 |
| coupling_cohesion | 6 | 66 | 11 | 129 | 3.500 | 9 |
| dependency_structure | 7 | 116 | 2 | 339 | 3 | 5 |
| security | 16 | 2 | 1 | 355 | 1 | 2 |

### where the TD changes come from

| source | complexity | concurrency | coupling_cohesion | dependency_structure | security | total |
|---|---|---|---|---|---|---|
| SmellBench (LLM-written refactoring) | 5 | 0 | 6 | 4 | 0 | 15 |
| natural fix commit (libpng) | 0 | 0 | 0 | 0 | 1 | 1 |
| scripted / hand-written injection | 1 | 26 | 0 | 3 | 15 | 45 |
| total | 6 | 26 | 6 | 7 | 16 | 61 |

### the project's own tests, measured on the clean and on the TD side before the tests folders were removed

| project | pairs | tests_per_run | failing_on_clean | failing_on_TD | pairs_where_both_sides_pass |
|---|---|---|---|---|---|
| C-Thread-Pool | 4 | 5 | 0 | 0 | 4 |
| boltons | 24 | 525 | 0 | 0 | 24 |
| cJSON | 1 | 19 | 0 | 0 | 1 |
| click | 10 | 1314 | 0 | 0 | 10 |
| jansson | 6 | 215 | 0 | 0 | 6 |
| jinja | 5 | 909 | 0 | 0 | 5 |
| libpng | 1 | 37 | 0 | 0 | 1 |
| libyaml | 5 | 3 | 0 | 0 | 5 |
| werkzeug | 2 | 1064 | 0 | 0 | 2 |
| zlib | 3 | 18 | 0 | 0 | 3 |

A pair was admitted only if the TD side passed the project's own tests exactly like the clean side (the change is behaviour-preserving); the libpng pair is a real vulnerability fix and its vulnerable side was admitted with the passing test suite as well.

## 1.3 The injected bugs (3 per pair, the same in the clean and in the TD project)

* 183 bugs in 61 pairs; 70 (38%) are in a file the TD change also touched.

### bug kinds

| kind | complexity | concurrency | coupling_cohesion | dependency_structure | security | total |
|---|---|---|---|---|---|---|
| arith | 4 | 13 | 1 | 4 | 5 | 27 |
| bool_op | 6 | 9 | 3 | 1 | 4 | 23 |
| cmp_boundary | 0 | 10 | 0 | 3 | 4 | 17 |
| cmp_equality | 0 | 8 | 6 | 4 | 5 | 23 |
| const_off_by_one | 2 | 14 | 3 | 2 | 14 | 35 |
| negate_cond | 6 | 24 | 5 | 7 | 16 | 58 |
| total | 18 | 78 | 18 | 21 | 48 | 183 |

### checks done on the bugged projects (numbers recorded when the checks were run)

| check | result | status |
|---|---|---|
| bugged folders differ from the originals exactly in the bug files; clean_bug vs TD_bug differ exactly in the files of td.patch | 61 / 61 pairs | pass |
| bugged Python files parse | 246 / 246 | pass |
| bugged C files pass a syntax compile (`gcc -fsyntax-only`) with no new error | 59 / 59 files with a .c suffix | pass |
| running the injection again reproduces identical bug patches | 3 pairs re-run (Python P1, Python P30, C/C++ P5) | pass |
| bugs validated with the projects' test suites | not done (a partial attempt - boltons 12 of 24 candidates caught by tests, click 9/24, zlib 7/24, libyaml 2/24 - was stopped; nothing from it is used) | not validated |

## 1.4 Environment of the construction

| package | version |
|---|---|
| python | 3.13.13 |
| numpy | 2.5.4 |
| pandas | 3.0.6 |
| scikit-learn | 1.9.1 |
| scipy | 1.18.1 |
| joblib | 1.6.0 |
