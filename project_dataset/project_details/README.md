# project_details - git history, SonarQube and properties of the 10 projects

One folder per project, the same layout everywhere:
```
<project>/
  README.md                what the project is, which pairs it contributes, what the files contain
  pairs.csv                its pairs: TD type/subtype, CWE, description, files and lines changed, validation (the columns of ../properties_all_pairs.csv)
  git_history/
      commits.csv                 every non-merge commit: sha, date, pseudonymised author (sha1 of the e-mail, 10 hex digits), subject, lines added/deleted, source files touched, bug-fix flag
      releases.csv                all release tags with their date
      szz_bugs.csv                bugs mined with SZZ: fix commit, bug-introducing commit, bug lifetime in days
      summary.json                commits, authors, first/last commit, bug-fix commits, mined bugs, median bug lifetime
      history_interest_of_pairs.csv   the earlier historical analysis of the files each pair touches (commits, effort in person-months)
  sonarqube/
      README.md                   what is in this folder for this project
      issues_by_release/<tag>.json    (Python projects) every unresolved code smell SonarQube found in each of the last 20 releases, scanned in chronological order
      releases_summary.csv            code smells per release by severity
      server_projects.csv / server_measures.csv / server_issues.csv   the server projects of this dataset project, their measures and issues (from ../../sonarqube_server)
      scan_of_TD_projects.csv         SonarQube issues found when the TD folders of the pairs were scanned (Python: real issues; C/C++: placeholder rows, no analyzer)
      version_wise_interest.csv       technical-debt instances followed from release to release: interest / principal increase / repayment, changed lines, COCOMO II effort
```
## Projects
| project | language | pairs | TD types of its pairs | commits | years | bugs mined (SZZ) | SonarQube |
|---|---|---|---|---|---|---|---|
| C-Thread-Pool | C/C++ | 4 | concurrency 2, security 2 | 224 | 2011-2025 |  | no C/C++ analyzer |
| boltons | Python | 24 | concurrency 24 | 1549 | 2013-2026 | 158 | per-release issues (20 releases) |
| cJSON | C/C++ | 1 | dependency_structure 1 | 955 | 2009-2026 | 103 | no C/C++ analyzer |
| click | Python | 10 | dependency_structure 4, coupling_cohesion 3, complexity 3 | 2172 | 2014-2026 | 187 | per-release issues (20 releases) |
| jansson | C/C++ | 6 | security 4, dependency_structure 1, complexity 1 | 874 | 2009-2026 | 45 | no C/C++ analyzer |
| jinja | Python | 5 | coupling_cohesion 3, complexity 2 | 2175 | 2007-2025 | 280 | per-release issues (20 releases) |
| libpng | C/C++ | 1 | security 1 | 4645 | 2009-2026 | 225 | no C/C++ analyzer |
| libyaml | C/C++ | 5 | security 5 | 227 | 2006-2026 | 26 | no C/C++ analyzer |
| werkzeug | Python | 2 | security 2 | 4494 | 2007-2026 | 568 | per-release issues (20 releases) |
| zlib | C/C++ | 3 | security 2, dependency_structure 1 | 1126 | 2011-2026 | 56 | no C/C++ analyzer |

## How the details were obtained
* commits and releases: the full git history of each repository (bare clone), with the bug-fix flag from the commit message (fix, bug, crash, leak, overflow, regression, CVE ... and not typo/docs/style).
* SZZ: for every bug-fix commit the changed lines are traced back with `git blame` to the commit that last touched them (blank and comment lines ignored); lifetime = fix date - that date.
* SonarQube: Community Build 26.8 on localhost; it has **no C/C++ analyzer**, so the five C/C++ projects have no SonarQube issues; their smells per release come from a structural detector (Long Method nloc>50, Complex Method CCN>10, Many Parameters >5).
* version-wise interest follows the 2025 method (Wiriyakul & Senivongse): smell instances tracked from release to release, the lines re-worked inside a smell while it persists are its interest, converted to effort with COCOMO II.
* Author e-mails are replaced by a hash. C-Thread-Pool has too little history of smells for a version-wise interest file.
