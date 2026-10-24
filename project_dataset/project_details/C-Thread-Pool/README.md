# C-Thread-Pool

* repository: https://github.com/Pithikos/C-Thread-Pool
* language: C/C++
* pairs in the dataset: 4 (C_C++/P11, C_C++/P12, C_C++/P13, C_C++/P14)
* base commit(s) of the pairs: 2b56942a73
* induced TD types: {'concurrency': 2, 'security': 2}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 224, "first_commit": "2011-11-05", "last_commit": "2025-05-18", "authors": 31, "bug_fix_commits": 36, "lines_added": 2901, "lines_deleted": 2107, "release_tags": 0}
