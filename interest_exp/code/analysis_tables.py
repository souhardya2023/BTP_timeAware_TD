#!/usr/bin/env python3
"""Descriptive analysis of the interest paid: per project, per release, per rule, principal vs interest, concentration, sensitivity to the COCOMO II constants
and to the smell detector.

usage: analysis_tables.py DATA_DIR RESULTS_DIR
reads  DATA_DIR/transitions/*.csv (SonarQube issues for Python, structural smells for C/C++), DATA_DIR/transitions_structural/*.csv (structural smells for the Python projects)
writes RESULTS_DIR/tables/*.csv
"""
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cocomo

PYTHON = ["boltons", "click", "jinja", "werkzeug"]


def load(d):
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(d, "*.csv")))], ignore_index=True)


def with_principal(df):
    """principal of an instance = COCOMO II effort to rewrite its region, taken at its first observation (nloc0; nloc1 when it appears in that release pair)"""
    df = df.copy()
    df["principal_first"] = np.where(df.nloc0 > 0, df.principal_pm, df.nloc1.map(cocomo.pm))
    return df


def summary(df):
    ev = df[(df.cls == "interest") & (df.interest_lines > 0)]
    g = df.groupby("repo").agg(releases=("vi", lambda s: int(s.max()) + 2), instances=("key", "nunique"), instance_transitions=("key", "size"), repayments=("cls", lambda s: int((s == "repayment").sum())),
                               principal_increases=("cls", lambda s: int((s == "increase").sum())), introduced=("cls", lambda s: int((s == "introduced").sum())))
    g["interest_events"] = ev.groupby("repo").size()
    g["interest_lines"] = ev.groupby("repo").interest_lines.sum()
    g["interest_PM"] = ev.groupby("repo").pm_interest.sum()
    first = df.sort_values("vi").drop_duplicates(["repo", "key"])
    g["principal_PM_of_instances_at_first_sight"] = first.groupby("repo").principal_first.sum()
    g["interest_over_principal"] = g.interest_PM / g.principal_PM_of_instances_at_first_sight
    g["mean_interest_mPM_per_event"] = 1000 * g.interest_PM / g.interest_events
    return g.fillna(0).reset_index()


def main():
    d, res = sys.argv[1], sys.argv[2]
    T = os.path.join(res, "tables")
    os.makedirs(T, exist_ok=True)
    df = with_principal(load(os.path.join(d, "transitions")))
    S = summary(df)
    S.to_csv(os.path.join(T, "project_summary.csv"), index=False)
    # per release
    ev = df.assign(event=((df.cls == "interest") & (df.interest_lines > 0)))
    R = ev.groupby(["repo", "vi", "v0", "v1"]).agg(instances=("key", "size"), events=("event", "sum"), interest_lines=("interest_lines", "sum"), interest_PM=("pm_interest", "sum"),
                                                   repayments=("cls", lambda s: int((s == "repayment").sum())), introduced=("cls", lambda s: int((s == "introduced").sum()))).reset_index()
    R.to_csv(os.path.join(T, "release_series.csv"), index=False)
    # per rule / severity / smell type
    rules_f = os.path.join(HERE, "..", "..", "project_dataset", "sonarqube_server", "rules.csv")
    names = pd.read_csv(rules_f, keep_default_na=False).set_index("rule").name.to_dict() if os.path.exists(rules_f) else {}
    py = ev[ev.repo.isin(PYTHON)]
    B = py.groupby("rule").agg(instance_transitions=("key", "size"), distinct_instances=("key", "nunique"), events=("event", "sum"), interest_lines=("interest_lines", "sum"), interest_PM=("pm_interest", "sum")).reset_index()
    B["share_of_interest_PM"] = B.interest_PM / B.interest_PM.sum()
    B["events_per_100_instance_transitions"] = 100 * B.events / B.instance_transitions
    B.insert(1, "rule_name", B.rule.map(names).fillna(""))
    B.sort_values("interest_PM", ascending=False).to_csv(os.path.join(T, "interest_by_sonar_rule.csv"), index=False)
    sv = py.groupby("severity").agg(instance_transitions=("key", "size"), events=("event", "sum"), interest_PM=("pm_interest", "sum")).reset_index()
    sv["events_per_100_instance_transitions"] = 100 * sv.events / sv.instance_transitions
    sv.to_csv(os.path.join(T, "interest_by_sonar_severity.csv"), index=False)
    cc = ev[~ev.repo.isin(PYTHON)]
    cs = cc.groupby("rule").agg(instance_transitions=("key", "size"), distinct_instances=("key", "nunique"), events=("event", "sum"), interest_lines=("interest_lines", "sum"), interest_PM=("pm_interest", "sum")).reset_index()
    cs["events_per_100_instance_transitions"] = 100 * cs.events / cs.instance_transitions
    cs.to_csv(os.path.join(T, "interest_by_structural_smell_c.csv"), index=False)
    # principal vs interest per instance
    first = df.sort_values("vi").drop_duplicates(["repo", "key"]).set_index(["repo", "key"])
    ev = df.assign(event=((df.cls == "interest") & (df.interest_lines > 0))) if "event" not in df else ev
    g = ev.groupby(["repo", "key"]).agg(file=("file", "first"), function_name=("func", "first"), rule=("rule", "first"), transitions_present=("vi", "size"), first_release_index=("vi", "min"),
                                        interest_events=("event", "sum"), interest_lines=("interest_lines", "sum"), interest_PM=("pm_interest", "sum")).reset_index()
    g["principal_PM"] = [first.loc[(r, k), "principal_first"] for r, k in zip(g.repo, g.key)]
    g["interest_over_principal"] = np.where(g.principal_PM > 0, g.interest_PM / g.principal_PM, np.nan)
    g.sort_values("interest_PM", ascending=False).to_csv(os.path.join(T, "principal_vs_interest_per_instance.csv"), index=False)
    paid = g[g.interest_PM > 0]
    stats = dict(instances=len(g), instances_that_paid_interest=len(paid), share_that_paid=len(paid) / len(g), median_interest_over_principal_if_paid=paid.interest_over_principal.median(),
                 mean_interest_over_principal_if_paid=paid.interest_over_principal.mean(), instances_with_interest_above_principal=int((paid.interest_over_principal > 1).sum()),
                 median_transitions_present=g.transitions_present.median(), max_transitions_present=int(g.transitions_present.max()))
    pd.DataFrame([stats]).T.rename(columns={0: "value"}).reset_index().rename(columns={"index": "statistic"}).to_csv(os.path.join(T, "principal_vs_interest_summary.csv"), index=False)
    # concentration
    rows = []
    for r, h in g.groupby("repo"):
        s = h.interest_PM.sort_values(ascending=False).values
        tot = s.sum()
        if tot > 0:
            rows.append(dict(repo=r, instances=len(s), top_1_instance_share=s[0] / tot, top_5pct_share=s[:max(1, int(len(s) * .05))].sum() / tot, top_10pct_share=s[:max(1, int(len(s) * .10))].sum() / tot,
                             instances_needed_for_half=int(np.searchsorted(np.cumsum(s) / tot, 0.5) + 1)))
    pd.DataFrame(rows).to_csv(os.path.join(T, "interest_concentration.csv"), index=False)
    # lifetime of instances (consecutive transitions present) and fate
    last = df.sort_values("vi").groupby(["repo", "key"]).tail(1)
    fate = last.groupby("repo").agg(instances=("key", "size"), repaid=("cls", lambda s: int((s == "repayment").sum()))).reset_index()
    fate["share_repaid"] = fate.repaid / fate.instances
    fate["median_transitions_present"] = g.groupby("repo").transitions_present.median().reindex(fate.repo).values
    fate.to_csv(os.path.join(T, "instance_fate.csv"), index=False)
    # COCOMO sensitivity: recompute the effort of every event under both constant sets
    rows = []
    pm = {p: (lambda lines, p=p: cocomo.pm(lines, p)) for p in cocomo.PRESETS}
    e = ev[ev.event]
    for p, f in pm.items():
        e = e.assign(**{f"pm_{p}": e.interest_lines.map(f)})
    cs_ = e.groupby("repo")[[f"pm_{p}" for p in pm]].sum()
    cs_["ratio_paper_over_nominal"] = cs_.pm_paper / cs_.pm_nominal
    cs_.reset_index().to_csv(os.path.join(T, "cocomo_sensitivity.csv"), index=False)
    pd.DataFrame([dict(statistic="Spearman correlation of the project totals (nominal vs paper constants)", value=spearmanr(cs_.pm_nominal, cs_.pm_paper)[0]),
                  dict(statistic="Spearman correlation of the per-event effort", value=spearmanr(e.pm_nominal, e.pm_paper)[0]),
                  dict(statistic="nominal COCOMO II.2000: A, E", value=f"{cocomo.PRESETS['nominal']['A']}, {cocomo.PRESETS['nominal']['E']:.4f}"),
                  dict(statistic="paper preset: A, E", value=f"{cocomo.PRESETS['paper']['A']}, {cocomo.PRESETS['paper']['E']}")]).to_csv(os.path.join(T, "cocomo_sensitivity_summary.csv"), index=False)
    # detector comparison on the Python projects: SonarQube issues vs structural smells
    sd = os.path.join(d, "transitions_structural")
    if os.path.isdir(sd):
        D2 = load(sd)
        rows = []
        for r in PYTHON:
            a, b = df[df.repo == r], D2[D2.repo == r]
            ea, eb = a[(a.cls == "interest") & (a.interest_lines > 0)], b[(b.cls == "interest") & (b.interest_lines > 0)]
            sa = ea.groupby("vi").pm_interest.sum().reindex(range(a.vi.max() + 1), fill_value=0)
            sb = eb.groupby("vi").pm_interest.sum().reindex(range(a.vi.max() + 1), fill_value=0)
            rows.append(dict(repo=r, sonar_instances=a.key.nunique(), structural_instances=b.key.nunique(), sonar_events=len(ea), structural_events=len(eb), sonar_PM=ea.pm_interest.sum(), structural_PM=eb.pm_interest.sum(),
                             spearman_of_per_release_PM=spearmanr(sa, sb)[0] if sa.std() > 0 and sb.std() > 0 else np.nan))
        pd.DataFrame(rows).to_csv(os.path.join(T, "detector_comparison_python.csv"), index=False)
    print("tables written to", T)


if __name__ == "__main__":
    main()
