#!/usr/bin/env python3
"""Predict the interest an instance pays in the NEXT version, from version-wise transitions (out/versions/*.csv).

row = one TD instance present in version V0;  target = interest lines (and effort in PM) it pays between V0 and V1
features known at V0 only: detector rule, severity, SonarQube remediation effort, region size and complexity, age in versions,
interest already paid, number of earlier interest events.
protocols: leave-one-repo-out, and temporal (train transitions before 60% of a repo's versions, test later).
usage: model_next_release.py DATA_DIR RESULTS_DIR      (DATA_DIR/transitions/*.csv  ->  RESULTS_DIR/next_release_model_results.csv)
"""
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import average_precision_score, mean_absolute_error, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings("ignore")
SEV = {"INFO": 0, "MINOR": 1, "MAJOR": 2, "CRITICAL": 3, "BLOCKER": 4}
NUM = ["sev", "sonar_effort_min", "nloc0", "ccn0", "age", "past_il", "past_n", "lang_c", "principal_pm"]
SETS = {"size_only": ["nloc0", "ccn0"], "history_only": ["age", "past_il", "past_n"], "all_features": NUM}


def load(d):
    df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(d, "transitions", "*.csv")))], ignore_index=True)
    df = df[df.cls != "introduced"].copy()
    df["sev"] = df.severity.map(SEV).fillna(2)
    df["lang_c"] = df.repo.isin(["libpng", "zlib", "jansson", "cJSON", "libyaml"]).astype(int)
    df["any"] = (df.interest_lines > 0).astype(int)
    df["ly"] = np.log1p(df.interest_lines)
    return df


def models(cols):
    num = [c for c in cols]
    cat = ["rule"] if "sev" in cols else []
    pre = ColumnTransformer([("n", "passthrough", num)] + ([("c", OneHotEncoder(handle_unknown="ignore"), cat)] if cat else []))
    return (Pipeline([("p", pre), ("m", RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=0, n_jobs=-1, class_weight="balanced_subsample"))]),
            Pipeline([("p", pre), ("m", RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0, n_jobs=-1))]))


def score(te, pa, pl):
    y = te["any"].values
    r = {"n": len(te), "pos": round(y.mean(), 3)}
    if 0 < y.sum() < len(y):
        r["AUC"], r["PR_AUC"] = roc_auc_score(y, pa), average_precision_score(y, pa)
    r["Spearman"] = spearmanr(te.ly, pl)[0] if np.std(pl) > 0 else np.nan
    r["MAE_lines"] = mean_absolute_error(te.interest_lines, np.clip(np.expm1(pl), 0, None))
    return r


def evaluate(df, proto):
    rows = []
    if proto == "leave-one-repo-out":
        folds = [(df[df.repo != r], df[df.repo == r], r) for r in sorted(df.repo.unique())]
    else:
        cut = df.groupby("repo").vi.transform(lambda s: 0.6 * s.max())
        folds = [(df[df.vi < cut], df[df.vi >= cut], "all-repos")]
    for tr, te, name in folds:
        if len(te) < 20 or te["any"].sum() == 0:
            continue
        rows.append(dict(protocol=proto, fold=name, model="prior", **score(te, np.full(len(te), tr["any"].mean()), np.full(len(te), tr.ly.mean()))))
        for m, cols in SETS.items():
            c, r = models(cols)
            X = [*cols] + (["rule"] if m == "all_features" else [])
            c.fit(tr[X], tr["any"]); r.fit(tr[X], tr.ly)
            rows.append(dict(protocol=proto, fold=name, model=m, **score(te, c.predict_proba(te[X])[:, 1], r.predict(te[X]))))
    return pd.DataFrame(rows)


def main():
    d, res_dir = sys.argv[1], sys.argv[2]
    os.makedirs(res_dir, exist_ok=True)
    df = load(d)
    print(f"{len(df)} instance-transitions from {df.repo.nunique()} repos ({df.vi.nunique()} version steps); {df['any'].mean():.1%} pay interest in the next version")
    res = pd.concat([evaluate(df, p) for p in ("leave-one-repo-out", "temporal")])
    res.to_csv(os.path.join(res_dir, "next_release_model_results.csv"), index=False)
    pd.set_option("display.width", 200)
    for p, g in res.groupby("protocol"):
        print(f"\n== {p} ==")
        print(g.groupby("model")[["AUC", "PR_AUC", "Spearman", "MAE_lines"]].mean().round(3).to_string())
    print("\nper held-out repo (all_features):")
    print(res[(res.protocol == "leave-one-repo-out") & (res.model == "all_features")][["fold", "n", "pos", "AUC", "Spearman"]].round(3).to_string(index=False))
    # actual paid interest table
    print("\nactual paid interest (COCOMO II, preset in cocomo.py):")
    t = df.groupby("repo").agg(versions=("vi", lambda s: s.max() + 2), instances=("key", "nunique"), interest_events=("any", "sum"),
                              interest_lines=("interest_lines", "sum"), interest_PM=("pm_interest", "sum")).round(3)
    print(t.to_string())


if __name__ == "__main__":
    main()
