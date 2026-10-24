# libyaml

* repository: https://github.com/yaml/libyaml
* language: C/C++
* pairs in the dataset: 5 (C_C++/P15, C_C++/P16, C_C++/P17, C_C++/P18, C_C++/P19)
* base commit(s) of the pairs: 90a56d4500
* induced TD types: {'security': 5}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 227, "first_commit": "2006-05-12", "last_commit": "2026-08-21", "authors": 36, "bug_fix_commits": 45, "lines_added": 18567, "lines_deleted": 5555, "szz_bugs": 26, "szz_median_bug_lifetime_days": 829.9, "release_tags": 21}
