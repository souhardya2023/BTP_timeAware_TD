# boltons

* repository: https://github.com/mahmoud/boltons
* language: Python
* pairs in the dataset: 24 (Python/P3, Python/P4, Python/P5, Python/P6, Python/P7, Python/P8, Python/P9, Python/P10, Python/P26, Python/P27, Python/P28, Python/P29, Python/P30, Python/P31, Python/P32, Python/P33, Python/P34, Python/P35, Python/P36, Python/P37, Python/P38, Python/P39, Python/P40, Python/P41)
* base commit(s) of the pairs: 4e5faa3d7e
* induced TD types: {'concurrency': 24}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 1549, "first_commit": "2013-02-20", "last_commit": "2026-09-23", "authors": 129, "bug_fix_commits": 196, "lines_added": 32368, "lines_deleted": 14854, "szz_bugs": 158, "szz_median_bug_lifetime_days": 56.0, "release_tags": 54}
