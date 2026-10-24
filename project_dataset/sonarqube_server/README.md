# sonarqube_server - everything the SonarQube server holds about the projects

Exported from the study's SonarQube server (http://localhost:9000/projects, Community Build 26.8.0.126808) on 2026-10-24 12:11: 52 projects, 10727 issues, 101 rules.
The script is `../../pipeline/tools/export_sonarqube_server.py` (it reads the access token from the environment; the token is not stored anywhere in the dataset).

| file | content |
|---|---|
| `projects.csv` | one row per server project: key, name, quality gate, issues, first / last issue date, **which dataset pair or project it belongs to** (`dataset_pair`, `dataset_project`, `td_type`, `mapping`) |
| `measures.csv` | one row per server project: lines of code (`ncloc`), `bugs`, `vulnerabilities`, `code_smells`, technical debt in minutes (`sqale_index`) and its ratio, ratings, duplication, complexity, cognitive complexity, remediation efforts ... (`metrics.csv` defines them) |
| `issues/<project_key>.csv` | every issue of that project: rule, severity, type (BUG / VULNERABILITY / CODE_SMELL), status, file, line, message, effort, clean-code attribute, impacts, tags, creation / update date (issue authors are not exported) |
| `issues_all.csv` | all issues together (column `project_key`) |
| `rules.csv` | the rules that appear: name, language, type, severity, tags, short description |
| `hotspots.csv` | security hotspots (the server has none) |
| `metrics.csv`, `server_info.json` | metric definitions; server version and export date |

## What the 52 server projects are
| kind | projects | key |
|---|---|---|
| scans of the TD folders of Python pairs (`Language-Pair-TD` keys) | 20 | `Python-P1-TD` ... `Python-P26-TD`, `werkzeug-P1-TD` |
| scans of the TD folders (folder name as key) | 25 | `P2_TD` ... `P41_TD`. A key like `P20_TD` could mean Python P20 or C/C++ P20; it was assigned to the pair whose TD folder contains the files carrying the issues (the match is 52-69% because the tests folders, which were scanned too, were removed from the dataset later) |
| release-by-release scans | 5 | `hist-click`, `hist2-boltons`, `hist2-click`, `hist2-jinja`, `hist2-werkzeug` (the issues of each of the last 20 releases are in `../project_details/<project>/sonarqube/issues_by_release/`) |
| not part of the dataset | 2 | `BTP`, `search-o-SAURS` |

## Coverage and limits
* **36 of the 61 pairs have a SonarQube scan** (all Python: concurrency 19, coupling_cohesion 6, complexity 5, dependency_structure 4, security 2); 5 Python pairs and **all 20 C/C++ pairs have none**: SonarQube Community has no C/C++ analyzer. Nine pairs were scanned under two keys; the one with more issues is used in `properties_all_pairs.csv`.
* Only the **TD folder** of a pair was scanned (not the clean folder, not the bugged folders), and at that time the folder still contained its tests folder, so the counts include issues of test code.
* The issues are SonarQube's own view: 9675 code smells, 841 bugs and 211 vulnerabilities (by severity: 4066 major, 2616 minor, 2294 critical, 1674 info, 77 blocker).
* The token of the study has no permission for the analysis-history endpoints, so analysis dates are not exported (first / last issue dates are given instead).
* Because the coverage is partial (Python only, TD side only), the SonarQube measures are **not** used as features of the machine-learning dataset.

## Where else the SonarQube data appears
* `../properties_all_pairs.csv`: for every scanned pair the columns `sonar_project_key`, `sonar_ncloc`, `sonar_bugs`, `sonar_vulnerabilities`, `sonar_code_smells`, `sonar_debt_minutes`, `sonar_debt_ratio`, `sonar_duplication_pct` (empty where there is no scan);
* `../project_details/<project>/sonarqube/`: `server_projects.csv`, `server_measures.csv`, `server_issues.csv` of the server projects that belong to that project.
