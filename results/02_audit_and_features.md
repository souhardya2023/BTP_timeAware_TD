# 2. Do the TD changes move the metrics? (the audit) and what the vectors look like

## 2.1 Metric audit of the TD changes before filtering (102 pairs)

A pair counts as 'metric moved' when a metric of its own TD type changed in the debt direction: security findings up (or validation guards down), lock / acquire count down, CCN / nesting / long functions up, dependency edges / cycles / fan-in-out up. Size = lines added + deleted.

| language | type | source | pairs | lines median (min-max) | files median | metric moved |
|---|---|---|---|---|---|---|
| C_C++ | complexity | scripted | 1 | 58 (58-58) | 1 | 1/1 |
| C_C++ | coupling_cohesion | scripted | 8 | 33 (10-162) | 2 | 0/8 |
| C_C++ | dependency_structure | scripted | 3 | 2 (2-2) | 1 | 3/3 |
| C_C++ | security | natural | 11 | 58 (2-355) | 1 | 0/11 |
| C_C++ | security | scripted | 8 | 3 (2-3) | 1 | 6/8 |
| Python | complexity | SmellBench | 5 | 138 (58-316) | 2 | 5/5 |
| Python | concurrency | scripted | 24 | 12 (3-95) | 1 | 24/24 |
| Python | coupling_cohesion | SmellBench | 17 | 74 (11-256) | 3 | 6/17 |
| Python | dependency_structure | SmellBench | 18 | 113 (9-487) | 2.5 | 4/18 |
| Python | security | scripted | 7 | 2 (1-4) | 1 | 2/7 |

Overall: the metric moved in 51 of 102 pairs. The 50 pairs in which **no** metric of the pair's own type changed were removed (`data/dropped_unchanged.csv`); one pair whose metric moved the other way was kept.

### what was removed

| td_type | C_C++ | Python | total |
|---|---|---|---|
| coupling_cohesion | 8 | 11 | 19 |
| dependency_structure | 0 | 14 | 14 |
| security | 12 | 5 | 17 |
| total | 20 | 30 | 50 |

The removal took out all C/C++ coupling pairs (functions moved between modules) and 10 of 11 natural pairs, because the import-graph and flawfinder metrics cannot see those changes. 'Not moved' means 'not visible to these metrics', not 'not debt'.

## 2.2 The same audit on the final 61 pairs

| td_type | pairs | metric_moved | lines_median |
|---|---|---|---|
| complexity | 6 | 6 | 115.500 |
| concurrency | 26 | 26 | 10 |
| coupling_cohesion | 6 | 6 | 66 |
| dependency_structure | 7 | 7 | 116 |
| security | 16 | 15 | 2 |

Metric moved in 60 of 61 pairs; the exception is the natural libpng pair (flawfinder reports fewer findings on the vulnerable side).

## 2.3 The feature vector (133 features of a project)

| block | what | features |
|---|---|---|
| code | C idioms | 8 |
| code | Python idioms | 11 |
| code | functions: count, size, cyclomatic complexity, parameters, tokens | 20 |
| code | lines of code, comments, file sizes, indentation | 11 |
| structure | dependency graph (imports / #includes) | 33 |
| structure | directory layout and file sizes | 13 |
| technical_debt | class cohesion | 4 |
| technical_debt | code smells and their principal (COCOMO II) | 15 |
| technical_debt | concurrency idioms | 6 |
| technical_debt | duplicated code | 2 |
| technical_debt | security findings and validation guards | 3 |
| technical_debt | self-admitted debt in comments | 7 |

* dataset: 61 rows; `full` layout 399 features (+ time), `delta_only` 133 (+ time); missing values: 0; infinite values: 0.
* constant features across the 61 clean projects: 1 of 133.
* pairs whose TD vector equals the clean vector exactly: 0 of 61.
* size of the TD change relative to the spread between projects: mean |delta| / std(clean) is 0.008 on average, 0.149 at most (s_pagerank_entropy). The changes are small against the differences between projects, which is why project identity is the main source of leakage.

### features that differ most between the TD types (ANOVA F of the difference columns against td_type)

| feature | F | p |
|---|---|---|
| time_diff_min | 120.2 | 8.6e-27 |
| t_very_complex | 23.1 | 2.7e-11 |
| s_fan_out_mean | 17.6 | 2.2e-09 |
| s_fan_in_mean | 17.6 | 2.2e-09 |
| s_graph_edges_per_node | 17.6 | 2.2e-09 |
| t_principal_pm | 16.2 | 6.9e-09 |
| c_sloc | 12.6 | 2.2e-07 |
| c_loc | 11.3 | 8.7e-07 |
| c_py_raise_per_kloc | 10.3 | 2.5e-06 |
| c_fn_nloc_std | 9.6 | 5.6e-06 |
| t_satd_doc | 9.4 | 6.7e-06 |
| c_comment_ratio | 8.8 | 1.5e-05 |
| c_py_doc_classes | 8.2 | 2.9e-05 |
| c_py_classes | 8.2 | 2.9e-05 |
| t_satd_requirement | 8.0 | 3.4e-05 |

`time_diff_min` ranks **1** of 109 by this F value (F = 120.2).
