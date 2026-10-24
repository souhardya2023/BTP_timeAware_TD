# click

* repository: https://github.com/pallets/click
* language: Python
* pairs in the dataset: 10 (Python/P11, Python/P12, Python/P13, Python/P17, Python/P18, Python/P19, Python/P20, Python/P21, Python/P22, Python/P23)
* base commit(s) of the pairs: 1d038f2707
* induced TD types: {'dependency_structure': 4, 'coupling_cohesion': 3, 'complexity': 3}

## Contents
* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)
* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag
* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`
* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches
* `sonarqube/` - see its README

History summary: {"commits_non_merge": 2172, "first_commit": "2014-04-24", "last_commit": "2026-09-23", "authors": 468, "bug_fix_commits": 268, "lines_added": 29321, "lines_deleted": 15796, "szz_bugs": 187, "szz_median_bug_lifetime_days": 148.9, "release_tags": 71}
