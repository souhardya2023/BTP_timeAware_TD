# jansson

* repository: https://github.com/akheron/jansson
* language: C/C++
* pairs in the dataset: 6 (C_C++/P1, C_C++/P2, C_C++/P3, C_C++/P4, C_C++/P8, C_C++/P10)
* base commit(s) of the pairs: 851a2145e3
* induced TD types: {'security': 4, 'dependency_structure': 1, 'complexity': 1}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 874, "first_commit": "2009-05-12", "last_commit": "2026-07-09", "authors": 114, "bug_fix_commits": 114, "lines_added": 21033, "lines_deleted": 8285, "szz_bugs": 45, "szz_median_bug_lifetime_days": 84.5, "release_tags": 34}
