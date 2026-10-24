# zlib

* repository: https://github.com/madler/zlib
* language: C/C++
* pairs in the dataset: 3 (C_C++/P5, C_C++/P6, C_C++/P9)
* base commit(s) of the pairs: 767c4c9478
* induced TD types: {'security': 2, 'dependency_structure': 1}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 1126, "first_commit": "2011-09-10", "last_commit": "2026-09-21", "authors": 95, "bug_fix_commits": 159, "lines_added": 45813, "lines_deleted": 20993, "szz_bugs": 56, "szz_median_bug_lifetime_days": 597.0, "release_tags": 78}
