#!/usr/bin/env python3
"""Predict the INTEREST IN PERSON-MONTHS that a technical-debt instance pays in the next release.

unit      one row = one smell instance (SonarQube issue for Python, structural smell for C/C++) present in release V0
target    pm_interest = COCOMO II effort (person-months) of the lines re-worked inside the instance between V0 and V1 (2025 method; see interest_versions.py)
          reported in milli-person-months (mPM = 1/1000 PM) because one event is worth about 1.5 - 30 mPM
features  known at V0 only: rule, severity, SonarQube remediation effort, region size and complexity, principal (COCOMO II of the region), age in releases,
          interest already paid (lines, events)
protocols leave-one-repo-out (train on 8 repositories, test on the 9th) and temporal (releases before 60% of each repository's history -> later ones)
models    zero (predict no interest), mean, persistence (average interest so far), size_only RF, rf_pm (random forest on the PM scale), gb_pm (gradient boosting),
          hurdle_rf = P(any interest) x E[PM | interest] (two random forests)
metrics   MAE / RMSE in mPM, skill = 1 - MAE/MAE_zero, R2, Spearman (all rows and rows with interest), AUC of the predicted PM for "any interest"
second level  total interest of a repository in the next release (sum over instances): predicted vs actual, correlation over the (repository, release) points;
          and a direct model of that total (persistence of the last release's total, ridge, random forest)

usage: model_pm.py DATA_DIR RESULTS_DIR
output RESULTS_DIR/pm_model_results.csv, pm_model_by_fold.csv, pm_aggregate_results.csv, pm_project_level_results.csv, pm_predictions.csv, pm_importance.csv
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, roc_auc_score

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cocomo
from model_next_release import NUM, load as load_transitions

K = 1000.0                                   # PM -> milli-PM
SIZE = ["nloc0", "ccn0", "principal_pm"]
MODELS = ["zero", "mean", "persistence", "size_only_rf", "rf_pm", "gb_pm", "hurdle_rf"]


def load(d):
    df = load_transitions(d)
    df["y"] = df.pm_interest * K                                     # mPM
    df["avg_lines"] = df.past_il / (df.age + 1)
    df["persist"] = df.avg_lines.map(cocomo.pm) * K                  # expected mPM from the average interest so far
    return df


def design(df, cols, rules):
    X = df[cols].copy()
    for r in rules:
        X["rule=" + r] = (df.rule == r).astype(float)
    return X


def fit_predict(model, tr, te):
    rules = sorted(tr.rule.unique())
    if model == "zero":
        return np.zeros(len(te)), None
    if model == "mean":
        return np.full(len(te), tr.y.mean()), None
    if model == "persistence":
        return te.persist.values, None
    cols = SIZE if model == "size_only_rf" else NUM
    Xtr, Xte = design(tr, cols, rules if model != "size_only_rf" else []), design(te, cols, rules if model != "size_only_rf" else [])
    if model in ("size_only_rf", "rf_pm"):
        m = RandomForestRegressor(300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(Xtr, tr.y)
        return m.predict(Xte), m
    if model == "gb_pm":
        m = GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0).fit(Xtr, tr.y)
        return np.clip(m.predict(Xte), 0, None), m
    if model == "hurdle_rf":
        pos = tr[tr.y > 0]
        c = RandomForestClassifier(300, min_samples_leaf=5, random_state=0, n_jobs=-1, class_weight="balanced_subsample").fit(Xtr, (tr.y > 0).astype(int))
        r = RandomForestRegressor(300, min_samples_leaf=3, random_state=0, n_jobs=-1).fit(design(pos, cols, rules), pos.y)
        p = c.predict_proba(Xte)[:, 1]
        base = tr.y.eq(0).mean()
        # the balanced classifier over-states the probability: recalibrate it so that the mean probability equals the training rate of interest
        p = np.clip(p * (1 - base) / max(p.mean(), 1e-9), 0, 1) if len(p) else p
        return p * r.predict(design(te, cols, rules)), c
    raise ValueError(model)


def folds(df, protocol):
    if protocol == "leave-one-repo-out":
        return [(df[df.repo != r], df[df.repo == r], r) for r in sorted(df.repo.unique())]
    cut = df.groupby("repo").vi.transform(lambda s: 0.6 * s.max())
    return [(df[df.vi < cut], df[df.vi >= cut], "all")]


def metrics(y, p, zero_mae):
    out = dict(n=len(y), share_with_interest=float((y > 0).mean()), actual_total_mPM=float(y.sum()), predicted_total_mPM=float(p.sum()),
               MAE_mPM=mean_absolute_error(y, p), RMSE_mPM=float(np.sqrt(mean_squared_error(y, p))), R2=r2_score(y, p))
    out["skill_vs_zero"] = 1 - out["MAE_mPM"] / zero_mae if zero_mae > 0 else np.nan
    out["spearman_all"] = spearmanr(y, p)[0] if np.std(p) > 0 else np.nan
    pos = y > 0
    out["spearman_positives"] = spearmanr(y[pos], p[pos])[0] if pos.sum() > 3 and np.std(p[pos]) > 0 else np.nan
    out["AUC_any_interest"] = roc_auc_score(pos, p) if 0 < pos.sum() < len(y) and np.std(p) > 0 else np.nan
    return out


def project_level(df, protocol):
    """total interest (mPM) of a repository between two releases, from the state at the first release"""
    g = df.groupby(["repo", "vi"]).agg(instances=("key", "nunique"), principal_mPM=("principal_pm", lambda s: s.sum() * K), mean_age=("age", "mean"), past_il=("past_il", "sum"),
                                       y=("y", "sum"), lang_c=("lang_c", "first")).reset_index().sort_values(["repo", "vi"])
    g["prev_y"] = g.groupby("repo").y.shift(1)
    g = g.dropna(subset=["prev_y"]).copy()
    cols = ["instances", "principal_mPM", "mean_age", "past_il", "prev_y", "lang_c"]
    rows, preds = [], []
    for tr, te, name in folds(g, protocol):
        for m in ("zero", "mean", "persistence", "ridge", "random_forest"):
            if m == "zero":
                p = np.zeros(len(te))
            elif m == "mean":
                p = np.full(len(te), tr.y.mean())
            elif m == "persistence":
                p = te.prev_y.values
            elif m == "ridge":
                mu, sd = tr[cols].mean(), tr[cols].std().replace(0, 1)
                p = np.clip(Ridge(alpha=10).fit((tr[cols] - mu) / sd, tr.y).predict((te[cols] - mu) / sd), 0, None)
            else:
                p = RandomForestRegressor(300, min_samples_leaf=3, random_state=0, n_jobs=-1).fit(tr[cols], tr.y).predict(te[cols])
            preds.append(pd.DataFrame(dict(protocol=protocol, fold=name, model=m, repo=te.repo.values, vi=te.vi.values, y=te.y.values, p=p)))
    P = pd.concat(preds)
    for m, h in P.groupby("model"):
        y, p = h.y.values, h.p.values
        z = P[P.model == "zero"].y.abs().mean()
        rows.append(dict(protocol=protocol, model=m, points=len(h), MAE_mPM=mean_absolute_error(y, p), skill_vs_zero=1 - mean_absolute_error(y, p) / z, R2=r2_score(y, p),
                         pearson=pearsonr(y, p)[0] if np.std(p) > 0 else np.nan, spearman=spearmanr(y, p)[0] if np.std(p) > 0 else np.nan))
    return pd.DataFrame(rows)


def main():
    d, res = sys.argv[1], sys.argv[2]
    os.makedirs(res, exist_ok=True)
    df = load(d).reset_index(drop=True)
    print(f"{len(df)} instance-transitions, {(df.y > 0).mean():.1%} with interest, total {df.y.sum():.0f} mPM")
    pooled, byfold, aggr, preds = [], [], [], []
    for protocol in ("leave-one-repo-out", "temporal"):
        P = {m: np.zeros(len(df)) for m in MODELS}
        mask = np.zeros(len(df), bool)
        for tr, te, name in folds(df, protocol):
            mask[te.index] = True
            for m in MODELS:
                p, _ = fit_predict(m, tr, te)
                P[m][te.index] = p
        te_all = df[mask]
        zero_mae = te_all.y.abs().mean()
        for m in MODELS:
            pooled.append(dict(protocol=protocol, model=m, **metrics(te_all.y.values, P[m][mask], zero_mae)))
            if protocol == "leave-one-repo-out":
                for r, h in te_all.groupby("repo"):
                    byfold.append(dict(protocol=protocol, model=m, repo=r, **metrics(h.y.values, P[m][h.index], h.y.abs().mean())))
        # level 2: totals per (repository, release)
        for m in MODELS:
            t = te_all.assign(p=P[m][mask]).groupby(["repo", "vi"]).agg(y=("y", "sum"), p=("p", "sum")).reset_index()
            aggr.append(dict(protocol=protocol, model=m, points=len(t), pearson=pearsonr(t.y, t.p)[0] if t.p.std() > 0 else np.nan, spearman=spearmanr(t.y, t.p)[0] if t.p.std() > 0 else np.nan,
                             R2=r2_score(t.y, t.p), MAE_mPM=mean_absolute_error(t.y, t.p), total_ratio_pred_over_actual=t.p.sum() / t.y.sum()))
            if m in ("zero", "persistence", "rf_pm", "hurdle_rf"):
                preds.append(te_all.assign(model=m, predicted_mPM=P[m][mask], protocol=protocol)[["protocol", "model", "repo", "vi", "key", "rule", "y", "predicted_mPM"]])
    pd.DataFrame(pooled).to_csv(os.path.join(res, "pm_model_results.csv"), index=False)
    pd.DataFrame(byfold).to_csv(os.path.join(res, "pm_model_by_fold.csv"), index=False)
    pd.DataFrame(aggr).to_csv(os.path.join(res, "pm_aggregate_results.csv"), index=False)
    pd.concat(preds).rename(columns={"y": "actual_mPM"}).to_csv(os.path.join(res, "pm_predictions.csv"), index=False)
    pd.concat([project_level(df, p) for p in ("leave-one-repo-out", "temporal")]).to_csv(os.path.join(res, "pm_project_level_results.csv"), index=False)
    rules = sorted(df.rule.unique())
    rf = RandomForestRegressor(300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(design(df, NUM, rules), df.y)
    imp = pd.Series(rf.feature_importances_, index=design(df, NUM, rules).columns).sort_values(ascending=False)
    imp.rename("importance").reset_index().rename(columns={"index": "feature"}).to_csv(os.path.join(res, "pm_importance.csv"), index=False)
    pd.set_option("display.width", 220)
    print(pd.DataFrame(pooled).round(3).to_string(index=False))
    print(pd.read_csv(os.path.join(res, "pm_project_level_results.csv")).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
