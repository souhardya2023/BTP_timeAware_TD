# What every column of the dataset means

## Columns that are NOT features (identifiers and split)
| column | meaning |
|---|---|
| `id` | the datapoint: `Python/P12` or `C_C++/P3` = pair P12 / P3 of `project_dataset/Python` / `project_dataset/C_C++` |
| `project`, `language` | the open-source project the pair comes from, and Python or C/C++. **Do not feed `project` to a model**: pairs of one project share their TD type (all 24 boltons pairs are concurrency). |
| `fold` | 5-fold split, stratified by TD type (use it to compare models on identical splits) |
| `fold_by_project` | 5-fold split in which no project is in two folds (the honest split: the model never sees the project it is tested on) |
| `td_type` | **the target**: complexity, concurrency, coupling_cohesion, dependency_structure or security |
| `label` | the target as an integer (`label_map.json`) |

## The time feature
| column | meaning |
|---|---|
| `time_diff_min` | minutes to fix the injected bugs by hand in the project WITH the technical debt minus in the project WITHOUT it (sum over the pair's 3 bugs). Only in `dataset_with_time.csv`. Its values come from the ground-truth time model in `../pipeline/bug_injection/sample_times.py`; measured times can replace them with `make_dataset.py times`. |

## The feature columns (133 features, three groups)
`clean__X` = feature X of the project without technical debt (but with its 3 bugs), `td__X` = of the same project with the technical debt (and the same bugs), `delta__X` = `td__X - clean__X`. The `delta_only` dataset keeps only the `delta__X` columns.
Counts are log-scaled (`log(1+n)`) or given per KLOC (per 1000 source lines); ratios and shares are 0..1; `p50 / p90 / p100` = median, 90th percentile, maximum.

## Structure (`s_`, 46)
| feature | meaning |
|---|---|
| `s_files`, `s_dirs` | number of source files / directories (log) |
| `s_files_per_dir_mean/max` | files per directory |
| `s_depth_mean/max` | directory depth of the files |
| `s_file_bytes_log_mean/p50/p90/p100` | distribution of file sizes (log bytes) |
| `s_file_size_gini` | how unequal the file sizes are (0 equal, 1 one giant file) |
| `s_share_headers`, `s_share_init` | share of header files (C) / `__init__.py` files (Python) |
| `s_graph_nodes`, `s_graph_edges` | files and dependency links (imports in Python, `#include` in C), log |
| `s_graph_density`, `s_graph_edges_per_node` | how connected the dependency graph is |
| `s_cyc_groups` | number of dependency cycles (groups of files that depend on each other) |
| `s_cyc_nodes_share`, `s_cyc_largest` | share of files in cycles / size of the largest cycle (share of all files) |
| `s_fan_in_*` | how many files depend on a file (mean, median, p90, max) = how reused it is |
| `s_fan_out_*` | how many files a file depends on = how coupled it is |
| `s_fan_in_gini`, `s_fan_out_gini` | whether a few files carry most of the links |
| `s_instability_mean` | mean of fan-out / (fan-in + fan-out): 1 = depends on others, 0 = only depended upon |
| `s_isolated_share` | share of files with no link at all |
| `s_dep_depth` | longest dependency chain (cycles collapsed), scaled by log2 of the file count |
| `s_weak_components` | separate sub-projects (connected parts) per file |
| `s_clustering`, `s_modularity`, `s_communities` | how clustered the graph is, how well it splits into modules, how many modules per file |
| `s_assortativity` | whether highly linked files link to each other |
| `s_pagerank_max`, `s_pagerank_entropy` | importance of the most central file / how evenly importance is spread |
| `s_spec_0..5` | six smallest non-zero eigenvalues of the normalised graph Laplacian (the "shape" of the dependency structure) |

## Code (`c_`, 50)
| feature | meaning |
|---|---|
| `c_loc`, `c_sloc` | lines / source lines of code (log) |
| `c_comment_ratio`, `c_blank_ratio` | share of comment / blank lines |
| `c_file_sloc_log_*`, `c_big_files` | distribution of file lengths; share of files over 1000 source lines |
| `c_indent_max/mean` | indentation depth (a proxy for nesting) |
| `c_functions`, `c_funcs_per_kloc` | number of functions (log) and per KLOC |
| `c_fn_nloc_*` | function length in lines (mean, median, p90, max) and its spread `c_fn_nloc_std` |
| `c_fn_ccn_*` | cyclomatic complexity per function (mean, median, p90, max); `c_fn_ccn_sum_per_kloc` = total complexity per KLOC |
| `c_fn_par_*` | number of parameters per function |
| `c_fn_tok_*` | tokens per function |
| `c_fn_short_share` | share of functions of 5 lines or fewer |
| `c_py_classes`, `c_py_methods_per_class` | Python classes (log) and methods per class |
| `c_py_annotated`, `c_py_doc_funcs`, `c_py_doc_classes`, `c_py_decorated`, `c_py_async` | share of Python functions with type hints / docstrings, classes with docstrings, decorated functions, async functions |
| `c_py_try/bare_except/raise/lambda_per_kloc` | `try` blocks, bare `except:`, `raise`, `lambda` per KLOC |
| `c_c_defines/ifdefs/goto/alloc/arrow/casts/statics/asserts_per_kloc` | C idioms per KLOC: `#define`, `#if`, `goto`, `malloc/calloc/realloc/free`, `->`, pointer casts, `static`, `assert` |

## Technical debt (`t_`, 37)
| feature | meaning |
|---|---|
| `t_long_method`, `t_complex_method`, `t_many_params` | functions over 50 lines / over complexity 10 / over 5 parameters, per KLOC |
| `t_long_share`, `t_complex_share`, `t_params_share`, `t_smell_share` | the same as shares of all functions; `t_smell_share` = functions with any of the three smells |
| `t_smell_count` | number of smelly functions (log) |
| `t_principal_pm`, `t_principal_pm_per_kloc` | principal: COCOMO II effort (person-months) to rewrite all smelly functions (log of milli-person-months) and per KLOC |
| `t_very_complex`, `t_huge_functions`, `t_large_files` | functions over complexity 20 / over 150 lines, per KLOC; share of files over 1000 lines |
| `t_smell_file_share`, `t_smell_top1_share` | share of files that contain a smell; share of all smells sitting in the worst file |
| `t_god_classes` | share of Python classes with over 20 methods or 500 lines |
| `t_lcom4_mean/gt1_share/max` | class cohesion (LCOM4 = groups of methods that share no attribute; 1 = cohesive, more = should be split) |
| `t_satd_design/defect/requirement/test/doc/any` | comments admitting debt (hack, fixme, todo, "needs tests", "undocumented") per KLOC; `t_satd_ratio` = share of comments that do |
| `t_dup_ratio`, `t_dup_blocks` | share of code lines inside repeated 6-line windows; number of repeated windows (log) |
| `t_sec_findings`, `t_sec_high` | security findings (bandit for Python, flawfinder for C) per KLOC; the medium/high ones |
| `t_guards_per_kloc` | validation guards (`if bad: return/raise`) per KLOC |
| `t_conc_lock/thread/wait/atomic/global_mut_per_kloc` | locks, thread creation, waits/conditions, atomics, shared mutable globals per KLOC; `t_conc_uses_threads` = 1 if the project uses threads |
