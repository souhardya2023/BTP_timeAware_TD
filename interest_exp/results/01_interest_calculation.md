# 1. Calculating the technical-debt interest (version by version, 2025 method)

## 1.1 Method

Source: Wiriyakul & Senivongse (2025), 'Estimating Technical Debt Through Changes Related to Code Smells in the Evolution of Software Projects'. The calculation (`code/interest_versions.py`):

1. **Versions** = the last 20 release tags of each project (13 for libyaml, which has fewer).
2. **TD instances** of every version: unresolved SonarQube code smells for the four Python projects (issue keys are stable across scans, so an instance is followed by its key); structural smells for the five C/C++ projects, because SonarQube Community has no C/C++ analyzer (Long Method nloc > 50, Complex Method CCN > 10, Many Parameters > 5, one instance per function and smell).
3. **Tracking**: an instance of version V0 is looked up in V1 by its issue key, or by rule + file + function.
4. **Changes**: `git diff -U0 V0 V1`; the added and modified *source* lines (comments and blank lines excluded) inside the function that contains the instance are its changed lines.
5. **Classification** per instance and release pair: the instance disappears -> principal repayment; it appears -> principal increase (introduced); it stays -> the growth of the function (up to the changed lines) is principal increase and the remaining changed lines are **interest** (work done inside the debt while it remains). A function with several instances shares its interest among them (one piece of work is not counted twice).
6. **Effort** = COCOMO II `PM = A x KSLOC^E` of the interest lines of one event (nominal COCOMO II.2000: A = 2.94, E = 1.0997, effort multipliers 1; the constants of the paper itself could not be checked, the preset `paper` uses A = 2.64, E = 0.91). The **principal** of an instance = COCOMO II of the size of its region (the effort to rewrite it).
The 'person-month' unit is the effort of one person working for a month; interest of one event is small (a few lines): the tables also give it in milli-person-months (mPM = 1/1000 PM).

## 1.2 Result per project

| project | releases | instances | instance_transitions | interest_events | interest_lines | interest_PM | mean_interest_mPM_per_event | repayments | principal_increases | introduced |
|---|---|---|---|---|---|---|---|---|---|---|
| boltons | 20 | 355 | 5802 | 191 | 308 | 0.524 | 2.744 | 70 | 19 | 42 |
| cJSON | 20 | 52 | 808 | 27 | 50 | 0.094 | 3.477 | 5 | 18 | 11 |
| click | 20 | 100 | 1181 | 155 | 708.333 | 1.323 | 8.535 | 28 | 9 | 21 |
| jansson | 20 | 58 | 639 | 170 | 825 | 1.597 | 9.395 | 4 | 6 | 35 |
| jinja | 20 | 321 | 2152 | 195 | 1254 | 2.441 | 12.519 | 100 | 8 | 57 |
| libpng | 20 | 303 | 5388 | 233 | 723 | 1.332 | 5.715 | 25 | 36 | 26 |
| libyaml | 13 | 75 | 854 | 114 | 192 | 0.341 | 2.992 | 3 | 19 | 13 |
| werkzeug | 20 | 196 | 2699 | 142 | 317 | 0.555 | 3.906 | 53 | 3 | 34 |
| zlib | 20 | 97 | 1330 | 380 | 1195 | 2.314 | 6.089 | 22 | 22 | 32 |

Total over the 9 projects: 1607 interest events, 5572 re-worked lines, **10.52 person-months** of interest paid; 20853 instance-releases analysed (an instance counts once per release it is present in).

### interest relative to the principal (principal of all instances at first sight)

| project | principal_PM | interest_PM | interest_over_principal |
|---|---|---|---|
| boltons | 11.631 | 0.524 | 0.045 |
| cJSON | 8.991 | 0.094 | 0.010 |
| click | 5.698 | 1.323 | 0.232 |
| jansson | 26.308 | 1.597 | 0.061 |
| jinja | 17.646 | 2.441 | 0.138 |
| libpng | 68.241 | 1.332 | 0.020 |
| libyaml | 13.224 | 0.341 | 0.026 |
| werkzeug | 8.387 | 0.555 | 0.066 |
| zlib | 19.706 | 2.314 | 0.117 |

`interest_over_principal` = interest paid over the 20 releases divided by the effort to rewrite all the instances once; a value below 1 means that so far less effort went into working inside the debt than rewriting it would take.

## 1.3 Over time (per release pair)

| project | release_pairs | median_PM_per_release | max_PM_in_one_release | release_with_max | share_of_release_pairs_without_interest |
|---|---|---|---|---|---|
| boltons | 19 | 0.012 | 0.170 | 23.1.1 -> 24.0.0 | 0.263 |
| cJSON | 19 | 0 | 0.062 | v1.7.10 -> v1.7.11 | 0.632 |
| click | 19 | 0.020 | 0.588 | 8.1.8 -> 8.2.0 | 0.211 |
| jansson | 19 | 0.034 | 0.802 | v2.12 -> v2.13 | 0.211 |
| jinja | 19 | 0.013 | 1.087 | 2.10.3 -> 2.11.0 | 0.263 |
| libpng | 19 | 0.018 | 0.583 | v1.6.46 -> v1.6.47 | 0.158 |
| libyaml | 12 | 0.016 | 0.112 | 0.1.1 -> 0.1.2 | 0.250 |
| werkzeug | 19 | 0.009 | 0.144 | 3.1.8 -> 3.1.9 | 0.263 |
| zlib | 19 | 0.041 | 0.663 | v1.2.8 -> v1.2.9 | 0 |

Full series: `tables/release_series.csv` (project, release pair, instances, events, lines, PM, repayments, introduced).

## 1.4 What pays the interest

### SonarQube rules (Python projects), 12 rules with the most interest

| rule | rule_name | distinct_instances | events | interest_lines | interest_PM | share_of_interest_PM | events_per_100_instance_transitions |
|---|---|---|---|---|---|---|---|
| python:S3776 | Cognitive Complexity of functions should not be too high | 209 | 272 | 1378.433 | 2.622 | 0.541 | 11.193 |
| python:S107 | Functions, methods and lambdas should not have too many parameters | 15 | 20 | 182.333 | 0.355 | 0.073 | 10.929 |
| python:S5806 | Builtins should not be shadowed by local variables | 54 | 48 | 176.917 | 0.325 | 0.067 | 9.057 |
| python:S1192 | String literals should not be duplicated | 51 | 28 | 125.750 | 0.242 | 0.050 | 5.501 |
| python:S1172 | Unused function parameters should be removed | 162 | 69 | 118 | 0.199 | 0.041 | 4.475 |
| python:S1135 | Track uses of "TODO" tags | 92 | 57 | 109.100 | 0.190 | 0.039 | 3.457 |
| python:S8513 | "startswith" and "endswith" calls should use tuples instead of multiple "or" operators | 6 | 7 | 80.667 | 0.169 | 0.035 | 16.667 |
| python:S5720 | "self" should be the first argument to instance methods | 10 | 10 | 54 | 0.101 | 0.021 | 19.608 |
| python:S3626 | Jump statements should not be redundant | 60 | 33 | 56.233 | 0.094 | 0.019 | 3.039 |
| python:S7498 | Literal syntax should be preferred when creating empty collections or dictionaries with keyword arguments | 9 | 13 | 40.833 | 0.076 | 0.016 | 10.236 |
| python:S6659 | 'startswith' or 'endswith' methods should be used instead of string slicing in condition expressions | 19 | 16 | 39.500 | 0.072 | 0.015 | 9.040 |
| python:S1481 | Unused local variables should be removed | 30 | 11 | 38.500 | 0.069 | 0.014 | 3.323 |

62 rules appear; the first 5 carry 77% of the interest PM of the Python projects. All rules: `tables/interest_by_sonar_rule.csv`.

### SonarQube severity

| severity | instance_transitions | events | interest_PM | events_per_100_instance_transitions |
|---|---|---|---|---|
| BLOCKER | 19 | 6 | 0.033 | 31.579 |
| CRITICAL | 3443 | 323 | 3.014 | 9.381 |
| INFO | 1649 | 57 | 0.190 | 3.457 |
| MAJOR | 3652 | 207 | 1.268 | 5.668 |
| MINOR | 3071 | 90 | 0.339 | 2.931 |

### structural smells (C/C++ projects)

| rule | instance_transitions | distinct_instances | events | interest_lines | interest_PM | events_per_100_instance_transitions |
|---|---|---|---|---|---|---|
| complex_method | 4740 | 313 | 491 | 1793.167 | 3.409 | 10.359 |
| long_method | 3504 | 224 | 362 | 1021.167 | 1.955 | 10.331 |
| many_params | 775 | 48 | 71 | 170.667 | 0.314 | 9.161 |

## 1.5 Principal vs interest per instance

| statistic | value |
|---|---|
| instances | 1557 |
| instances_that_paid_interest | 768 |
| share_that_paid | 0.493 |
| median_interest_over_principal_if_paid | 0.085 |
| mean_interest_over_principal_if_paid | 0.196 |
| instances_with_interest_above_principal | 14 |
| median_transitions_present | 17 |
| max_transitions_present | 19 |

### the 10 instances that paid the most interest

A function that is flagged by two smells (e.g. Long Method and Complex Method) appears twice, each instance with half of the function's interest; `principal_PM` is the effort to rewrite the function once.

| repo | file | function_name | rule | transitions_present | interest_events | interest_lines | interest_PM | principal_PM | interest_over_principal |
|---|---|---|---|---|---|---|---|---|---|
| zlib | deflate.c | deflate | complex_method | 19 | 5 | 73 | 0.173 | 0.660 | 0.262 |
| zlib | deflate.c | deflate | long_method | 19 | 5 | 73 | 0.173 | 0.660 | 0.262 |
| click | src/click/testing.py | isolation | python:S3776 | 19 | 6 | 75 | 0.152 | 0.193 | 0.785 |
| jansson | src/dump.c | do_dump | long_method | 19 | 12 | 56.167 | 0.111 | 0.504 | 0.221 |
| jansson | src/dump.c | do_dump | complex_method | 19 | 12 | 56.167 | 0.111 | 0.504 | 0.221 |
| jansson | src/pack_unpack.c | unpack | long_method | 19 | 6 | 47.500 | 0.097 | 0.206 | 0.474 |
| jansson | src/pack_unpack.c | unpack | complex_method | 19 | 6 | 47.500 | 0.097 | 0.206 | 0.474 |
| zlib | zutil.c | zlibCompileFlags | complex_method | 19 | 6 | 49 | 0.096 | 0.099 | 0.963 |
| zlib | gzwrite.c | gzvprintf | complex_method | 13 | 5 | 49 | 0.096 | 0.076 | 1.259 |
| zlib | deflate.c | deflate_stored | complex_method | 19 | 8 | 48.500 | 0.095 | 0.069 | 1.376 |

### concentration of interest in a few instances

| repo | instances | top_1_instance_share | top_5pct_share | top_10pct_share | instances_needed_for_half |
|---|---|---|---|---|---|
| boltons | 355 | 0.064 | 0.478 | 0.680 | 19 |
| cJSON | 52 | 0.662 | 0.716 | 0.843 | 1 |
| click | 100 | 0.115 | 0.340 | 0.526 | 10 |
| jansson | 58 | 0.070 | 0.139 | 0.315 | 9 |
| jinja | 321 | 0.038 | 0.427 | 0.636 | 21 |
| libpng | 303 | 0.061 | 0.417 | 0.588 | 22 |
| libyaml | 75 | 0.144 | 0.359 | 0.563 | 6 |
| werkzeug | 196 | 0.153 | 0.556 | 0.732 | 8 |
| zlib | 97 | 0.075 | 0.232 | 0.415 | 13 |

### what happens to the instances (last release pair in which each appears)

| repo | instances | repaid | share_repaid | median_transitions_present |
|---|---|---|---|---|
| boltons | 355 | 70 | 0.197 | 19 |
| cJSON | 52 | 5 | 0.096 | 19 |
| click | 100 | 28 | 0.280 | 10 |
| jansson | 58 | 3 | 0.052 | 10.500 |
| jinja | 321 | 100 | 0.312 | 5 |
| libpng | 303 | 24 | 0.079 | 19 |
| libyaml | 75 | 2 | 0.027 | 12 |
| werkzeug | 196 | 38 | 0.194 | 15.500 |
| zlib | 97 | 20 | 0.206 | 19 |

## 1.6 Sensitivity

### COCOMO II constants (nominal COCOMO II.2000 vs the constants of the paper summary)

| repo | pm_nominal | pm_paper | ratio_paper_over_nominal |
|---|---|---|---|
| boltons | 0.503 | 1.394 | 2.772 |
| cJSON | 0.092 | 0.207 | 2.259 |
| click | 1.296 | 2.894 | 2.233 |
| jansson | 1.506 | 3.374 | 2.240 |
| jinja | 2.384 | 4.946 | 2.075 |
| libpng | 1.266 | 3.073 | 2.427 |
| libyaml | 0.326 | 0.846 | 2.595 |
| werkzeug | 0.548 | 1.373 | 2.508 |
| zlib | 2.198 | 4.897 | 2.228 |

| statistic | value |
|---|---|
| Spearman correlation of the project totals (nominal vs paper constants) | 0.9666666666666667 |
| Spearman correlation of the per-event effort | 1.0 |
| nominal COCOMO II.2000: A, E | 2.94, 1.0997 |
| paper preset: A, E | 2.64, 0.91 |

The paper-summary constants give 2.07 to 2.77 times the effort of the nominal ones (E = 0.91 < 1 makes small changes relatively more expensive); the ranking of events is identical and the ranking of the projects almost (Spearman 0.97).

### SonarQube issues vs the structural smell detector (Python projects)

| repo | sonar_instances | structural_instances | sonar_events | structural_events | sonar_PM | structural_PM | spearman_of_per_release_PM |
|---|---|---|---|---|---|---|---|
| boltons | 355 | 64 | 191 | 73 | 0.524 | 0.250 | 0.810 |
| click | 100 | 93 | 155 | 207 | 1.323 | 1.403 | 0.975 |
| jinja | 321 | 129 | 195 | 119 | 2.441 | 2.160 | 0.839 |
| werkzeug | 196 | 114 | 142 | 156 | 0.555 | 0.628 | 0.861 |

The total amount of interest depends on the detector (SonarQube finds 972 instances in the four Python projects, the structural detector 400; total interest 4.84 vs 4.44 PM), while the pattern over the releases is similar (Spearman correlation of the per-release PM of the two detectors: 0.81 to 0.98).
