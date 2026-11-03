# code

| file | what it does |
|---|---|
| `run_all.py` | runs all steps in order (transitions, structural, snapshots, models, pairs, analysis, reeval, report) |
| `clone_repos.sh` | bare clones of the 10 repositories (git histories) |
| `versions.py` | the last K release tags of a repository |
| `cocomo.py` | COCOMO II effort for a number of lines (presets `nominal` = COCOMO II.2000, `paper` = the constants of the paper summary) |
| `interest_versions.py` | **the interest calculation**: follows every debt instance from release to release, classifies the change (interest / principal increase / repayment), converts to person-months |
| `sonar_versions.py` | scans every release with a SonarQube server (Python projects) and stores the issues; needs `SONAR_TOKEN` |
| `history.py` | function-level history: smell functions followed through the commits, snapshots with features and the interest in the next 100 commits |
| `model_next_release.py` | classification: will an instance pay interest in the next release |
| `model_pm.py` | **regression of the interest in person-months** (baselines, hurdle model, totals per release, project level) |
| `model_snapshots.py` | the function-level model on the commit history |
| `score_pairs.py` | applies the function-level model to the 61 dataset pairs |
| `analysis_tables.py` | descriptive tables: per project / release / rule, principal vs interest, concentration, sensitivity to COCOMO constants and to the detector |
| `reeval_first_model.py` | re-evaluates the first prediction model of the study |
| `build_report.py` | writes `results/*.md` from the tables |
