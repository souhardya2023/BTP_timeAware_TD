# cJSON

* repository: https://github.com/DaveGamble/cJSON
* language: C/C++
* pairs in the dataset: 1 (C_C++/P7)
* base commit(s) of the pairs: 6d9f2443ab
* induced TD types: {'dependency_structure': 1}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 955, "first_commit": "2009-08-26", "last_commit": "2026-09-16", "authors": 101, "bug_fix_commits": 176, "lines_added": 16805, "lines_deleted": 6829, "szz_bugs": 103, "szz_median_bug_lifetime_days": 67.0, "release_tags": 49}
