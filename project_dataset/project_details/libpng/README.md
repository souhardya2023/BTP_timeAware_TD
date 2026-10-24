# libpng

* repository: https://github.com/pnggroup/libpng
* language: C/C++
* pairs in the dataset: 1 (C_C++/P20)
* base commit(s) of the pairs: 55d20aaa32
* induced TD types: {'security': 1}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 4645, "first_commit": "2009-04-06", "last_commit": "2026-10-05", "authors": 121, "bug_fix_commits": 458, "lines_added": 275518, "lines_deleted": 219845, "szz_bugs": 225, "szz_median_bug_lifetime_days": 71.1, "release_tags": 1634}
