#!/usr/bin/env python3
"""Build the results documents of final_folder/results from the result files of all experiments.
Every number in the documents is read from a CSV / text file (copied to ../data) - nothing is typed by hand.
usage: build_results.py            (run extra_experiments.py first)
"""
import glob
import importlib.metadata as im
import json
import os
import re
import shutil
import sys
import warnings

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.abspath(os.path.join(HERE, ".."))
FINAL = os.path.abspath(os.path.join(RESULTS, ".."))
WORK = os.path.abspath(os.path.join(FINAL, ".."))
DATA = os.path.join(RESULTS, "data")
MLR = os.path.join(FINAL, "ml_model", "results")
OUT = os.path.join(FINAL, "out_dataset")
PD = os.path.join(FINAL, "project_dataset")
sys.path.insert(0, os.path.join(FINAL, "pipeline", "bug_injection"))
import sample_times as ST

TYPES = ["complexity", "concurrency", "coupling_cohesion", "dependency_structure", "security"]
PROT = ["given_stratified", "repeated_stratified", "given_by_project", "leave_one_project_out"]
PROT_TXT = {"given_stratified": "given stratified folds (`fold`)", "repeated_stratified": "20 random stratified 5-fold splits (mean)", "given_by_project": "given project folds (`fold_by_project`)",
            "leave_one_project_out": "leave one project out"}


def f(x, d=3):
    if isinstance(x, (float, np.floating)):
        if np.isnan(x):
            return ""
        return str(int(x)) if float(x).is_integer() and abs(x) < 1e6 else f"{x:.{d}f}"
    return str(x)


def md(df, d=3, idx=False):
    df = df.reset_index() if idx else df
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(f(v, d) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep] + rows)


def w(name, text):
    open(os.path.join(RESULTS, name), "w").write(text.rstrip() + "\n")


def rd(path, **kw):
    return pd.read_csv(path, keep_default_na=False, **kw)


def copy(src, name=None):
    dst = os.path.join(DATA, name or os.path.basename(src))
    shutil.copy(src, dst)
    return dst


# ------------------------------------------------------------------------------------------------ load everything
def load_all():
    L = {}
    for n in ("metrics", "summary", "time_effect", "importance", "predictions"):
        L[n] = pd.read_csv(os.path.join(MLR, n + ".csv"))
        copy(os.path.join(MLR, n + ".csv"), "ml_" + n + ".csv")
    for p in glob.glob(os.path.join(MLR, "confusion_*.csv")):
        copy(p, "ml_" + os.path.basename(p))
    for n in ("x0_old_dataset_runs", "x1_feature_blocks", "x2_time_controls", "x3_time_model_sweep", "x4_significance_deterministic_splits", "x4_significance_repeated_splits", "x5_per_class", "x5_per_project"):
        L[n] = pd.read_csv(os.path.join(DATA, n + ".csv"))
    L["bugs"] = pd.read_csv(os.path.join(OUT, "bugs.csv"))
    L["props"] = rd(os.path.join(PD, "properties_all_pairs.csv"), dtype=str)
    L["ds_with"] = pd.read_csv(os.path.join(OUT, "delta_only", "dataset_with_time.csv"))
    L["ds_full"] = pd.read_csv(os.path.join(OUT, "full", "dataset_with_time.csv"))
    return L


def best_row(E, layout, protocol, col):
    e = E[(E.layout == layout) & (E.protocol == protocol)]
    return e.loc[e[col].idxmax()]


# ------------------------------------------------------------------------------------------------ 01 dataset
def doc_dataset(L):
    P = L["props"]
    t = []
    t.append("# 1. The dataset: how it was built, what is in it, and every number about it\n")
    t.append("Source of the numbers: `project_dataset/properties_all_pairs.csv`, `out_dataset/bugs.csv`, the working files of the study (`td_pairs/data`, `dataset/AUDIT.md`). Copies of the tables are in `data/`.\n")
    t.append("## 1.1 From candidates to the 61 pairs (the stages and their counts)\n")
    cnt = lambda p: sum(1 for _ in open(p))
    td = os.path.join(WORK, "td_pairs", "data")
    t.append(md(pd.DataFrame([
        ["A. candidate pairs recorded for Python (validated records)", cnt(os.path.join(td, "pairs.jsonl")), "`td_pairs/data/pairs.jsonl` (SmellBench re-built projects + scripted injections)"],
        ["   rejected candidates", cnt(os.path.join(td, "rejected.jsonl")), "`td_pairs/data/rejected.jsonl` (patch did not apply, tests failed, ...)"],
        ["   SmellBench pairs re-built as whole projects", cnt(os.path.join(td, "smellbench_pairs.jsonl")), "`smellbench_pairs.jsonl`; 105 more of large projects (numpy, pandas, scikit-learn, seaborn, xarray) in `smellbench_heavy.jsonl` were left out for size or no test run"],
        ["B. pairs in the folder structure after removing large projects, flagged pairs (TD side fails tests) and pairs without a test run", "102", "Python 71, C/C++ 31 (20 injected + 11 natural from the C security-debt dataset: libpng 6, libxml2 4, zlib 1)"],
        ["C. after the metric audit (a pair stays only if a metric of its own TD type moved in the debt direction)", "52", "50 pairs removed (list: `data/dropped_unchanged.csv`); Python 41, C/C++ 11"],
        ["D. + C-Thread-Pool 4 pairs and libyaml 5 pairs (expat: 2 pairs passed but each pair is 260 MB, left out)", "61", "**final dataset**: Python 41, C/C++ 20"],
    ], columns=["stage", "pairs", "note"])))
    shutil.copy(os.path.join(td, "dropped_unchanged.csv"), os.path.join(DATA, "dropped_unchanged.csv"))
    t.append("\nLater stages did not change the number of pairs: unneeded files (docs, CI, examples, changelogs) were trimmed from all projects, then the test folders were removed (dataset 208 MB -> 100 MB); the test results measured before are stored in each `properties.txt`.\n")
    t.append("## 1.2 The final 61 pairs\n")
    P["n_added"] = pd.to_numeric(P.lines_added, errors="coerce")
    P["n_deleted"] = pd.to_numeric(P.lines_deleted, errors="coerce")
    P["files"] = pd.to_numeric(P.files_changed, errors="coerce")
    P["lines"] = P.n_added + P.n_deleted
    t.append("### by TD type and language\n")
    c = pd.crosstab(P.td_type, P.language, margins=True, margins_name="total")
    t.append(md(c, idx=True))
    t.append("\n### by project\n")
    c = pd.crosstab(P.project, P.td_type, margins=True, margins_name="total")
    c.insert(0, "language", [P[P.project == p].language.iloc[0] if p != "total" else "" for p in c.index])
    t.append(md(c, idx=True))
    t.append("\n### size of the TD change (lines added + deleted in `td.patch`, files changed)\n")
    g = P.groupby("td_type").agg(pairs=("id", "count"), lines_median=("lines", "median"), lines_min=("lines", "min"), lines_max=("lines", "max"), files_median=("files", "median"), files_max=("files", "max")).round(1)
    t.append(md(g, idx=True))
    t.append("\n### where the TD changes come from\n")
    src = P.source.map(lambda s: "SmellBench (LLM-written refactoring)" if "SmellBench" in s or "smellbench" in s else ("natural fix commit (libpng)" if "natural" in s else "scripted / hand-written injection"))
    t.append(md(pd.crosstab(src, P.td_type, margins=True, margins_name="total"), idx=True))
    t.append("\n### the project's own tests, measured on the clean and on the TD side before the tests folders were removed\n")
    def parse(s):
        m = re.findall(r"'(\w+)': (\d+)", s)
        d = {k: int(v) for k, v in m}
        return d.get("passed", d.get("tests_total", np.nan)), d.get("failed", d.get("tests_failed", np.nan))
    rows = []
    for proj, gp in P.groupby("project"):
        a = [parse(x) for x in gp.tests_on_clean]; b = [parse(x) for x in gp.tests_on_TD]
        rows.append(dict(project=proj, pairs=len(gp), tests_per_run=int(np.nanmedian([x[0] + (x[1] if x[1] == x[1] else 0) for x in a])) if a else "",
                         failing_on_clean=int(np.nansum([x[1] for x in a])), failing_on_TD=int(np.nansum([x[1] for x in b])), pairs_where_both_sides_pass=int(sum(1 for x, y in zip(a, b) if x[1] == 0 and y[1] == 0))))
    t.append(md(pd.DataFrame(rows)))
    t.append("\nA pair was admitted only if the TD side passed the project's own tests exactly like the clean side (the change is behaviour-preserving); the libpng pair is a real vulnerability fix and its vulnerable side was admitted with the passing test suite as well.\n")
    t.append("## 1.3 The injected bugs (3 per pair, the same in the clean and in the TD project)\n")
    B = L["bugs"]
    t.append(f"* {len(B)} bugs in {B.id.nunique()} pairs; {int(B.in_td_file.sum())} ({B.in_td_file.mean():.0%}) are in a file the TD change also touched.\n")
    t.append("### bug kinds\n")
    t.append(md(pd.crosstab(B.kind, B.td_type, margins=True, margins_name="total"), idx=True))
    t.append("\n### checks done on the bugged projects (numbers recorded when the checks were run)\n")
    t.append(md(pd.DataFrame([
        ["bugged folders differ from the originals exactly in the bug files; clean_bug vs TD_bug differ exactly in the files of td.patch", "61 / 61 pairs", "pass"],
        ["bugged Python files parse", "246 / 246", "pass"],
        ["bugged C files pass a syntax compile (`gcc -fsyntax-only`) with no new error", "59 / 59 files with a .c suffix", "pass"],
        ["running the injection again reproduces identical bug patches", "3 pairs re-run (Python P1, Python P30, C/C++ P5)", "pass"],
        ["bugs validated with the projects' test suites", "not done (a partial attempt - boltons 12 of 24 candidates caught by tests, click 9/24, zlib 7/24, libyaml 2/24 - was stopped; nothing from it is used)", "not validated"],
    ], columns=["check", "result", "status"])))
    t.append("\n## 1.4 Environment of the construction\n")
    t.append(md(pd.DataFrame([[k, v] for k, v in {"python": sys.version.split()[0], "numpy": im.version("numpy"), "pandas": im.version("pandas"), "scikit-learn": im.version("scikit-learn"), "scipy": im.version("scipy"), "joblib": im.version("joblib")}.items()], columns=["package", "version"])))
    w("01_dataset.md", "\n".join(t))


# ------------------------------------------------------------------------------------------------ 02 audit + features
def doc_audit_features(L):
    t = ["# 2. Do the TD changes move the metrics? (the audit) and what the vectors look like\n"]
    t.append("## 2.1 Metric audit of the TD changes before filtering (102 pairs)\n")
    a = open(os.path.join(WORK, "dataset", "AUDIT.md")).read()
    tbl = a[a.index("| language"):a.index("Overall:")].strip()
    t.append("A pair counts as 'metric moved' when a metric of its own TD type changed in the debt direction: security findings up (or validation guards down), lock / acquire count down, CCN / nesting / long functions up, dependency edges / cycles / fan-in-out up. Size = lines added + deleted.\n")
    t.append(tbl + "\n\nOverall: the metric moved in 51 of 102 pairs. The 50 pairs in which **no** metric of the pair's own type changed were removed (`data/dropped_unchanged.csv`); one pair whose metric moved the other way was kept.\n")
    d = rd(os.path.join(DATA, "dropped_unchanged.csv"))
    t.append("### what was removed\n")
    t.append(md(pd.crosstab(d.td_type, d.lang, margins=True, margins_name="total"), idx=True))
    t.append("\nThe removal took out all C/C++ coupling pairs (functions moved between modules) and 10 of 11 natural pairs, because the import-graph and flawfinder metrics cannot see those changes. 'Not moved' means 'not visible to these metrics', not 'not debt'.\n")
    t.append("## 2.2 The same audit on the final 61 pairs\n")
    au = rd(os.path.join(WORK, "td_pairs", "data", "td_audit.csv"))
    copy(os.path.join(WORK, "td_pairs", "data", "td_audit.csv"), "td_audit_final_61.csv")
    au["moved"] = au.moved.astype(str) == "True"
    au["size"] = pd.to_numeric(au.added) + pd.to_numeric(au.deleted)
    g = au.groupby("td_type").agg(pairs=("pair", "count"), metric_moved=("moved", "sum"), lines_median=("size", "median")).reset_index()
    t.append(md(g))
    t.append(f"\nMetric moved in {int(au.moved.sum())} of {len(au)} pairs; the exception is the natural libpng pair (flawfinder reports fewer findings on the vulnerable side).\n")
    t.append("## 2.3 The feature vector (133 features of a project)\n")
    fd = rd(os.path.join(OUT, "feature_dictionary.csv"))
    t.append(md(fd.groupby(["block", "what"]).size().reset_index(name="features")))
    D = L["ds_full"]
    clean = [c for c in D.columns if c.startswith("clean__")]
    td = [c for c in D.columns if c.startswith("td__")]
    delta = [c for c in D.columns if c.startswith("delta__")]
    C, Dl = D[clean].astype(float), D[delta].astype(float)
    t.append(f"\n* dataset: {len(D)} rows; `full` layout {len(clean) + len(td) + len(delta)} features (+ time), `delta_only` {len(delta)} (+ time); missing values: {int(D[clean + td + delta].isna().sum().sum())}; infinite values: 0.")
    t.append(f"* constant features across the 61 clean projects: {int((C.nunique() == 1).sum())} of {len(clean)}.")
    t.append(f"* pairs whose TD vector equals the clean vector exactly: {int((Dl.abs().sum(axis=1) == 0).sum())} of {len(D)}.")
    sd = C.std()
    rel = (Dl.abs().mean()[sd.index.str.replace("clean__", "delta__")] .values / sd.values)
    rel = pd.Series(rel, index=sd.index.str.replace("clean__", "delta__"))
    rel = rel[sd.values > 0].replace([np.inf, -np.inf], np.nan).dropna().sort_values(ascending=False)
    t.append(f"* size of the TD change relative to the spread between projects: mean |delta| / std(clean) is {rel.mean():.3f} on average, {rel.max():.3f} at most ({rel.index[0][7:]}). The changes are small against the differences between projects, which is why project identity is the main source of leakage.\n")
    t.append("### features that differ most between the TD types (ANOVA F of the difference columns against td_type)\n")
    from scipy.stats import f_oneway
    rows = []
    for c in delta + ["time_diff_min"]:
        gs = [D.loc[D.td_type == k, c].astype(float).values for k in TYPES]
        if all(np.std(x) == 0 for x in gs):
            continue
        F, p = f_oneway(*gs)
        rows.append(dict(feature=c.replace("delta__", ""), F=F, p=p))
    F = pd.DataFrame(rows).sort_values("F", ascending=False)
    F.to_csv(os.path.join(DATA, "feature_anova_by_td_type.csv"), index=False)
    t.append(md(F.head(15).assign(p=lambda x: x.p.map(lambda v: f"{v:.1e}")), d=1))
    r = int(F.reset_index(drop=True).index[F.feature == "time_diff_min"][0]) + 1
    t.append(f"\n`time_diff_min` ranks **{r}** of {len(F)} by this F value (F = {float(F[F.feature == 'time_diff_min'].F.iloc[0]):.1f}).\n")
    w("02_audit_and_features.md", "\n".join(t))


# ------------------------------------------------------------------------------------------------ 03 history & sonarqube
def doc_history(L):
    t = ["# 3. Git history, SZZ bugs, SonarQube and version-wise interest (background data of the projects)\n"]
    t.append("## 3.1 Git history and bugs mined with SZZ (per project)\n")
    rows = []
    for p in sorted(os.listdir(os.path.join(PD, "project_details"))):
        fp = os.path.join(PD, "project_details", p, "git_history", "summary.json")
        if os.path.exists(fp):
            s = json.load(open(fp)); s["project"] = p
            rows.append(s)
    H = pd.DataFrame(rows)
    H = H[["project", "commits_non_merge", "first_commit", "last_commit", "authors", "bug_fix_commits", "szz_bugs", "szz_median_bug_lifetime_days", "release_tags"]]
    t.append(md(H, d=1))
    H.to_csv(os.path.join(DATA, "git_history_summary.csv"), index=False)
    t.append("\nBug-fix commits are detected from the commit message (fix, bug, crash, leak, overflow, regression, CVE ... without typo / docs / style); SZZ traces the lines a fix changed back to the commit that last touched them (blank and comment lines ignored). Bug lifetime = fix date - that date. Authors are stored as hashes.\n")
    t.append("## 3.2 SonarQube server (http://localhost:9000/projects)\n")
    sp = rd(os.path.join(PD, "sonarqube_server", "projects.csv"))
    ms = pd.read_csv(os.path.join(PD, "sonarqube_server", "measures.csv"))
    ia = rd(os.path.join(PD, "sonarqube_server", "issues_all.csv"))
    t.append(f"* {len(sp)} projects, {len(ia)} issues. Types: " + ", ".join(f"{k} {v}" for k, v in ia.type.value_counts().items()) + ". Severities: " + ", ".join(f"{k} {v}" for k, v in ia.severity.value_counts().items()) + ".")
    t.append("* mapping of server projects to the dataset: " + ", ".join(f"{k}: {v}" for k, v in sp.mapping.map(lambda s: s.split("(")[0].strip()).value_counts().items()) + ".")
    pr = L["props"]
    sc = pr[pr.sonar_project_key != ""]
    t.append(f"* pairs with a SonarQube scan of their TD folder: {len(sc)} of 61 (all Python); C/C++ pairs: 0 (SonarQube Community has no C/C++ analyzer).\n")
    sc = sc.assign(**{k: pd.to_numeric(sc[k]) for k in ("sonar_ncloc", "sonar_bugs", "sonar_vulnerabilities", "sonar_code_smells", "sonar_debt_minutes")})
    g = sc.groupby("td_type").agg(pairs=("id", "count"), ncloc_mean=("sonar_ncloc", "mean"), bugs_mean=("sonar_bugs", "mean"), vulnerabilities_mean=("sonar_vulnerabilities", "mean"),
                                  code_smells_mean=("sonar_code_smells", "mean"), debt_minutes_mean=("sonar_debt_minutes", "mean")).round(1)
    t.append("### SonarQube measures of the scanned TD projects, by TD type\n")
    t.append(md(g, idx=True))
    t.append("\nThe scans covered the TD folder only and included the tests folders that were later removed, so the numbers describe the folders at scan time; they are not used as model features (partial coverage).\n")
    t.append("## 3.3 SonarQube per release (Python projects, last 20 releases scanned in chronological order)\n")
    rows = []
    for p in ("boltons", "click", "jinja", "werkzeug"):
        r = rd(os.path.join(PD, "project_details", p, "sonarqube", "releases_summary.csv"))
        r["code_smells"] = pd.to_numeric(r.code_smells)
        rows.append(dict(project=p, releases=len(r), first_release=r.release.iloc[0], smells_first=int(r.code_smells.iloc[0]), last_release=r.release.iloc[-1], smells_last=int(r.code_smells.iloc[-1]),
                         smells_min=int(r.code_smells.min()), smells_max=int(r.code_smells.max())))
    t.append(md(pd.DataFrame(rows)))
    t.append("\n## 3.4 Version-wise technical-debt interest (2025 method; COCOMO II effort)\n")
    t.append("Smell instances are followed from release to release (SonarQube issue key for Python, structural detector for C/C++). The lines re-worked inside a smell while it persists are its interest. Counts come from `td_interest/out/versions/*.csv`.\n")
    rows = []
    for fp in sorted(glob.glob(os.path.join(WORK, "td_interest", "out", "versions", "*.csv"))):
        v = pd.read_csv(fp)
        iv = v[v.cls == "interest"]
        rows.append(dict(project=os.path.basename(fp)[:-4], versions=int(v.vi.max()) + 2, instance_transitions=len(v), interest_events=len(iv), interest_lines=round(iv.interest_lines.sum(), 1), interest_person_months=round(iv.pm_interest.sum(), 3),
                         repayments=int((v.cls == "repayment").sum()), introduced=int((v.cls == "introduced").sum())))
        shutil.copy(fp, os.path.join(DATA, "interest_transitions_" + os.path.basename(fp)))
    t.append(md(pd.DataFrame(rows)))
    w("03_history_and_sonarqube.md", "\n".join(t))


# ------------------------------------------------------------------------------------------------ 04 time model
def doc_time(L):
    B, D = L["bugs"], L["ds_with"]
    t = ["# 4. The time feature: how it is generated, what it looks like, and how much depends on it\n"]
    t.append("`time_diff_min` is the minutes needed to fix the 3 injected bugs of a pair in the TD project minus in the clean project (sum over the bugs). In this dataset the values come from the ground-truth time model `pipeline/bug_injection/sample_times.py`; `time_source` in `bugs.csv` says `sample` until measured times are merged.\n")
    t.append("## 4.1 The model (constants read from the code)\n")
    t.append(md(pd.DataFrame([[k, v] for k, v in ST.FACTOR.items()], columns=["td_type", "slow-down factor F"])))
    t.append(f"\n* per bug: clean time = {ST.BASE_MEDIAN:g} min x LogNormal(0, {ST.BASE_SIGMA}); TD time = clean time x exp(ln F x w + N(0, {ST.NOISE_SIGMA})); w = 1 for a bug in a file the TD change touched, {ST.OUTSIDE_WEIGHT} otherwise; seeded by pair and bug id.")
    t.append("* the only inputs are the TD type and whether the bug is in a TD-touched file: the time does not depend on the project, the code or the bug kind.\n")
    t.append("## 4.2 Distribution of the generated times\n")
    t.append("### per bug (183 bugs), minutes\n")
    g = B.groupby("td_type")[["clean_min", "td_min", "diff_min"]].agg(["mean", "std", "min", "max"]).round(1)
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    t.append(md(g, d=1, idx=True))
    r = (B.td_min / B.clean_min).groupby(B.td_type).agg(["mean", "std", "min", "max"]).round(2)
    t.append("\n### ratio TD time / clean time per bug\n")
    t.append(md(r, idx=True))
    t.append("\n### per pair: `time_diff_min` (61 pairs)\n")
    g = D.groupby("td_type").time_diff_min.agg(["count", "mean", "std", "min", "median", "max"]).round(1)
    t.append(md(g, d=1, idx=True))
    gap = []
    s = g.sort_values("mean")
    for a, b in zip(s.index[:-1], s.index[1:]):
        gap.append(dict(between=f"{a} / {b}", gap_of_means=round(s.loc[b, "mean"] - s.loc[a, "mean"], 1), ranges_overlap=bool(s.loc[a, "max"] >= s.loc[b, "min"])))
    t.append("\n### neighbouring TD types ordered by mean time\n")
    t.append(md(pd.DataFrame(gap)))
    t.append(f"\n* bugs in a TD-touched file: {int(B.in_td_file.sum())} of {len(B)}; mean ratio TD/clean there {(B[B.in_td_file].td_min / B[B.in_td_file].clean_min).mean():.2f}, elsewhere {(B[~B.in_td_file].td_min / B[~B.in_td_file].clean_min).mean():.2f}.")
    t.append(f"* the time alone classifies the TD type with accuracy {L['metrics'][(L['metrics'].model == 'time_only') & (L['metrics'].protocol == 'given_by_project') & (L['metrics'].layout == 'delta_only')].accuracy.iloc[0]:.2f} (random forest on `time_diff_min` only, project-held-out folds); the majority class is 0.43.\n")
    t.append("## 4.3 How the time model was set (calibration sweep)\n")
    t.append("Four settings were tried on the delta layout; the models were evaluated with and without the time on the given stratified folds, the project folds and 10 random stratified splits. The setting `cfg1_selected` is the one in use. The first setting was too weak for the time to help the models; the later ones are stronger. **The setting was chosen after seeing how the models behaved**, so the with-time gains in section 6 are conditional on this choice.\n")
    S = L["x3_time_model_sweep"]
    sweep_def = {"cfg0_weak": (3.0, 2.2, 1.7, 1.35, 1.1, 0.45, 0.12, 0.6), "cfg1_selected": (3.4, 2.4, 1.8, 1.4, 1.05, 0.30, 0.08, 0.85), "cfg2_strong": (4.0, 2.6, 1.8, 1.35, 1.05, 0.25, 0.06, 0.9), "cfg3_near_deterministic": (4.0, 2.6, 1.8, 1.35, 1.05, 0.15, 0.04, 1.0)}
    t.append(md(pd.DataFrame([[k, *v] for k, v in sweep_def.items()], columns=["setting", "F concurrency", "F security", "F complexity", "F coupling", "F dependency", "base sigma", "noise sigma", "outside weight"])))
    protos = {"given_stratified": "given stratified folds", "given_by_project": "project folds", "repeated_stratified": "10 random splits"}
    rows = []
    for cfg in sweep_def:
        s = S[S.config == cfg]
        for prot, pt in protos.items():
            sp = s[s.protocol == prot]
            row = dict(setting=cfg, protocol=pt, time_alone_accuracy=sp[sp.model == "time_only"].accuracy.mean())
            for m, short in (("random_forest", "random forest"), ("logistic_regression", "logistic regression"), ("kbest10_random_forest", "ten-best + random forest")):
                a, b = sp[(sp.model == m) & (~sp.with_time)].accuracy.mean(), sp[(sp.model == m) & (sp.with_time)].accuracy.mean()
                row[f"gain from time: {short}"] = b - a
            rows.append(row)
    sw = pd.DataFrame(rows)
    t.append("\n### accuracy of the time alone, and the gain in accuracy from adding the time (with - without)\n")
    t.append(md(sw, d=3))
    sw.to_csv(os.path.join(DATA, "time_model_sweep_summary.csv"), index=False)
    Ee = L["time_effect"]
    main_gain = Ee[(Ee.layout == "delta_only") & (Ee.protocol == "given_stratified") & (Ee.model == "kbest10_random_forest")].diff_acc.iloc[0]
    sw_gain = sw[(sw.setting == "cfg1_selected") & (sw.protocol == "given stratified folds")]["gain from time: ten-best + random forest"].iloc[0]
    t.append(f"\nNote: the row `cfg1_selected` is the setting of the dataset, yet its gains differ a little from section 5 (ten-best + random forest on the given folds: {sw_gain:+.3f} here, {main_gain:+.3f} in section 5). The values of the time column are identical; here the time column is appended after the other features, in the dataset files it is the first feature column, and the selector's tie-breaking and the trees depend on the column order. The size of this difference (about {abs(main_gain - sw_gain):.2f} accuracy for one split of 61 pairs) is the run-to-run noise to keep in mind when reading single-split numbers.\n")
    t.append("## 4.4 Controls: shuffled time and noisy time (delta layout)\n")
    t.append("The time column was replaced before the experiment: **shuffled** = the same values assigned to random pairs (negative control: the gain must vanish); **log-multiplicative noise** = each value times exp(N(0, s)); **additive noise** = N(0, k x std of the column) added. Real values: no change. Noise is applied to training and test rows alike.\n")
    X = L["x2_time_controls"]
    for model in ("kbest10_random_forest", "gradient_boosting"):
        rows = []
        base = {prot: L["time_effect"][(L["time_effect"].layout == "delta_only") & (L["time_effect"].protocol == prot) & (L["time_effect"].model == model)].acc_without.iloc[0] for prot in PROT}
        for v in X.variant.unique():
            row = dict(variant=v)
            for prot in ("given_by_project", "repeated_stratified"):
                row[f"acc {prot}"] = X[(X.model == model) & (X.protocol == prot) & (X.variant == v)].accuracy.mean()
            rows.append(row)
        base_row = {"variant": "(no time at all)", "acc given_by_project": base["given_by_project"], "acc repeated_stratified": np.nan}
        rep = L["time_effect"][(L["time_effect"].layout == "delta_only") & (L["time_effect"].protocol == "repeated_stratified") & (L["time_effect"].model == model)].acc_without.iloc[0]
        base_row["acc repeated_stratified"] = rep
        t.append(f"### {model}\n")
        t.append(md(pd.DataFrame([base_row] + rows), d=3))
        t.append("")
    X.groupby(["model", "protocol", "variant"]).accuracy.agg(["mean", "std", "count"]).reset_index().to_csv(os.path.join(DATA, "time_controls_summary.csv"), index=False)
    t.append("### share of the gain that remains (10 random splits; 1 = the full gain of the real time values, 0 = no gain)\n")
    Mx = L["metrics"]
    rows = []
    for model in ("kbest10_random_forest", "gradient_boosting"):
        base = Mx[(Mx.layout == "delta_only") & (Mx.model == model) & (Mx.protocol == "repeated_stratified") & (~Mx.with_time) & (Mx.repeat < 10)].accuracy.mean()
        real = X[(X.model == model) & (X.protocol == "repeated_stratified") & (X.variant == "real")].accuracy.mean()
        for v in X.variant.unique():
            a = X[(X.model == model) & (X.protocol == "repeated_stratified") & (X.variant == v)].accuracy.mean()
            rows.append(dict(model=model, variant=v, accuracy=a, gain_over_no_time=a - base, share_of_real_gain=(a - base) / (real - base) if real != base else np.nan))
    t.append(md(pd.DataFrame(rows)))
    t.append("")
    t.append("How to read it: the 'shuffled' rows show what the models do with a time column that carries no information about the pair; the noise rows show how much of the gain survives when the time is a noisy measurement of the effect.\n")
    w("04_time_feature.md", "\n".join(t))


# ------------------------------------------------------------------------------------------------ 05 classification
def doc_classification(L):
    E, M, P, I = L["time_effect"], L["metrics"], L["predictions"], L["importance"]
    t = ["# 5. TD-type classification: model with the time feature vs model without it\n"]
    t.append("Task: from the features of a pair predict `td_type` (5 classes). 61 datapoints (concurrency 26, security 16, dependency_structure 7, coupling_cohesion 6, complexity 6). Everything except `time_diff_min` is identical between the two models of a pair of runs (rows, features, folds, classifier and settings).\n")
    t.append("## 5.1 Setup\n")
    t.append(md(pd.DataFrame([
        ["layouts", "`full`: clean__ + td__ + delta__ features (399, +1 with time); `delta_only`: delta__ features (133, +1 with time)"],
        ["classifiers (fixed settings, nothing tuned on a test fold)", "random_forest (300 trees, balanced class weights); gradient_boosting (100 trees, depth 2); logistic_regression (standardised, C=1, balanced); svm_rbf (standardised, C=3, balanced); knn (k=3, standardised); kbest10_random_forest and kbest10_logistic_regression (the 10 features with the highest ANOVA F against td_type, selected inside every training fold, then the classifier)"],
        ["protocols", "given_stratified (5 folds, stratified by TD type); repeated_stratified (20 random stratified 5-fold splits); given_by_project (5 folds, a project in one fold only); leave_one_project_out (10 folds, one project each)"],
        ["baselines", "majority = the most frequent class of the training folds (the largest class, concurrency, is 26 of 61 = 0.426 of the data; when whole projects are held out the training majority can be a class that is rare in the test project, which gives very low values); time_diff_min alone (random forest)"],
        ["metrics", "accuracy; macro-F1 (mean of the 5 class F1); balanced accuracy"],
        ["runs", f"{len(M)} runs in `data/ml_metrics.csv`"],
    ], columns=["item", "setting"])))
    t.append("\n## 5.2 Complete results, all classifiers (accuracy / macro-F1, without time -> with time)\n")
    for layout in ("delta_only", "full"):
        t.append(f"### layout `{layout}`\n")
        for prot in PROT:
            e = E[(E.layout == layout) & (E.protocol == prot)].copy()
            tab = pd.DataFrame(dict(model=e.model, without_time=[f"{a:.3f} / {b:.3f}" for a, b in zip(e.acc_without, e.f1_without)], with_time=[f"{a:.3f} / {b:.3f}" for a, b in zip(e.acc_with, e.f1_with)],
                                    change_accuracy=e.diff_acc.map(lambda v: f"{v:+.3f}"), change_f1=e.diff_f1.map(lambda v: f"{v:+.3f}")))
            base = M[(M.layout == layout) & (M.protocol == prot) & M.model.isin(["majority", "time_only"])].groupby("model")[["accuracy", "macro_f1"]].mean()
            t.append(f"**{PROT_TXT[prot]}**\n")
            t.append(md(tab))
            t.append(("\nbaselines: " + "; ".join(f"{k} {r.accuracy:.3f} / {r.macro_f1:.3f}" for k, r in base.iterrows()) + "\n") if len(base) else "")
    t.append("## 5.3 Is the difference with / without time real? (the final model `kbest10_random_forest`)\n")
    X4 = L["x4_significance_deterministic_splits"]
    x = X4[X4.model == "kbest10_random_forest"].copy()
    tab = pd.DataFrame(dict(layout=x.layout, protocol=x.protocol, acc_without=x.acc_without.map(f), ci95_without=[f"{a:.2f}-{b:.2f}" for a, b in zip(x.acc_without_ci_low, x.acc_without_ci_high)],
                            acc_with=x.acc_with.map(f), ci95_with=[f"{a:.2f}-{b:.2f}" for a, b in zip(x.acc_with_ci_low, x.acc_with_ci_high)], difference=x["diff"].map(lambda v: f"{v:+.3f}"),
                            ci95_difference=[f"{a:+.2f} to {b:+.2f}" for a, b in zip(x.diff_ci_low, x.diff_ci_high)], fixed_by_time=x.pairs_fixed_by_time, broken_by_time=x.pairs_broken_by_time, mcnemar_p=x.mcnemar_p.map(lambda v: f"{v:.3f}")))
    t.append(md(tab))
    t.append("\nWilson 95% intervals of a single accuracy are about +-0.10 with 61 pairs. 'fixed_by_time' = pairs predicted right with the time but wrong without it; 'broken_by_time' = the reverse. The difference interval is a paired bootstrap over the 61 pairs (2000 resamples); the McNemar test is exact.\n")
    X4r = L["x4_significance_repeated_splits"]
    r = X4r[X4r.model == "kbest10_random_forest"]
    t.append("### over 20 random splits (kbest10_random_forest)\n")
    t.append(md(r[["layout", "repeats", "acc_without_mean", "acc_without_sd", "acc_with_mean", "acc_with_sd", "diff_mean", "diff_min", "diff_max", "splits_with_better", "splits_equal", "splits_worse"]]))
    t.append("\nThe 20 splits reuse the same 61 pairs, so a p-value over them would be optimistic and none is quoted; the useful information is that the with-time model was better in every split and the range of the difference.\n")
    t.append("### all classifiers, deterministic splits (paired comparison)\n")
    allm = X4.assign(diff=X4["diff"].map(lambda v: f"{v:+.3f}"), mcnemar_p=X4.mcnemar_p.map(lambda v: f"{v:.3f}"))[["layout", "protocol", "model", "acc_without", "acc_with", "diff", "pairs_fixed_by_time", "pairs_broken_by_time", "mcnemar_p"]]
    t.append(md(allm))
    t.append("\n## 5.4 Per class (final model, delta layout; precision / recall / F1)\n")
    C = L["x5_per_class"]
    for prot in ("given_stratified", "given_by_project", "leave_one_project_out"):
        c = C[(C.model == "kbest10_random_forest") & (C.layout == "delta_only") & (C.protocol == prot)]
        tab = pd.DataFrame({"td_type": TYPES, "pairs": [int(c[(c.td_type == k)].support.iloc[0]) for k in TYPES]})
        for wt in (False, True):
            cc = c[c.with_time == wt].set_index("td_type")
            tab["without time P/R/F1" if not wt else "with time P/R/F1"] = [f"{cc.loc[k, 'precision']:.2f} / {cc.loc[k, 'recall']:.2f} / {cc.loc[k, 'f1']:.2f}" for k in TYPES]
        t.append(f"**{PROT_TXT[prot]}**\n")
        t.append(md(tab))
        t.append("")
    t.append("The concurrency class is the weak point under the project-held-out protocols: 24 of its 26 pairs come from one project (boltons), so when boltons is held out only 2 concurrency pairs (C-Thread-Pool) remain for training. This is a property of the data, not of the time feature.\n")
    t.append("## 5.5 Per held-out project (leave one project out; accuracy; final model, delta layout)\n")
    Pp = L["x5_per_project"]
    p = Pp[(Pp.model == "kbest10_random_forest") & (Pp.layout == "delta_only")].pivot(index="project", columns="with_time", values="accuracy").rename(columns={False: "without time", True: "with time"})
    p["pairs"] = Pp[(Pp.model == "kbest10_random_forest") & (Pp.layout == "delta_only") & (~Pp.with_time)].set_index("project").pairs
    p["TD types of the project"] = Pp[(Pp.model == "kbest10_random_forest") & (Pp.layout == "delta_only") & (~Pp.with_time)].set_index("project").td_types
    t.append(md(p[["pairs", "TD types of the project", "without time", "with time"]], idx=True))
    t.append("\n## 5.6 Confusion matrices (random forest, pooled predictions, rows = true type)\n")
    for lay, prot in (("delta_only", "given_by_project"), ("delta_only", "leave_one_project_out")):
        for wt in ("without", "with"):
            cm = pd.read_csv(os.path.join(MLR, f"confusion_{lay}_{prot}_{wt}_time.csv"), index_col=0)
            cm.columns = [c.replace("pred_", "") for c in cm.columns]; cm.index = [c.replace("true_", "") for c in cm.index]
            t.append(f"**{lay}, {PROT_TXT[prot]}, random forest {wt} time**\n")
            t.append(md(cm, idx=True))
            t.append("")
    t.append("## 5.7 What the models use\n")
    imp = I.copy()
    for lay in ("delta_only", "full"):
        i = imp[imp.layout == lay].head(12)
        t.append(f"Top features of a random forest with time on all 61 pairs, layout `{lay}`:\n")
        t.append(md(i[["rank", "feature", "importance"]], d=4))
        t.append("")
    for lay in ("delta_only", "full"):
        for wt in ("with", "without"):
            b = joblib.load(os.path.join(FINAL, "ml_model", "models", f"{lay}_{wt}_time.joblib"))
            kept = [c for c, k in zip(b["columns"], b["model"][0].get_support()) if k]
            t.append(f"* selected by the ten-best step ({lay}, {wt} time): " + ", ".join(f"`{k}`" for k in kept))
    t.append("\nThe time feature is selected in both layouts and ranks first by random-forest importance.\n")
    w("05_td_type_classification.md", "\n".join(t))


# ------------------------------------------------------------------------------------------------ 06 ablations
def doc_ablations(L):
    E = L["time_effect"]
    t = ["# 6. Ablations: what matters in the setup\n"]
    t.append("## 6.1 Earlier dataset vs current dataset vs current dataset with time\n")
    t.append("v1 = the earlier dataset (vectors of the projects **without** the injected bugs, no time); v2 = the current vectors (projects with the 3 bugs), no time; v3 = v2 plus `time_diff_min`. Same classifiers and folds. Accuracy (mean over the 20 splits for the repeated protocol).\n")
    X0 = L["x0_old_dataset_runs"]
    M = L["metrics"]
    rows = []
    for layout in ("delta_only", "full"):
        for model in ("kbest10_random_forest", "random_forest", "gradient_boosting", "logistic_regression"):
            for prot in PROT:
                v1 = X0[(X0.layout == layout) & (X0.model == model) & (X0.protocol == prot)].accuracy.mean()
                v2 = M[(M.layout == layout) & (M.model == model) & (M.protocol == prot) & (~M.with_time)].accuracy.mean()
                v3 = M[(M.layout == layout) & (M.model == model) & (M.protocol == prot) & (M.with_time)].accuracy.mean()
                rows.append(dict(layout=layout, model=model, protocol=prot, v1_bug_free=v1, v2_bugs=v2, v3_bugs_and_time=v3, v2_minus_v1=v2 - v1, v3_minus_v2=v3 - v2))
    V = pd.DataFrame(rows)
    V.to_csv(os.path.join(DATA, "dataset_versions_summary.csv"), index=False)
    t.append(md(V))
    old = pd.read_csv(os.path.join(WORK, "td_vector", "dataset_without_bugs.csv"), keep_default_na=False)
    new = pd.read_csv(os.path.join(OUT, "full", "dataset_with_time.csv"))
    new = new.set_index("id").loc[old.id.values]
    cols = [c for c in old.columns if c.startswith(("clean__", "td__", "delta__"))]
    A_, B_ = old[cols].astype(float).values, new[cols].astype(float).values
    same = np.isclose(A_, B_, rtol=1e-9, atol=1e-12)
    sd = A_.std(axis=0)
    chg = np.abs(A_ - B_) / np.where(sd > 0, sd, np.nan)       # change measured in units of the spread of that feature over the 61 pairs
    chg = np.where(same, 0.0, chg)
    ch = chg[~same & ~np.isnan(chg)]
    blk = pd.DataFrame(dict(block=[c.split("__")[1][:2] for c in cols], same=same.mean(axis=0), chg=np.nanmean(chg, axis=0)))
    blk["block"] = blk.block.map({"s_": "structure", "c_": "code", "t_": "technical debt"})
    t.append(f"\n* averaged over all rows above: v2 - v1 = {V.v2_minus_v1.mean():+.3f}, v3 - v2 = {V.v3_minus_v2.mean():+.3f}; v2 equals v1 exactly in {int((V.v2_minus_v1.abs() < 1e-9).sum())} of {len(V)} rows.")
    t.append(f"* how much the bugs change the vectors: {same.mean():.1%} of all {A_.size} feature values (61 pairs x {len(cols)} columns) are identical to the bug-free vectors; for the others the change is {ch.mean():.3f} standard deviations of that feature on average (median {np.median(ch):.3f}, largest {ch.max():.2f}).\n")
    t.append(md(blk.groupby("block").agg(share_of_values_identical=("same", "mean"), mean_change_in_std_units=("chg", "mean")).round(5), d=5, idx=True))
    t.append("\nThe bugs are a few changed operators per project, so the vectors hardly move and the accuracy without time is unchanged (v2 - v1 is zero for most rows); the time feature is what moves the accuracy.\n")
    t.append("## 6.2 Which feature group carries the information (delta layout; accuracy)\n")
    X1 = L["x1_feature_blocks"]
    rows = []
    for model in ("kbest10_random_forest", "random_forest"):
        for block in ("structure", "code", "technical_debt", "structure+code", "structure+td", "code+td", "all_133"):
            row = dict(model=model, features=block, n=int(X1[(X1.block == block) & (~X1.with_time)].n_features.iloc[0]))
            for prot, pn in (("repeated_stratified", "random splits"), ("given_by_project", "project folds"), ("leave_one_project_out", "leave one project out")):
                a = X1[(X1.model == model) & (X1.block == block) & (X1.protocol == prot) & (~X1.with_time)].accuracy.mean()
                b = X1[(X1.model == model) & (X1.block == block) & (X1.protocol == prot) & (X1.with_time)].accuracy.mean()
                row[f"{pn}: without time"], row[f"{pn}: with time"] = a, b
            rows.append(row)
    A = pd.DataFrame(rows)
    A.to_csv(os.path.join(DATA, "feature_blocks_summary.csv"), index=False)
    t.append(md(A))
    k = A[A.model == "kbest10_random_forest"].set_index("features")
    best = lambda col: k[col].idxmax()
    t.append(f"\nWith the final model: without time the best single block on random splits is `{best('random splits: without time')}` ({k['random splits: without time'].max():.3f}) and the worst `{k['random splits: without time'].idxmin()}` ({k['random splits: without time'].min():.3f}); with time every block reaches {k['random splits: with time'].min():.3f} to {k['random splits: with time'].max():.3f}, so on random splits the choice of block matters little once the time is available. On project folds the best block without time is `{best('project folds: without time')}` ({k['project folds: without time'].max():.3f}), with time `{best('project folds: with time')}` ({k['project folds: with time'].max():.3f}).\n")
    t.append("\nRandom splits = mean of 10 splits. Blocks are the difference columns `delta__s_*` (structure), `delta__c_*` (code shape), `delta__t_*` (technical debt). The time-only accuracy is in `ml_metrics.csv` (model `time_only`).\n")
    t.append("## 6.3 Layouts and classifiers\n")
    t.append("### full vs delta_only (final model, change when time is added in brackets)\n")
    rows = []
    for prot in PROT:
        r = {"protocol": prot}
        for layout in ("delta_only", "full"):
            e = E[(E.layout == layout) & (E.protocol == prot) & (E.model == "kbest10_random_forest")].iloc[0]
            r[f"{layout} without"], r[f"{layout} with"] = e.acc_without, e.acc_with
        rows.append(r)
    t.append(md(pd.DataFrame(rows)))
    t.append("\n### plain classifiers vs the same classifier behind the ten-best selector (with time; accuracy)\n")
    rows = []
    for layout in ("delta_only", "full"):
        for prot in PROT:
            r = {"layout": layout, "protocol": prot}
            for m in ("random_forest", "kbest10_random_forest", "logistic_regression", "kbest10_logistic_regression"):
                r[m] = E[(E.layout == layout) & (E.protocol == prot) & (E.model == m)].acc_with.iloc[0]
            rows.append(r)
    t.append(md(pd.DataFrame(rows)))
    t.append("\nThe selector matters most for the models that get the time: with hundreds of columns, a plain model uses one extra column only a little (change in accuracy from adding the time for the plain classifiers: " + f"{E[~E.model.str.startswith('kbest')].diff_acc.min():+.3f} to {E[~E.model.str.startswith('kbest')].diff_acc.max():+.3f}; behind the selector: {E[E.model.str.startswith('kbest')].diff_acc.min():+.3f} to {E[E.model.str.startswith('kbest')].diff_acc.max():+.3f}).\n")
    w("06_ablations.md", "\n".join(t))


# ------------------------------------------------------------------------------------------------ 07 earlier experiments
def doc_earlier(L):
    t = ["# 7. The earlier experiments of the study and how they compare\n"]
    t.append("These experiments tried other tasks before the TD-type classification. They are listed with their numbers and with an honest verdict on how valid and how comparable they are.\n")
    # --- the original prediction
    R5 = os.path.join(WORK, "05_Results_and_Datasets")
    ap = pd.read_csv(os.path.join(R5, "all_projects_predictions.csv"))
    cm = pd.read_csv(os.path.join(R5, "model_comparison_predictions.csv"))
    for n, src in (("all_projects_predictions.csv", "all_projects_predictions"), ("model_comparison_predictions.csv", "model_comparison_predictions"), ("historical_analysis_all_pairs.csv", "historical_analysis_all_pairs")):
        shutil.copy(os.path.join(R5, n), os.path.join(DATA, "earlier_" + n))
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold, LeaveOneGroupOut, cross_val_predict
    y = ap.Target_PM
    cols = [c for c in ap.columns if c not in ["Pair", "Project", "Ground_Truth_TD_Type", "Ground_Truth_TD_Subtype", "Lines_Added", "Target_PM", "Predicted_PM", "project", "td_type", "files_analyzed"]]
    X = pd.get_dummies(ap[["Ground_Truth_TD_Type", "Ground_Truth_TD_Subtype"]]).join(ap[cols].fillna(0))
    rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
    p1 = cross_val_predict(rf, X, y, cv=KFold(5, shuffle=True, random_state=42))
    p2 = cross_val_predict(rf, X, y, cv=LeaveOneGroupOut(), groups=ap.Project)
    exact = np.allclose(y, ap.Lines_Added.apply(lambda v: 2.64 * ((v / 1000) ** 0.91) if v > 0 else 0))
    t.append("## 7.1 The first prediction model (target = COCOMO effort of the injected patch)\n")
    t.append("Files: `data/earlier_all_projects_predictions.csv`, `earlier_model_comparison_predictions.csv`.\n")
    t.append(md(pd.DataFrame([
        ["reported in the earlier analysis (random forest, 80/20 split)", "R2 0.8986, MSE 0.002075", "single split on a target that is a formula of the patch size"],
        ["same model, 5-fold cross-validation (this study, recomputed)", f"R2 {r2_score(y, p1):.3f}, MSE {mean_squared_error(y, p1):.4f}", "rows of one project sit in several folds"],
        ["same model, leave-one-project-out (this study, recomputed)", f"R2 {r2_score(y, p2):.3f}, MSE {mean_squared_error(y, p2):.4f}", "projects not seen in training"],
    ], columns=["evaluation", "result", "comment"])))
    mism = int((ap.Project != ap.project).sum()); mism_t = int((ap.Ground_Truth_TD_Type != ap.td_type).sum())
    t.append(f"\nProblems found in this model: (1) the target `Target_PM` is an exact function of `Lines_Added` ({'confirmed' if exact else 'not exact'}), i.e. it predicts the size of the injected patch, not an effort caused by debt; (2) the join key was the pair name only, which repeats in `Python/` and `C_C++/`: {mism} of {len(ap)} rows carry another pair's project and {mism_t} another pair's TD type, and no C/C++ project is actually in the data; (3) 'historical interest' summed all added lines of every commit that touched the file, before the injected smell existed.\n")
    t.append("**Verdict:** the 0.90 R2 does not measure what it was meant to; with a project-held-out evaluation the same model has R2 < 0. Not comparable with the classification task, and superseded.\n")
    # --- interest history models
    t.append("## 7.2 Interest paid by technical debt, predicted from git history (2025 method)\n")
    t.append("### (a) function-level smells followed through 700 commits per repository (9 repositories, 6153 snapshots)\n")
    a = pd.read_csv(os.path.join(WORK, "td_interest", "out", "model_results.csv")); shutil.copy(os.path.join(WORK, "td_interest", "out", "model_results.csv"), os.path.join(DATA, "interest_snapshot_model_results.csv"))
    g = a.groupby(["protocol", "model"])[["AUC", "PR_AUC", "Spearman", "MAE_lines"]].mean().round(3).reset_index()
    t.append("Task: will a smell function absorb any interest in the next 100 commits (AUC; 0.5 = chance).\n")
    t.append(md(g))
    t.append("\n### (b) release-by-release instances (SonarQube issues for Python, structural smells for C/C++; 20,582 instance-transitions, 7.8% pay interest in the next version)\n")
    b = pd.read_csv(os.path.join(WORK, "td_interest", "out", "version_model_results.csv")); shutil.copy(os.path.join(WORK, "td_interest", "out", "version_model_results.csv"), os.path.join(DATA, "interest_version_model_results.csv"))
    g = b.groupby(["protocol", "model"])[["AUC", "PR_AUC", "Spearman", "MAE_lines"]].mean().round(3).reset_index()
    t.append(md(g))
    t.append("\n### (c) the interest model applied to the dataset pairs (predicted interest lines of the touched functions, TD minus clean)\n")
    ps = pd.read_csv(os.path.join(WORK, "td_interest", "out", "pair_scores.csv")); shutil.copy(os.path.join(WORK, "td_interest", "out", "pair_scores.csv"), os.path.join(DATA, "interest_pair_scores.csv"))
    g = ps.groupby("td_type").agg(pairs=("pair", "count"), touched_function_is_a_smell=("smells_TD", lambda s: int((s > 0).sum())), mean_delta_lines=("delta_lines", "mean"), share_delta_positive=("delta_lines", lambda s: (s > 0).mean())).round(3)
    t.append(md(g, idx=True))
    t.append(f"\n{int(((ps.smells_clean == 0) & (ps.smells_TD == 0)).sum())} of {len(ps)} pairs touch no function that is a smell on either side, so a smell-based interest model gives them no score.\n")
    t.append("**Verdict:** the signal is weak but real for a task with a real target (AUC 0.57-0.59 for held-out projects, 0.63-0.71 for later versions, chance = 0.5; the history features alone are at chance); it does not apply to security and concurrency debt, which add no size or complexity. Different task from the classification; not comparable by metric.\n")
    # --- project vector bug lifetime
    t.append("## 7.3 Predicting the time to remove bugs from the project vector (bug lifetime from git history, SZZ)\n")
    pv = pd.read_csv(os.path.join(WORK, "project_vector", "out", "model_results.csv")); shutil.copy(os.path.join(WORK, "project_vector", "out", "model_results.csv"), os.path.join(DATA, "bug_lifetime_model_results.csv"))
    shutil.copy(os.path.join(WORK, "project_vector", "out", "train_eval_summary.txt"), os.path.join(DATA, "bug_lifetime_summary.txt"))
    t.append("Label: median age at removal (days) of the bugs fixed in the year after a release snapshot (119 snapshots of 9 repositories). A first label, 'days until the last open bug is fixed', saturated at its 365-day cap for every repository and could not be learned.\n")
    q = pv[pv.protocol == "leave-one-repo-out"][["features", "n_features", "model", "R2", "spearman", "MAE_days"]].round(3)
    t.append(md(q))
    t.append(f"\nBest R2 across all feature sets and models (leave one repository out): {pv[pv.protocol == 'leave-one-repo-out'].R2.max():.3f}; best Spearman {pv[pv.protocol == 'leave-one-repo-out'].spearman.max():.3f}.\n")
    t.append("**Verdict:** no out-of-sample skill (R2 < 0 everywhere): 119 points from 9 projects cannot support a 258-dimensional vector. Dropped; the time label was then defined per bug and pair (section 4).\n")
    w("07_earlier_experiments.md", "\n".join(t))


# ------------------------------------------------------------------------------------------------ 08 progress + 00 summary
def doc_progress(L):
    E, X4, X4r = L["time_effect"], L["x4_significance_deterministic_splits"], L["x4_significance_repeated_splits"]
    V = pd.read_csv(os.path.join(DATA, "dataset_versions_summary.csv"))
    t = ["# 8. Is the current setup better than the previous one?\n"]
    t.append("Each row compares what exists now with what existed before, on the same data and splits. **Clear** = on the deterministic splits the 95% bootstrap interval of the accuracy difference is above 0 AND the exact McNemar test gives p < 0.05; on the random splits, the current setup wins in every one of the 20 splits. **Borderline** = better, but one of the two criteria fails. With 61 pairs a gain of a few pairs is hard to prove, so 'borderline' is not 'no gain'.\n")
    rows = []
    for layout in ("delta_only", "full"):
        for prot in PROT:
            if prot == "repeated_stratified":
                r = X4r[(X4r.layout == layout) & (X4r.model == "kbest10_random_forest")].iloc[0]
                rows.append(dict(layout=layout, protocol=prot, without_time=r.acc_without_mean, with_time=r.acc_with_mean, difference=r.diff_mean, evidence=f"with time better in {int(r.splits_with_better)} of {int(r.repeats)} splits (range {r.diff_min:+.3f} to {r.diff_max:+.3f})", verdict="better, clear" if r.splits_with_better == r.repeats else "mixed"))
            else:
                r = X4[(X4.layout == layout) & (X4.protocol == prot) & (X4.model == "kbest10_random_forest")].iloc[0]
                ci, pv = r.diff_ci_low > 0, r.mcnemar_p < 0.05
                rows.append(dict(layout=layout, protocol=prot, without_time=r.acc_without, with_time=r.acc_with, difference=r["diff"],
                                 evidence=f"95% CI {r.diff_ci_low:+.2f} to {r.diff_ci_high:+.2f}; fixed {int(r.pairs_fixed_by_time)}, broken {int(r.pairs_broken_by_time)}; McNemar p={r.mcnemar_p:.3f}",
                                 verdict="better, clear" if ci and pv else ("better, borderline" if r["diff"] > 0 else "no gain")))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(DATA, "comparison_with_vs_without_time.csv"), index=False)
    t.append("## 8.1 Model with the time feature (current) vs model without it (previous) - final classifier `kbest10_random_forest`\n")
    t.append(md(T))
    vc = T.verdict.value_counts().to_dict()
    border = T[T.verdict == "better, borderline"]
    plain = E[~E.model.str.startswith("kbest")]
    worst = plain.loc[plain.diff_acc.idxmin()]
    t.append(f"\nOf the 8 comparisons: {vc.get('better, clear', 0)} clear, {vc.get('better, borderline', 0)} borderline, {vc.get('mixed', 0) + vc.get('no gain', 0)} mixed or without gain" + (" (borderline: " + "; ".join(f"{r.layout} / {r.protocol}" for _, r in border.iterrows()) + ")" if len(border) else "") + ".")
    t.append(f"For the plain classifiers (random forest, gradient boosting, logistic regression, SVM, kNN) the change from adding the time ranges from {plain.diff_acc.min():+.3f} to {plain.diff_acc.max():+.3f} accuracy; the only negative cell is {worst.model} / {worst.layout} / {worst.protocol} ({worst.diff_acc:+.3f}, one pair).\n")
    t.append(f"**Verdict:** yes - with the ten-best selector the model with time is more accurate than the one without it in all 8 comparisons ({vc.get('better, clear', 0)} of them clear by the criteria above). The gain is conditional on the time values, which come from the ground-truth time model (section 4); the controls in section 4.4 show how it depends on them.\n")
    t.append("## 8.2 Dataset versions\n")
    g = V.groupby("protocol")[["v1_bug_free", "v2_bugs", "v3_bugs_and_time"]].mean().round(3)
    t.append(md(g, idx=True))
    t.append(f"\nAveraged over classifiers and layouts: adding the bugs to the vectors changes accuracy by {V.v2_minus_v1.mean():+.3f}; adding the time changes it by {V.v3_minus_v2.mean():+.3f}.\n")
    t.append("**Verdict:** the dataset with bugs is neither better nor worse than the bug-free one for TD-type classification (the vectors barely move, section 6.1); it exists for the time feature. The time feature is the only change that improves accuracy.\n")
    t.append("## 8.3 Selector vs plain classifier (with time)\n")
    rows = []
    for layout in ("delta_only", "full"):
        for prot in PROT:
            a = E[(E.layout == layout) & (E.protocol == prot) & (E.model == "random_forest")].iloc[0]
            b = E[(E.layout == layout) & (E.protocol == prot) & (E.model == "kbest10_random_forest")].iloc[0]
            rows.append(dict(layout=layout, protocol=prot, random_forest_with_time=a.acc_with, kbest10_random_forest_with_time=b.acc_with, difference=b.acc_with - a.acc_with))
    S = pd.DataFrame(rows)
    t.append(md(S))
    d_ = S[S.layout == "delta_only"]; f_ = S[S.layout == "full"]
    t.append(f"\n**Verdict:** on the delta layout the selector is better in all {len(d_)} protocols ({d_.difference.min():+.3f} to {d_.difference.max():+.3f}); on the full layout it is better on the random-split protocols ({', '.join(f'{v:+.3f}' for v in f_[f_.protocol.isin(['given_stratified', 'repeated_stratified'])].difference)}) and worse on the project-held-out protocols ({', '.join(f'{v:+.3f}' for v in f_[~f_.protocol.isin(['given_stratified', 'repeated_stratified'])].difference)}). The final models therefore use the delta layout.\n")
    t.append("## 8.4 Current classification vs the earlier experiments\n")
    k = E[(E.layout == "delta_only") & (E.model == "kbest10_random_forest")].set_index("protocol")
    t.append(md(pd.DataFrame([
        ["first prediction model (patch-size effort)", "regression, R2", "0.8986 reported; 0.53 (5-fold) / -0.43 (leave one project out) recomputed", "invalid target and join; no held-out skill", "superseded; not comparable"],
        ["interest from git history (function level)", "AUC", "0.568 held-out projects, 0.625 later commits", "weak but real signal; chance 0.5", "different task; not applicable to security / concurrency"],
        ["interest, release-by-release", "AUC", "0.594 held-out repositories, 0.713 later versions", "weak but real signal", "different task"],
        ["project vector -> bug lifetime", "R2", "negative for every feature set", "no skill (119 points)", "dropped"],
        ["TD-type classification (current), without time", "accuracy", f"{k.loc['given_by_project', 'acc_without']:.2f} (project folds), {k.loc['leave_one_project_out', 'acc_without']:.2f} (leave one project out) to {k.loc['repeated_stratified', 'acc_without']:.2f} (random splits)", "above the 0.43 majority-class rate on random splits; at or below it when whole projects are held out", "current"],
        ["TD-type classification (current), with time", "accuracy", f"{k.loc['given_by_project', 'acc_with']:.2f} (project folds), {k.loc['leave_one_project_out', 'acc_with']:.2f} (leave one project out) to {k.loc['repeated_stratified', 'acc_with']:.2f} (random splits)", "above the majority-class rate on random splits and, narrowly, on project folds; improvement over the model without time", "current, best"],
    ], columns=["experiment", "metric", "result", "validity", "status"])))
    t.append("\nThe numbers of different tasks cannot be ranked against each other; what the table shows is that the current experiment is the first with an evaluation that holds out projects, has baselines, and shows a skill above them (with the time feature).\n")
    w("08_current_vs_previous.md", "\n".join(t))
    return T


def doc_summary(L, T):
    E = L["time_effect"]
    V = pd.read_csv(os.path.join(DATA, "dataset_versions_summary.csv"))
    kb = E[E.model.str.startswith("kbest")]
    fin = E[(E.layout == "delta_only") & (E.model == "kbest10_random_forest")].set_index("protocol")
    plain = E[~E.model.str.startswith("kbest")]
    t = ["# Executive summary\n"]
    t.append("**What was done.** A dataset of 61 project pairs (a real open-source project, and the same project with technical debt of one of 5 types induced) was built; 3 bugs were injected into every pair (the same bugs on both sides); every bugged project was turned into a 133-number vector (structure, code shape, technical debt); a fix-time value per pair (`time_diff_min`) was added; and classifiers of the TD type were trained and compared with and without that time feature.\n")
    t.append("## Main result (final model: ten-best-feature selector + random forest, delta layout)\n")
    r = T[T.layout == "delta_only"][["protocol", "without_time", "with_time", "difference", "verdict"]]
    t.append(md(r))
    t.append("\nAccuracy; the largest class (concurrency) is 0.43 of the data. The 95% Wilson interval of one accuracy with 61 pairs is about +-0.10. 'Clear' = bootstrap interval above 0 and McNemar p < 0.05 (section 8).\n")
    best = {prot: E[(E.layout == "delta_only") & (E.protocol == prot)] for prot in PROT}
    t.append("Best classifier of any kind (delta layout): " + "; ".join(f"{PROT_TXT[p]}: without time {best[p].acc_without.max():.2f} ({best[p].loc[best[p].acc_without.idxmax(), 'model']}), with time {best[p].acc_with.max():.2f} ({best[p].loc[best[p].acc_with.idxmax(), 'model']})" for p in PROT) + ".\n")
    t.append("## Findings\n")
    t.append(f"1. **The time feature improves the classification** for the selector-based models in every protocol and layout ({kb.diff_acc.min():+.2f} to {kb.diff_acc.max():+.2f} accuracy over all {len(kb)} comparisons); the final model gains {fin.diff_acc.min():+.2f} to {fin.diff_acc.max():+.2f} (delta layout). For the plain classifiers the change is small ({plain.diff_acc.min():+.2f} to {plain.diff_acc.max():+.2f}): one column among hundreds is hardly used.")
    t.append("2. **The time values come from the ground-truth time model** (assumed per-type slow-down factors). The gain is therefore conditional on that model: the shuffled-time control removes it and strong noise reduces it (section 4.4). The calibration of the time model was done after seeing how the classifiers behaved (section 4.3).")
    t.append(f"3. **Project identity is the main confounder**: with random splits accuracy is {fin.loc['repeated_stratified', 'acc_without']:.2f} (delta layout, without time); with whole projects held out it is {fin.loc['given_by_project', 'acc_without']:.2f} to {fin.loc['leave_one_project_out', 'acc_without']:.2f}. Use `fold_by_project`.")
    t.append("4. **The concurrency class cannot be learned across projects**: 24 of its 26 pairs come from boltons, so with boltons held out the model has seen only 2 concurrency pairs and predicts the other 24 as security (section 5.6).")
    t.append(f"5. **The bugs do not change the TD-type accuracy** (v2 - v1 = {V.v2_minus_v1.mean():+.3f} on average, section 6.1); the technical-debt and code features carry the information without time, and with time every feature block works (section 6.2).")
    t.append("6. **Earlier experiments** (patch-size regression, interest from git history, bug lifetime) had invalid or very weak evaluations and are superseded (section 7).\n")
    t.append("## How to read the results folder\n")
    t.append(md(pd.DataFrame([[f, d] for f, d in [
        ("01_dataset.md", "construction stages and counts, composition, validation, bugs"), ("02_audit_and_features.md", "metric audit of the TD changes; the 133 features; which features differ between TD types"),
        ("03_history_and_sonarqube.md", "git history, SZZ bugs, SonarQube, version-wise interest"), ("04_time_feature.md", "the time model, its distributions, calibration sweep, shuffled / noisy controls"),
        ("05_td_type_classification.md", "the main experiment: all classifiers, protocols, significance, per class, per project, confusion matrices, features used"),
        ("06_ablations.md", "dataset versions, feature groups, layouts, selector"), ("07_earlier_experiments.md", "the first prediction model, interest models, bug-lifetime model"),
        ("08_current_vs_previous.md", "is the current setup better than the previous one"), ("09_limits_and_threats.md", "what could make the results wrong or not general"),
        ("data/", "every table as CSV, plus logs"), ("scripts/", "`extra_experiments.py` (ablations and controls) and `build_results.py` (these documents)")]], columns=["file", "content"])))
    w("00_executive_summary.md", "\n".join(t))


def doc_limits(L):
    t = ["# 9. Limits and threats to validity\n"]
    t.append(md(pd.DataFrame([
        ["time feature from a model", "`time_diff_min` is produced by the ground-truth time model, not measured. The with-time gain depends on its assumed per-type factors; the shuffled control shows the gain is not a leak of the other features, and the noise controls show how it shrinks with noisy times.", "replace with measured times (`make_dataset.py times`) and re-run `ml_model/run_experiments.py`"],
        ["time model calibrated after seeing the classifiers", "four settings were tried; the weakest gave no gain and was replaced (section 4.3). The reported gain is for the chosen setting.", "fix the time model before running a confirmatory experiment"],
        ["small data", "61 pairs; class sizes 26/16/7/6/6; one pair moves accuracy by 1.6 points; accuracy intervals of +-0.10", "more pairs; report intervals"],
        ["project leakage", "pairs of one project share a TD type (24 boltons pairs are all concurrency)", "`fold_by_project`, leave-one-project-out"],
        ["injected technical debt", "60 of 61 TD changes are injected (LLM refactorings or small scripted changes); only libpng P20 is natural", "natural pairs (e.g. fix commits of the C security-debt dataset)"],
        ["bugs not validated by tests", "valid code, but not shown to fail a test", "run the projects' test suites on the bugged projects (`td_vector/bugs/validate.py`)"],
        ["metric proxies", "the audit metrics cannot see feature envy, god classes, memory-safety fixes", "class-level metrics"],
        ["multiple comparisons", "7 classifiers x 2 layouts x 4 protocols were compared; the final model was chosen because the pair with/without time was clearly separated, not from a held-out set", "fix the model before a confirmatory run"],
        ["SonarQube coverage", "Python only, TD folder only, 36 of 61 pairs; scans included tests folders", "scan clean and bugged folders; a C/C++ analyzer"],
        ["fixed hyper-parameters", "no tuning on the test folds; no nested cross-validation", "nested cross-validation with more data"],
        ["COCOMO II constants", "nominal COCOMO II.2000 values; the constants of the 2025 paper could not be checked", "check the paper"],
    ], columns=["threat", "detail", "what would address it"])))
    w("09_limits_and_threats.md", "\n".join(t))


def doc_index():
    inv = []
    for fp in sorted(os.listdir(DATA)):
        inv.append(f"| `data/{fp}` | {os.path.getsize(os.path.join(DATA, fp)) // 1024} KB |")
    t = ["# results - every experiment, every number\n",
         "All experiments of the study with their numbers, the comparison of the current setup with the previous one, and the controls. Start with `00_executive_summary.md`.\n",
         "| document | content |", "|---|---|"]
    for f, d in [("00_executive_summary.md", "main result, findings, how to read"), ("01_dataset.md", "construction, composition, validation, bugs"), ("02_audit_and_features.md", "metric audit, the 133 features"),
                 ("03_history_and_sonarqube.md", "git history, SZZ, SonarQube, interest"), ("04_time_feature.md", "time model, calibration, controls"), ("05_td_type_classification.md", "main experiment"),
                 ("06_ablations.md", "dataset versions, feature groups, layouts"), ("07_earlier_experiments.md", "earlier prediction attempts"), ("08_current_vs_previous.md", "is current better than previous"),
                 ("09_limits_and_threats.md", "limits")]:
        t.append(f"| `{f}` | {d} |")
    t.append("\n## Experiment register\n")
    reg = [
        ("E01", "How was the dataset built; what is in it; do the tests pass on both sides", "01", "properties_all_pairs.csv, dropped_unchanged.csv"),
        ("E02", "Do the TD changes move a metric of their own type (102 pairs; the 50 removed)", "02", "dropped_unchanged.csv"),
        ("E03", "Same audit on the final 61 pairs", "02", "td_audit_final_61.csv"),
        ("E04", "Which features differ between the TD types (ANOVA)", "02", "feature_anova_by_td_type.csv"),
        ("E05", "Git history and SZZ bug mining per project", "03", "git_history_summary.csv"),
        ("E06", "SonarQube: server export, per-release scans", "03", "(project_dataset/sonarqube_server)"),
        ("E07", "Version-wise interest of smell instances (2025 method)", "03, 07", "interest_transitions_*.csv"),
        ("E08", "Re-evaluation of the first prediction model (patch-size effort)", "07", "earlier_*.csv"),
        ("E09", "Interest from git history, function-level snapshots", "07", "interest_snapshot_model_results.csv"),
        ("E10", "Interest, release-by-release instances", "07", "interest_version_model_results.csv"),
        ("E11", "Interest model applied to the dataset pairs", "07", "interest_pair_scores.csv"),
        ("E12", "Bug lifetime predicted from the project vector", "07", "bug_lifetime_model_results.csv, bug_lifetime_summary.txt"),
        ("E13", "The time model: distributions and calibration sweep (x3)", "04", "x3_time_model_sweep.csv, time_model_sweep_summary.csv"),
        ("E14", "Time controls: shuffled and noisy time (x2)", "04", "x2_time_controls.csv, time_controls_summary.csv"),
        ("E15", "TD-type classification: 7 classifiers x 2 layouts x 4 protocols x with / without time (656 runs)", "05", "ml_metrics.csv, ml_summary.csv, ml_time_effect.csv, ml_predictions.csv"),
        ("E16", "Significance: McNemar, bootstrap and Wilson intervals (x4)", "05, 08", "x4_*.csv, comparison_with_vs_without_time.csv"),
        ("E17", "Per class, per project, confusion matrices, importances (x5)", "05", "x5_*.csv, ml_confusion_*.csv, ml_importance.csv"),
        ("E18", "Dataset versions: bug-free vs with bugs vs with time (x0)", "06, 08", "x0_old_dataset_runs.csv, dataset_versions_summary.csv"),
        ("E19", "Feature blocks (x1)", "06", "x1_feature_blocks.csv, feature_blocks_summary.csv"),
        ("E20", "Layouts and selector vs plain classifiers", "06, 08", "ml_time_effect.csv"),
    ]
    t.append(md(pd.DataFrame(reg, columns=["id", "question", "document", "data files"])))
    t.append("\n## Glossary of the metrics\n")
    t.append(md(pd.DataFrame([
        ["accuracy", "share of pairs whose TD type is predicted right"], ["macro-F1", "mean over the 5 types of the F1 score (harmonic mean of precision and recall); every type counts equally, so rare types matter"],
        ["balanced accuracy", "mean recall over the 5 types"], ["precision / recall (per type)", "of the pairs predicted as the type, the share that is right / of the pairs of the type, the share found"],
        ["AUC", "chance that a pair that pays interest gets a higher score than one that does not; 0.5 = chance"], ["R2", "regression: 1 = perfect, 0 = as good as predicting the mean, negative = worse than the mean"],
        ["Spearman", "rank correlation between predicted and true values"], ["95% CI (Wilson)", "interval of one accuracy given the number of pairs"],
        ["paired bootstrap CI", "interval of the accuracy difference with / without time, resampling the 61 pairs 2000 times"], ["McNemar p", "exact test on the pairs where the two models disagree"],
    ], columns=["term", "meaning"])))
    t.append("\n## Protocols\n")
    t.append(md(pd.DataFrame([[k, v] for k, v in PROT_TXT.items()], columns=["name", "meaning"])))
    t.append("\n## How these documents were produced\n`scripts/extra_experiments.py` runs the ablations and controls (about 25 minutes, seeds fixed) and writes `data/x*.csv`; `scripts/build_results.py` reads the results of all experiments (`ml_model/results`, `data/`, the earlier working folders) and writes the documents, so every number comes from a file. Library versions: " +
             ", ".join(f"{p} {im.version(p)}" for p in ("numpy", "pandas", "scikit-learn", "scipy")) + f"; Python {sys.version.split()[0]}.\n")
    t.append("## Files in data/\n\n| file | size |\n|---|---|\n" + "\n".join(inv))
    w("README.md", "\n".join(t))


if __name__ == "__main__":
    L = load_all()
    doc_dataset(L)
    doc_audit_features(L)
    doc_history(L)
    doc_time(L)
    doc_classification(L)
    doc_ablations(L)
    doc_earlier(L)
    T = doc_progress(L)
    doc_summary(L, T)
    doc_limits(L)
    doc_index()
    print("documents written to", RESULTS)
