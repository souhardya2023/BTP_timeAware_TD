# real_project_analysis: patterns and properties of technical debt in 33 real projects

Purpose: gather much more insight from real projects before building the new dataset. The result is
`INSIGHTS_REAL_PROJECTS.txt` (20 insights with numbers, strength, figure and source) and `DATASET_DESIGN_SPEC.md` (the measurable properties the new dataset must reproduce, with acceptance tests).

```
INSIGHTS_REAL_PROJECTS.txt   the insights (RP1-RP20), corrections of earlier ones, status of the earlier plan
DATASET_DESIGN_SPEC.md       properties for the new dataset (H1-H13 history, C1-C9 commits) and what the old benchmark got wrong
figures/                     A1-A9 (matplotlib, default colours)
results/                     a3_report.txt, a3b_report.txt, a4_report.txt (the full printed analyses) and every table as CSV, a*_numbers.json
data/                        per repository: transitions (interest per instance and release pair), releases, files, funcs, commits, commit_funcs
code/                        a0 clone, a1 release tables, a2 commit mining, a3/a3b release analyses, a4 commit analysis, a5 figures
```

## Corpus
33 repositories (16 Python, 17 C/C++; the 9 of the earlier study + 24 new), the last 20 release tags of each, 11,503 debt instances, 148,524 instance-releases, 448.7 person-months of interest; and the last 700 source-touching commits of 34 repositories (20,988 commits). Debt instance = a function that is a Long Method (> 50 lines), Complex Method (CCN > 10) or Many Parameters (> 5), tracked from release to release (the structural detector of `interest_exp`, used for all repositories); interest = changed lines inside a persisting debt function beyond its growth, COCOMO II.

## Run
```
code/a0_clone_corpus.sh                         # bare clones of the 24 new repositories into ../../../repos  (needs network, ~1 GB)
code/a1_run_all.sh                              # data/transitions, releases, files, funcs      (about 30 min, 3 processes)
code/a2_run_all.sh                              # data/commits, commit_funcs                    (about 25 min, 2 processes)
python code/a3_release_analysis.py              # RP1-RP13 -> results/a3_*                      (about 4 min)
python code/a3b_checks.py                       # corrections and robustness -> results/a3b_*
python code/a4_commit_analysis.py               # RP14-RP19 -> results/a4_*
python code/a5_figures.py                       # figures/                                      (needs matplotlib)
```
a1-a4 use `project_vector/.venv` (pandas, statsmodels, scikit-learn, lizard); a5 uses a Python with matplotlib. The earlier study's code `interest_exp/code` (history.py, interest_versions.py) is imported.

## Headline results (details and caveats in the insight file)
* Confirmed on 33 repositories: interest is concentrated (Gini 0.72 per repository, 0.88 pooled) and persistent (odds ratio 4.6 for an earlier event, size controlled); the chance of work rises with region size (logit slope 0.61, interest lines ~ size^0.93).
* **Corrections:** "debt is avoided" (enrichment 0.39) was a denominator artefact: among functions present in both releases debt is edited in proportion (enrichment 1.11; odds ratio 1.07 at equal size). "Size alone ties persistence" does not hold on 33 repositories (-5.4 points); size x history is +2-3 points above persistence. Debt activity falls with age (not rises).
* **New:** the release type is the clock (event rate patch 0.09, minor 0.28, major 0.31); step + days explain R2 0.27 of the release interest before the release; 76 % of new debt is born in new functions; debt is created and removed in big commits and grows net; a real commit changes a median 0.15 % of the project; natural pair candidates: 419 debt-introducing, 143 refactoring, 244 security-fix, 121 concurrency-fix commits.
* Not useful: nearby recent activity ('path of work') and the project clock add nothing to size + history.
