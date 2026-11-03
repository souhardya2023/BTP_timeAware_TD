# interest_exp - technical-debt interest: calculation and prediction

Everything about the **interest** of technical debt (the effort spent working inside code that carries debt, in **person-months**): how it is calculated version by version following the 2025 paper
(Wiriyakul & Senivongse), what it amounts to in 9 real projects, and what can be predicted. Code, data and results are here and can be re-run.

```
interest_exp/
  code/       the experiment code + run_all.py (the whole run) + clone_repos.sh (gets the git histories)       see code/README.md
  data/       the inputs and intermediate tables: instance-by-instance transitions, function-level snapshots     see data/README.md
  results/    the documents (00_summary.md first) and every table as CSV
  requirements.txt
```
## Result in short (20853 instance-releases, 1557 debt instances, 9 projects x 20 releases)
| | |
|---|---|
| interest paid, all projects | **10.52 person-months** (1607 events, 5572 re-worked lines); per project 0.09 - 2.44 |
| interest relative to the effort of rewriting all instances once | 0.06 overall (per project 0.01 - 0.23) |
| will an instance pay any interest in the next release (AUC) | 0.59 for unseen projects, 0.71 for later releases (chance 0.5) |
| how many person-months an instance pays | **not predictable** from the available features: no model beats "predict zero" in MAE, R2 <= 0 |
| total interest of all instances | two-part model: predicted / actual = 1.14 (leave one project out) |

Details and all numbers: `results/00_summary.md`.

## How the interest is calculated (step by step)

**Idea (Wiriyakul & Senivongse 2025).** Technical debt is a code smell that stays in the code. As long as it stays, every change that developers make *inside* the smelly code is work they do in the presence of the debt; that work is the **interest**. If they remove the smell it is **repayment** of the principal; if they make it bigger it is an **increase of the principal**. The interest is converted to effort in person-months with COCOMO II.

**Inputs.** (1) the last 20 release tags of a project, oldest to newest ("versions"); (2) for every version the list of technical-debt **instances**; (3) the git diff between consecutive versions.
* An **instance** is one detected smell at one place. Python projects: an unresolved SonarQube code smell (it has a stable *issue key*, so the same smell is recognised in the next version). C/C++ projects: SonarQube Community has no C/C++ analyzer, so a **structural smell** is used: a function that is a Long Method (more than 50 lines), a Complex Method (cyclomatic complexity above 10) or has Many Parameters (more than 5) - one instance per function and smell.
* The **region** of an instance is the function that contains it; its size is measured in source lines (comments and blank lines are not counted).

**For every instance present in version V0 and every release pair V0 -> V1:**
1. **Find it in V1** (same issue key; otherwise same rule, file and function name; files renamed in the release are followed).
2. **Count the changed lines**: from `git diff -U0 V0 V1`, the *added or modified* source lines of V1 that lie inside the region. Deleted lines are not counted (as in the paper); comments and blank lines are not counted.
3. **Classify:**
   * the instance is **gone** in V1 -> *principal repayment* (the refactoring effort is not counted as interest);
   * the instance is **new** in V1 -> *principal increase* ("introduced");
   * the instance is **still there** -> the region's growth `max(0, size in V1 - size in V0)` is the *principal increase*, and the changed lines **beyond that growth** are the **interest lines**: `interest lines = changed lines - min(changed lines, growth)`. (Work that only makes the function longer is growing the debt; work on lines that already existed is paid while the debt remains.)
4. **If a function holds several instances** (for example the same function is both Long Method and Complex Method) the changed lines are one piece of work: the interest lines and the effort are divided equally among its instances in that release pair.
5. **Effort of an event** = COCOMO II applied to its interest lines:

   `PM = A x (interest lines / 1000) ^ E`  with A = 2.94, E = 1.0997 (nominal COCOMO II.2000: E = 0.91 + 0.01 x 18.97, effort multipliers = 1). The constants of the 2025 paper could not be checked; the preset `paper` (A = 2.64, E = 0.91) is in `code/cocomo.py` and gives about 2.1 - 2.8 times larger values (`results/tables/cocomo_sensitivity.csv`).
6. **Principal of an instance** = the COCOMO II effort of its region size: the effort to rewrite the function once.
7. **Totals**: the *interest paid by an instance* = the sum of its events over the releases; *of a project* = the sum over its instances; the project value is compared with the sum of the principals of its instances.

**Worked example (real data, `data/transitions/click.csv`).** Project click, release pair 8.1.3 -> 8.1.4, function `__init__` in `src/click/_termui_impl.py`, instance `python:S107` ("too many parameters"):
* region: 56 lines in 8.1.3, 60 lines in 8.1.4 -> growth = 4 lines (principal increase);
* changed (added or modified source) lines inside the region: 12;
* interest lines = 12 - min(12, 4) = **8**;
* effort = 2.94 x (8 / 1000) ^ 1.0997 = **0.0145 person-months** (14.5 milli-person-months);
* principal of this instance = 2.94 x (56 / 1000) ^ 1.0997 = 0.1235 person-months, so this one event is 12% of the effort of rewriting the function.

**Example of shared work.** In the same release pair, `__init__` in `src/click/core.py` is flagged by 2 instances (python:S107, python:S3776); 2 lines were changed in it, so each instance gets 1.0 interest lines and 0.00158 person-months, together 0.00316.

**Units.** A *person-month* is the effort of one person for one month. One event is worth a few milli-person-months (1 mPM = 0.001 PM); the nine projects together paid 10.52 person-months over 20 releases each. SLOC = source lines of code, KSLOC = thousand SLOC.

**What this measures and what it does not.** It is the effort *implied by the size of the changes made inside debt-carrying code* (an estimate from changed lines), not measured developer time; a change inside a smell is counted whether or not the smell made it harder; the result depends on the smell detector (SonarQube finds 972 instances in the four Python projects, the structural detector 400) and on the COCOMO II constants; the paper's own detectors (JDeodorant, NiCad) were not used.

## How the prediction is set up
* **Unit of prediction**: an instance present in release V0. **Targets**: will it pay any interest between V0 and V1 (yes/no), and how many person-months (shown in milli-person-months).
* **Features** (known at V0 only): rule, severity, SonarQube's own remediation estimate, region size and cyclomatic complexity, principal, age in releases (releases since it first appeared), interest already paid (lines and events), language.
* **Evaluation on unseen data**: *leave-one-repo-out* (train on 8 projects, test on the 9th) and *temporal* (train on the first 60% of each project's releases, test on the later ones). Never a random split of rows, because rows of one instance are strongly related.
* **Models**: for the amount: `zero`, `mean`, `persistence` (the average interest of the instance so far), size-only forest, random forest, gradient boosting, and the two-part `hurdle_rf` = P(any interest) x expected effort given interest; for the yes/no: the same features with a forest classifier and baselines. A second, function-level model works on the commit history (next 100 commits). **Metrics**: MAE and R2 in mPM, `skill_vs_zero` = 1 - MAE / MAE(zero model), Spearman, AUC (0.5 = chance), and totals per repository and release.
* The experiment on the 61 dataset pairs (`results/03_pairs_and_first_model.md`) applies the function-level model to the functions each technical-debt change touched, clean vs TD side.

## Where to find what
| question | where |
|---|---|
| how much interest did each project pay, per release, per rule, per instance | `results/01_interest_calculation.md`, `results/tables/` |
| what can be predicted, with all models and numbers | `results/02_predicting_interest.md`, `results/pm_*.csv` |
| the pairs of the dataset, the first model of the study | `results/03_pairs_and_first_model.md` |
| every interest event with its inputs | `data/transitions/<project>.csv` (columns explained in `data/README.md`) |
| the code of the calculation | `code/interest_versions.py` (+ `code/cocomo.py`, `code/history.py` for the structural smells) |

## How to run
```
pip install -r requirements.txt
bash code/clone_repos.sh ../../repos            # bare clones of the 10 repositories (about 95 MB); or set INTEREST_REPOS
python code/run_all.py --repos ../../repos      # about 15 minutes; --steps transitions,structural,snapshots,models,pairs,analysis,reeval,report
```
`run_all.py` reads the SonarQube issues of every release of the Python projects from `../project_dataset/project_details/<project>/sonarqube/issues_by_release`; to re-scan the releases with your own SonarQube server use `code/sonar_versions.py` (needs `SONAR_TOKEN`). The repositories change over time: a fresh clone contains newer commits and releases than the study used (2026-10-08), so numbers differ slightly unless the clones are reset to that date.
The calculation was verified: re-running it from the git histories reproduced all 9 transition files exactly.

## What is not in this folder
The repositories themselves (git histories) and SonarQube server projects; the interest is not defined for the 61 injected dataset pairs (no history after the injected debt): the pair experiment (`results/03_pairs_and_first_model.md`) shows what a model trained on the real repositories says about them.
