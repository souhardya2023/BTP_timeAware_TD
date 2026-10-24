# jinja

* repository: https://github.com/pallets/jinja
* language: Python
* pairs in the dataset: 5 (Python/P14, Python/P15, Python/P16, Python/P24, Python/P25)
* base commit(s) of the pairs: 15206881c0
* induced TD types: {'coupling_cohesion': 3, 'complexity': 2}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 2175, "first_commit": "2007-02-26", "last_commit": "2025-06-14", "authors": 339, "bug_fix_commits": 363, "lines_added": 56666, "lines_deleted": 38433, "szz_bugs": 280, "szz_median_bug_lifetime_days": 39.9, "release_tags": 55}
