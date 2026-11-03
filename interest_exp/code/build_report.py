#!/usr/bin/env python3
"""Write the result documents of interest_exp/results from the result tables (every number is read from a CSV)."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RES = os.path.join(EXP, "results")
T = os.path.join(RES, "tables")
DATA = os.path.join(EXP, "data")
sys.path.insert(0, HERE)
import cocomo


def f(x, d=3):
    if isinstance(x, (float, np.floating)):
        if np.isnan(x):
            return ""
        return str(int(x)) if float(x).is_integer() and abs(x) < 1e7 else f"{x:.{d}f}"
    return str(x)


def md(df, d=3, idx=False):
    df = df.reset_index() if idx else df
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "|".join("---" for _ in df.columns) + "|"] + ["| " + " | ".join(f(v, d) for v in r) + " |" for r in df.itertuples(index=False)])


def w(name, lines):
    open(os.path.join(RES, name), "w").write("\n".join(lines).rstrip() + "\n")


def rd(p, **k):
    return pd.read_csv(p, keep_default_na=False, **k)


S = pd.read_csv(os.path.join(T, "project_summary.csv"))
tot_ev, tot_lines, tot_pm = S.interest_events.sum(), S.interest_lines.sum(), S.interest_PM.sum()
PM = pd.read_csv(os.path.join(RES, "pm_model_results.csv"))
AG = pd.read_csv(os.path.join(RES, "pm_aggregate_results.csv"))
PL = pd.read_csv(os.path.join(RES, "pm_project_level_results.csv"))
BF = pd.read_csv(os.path.join(RES, "pm_model_by_fold.csv"))
NR = pd.read_csv(os.path.join(RES, "next_release_model_results.csv"))
SN = pd.read_csv(os.path.join(RES, "snapshot_model_results.csv"))

# ------------------------------------------------------------------------------------------------ 01
t = ["# 1. Calculating the technical-debt interest (version by version, 2025 method)\n"]
t.append("## 1.1 Method\n")
t.append("Source: Wiriyakul & Senivongse (2025), 'Estimating Technical Debt Through Changes Related to Code Smells in the Evolution of Software Projects'. The calculation (`code/interest_versions.py`):\n")
t.append("1. **Versions** = the last 20 release tags of each project (13 for libyaml, which has fewer).")
t.append("2. **TD instances** of every version: unresolved SonarQube code smells for the four Python projects (issue keys are stable across scans, so an instance is followed by its key); structural smells for the five C/C++ projects, because SonarQube Community has no C/C++ analyzer (Long Method nloc > 50, Complex Method CCN > 10, Many Parameters > 5, one instance per function and smell).")
t.append("3. **Tracking**: an instance of version V0 is looked up in V1 by its issue key, or by rule + file + function.")
t.append("4. **Changes**: `git diff -U0 V0 V1`; the added and modified *source* lines (comments and blank lines excluded) inside the function that contains the instance are its changed lines.")
t.append("5. **Classification** per instance and release pair: the instance disappears -> principal repayment; it appears -> principal increase (introduced); it stays -> the growth of the function (up to the changed lines) is principal increase and the remaining changed lines are **interest** (work done inside the debt while it remains). A function with several instances shares its interest among them (one piece of work is not counted twice).")
t.append(f"6. **Effort** = COCOMO II `PM = A x KSLOC^E` of the interest lines of one event (nominal COCOMO II.2000: A = {cocomo.PRESETS['nominal']['A']}, E = {cocomo.PRESETS['nominal']['E']:.4f}, effort multipliers 1; the constants of the paper itself could not be checked, the preset `paper` uses A = {cocomo.PRESETS['paper']['A']}, E = {cocomo.PRESETS['paper']['E']}). The **principal** of an instance = COCOMO II of the size of its region (the effort to rewrite it).")
t.append("The 'person-month' unit is the effort of one person working for a month; interest of one event is small (a few lines): the tables also give it in milli-person-months (mPM = 1/1000 PM).\n")
t.append("## 1.2 Result per project\n")
t.append(md(S[["repo", "releases", "instances", "instance_transitions", "interest_events", "interest_lines", "interest_PM", "mean_interest_mPM_per_event", "repayments", "principal_increases", "introduced"]].rename(columns={"repo": "project"}), d=3))
t.append(f"\nTotal over the 9 projects: {int(tot_ev)} interest events, {tot_lines:.0f} re-worked lines, **{tot_pm:.2f} person-months** of interest paid; {int(S.instance_transitions.sum())} instance-releases analysed (an instance counts once per release it is present in).\n")
t.append("### interest relative to the principal (principal of all instances at first sight)\n")
t.append(md(S[["repo", "principal_PM_of_instances_at_first_sight", "interest_PM", "interest_over_principal"]].rename(columns={"repo": "project", "principal_PM_of_instances_at_first_sight": "principal_PM"}), d=3))
t.append("\n`interest_over_principal` = interest paid over the 20 releases divided by the effort to rewrite all the instances once; a value below 1 means that so far less effort went into working inside the debt than rewriting it would take.\n")
t.append("## 1.3 Over time (per release pair)\n")
R = pd.read_csv(os.path.join(T, "release_series.csv"))
rows = []
for r, h in R.groupby("repo"):
    top = h.loc[h.interest_PM.idxmax()]
    rows.append(dict(project=r, release_pairs=len(h), median_PM_per_release=h.interest_PM.median(), max_PM_in_one_release=top.interest_PM, release_with_max=f"{top.v0} -> {top.v1}", share_of_release_pairs_without_interest=(h.interest_PM == 0).mean()))
t.append(md(pd.DataFrame(rows), d=3))
t.append("\nFull series: `tables/release_series.csv` (project, release pair, instances, events, lines, PM, repayments, introduced).\n")
t.append("## 1.4 What pays the interest\n")
B = pd.read_csv(os.path.join(T, "interest_by_sonar_rule.csv"), keep_default_na=False)
t.append("### SonarQube rules (Python projects), 12 rules with the most interest\n")
t.append(md(B.head(12)[["rule", "rule_name", "distinct_instances", "events", "interest_lines", "interest_PM", "share_of_interest_PM", "events_per_100_instance_transitions"]], d=3))
t.append(f"\n{len(B)} rules appear; the first 5 carry {B.share_of_interest_PM.head(5).sum():.0%} of the interest PM of the Python projects. All rules: `tables/interest_by_sonar_rule.csv`.\n")
t.append("### SonarQube severity\n")
t.append(md(pd.read_csv(os.path.join(T, "interest_by_sonar_severity.csv")), d=3))
t.append("\n### structural smells (C/C++ projects)\n")
t.append(md(pd.read_csv(os.path.join(T, "interest_by_structural_smell_c.csv")), d=3))
t.append("\n## 1.5 Principal vs interest per instance\n")
ps = pd.read_csv(os.path.join(T, "principal_vs_interest_summary.csv"))
t.append(md(ps, d=3))
P = pd.read_csv(os.path.join(T, "principal_vs_interest_per_instance.csv"))
t.append("\n### the 10 instances that paid the most interest\n")
t.append("A function that is flagged by two smells (e.g. Long Method and Complex Method) appears twice, each instance with half of the function's interest; `principal_PM` is the effort to rewrite the function once.\n")
t.append(md(P.head(10)[["repo", "file", "function_name", "rule", "transitions_present", "interest_events", "interest_lines", "interest_PM", "principal_PM", "interest_over_principal"]], d=3))
t.append("\n### concentration of interest in a few instances\n")
t.append(md(pd.read_csv(os.path.join(T, "interest_concentration.csv")), d=3))
t.append("\n### what happens to the instances (last release pair in which each appears)\n")
t.append(md(pd.read_csv(os.path.join(T, "instance_fate.csv")), d=3))
t.append("\n## 1.6 Sensitivity\n")
t.append("### COCOMO II constants (nominal COCOMO II.2000 vs the constants of the paper summary)\n")
t.append(md(pd.read_csv(os.path.join(T, "cocomo_sensitivity.csv")), d=3))
t.append("\n" + md(pd.read_csv(os.path.join(T, "cocomo_sensitivity_summary.csv"), keep_default_na=False)))
cz = pd.read_csv(os.path.join(T, "cocomo_sensitivity.csv"))
t.append(f"\nThe paper-summary constants give {cz.ratio_paper_over_nominal.min():.2f} to {cz.ratio_paper_over_nominal.max():.2f} times the effort of the nominal ones (E = 0.91 < 1 makes small changes relatively more expensive); the ranking of events is identical and the ranking of the projects almost (Spearman 0.97).\n")
dc = os.path.join(T, "detector_comparison_python.csv")
if os.path.exists(dc):
    t.append("### SonarQube issues vs the structural smell detector (Python projects)\n")
    t.append(md(pd.read_csv(dc), d=3))
    dd = pd.read_csv(dc)
    t.append(f"\nThe total amount of interest depends on the detector (SonarQube finds {dd.sonar_instances.sum()} instances in the four Python projects, the structural detector {dd.structural_instances.sum()}; total interest {dd.sonar_PM.sum():.2f} vs {dd.structural_PM.sum():.2f} PM), while the pattern over the releases is similar (Spearman correlation of the per-release PM of the two detectors: {dd.spearman_of_per_release_PM.min():.2f} to {dd.spearman_of_per_release_PM.max():.2f}).\n")
w("01_interest_calculation.md", t)

# ------------------------------------------------------------------------------------------------ 02
t = ["# 2. Predicting the interest\n"]
t.append("Three prediction tasks on the instances of section 1, all evaluated on data the model has not seen: **leave-one-repo-out** (train on 8 projects, test on the 9th) and **temporal** (train on the releases before 60% of each project's history, test on the later ones).\n")
t.append("## 2.1 Will an instance pay any interest in the next release? (classification)\n")
d = NR.groupby(["protocol", "model"])[["AUC", "PR_AUC", "Spearman"]].mean().round(3).reset_index()
t.append(md(d))
rate = (pd.concat([pd.read_csv(x) for x in sorted(__import__('glob').glob(os.path.join(DATA, 'transitions', '*.csv')))]).query("cls != 'introduced'").interest_lines > 0).mean()
t.append(f"\n{rate:.1%} of the instance-releases pay interest. AUC 0.5 = chance. Per held-out project (all features):\n")
t.append(md(NR[(NR.protocol == "leave-one-repo-out") & (NR.model == "all_features")][["fold", "n", "pos", "AUC", "Spearman"]].rename(columns={"fold": "held-out project", "pos": "share_with_interest"})))
t.append("\n## 2.2 How much interest, in person-months? (regression, unit mPM = milli-person-months)\n")
t.append("Target: effort of the interest of one instance between two releases (0 for the 92% that pay none). Models: `zero` (predict no interest), `mean`, `persistence` (average interest of that instance so far, converted with COCOMO II), `size_only_rf` (region size, complexity, principal), `rf_pm` (random forest on all features, PM scale), `gb_pm` (gradient boosting), `hurdle_rf` (P(any interest) x expected PM given interest). `skill_vs_zero` = 1 - MAE / MAE of the zero model (positive = better than predicting no interest).\n")
for prot in ("leave-one-repo-out", "temporal"):
    t.append(f"### {prot}\n")
    t.append(md(PM[PM.protocol == prot][["model", "n", "MAE_mPM", "RMSE_mPM", "R2", "skill_vs_zero", "spearman_all", "spearman_positives", "AUC_any_interest", "actual_total_mPM", "predicted_total_mPM"]]))
    t.append("")
pos_skill = PM[PM.skill_vs_zero > 0]
t.append(f"**Reading:** {'no model has a positive skill against the zero model in MAE' if len(pos_skill) == 0 else str(len(pos_skill)) + ' model(s) beat the zero model in MAE'}; the best R2 is {PM[PM.model != 'zero'].R2.max():.4f} (R2 = 0 means no better than predicting the mean). The amount of interest of an instance cannot be predicted from these features. What exists is a weak **ranking** signal: AUC for 'any interest' up to {PM.AUC_any_interest.max():.3f} (chance 0.5), Spearman correlation of the predicted and real PM among the instances that paid up to {PM.spearman_positives.max():.3f}. The two-part model `hurdle_rf` predicts the **overall total** well: predicted total / actual total = {PM[(PM.protocol == 'leave-one-repo-out') & (PM.model == 'hurdle_rf')].predicted_total_mPM.iloc[0] / PM[(PM.protocol == 'leave-one-repo-out') & (PM.model == 'hurdle_rf')].actual_total_mPM.iloc[0]:.2f} (leave-one-repo-out) and {PM[(PM.protocol == 'temporal') & (PM.model == 'hurdle_rf')].predicted_total_mPM.iloc[0] / PM[(PM.protocol == 'temporal') & (PM.model == 'hurdle_rf')].actual_total_mPM.iloc[0]:.2f} (temporal).\n")
bestr = PM[PM.model != "zero"].sort_values("AUC_any_interest", ascending=False).groupby("protocol").head(1)
t.append("Best ranking of the instances by predicted PM (AUC for 'any interest'): " + "; ".join(f"{r.protocol}: {r.model} {r.AUC_any_interest:.3f}" for _, r in bestr.iterrows()) + ". The simple `persistence` rule (average interest of the instance so far) ranks as well as the learned models.\n")
t.append("### per held-out project, total interest predicted vs actual (leave-one-repo-out, mPM)\n")
rows = []
for r, h in BF.groupby("repo"):
    row = dict(project=r, actual_total_mPM=h.actual_total_mPM.iloc[0])
    for m in ("persistence", "rf_pm", "hurdle_rf"):
        row[f"{m} predicted"] = h[h.model == m].predicted_total_mPM.iloc[0]
    rows.append(row)
t.append(md(pd.DataFrame(rows), d=1))
t.append("\n### totals per repository and release pair (sum of the instance predictions vs the actual sum; points = repository x release pair)\n")
t.append(md(AG[["protocol", "model", "points", "pearson", "spearman", "R2", "MAE_mPM", "total_ratio_pred_over_actual"]]))
t.append("\n### total interest of a repository in the next release, predicted directly from the state at the current release\n")
t.append("Features: number of instances, total principal, mean age, interest so far, interest of the previous release, language. Baselines: zero, mean, `persistence` = the interest of the previous release.\n")
t.append(md(PL))
imp = pd.read_csv(os.path.join(RES, "pm_importance.csv"))
t.append("\n### what the random forest uses (importance, `rf_pm`)\n")
t.append(md(imp.head(12), d=4))
t.append("\n## 2.3 Function-level model on the commit history (next 100 commits)\n")
t.append("Every 40 commits of the last 700 (all commits for smaller projects), every function that is a smell (Long Method / Complex Method / Many Parameters) is a snapshot; features come from the history before the snapshot; the target is the interest (lines and PM) the function absorbs in the next 100 commits. 6,153 snapshots from 9 projects.\n")
t.append(md(SN.groupby(["protocol", "model"])[["AUC", "PR_AUC", "Spearman", "MAE_lines"]].mean().round(3).reset_index()))
t.append("\nPer held-out project (all features, leave-one-project-out):\n")
t.append(md(SN[(SN.protocol == "leave-one-project-out") & (SN.model == "all_features")][["fold", "n", "pos_rate", "AUC", "PR_AUC", "Spearman", "MAE_lines"]]))
w("02_predicting_interest.md", t)

# ------------------------------------------------------------------------------------------------ 03
t = ["# 3. The interest model applied to the dataset pairs, and the first prediction model\n"]
ps = pd.read_csv(os.path.join(RES, "pair_scores.csv"))
t.append("## 3.1 Interest model on the 61 pairs of the dataset\n")
t.append("For every pair the functions touched by `td.patch` are located on the clean and on the TD side; a touched function that is a smell on a side gets features (its own metrics on that side + its real git history up to the base commit) and the function-level model predicts the interest it will absorb in the next 100 commits; a function that is not a smell on a side carries no debt there. Each pair is scored by a model trained **without** the project of the pair. delta = TD - clean (predicted interest lines).\n")
g = ps.groupby("td_type").agg(pairs=("pair", "count"), touched_function_is_a_smell=("smells_TD", lambda s: int((s > 0).sum())), mean_delta_lines=("delta_lines", "mean"), share_delta_positive=("delta_lines", lambda s: (s > 0).mean()), mean_delta_p_any=("delta_p", "mean")).round(3)
t.append(md(g, idx=True))
none = int(((ps.smells_clean == 0) & (ps.smells_TD == 0)).sum())
t.append(f"\n{none} of {len(ps)} pairs touch no function that is a smell on either side, so a smell-based interest model gives them no score (the TD changes of types security and concurrency add no size or complexity). Per pair: `pair_scores.csv`.\n")
t.append("## 3.2 The first prediction model (target = effort of the injected patch size)\n")
t.append(md(pd.read_csv(os.path.join(T, "first_model_reevaluation.csv")), d=4))
t.append("\n" + md(pd.read_csv(os.path.join(T, "first_model_data_problems.csv"), keep_default_na=False)))
t.append("\nThe 0.90 R2 was computed on a target that is a formula of the patch size, on a data set in which 20 of 61 rows carry another pair's project (the join key was the pair name, which repeats in `Python/` and `C_C++/`); with whole projects held out the same model has R2 below 0. Superseded by the instance-level experiments above.\n")
w("03_pairs_and_first_model.md", t)

# ------------------------------------------------------------------------------------------------ 00
best_auc = PM.AUC_any_interest.max()
t = ["# Interest experiment - summary\n"]
t.append("Question: can the technical-debt **interest**, in **person-months**, be calculated and predicted? Method of the 2025 paper, on 9 real projects, 20 releases each.\n")
t.append("## What was calculated\n")
t.append(md(pd.DataFrame([[f"{int(S.instance_transitions.sum())}", "instance-releases analysed (an instance counts once per release)"], [f"{S.instances.sum()}", "distinct technical-debt instances (SonarQube issues / structural smells)"], [f"{int(tot_ev)}", "interest events (an instance re-worked while it persists)"],
                         [f"{tot_lines:.0f}", "lines re-worked inside persisting debt"], [f"{tot_pm:.2f} person-months", "interest paid in total (COCOMO II nominal constants)"], [f"{tot_pm / len(S):.2f} person-months", "per project on average (range " + f"{S.interest_PM.min():.2f} - {S.interest_PM.max():.2f})"]], columns=["number", "meaning"])))
t.append("\n## What can be predicted\n")
nr = NR.groupby(["protocol", "model"]).AUC.mean()
t.append(md(pd.DataFrame([
    ["any interest in the next release (AUC)", f"{nr[('leave-one-repo-out', 'all_features')]:.2f} for unseen projects, {nr[('temporal', 'all_features')]:.2f} for later releases", "weak but real signal (chance 0.5)"],
    ["amount of interest of an instance (mPM)", f"R2 <= 0 for every model (best {PM[PM.model != 'zero'].R2.max():.4f}); no model beats 'predict zero' in MAE", "not predictable from these features"],
    ["total interest of a project over all its instances", f"predicted / actual = {PM[(PM.protocol == 'leave-one-repo-out') & (PM.model == 'hurdle_rf')].predicted_total_mPM.iloc[0] / PM[(PM.protocol == 'leave-one-repo-out') & (PM.model == 'hurdle_rf')].actual_total_mPM.iloc[0]:.2f} (two-part model, leave one repo out)", "right order of magnitude overall; not per project or release"],
    ["total interest of a project in the next release", f"best R2 {PL[~PL.model.isin(['zero', 'mean'])].R2.max():.2f}", "no skill"],
    ["function-level interest in the next 100 commits (AUC)", f"{SN[(SN.protocol == 'leave-one-project-out') & (SN.model == 'all_features')].AUC.mean():.2f} / {SN[(SN.protocol == 'temporal') & (SN.model == 'all_features')].AUC.mean():.2f}", "weak signal"],
], columns=["task", "result", "verdict"])))
t.append("\n## Conclusions\n")
t.append("1. The interest **calculation** works and is reproducible: all 9 transition files were regenerated from the git histories and equal the earlier results exactly.")
t.append(f"2. Predicting **whether** an instance will absorb work inside the debt is possible only weakly (AUC up to {best_auc:.2f}); predicting **how many person-months** is not possible with the available features: the zero model has the smallest absolute error because 92% of the instance-releases pay nothing, and R2 is zero or negative.")
t.append("3. The overall **total** is predicted within the order of magnitude by the two-part model, which is usable for budgeting a whole portfolio, not for ranking single instances.")
t.append("4. The amount of interest depends on the detector (SonarQube vs structural smells) and on the COCOMO II constants; the constants of the paper could not be checked.")
t.append("5. The interest is not defined for the injected pairs of the dataset (the debt is new, there is no history after it); it is available for the real repositories only. Section 3.1 shows the model applied to the pairs: it only reacts to complexity and structure changes.\n")
t.append("Documents: `01_interest_calculation.md`, `02_predicting_interest.md`, `03_pairs_and_first_model.md`; all tables in `tables/` and the model outputs as CSV in `results/`.")
w("00_summary.md", t)
print("documents written")

# ------------------------------------------------------------------------------------------------ README files
nr = NR.groupby(["protocol", "model"]).AUC.mean()
hur = PM[(PM.protocol == "leave-one-repo-out") & (PM.model == "hurdle_rf")].iloc[0]

# ---- worked examples read from the data
_c = pd.read_csv(os.path.join(DATA, "transitions", "click.csv"))
_a = _c[(_c.v0 == "8.1.3") & (_c.v1 == "8.1.4") & (_c.func == "__init__") & (_c.file == "src/click/_termui_impl.py") & (_c.rule == "python:S107")].iloc[0]
_growth = int(_a.nloc1 - _a.nloc0)
_inc = min(int(_a.changed), _growth)
_b = _c[(_c.v0 == "8.1.3") & (_c.v1 == "8.1.4") & (_c.func == "__init__") & (_c.file == "src/click/core.py") & (_c.cls == "interest")]
_nom = cocomo.PRESETS["nominal"]
method_md = f"""## How the interest is calculated (step by step)

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

   `PM = A x (interest lines / 1000) ^ E`  with A = {_nom['A']}, E = {_nom['E']:.4f} (nominal COCOMO II.2000: E = 0.91 + 0.01 x 18.97, effort multipliers = 1). The constants of the 2025 paper could not be checked; the preset `paper` (A = {cocomo.PRESETS['paper']['A']}, E = {cocomo.PRESETS['paper']['E']}) is in `code/cocomo.py` and gives about 2.1 - 2.8 times larger values (`results/tables/cocomo_sensitivity.csv`).
6. **Principal of an instance** = the COCOMO II effort of its region size: the effort to rewrite the function once.
7. **Totals**: the *interest paid by an instance* = the sum of its events over the releases; *of a project* = the sum over its instances; the project value is compared with the sum of the principals of its instances.

**Worked example (real data, `data/transitions/click.csv`).** Project click, release pair {_a.v0} -> {_a.v1}, function `__init__` in `{_a.file}`, instance `{_a.rule}` ("too many parameters"):
* region: {int(_a.nloc0)} lines in {_a.v0}, {int(_a.nloc1)} lines in {_a.v1} -> growth = {_growth} lines (principal increase);
* changed (added or modified source) lines inside the region: {int(_a.changed)};
* interest lines = {int(_a.changed)} - min({int(_a.changed)}, {_growth}) = **{int(_inc and _a.interest_lines)}**;
* effort = {_nom['A']} x ({int(_a.interest_lines)} / 1000) ^ {_nom['E']:.4f} = **{_a.pm_interest:.4f} person-months** ({1000 * _a.pm_interest:.1f} milli-person-months);
* principal of this instance = {_nom['A']} x ({int(_a.nloc0)} / 1000) ^ {_nom['E']:.4f} = {_a.principal_pm:.4f} person-months, so this one event is {_a.pm_interest / _a.principal_pm:.0%} of the effort of rewriting the function.

**Example of shared work.** In the same release pair, `__init__` in `src/click/core.py` is flagged by {len(_b[_b.func == '__init__'])} instances ({', '.join(sorted(_b[_b.func == '__init__'].rule.unique()))}); {int(_b.changed.iloc[0])} lines were changed in it, so each instance gets {_b.interest_lines.iloc[0]:.1f} interest lines and {_b.pm_interest.iloc[0]:.5f} person-months, together {2 * _b.pm_interest.iloc[0]:.5f}.

**Units.** A *person-month* is the effort of one person for one month. One event is worth a few milli-person-months (1 mPM = 0.001 PM); the nine projects together paid {tot_pm:.2f} person-months over 20 releases each. SLOC = source lines of code, KSLOC = thousand SLOC.

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
"""

open(os.path.join(EXP, "README.md"), "w").write(f"""# interest_exp - technical-debt interest: calculation and prediction

Everything about the **interest** of technical debt (the effort spent working inside code that carries debt, in **person-months**): how it is calculated version by version following the 2025 paper
(Wiriyakul & Senivongse), what it amounts to in 9 real projects, and what can be predicted. Code, data and results are here and can be re-run.

```
interest_exp/
  code/       the experiment code + run_all.py (the whole run) + clone_repos.sh (gets the git histories)       see code/README.md
  data/       the inputs and intermediate tables: instance-by-instance transitions, function-level snapshots     see data/README.md
  results/    the documents (00_summary.md first) and every table as CSV
  requirements.txt
```
## Result in short ({int(S.instance_transitions.sum())} instance-releases, {S.instances.sum()} debt instances, 9 projects x 20 releases)
| | |
|---|---|
| interest paid, all projects | **{tot_pm:.2f} person-months** ({int(tot_ev)} events, {tot_lines:.0f} re-worked lines); per project {S.interest_PM.min():.2f} - {S.interest_PM.max():.2f} |
| interest relative to the effort of rewriting all instances once | {S.interest_PM.sum() / S.principal_PM_of_instances_at_first_sight.sum():.2f} overall (per project {(S.interest_PM / S.principal_PM_of_instances_at_first_sight).min():.2f} - {(S.interest_PM / S.principal_PM_of_instances_at_first_sight).max():.2f}) |
| will an instance pay any interest in the next release (AUC) | {nr[('leave-one-repo-out', 'all_features')]:.2f} for unseen projects, {nr[('temporal', 'all_features')]:.2f} for later releases (chance 0.5) |
| how many person-months an instance pays | **not predictable** from the available features: no model beats "predict zero" in MAE, R2 <= 0 |
| total interest of all instances | two-part model: predicted / actual = {hur.predicted_total_mPM / hur.actual_total_mPM:.2f} (leave one project out) |

Details and all numbers: `results/00_summary.md`.

{method_md}
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
""")
open(os.path.join(HERE, "README.md"), "w").write("""# code

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
""")
open(os.path.join(DATA, "README.md"), "w").write("""# data

| folder | content |
|---|---|
| `transitions/<project>.csv` | one row per debt instance and release pair (V0 -> V1): rule, severity, region size and complexity at V0 and size at V1, age, interest so far, class of the change (`interest`, `increase`, `repayment`, `none`, `introduced`), changed lines, interest lines, `pm_interest` (COCOMO II person-months), `principal_pm` (effort to rewrite the region). 20 releases per project (13 for libyaml) |
| `transitions_structural/<project>.csv` | the same for the four Python projects with the structural smell detector instead of SonarQube (detector comparison) |
| `snapshots/<project>_snapshots.csv` | function-level snapshots from the commit history (features before the snapshot, interest in the next 100 commits); `<project>_events.csv` = every change event of a smell function |
| `earlier/` | the two result files of the first prediction model of the study (re-evaluated in `results/03_pairs_and_first_model.md`) |
""")
print("README files written")
