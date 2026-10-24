# 3. Git history, SZZ bugs, SonarQube and version-wise interest (background data of the projects)

## 3.1 Git history and bugs mined with SZZ (per project)

| project | commits_non_merge | first_commit | last_commit | authors | bug_fix_commits | szz_bugs | szz_median_bug_lifetime_days | release_tags |
|---|---|---|---|---|---|---|---|---|
| C-Thread-Pool | 224 | 2011-11-05 | 2025-05-18 | 31 | 36 |  |  | 0 |
| boltons | 1549 | 2013-02-20 | 2026-09-23 | 129 | 196 | 158 | 56 | 54 |
| cJSON | 955 | 2009-08-26 | 2026-09-16 | 101 | 176 | 103 | 67 | 49 |
| click | 2172 | 2014-04-24 | 2026-09-23 | 468 | 268 | 187 | 148.9 | 71 |
| jansson | 874 | 2009-05-12 | 2026-07-09 | 114 | 114 | 45 | 84.5 | 34 |
| jinja | 2175 | 2007-02-26 | 2025-06-14 | 339 | 363 | 280 | 39.9 | 55 |
| libpng | 4645 | 2009-04-06 | 2026-10-05 | 121 | 458 | 225 | 71.1 | 1634 |
| libyaml | 227 | 2006-05-12 | 2026-08-21 | 36 | 45 | 26 | 829.9 | 21 |
| werkzeug | 4494 | 2007-05-04 | 2026-10-01 | 518 | 806 | 568 | 59.4 | 116 |
| zlib | 1126 | 2011-09-10 | 2026-09-21 | 95 | 159 | 56 | 597 | 78 |

Bug-fix commits are detected from the commit message (fix, bug, crash, leak, overflow, regression, CVE ... without typo / docs / style); SZZ traces the lines a fix changed back to the commit that last touched them (blank and comment lines ignored). Bug lifetime = fix date - that date. Authors are stored as hashes.

## 3.2 SonarQube server (http://localhost:9000/projects)

* 52 projects, 10727 issues. Types: CODE_SMELL 9675, BUG 841, VULNERABILITY 211. Severities: MAJOR 4066, MINOR 2616, CRITICAL 2294, INFO 1674, BLOCKER 77.
* mapping of server projects to the dataset: issue files found in the TD folder: 25, key pattern: 20, release-by-release scan: 5, not part of the dataset: 2.
* pairs with a SonarQube scan of their TD folder: 36 of 61 (all Python); C/C++ pairs: 0 (SonarQube Community has no C/C++ analyzer).

### SonarQube measures of the scanned TD projects, by TD type

| td_type | pairs | ncloc_mean | bugs_mean | vulnerabilities_mean | code_smells_mean | debt_minutes_mean |
|---|---|---|---|---|---|---|
| complexity | 5 | 14202.800 | 23.400 | 5.200 | 91.800 | 855 |
| concurrency | 19 | 12898 | 9 | 3 | 297 | 1279 |
| coupling_cohesion | 6 | 14379 | 29 | 6 | 95.500 | 875.500 |
| dependency_structure | 4 | 13339.800 | 1 | 2 | 76.800 | 718.800 |
| security | 2 | 21830 | 72 | 2.500 | 197 | 1661 |

The scans covered the TD folder only and included the tests folders that were later removed, so the numbers describe the folders at scan time; they are not used as model features (partial coverage).

## 3.3 SonarQube per release (Python projects, last 20 releases scanned in chronological order)

| project | releases | first_release | smells_first | last_release | smells_last | smells_min | smells_max |
|---|---|---|---|---|---|---|---|
| boltons | 20 | 18.0.1 | 309 | 26.2.0 | 281 | 281 | 311 |
| click | 20 | 8.1.0 | 61 | 8.5.0 | 54 | 54 | 66 |
| jinja | 20 | 2.9.6 | 140 | 3.1.6 | 97 | 93 | 145 |
| werkzeug | 20 | 2.3.6 | 152 | 3.1.9 | 132 | 132 | 152 |

## 3.4 Version-wise technical-debt interest (2025 method; COCOMO II effort)

Smell instances are followed from release to release (SonarQube issue key for Python, structural detector for C/C++). The lines re-worked inside a smell while it persists are its interest. Counts come from `td_interest/out/versions/*.csv`.

| project | versions | instance_transitions | interest_events | interest_lines | interest_person_months | repayments | introduced |
|---|---|---|---|---|---|---|---|
| boltons | 20 | 5802 | 191 | 308 | 0.524 | 70 | 42 |
| cJSON | 20 | 808 | 27 | 50 | 0.094 | 5 | 11 |
| click | 20 | 1181 | 155 | 708.300 | 1.323 | 28 | 21 |
| jansson | 20 | 639 | 170 | 825 | 1.597 | 4 | 35 |
| jinja | 20 | 2152 | 195 | 1254 | 2.441 | 100 | 57 |
| libpng | 20 | 5388 | 233 | 723 | 1.332 | 25 | 26 |
| libyaml | 13 | 854 | 114 | 192 | 0.341 | 3 | 13 |
| werkzeug | 20 | 2699 | 142 | 317 | 0.555 | 53 | 34 |
| zlib | 20 | 1330 | 380 | 1195 | 2.314 | 22 | 32 |
