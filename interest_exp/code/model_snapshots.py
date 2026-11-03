#!/usr/bin/env python3
"""Predict future interest of a smell instance and evaluate it honestly.

task      for every smell function at a snapshot commit: interest (lines, PM) it will absorb in the next HORIZON commits
          (a) will it absorb any?   (b) how much?
features  only what is known at the snapshot: size/complexity/params, file context, instance age, churn, past interest
protocols leave-one-project-out (train on 8 repos, test on the 9th)   and   temporal (train on first 60% of snapshots of every repo, test on the rest)
baselines mean/prior, size-only (nloc), persistence (past interest only)
metrics   AUC and PR-AUC for (a); Spearman and MAE for (b)

usage: model_snapshots.py DATA_DIR RESULTS_DIR      (DATA_DIR/snapshots/*_snapshots.csv  ->  RESULTS_DIR/snapshot_model_*.csv)
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import average_precision_score, mean_absolute_error, roc_auc_score

FEATS = ["nloc", "ccn", "par", "is_long", "is_cx", "is_par", "file_smells", "file_funcs", "age", "since_change", "n_changes",
         "churn50", "churn_all", "past_il", "past_pm", "past_n_int", "lang_c"]
SIZE_ONLY = ["nloc", "ccn", "par"]
HISTORY_ONLY = ["age", "since_change", "n_changes", "churn50", "churn_all", "past_il", "past_pm", "past_n_int"]


def load(d):
    df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(d, "snapshots", "*_snapshots.csv")))], ignore_index=True)
    df["lang_c"] = (df.lang == "c").astype(int)
    df["any"] = (df.fut_il > 0).astype(int)
    df["ly"] = np.log1p(df.fut_il)
    return df


def fit_predict(train, test, feats, seed=0):
    clf = RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=seed, n_jobs=-1, class_weight="balanced_subsample")
    reg = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=seed, n_jobs=-1)
    clf.fit(train[feats], train["any"])
    reg.fit(train[feats], train["ly"])
    return clf.predict_proba(test[feats])[:, 1], reg.predict(test[feats])


def score(test, p_any, p_ly):
    y, yl = test["any"].values, test["ly"].values
    out = {"n": len(test), "pos_rate": round(y.mean(), 3)}
    if 0 < y.sum() < len(y):
        out["AUC"] = roc_auc_score(y, p_any)
        out["PR_AUC"] = average_precision_score(y, p_any)
    out["Spearman"] = spearmanr(yl, p_ly)[0] if np.std(p_ly) > 0 and np.std(yl) > 0 else np.nan
    out["MAE_lines"] = mean_absolute_error(np.expm1(yl), np.clip(np.expm1(p_ly), 0, None))
    return out


def evaluate(df, protocol):
    models = {"size_only": SIZE_ONLY, "history_only": HISTORY_ONLY, "all_features": FEATS}
    rows, preds = [], []
    if protocol == "leave-one-project-out":
        folds = [(df[df.repo != r], df[df.repo == r], r) for r in sorted(df.repo.unique())]
    else:
        cut = df.groupby("repo").idx.transform(lambda s: s.quantile(0.6))
        # train snapshots must have their whole HORIZON window before the cut, otherwise their targets overlap the test period
        folds = [(df[df.idx + 100 <= cut], df[df.idx > cut], "all-repos")]
    for tr, te, name in folds:
        if len(te) < 20 or te["any"].sum() == 0 or te["any"].sum() == len(te) and False:
            continue
        base_p = np.full(len(te), tr["any"].mean())
        base_l = np.full(len(te), tr["ly"].mean())
        rows.append(dict(protocol=protocol, fold=name, model="prior (mean)", **score(te, base_p, base_l)))
        for m, f in models.items():
            pa, pl = fit_predict(tr, te, f)
            rows.append(dict(protocol=protocol, fold=name, model=m, **score(te, pa, pl)))
            t = te.copy(); t["model"], t["p_any"], t["p_logint"], t["fold"] = m, pa, pl, name
            preds.append(t[["repo", "idx", "file", "func", "model", "fold", "any", "fut_il", "p_any", "p_logint"]])
    return pd.DataFrame(rows), pd.concat(preds) if preds else pd.DataFrame()


def main():
    d, res_dir = sys.argv[1], sys.argv[2]
    os.makedirs(res_dir, exist_ok=True)
    df = load(d)
    print(f"snapshots {len(df)} from {df.repo.nunique()} repos; share with future interest {df['any'].mean():.2f}")
    allr, allp = [], []
    for proto in ("leave-one-project-out", "temporal"):
        r, p = evaluate(df, proto)
        allr.append(r); allp.append(p)
    res = pd.concat(allr)
    res.to_csv(os.path.join(res_dir, "snapshot_model_results.csv"), index=False)
    pd.concat(allp).to_csv(os.path.join(res_dir, "snapshot_model_predictions.csv"), index=False)
    pd.set_option("display.width", 200)
    for proto, g in res.groupby("protocol"):
        print(f"\n== {proto} ==")
        print(g.groupby("model")[["AUC", "PR_AUC", "Spearman", "MAE_lines"]].mean().round(3).to_string())
    print("\nper held-out project (all_features):")
    print(res[(res.protocol == "leave-one-project-out") & (res.model == "all_features")][["fold", "n", "pos_rate", "AUC", "PR_AUC", "Spearman", "MAE_lines"]].round(3).to_string(index=False))
    # feature importance on the full data
    clf = RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=0, n_jobs=-1, class_weight="balanced_subsample").fit(df[FEATS], df["any"])
    imp = pd.Series(clf.feature_importances_, index=FEATS).sort_values(ascending=False)
    print("\nfeature importance (any interest):"); print(imp.round(3).head(8).to_string())


if __name__ == "__main__":
    main()
