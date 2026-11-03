# data

| folder | content |
|---|---|
| `transitions/<project>.csv` | one row per debt instance and release pair (V0 -> V1): rule, severity, region size and complexity at V0 and size at V1, age, interest so far, class of the change (`interest`, `increase`, `repayment`, `none`, `introduced`), changed lines, interest lines, `pm_interest` (COCOMO II person-months), `principal_pm` (effort to rewrite the region). 20 releases per project (13 for libyaml) |
| `transitions_structural/<project>.csv` | the same for the four Python projects with the structural smell detector instead of SonarQube (detector comparison) |
| `snapshots/<project>_snapshots.csv` | function-level snapshots from the commit history (features before the snapshot, interest in the next 100 commits); `<project>_events.csv` = every change event of a smell function |
| `earlier/` | the two result files of the first prediction model of the study (re-evaluated in `results/03_pairs_and_first_model.md`) |
