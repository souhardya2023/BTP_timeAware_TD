# werkzeug

* repository: https://github.com/pallets/werkzeug
* language: Python
* pairs in the dataset: 2 (Python/P1, Python/P2)
* base commit(s) of the pairs: 594452f6a4
* induced TD types: {'security': 2}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 4494, "first_commit": "2007-05-04", "last_commit": "2026-10-01", "authors": 518, "bug_fix_commits": 806, "lines_added": 105445, "lines_deleted": 91632, "szz_bugs": 568, "szz_median_bug_lifetime_days": 59.4, "release_tags": 116}
