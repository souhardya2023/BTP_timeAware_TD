# SonarQube details of werkzeug

* `issues_by_release/<tag>.json` - every unresolved code smell SonarQube reported for each release (last 20 release tags, scanned in chronological order, so issue keys are stable from release to release).
* `releases_summary.csv` - code smells per release by severity.
* `scan_of_TD_projects.csv` - SonarQube issues found when the TD projects of this project's pairs were scanned (one row per issue, with the pair, TD type and subtype).
* `version_wise_interest.csv` - the technical-debt instances followed from release to release: classification (interest / increase / repayment), changed lines, COCOMO II effort in person-months.

See `../git_history/` for the commit history.

## From the SonarQube server (http://localhost:9000/projects)
* `server_projects.csv` - the server projects that belong to this dataset project (scans of the TD folders of its pairs, release scans) and how each key was mapped
* `server_measures.csv` - their measures (lines of code, bugs, vulnerabilities, code smells, technical debt in minutes, ratings, duplication, complexity ...)
* `server_issues.csv` - their issues (rule, severity, type, status, file, line, message, effort, tags, dates)
All projects of the server: `../../../sonarqube_server/`.
