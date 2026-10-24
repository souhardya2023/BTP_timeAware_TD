#!/usr/bin/env python3
"""Does the time feature help to classify the technical-debt type?   Two models per setting: one WITH time_diff_min, one WITHOUT.

data       ../out_dataset/{full,delta_only}/dataset_{with,without}_time.csv   (61 pairs, target td_type, 5 classes)
models     random forest, gradient boosting, logistic regression, SVM (RBF), kNN, and random forest / logistic regression behind a 10-best-features selector
           (selection is fitted inside every training fold) - fixed settings, no tuning on the test folds
protocols  given_stratified      the `fold` column (5 folds stratified by td_type)
           given_by_project      the `fold_by_project` column (no project in two folds: the model is tested on projects it never saw)
           leave_one_project_out each of the 10 projects is the test set once
           repeated_stratified   20 different random stratified 5-fold splits (to see how much the result depends on the split)
baselines  majority class, and the time feature alone (random forest)
metrics    accuracy, macro-F1, balanced accuracy; for the repeated protocol the mean over the 20 splits and the paired difference with/without time

usage: run_experiments.py [--repeats 20] [--workers 3]
output results/metrics.csv, summary.csv, time_effect.csv, predictions.csv, confusion_*.csv, importance.csv, report.md
"""
import concurrent.futures as cf
import os
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "out_dataset")
RES = os.path.join(HERE, "results")
META = ["id", "project", "language", "fold", "fold_by_project", "td_type", "label"]
CLASSES = ["complexity", "concurrency", "coupling_cohesion", "dependency_structure", "security"]
MODELS = {
    "random_forest": lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=1),
    "gradient_boosting": lambda: GradientBoostingClassifier(n_estimators=100, max_depth=2, random_state=0),
    "logistic_regression": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced")),
    "svm_rbf": lambda: make_pipeline(StandardScaler(), SVC(C=3.0, class_weight="balanced")),
    "knn": lambda: make_pipeline(StandardScaler(), KNeighborsClassifier(3)),
    # feature selection INSIDE every training fold (the 10 features with the highest ANOVA F against td_type), the same step for the with-time and the without-time model
    "kbest10_random_forest": lambda: make_pipeline(SelectKBest(f_classif, k=10), RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=1)),
    "kbest10_logistic_regression": lambda: make_pipeline(StandardScaler(), SelectKBest(f_classif, k=10), LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced")),
}


def load(layout, with_time):
    return pd.read_csv(os.path.join(DATA, layout, f"dataset_{'with' if with_time else 'without'}_time.csv"))


def splits(D, protocol, seed=0):
    idx = np.arange(len(D))
    if protocol == "given_stratified":
        return [(idx[D.fold != f], idx[D.fold == f]) for f in sorted(D.fold.unique())]
    if protocol == "given_by_project":
        return [(idx[D.fold_by_project != f], idx[D.fold_by_project == f]) for f in sorted(D.fold_by_project.unique())]
    if protocol == "leave_one_project_out":
        return [(idx[D.project != p], idx[D.project == p]) for p in sorted(D.project.unique())]
    return list(StratifiedKFold(5, shuffle=True, random_state=seed).split(idx, D.td_type))


def predict(D, cols, model, sp):
    pred = np.empty(len(D), dtype=object)
    for tr, te in sp:
        m = MODELS[model]() if model != "majority" else None
        if model == "majority":
            pred[te] = D.td_type.iloc[tr].value_counts().idxmax()
            continue
        m.fit(D.iloc[tr][cols], D.td_type.iloc[tr])
        pred[te] = m.predict(D.iloc[te][cols])
    return pred


def metrics(y, p):
    return dict(accuracy=accuracy_score(y, p), macro_f1=f1_score(y, p, average="macro", labels=CLASSES, zero_division=0), balanced_accuracy=balanced_accuracy_score(y, p))


def job(a):
    layout, model, with_time, protocol, seed = a
    D = load(layout, with_time)
    cols = [c for c in D.columns if c not in META]
    if model == "time_only":
        W = load(layout, True)
        D, cols, mdl = W, ["time_diff_min"], "random_forest"
    else:
        mdl = model
    p = predict(D, cols, mdl, splits(D, protocol, seed))
    return dict(layout=layout, model=model, with_time=with_time, protocol=protocol, repeat=seed, **metrics(D.td_type, p)), pd.DataFrame(dict(id=D.id, true=D.td_type, pred=p, layout=layout, model=model, with_time=with_time, protocol=protocol, repeat=seed))


def main():
    repeats = int(sys.argv[sys.argv.index("--repeats") + 1]) if "--repeats" in sys.argv else 20
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
    os.makedirs(RES, exist_ok=True)
    jobs = []
    for layout in ("full", "delta_only"):
        for protocol in ("given_stratified", "given_by_project", "leave_one_project_out"):
            for model in list(MODELS) + ["majority"]:
                for wt in ((False,) if model == "majority" else (False, True)):
                    jobs.append((layout, model, wt, protocol, 0))
            jobs.append((layout, "time_only", True, protocol, 0))
        for model in MODELS:
            for wt in (False, True):
                jobs += [(layout, model, wt, "repeated_stratified", s) for s in range(repeats)]
    print(len(jobs), "runs", flush=True)
    rows, preds = [], []
    with cf.ProcessPoolExecutor(workers) as ex:
        for k, (r, pr) in enumerate(ex.map(job, jobs, chunksize=2), 1):
            rows.append(r)
            if r["protocol"] != "repeated_stratified":
                preds.append(pr)
            if k % 50 == 0:
                print(k, "done", flush=True)
    M = pd.DataFrame(rows)
    M.to_csv(os.path.join(RES, "metrics.csv"), index=False)
    pd.concat(preds).to_csv(os.path.join(RES, "predictions.csv"), index=False)
    S = M.groupby(["layout", "protocol", "model", "with_time"])[["accuracy", "macro_f1", "balanced_accuracy"]].agg(["mean", "std"]).round(3)
    S.columns = ["_".join(c) for c in S.columns]
    S.reset_index().to_csv(os.path.join(RES, "summary.csv"), index=False)
    # paired effect of the time feature
    eff = []
    for (layout, protocol, model), g in M[M.model.isin(MODELS)].groupby(["layout", "protocol", "model"]):
        a, b = g[~g.with_time].sort_values("repeat"), g[g.with_time].sort_values("repeat")
        d_acc, d_f1 = b.accuracy.values - a.accuracy.values, b.macro_f1.values - a.macro_f1.values
        eff.append(dict(layout=layout, protocol=protocol, model=model, acc_without=a.accuracy.mean(), acc_with=b.accuracy.mean(), diff_acc=d_acc.mean(), diff_acc_std=d_acc.std() if len(d_acc) > 1 else np.nan,
                        f1_without=a.macro_f1.mean(), f1_with=b.macro_f1.mean(), diff_f1=d_f1.mean(), with_better_or_equal_share=float((d_acc >= 0).mean()), with_better_share=float((d_acc > 0).mean()), n=len(d_acc)))
    E = pd.DataFrame(eff).round(3)
    E.to_csv(os.path.join(RES, "time_effect.csv"), index=False)
    # confusion matrices (pooled predictions) of the random forest with / without time on the two honest protocols
    P = pd.concat(preds)
    for (layout, protocol, wt), g in P[(P.model == "random_forest") & P.protocol.isin(["given_by_project", "leave_one_project_out"])].groupby(["layout", "protocol", "with_time"]):
        cm = pd.DataFrame(confusion_matrix(g.true, g.pred, labels=CLASSES), index=[f"true_{c}" for c in CLASSES], columns=[f"pred_{c}" for c in CLASSES])
        cm.to_csv(os.path.join(RES, f"confusion_{layout}_{protocol}_{'with' if wt else 'without'}_time.csv"))
    # random forest importance with time, all data
    imp = []
    for layout in ("full", "delta_only"):
        W = load(layout, True)
        cols = [c for c in W.columns if c not in META]
        rf = RandomForestClassifier(500, class_weight="balanced", random_state=0, n_jobs=-1).fit(W[cols], W.td_type)
        s = pd.Series(rf.feature_importances_, index=cols).sort_values(ascending=False)
        imp.append(pd.DataFrame(dict(layout=layout, feature=s.index, importance=s.values, rank=np.arange(1, len(s) + 1))))
    I = pd.concat(imp)
    I.to_csv(os.path.join(RES, "importance.csv"), index=False)
    write_report(M, S.reset_index(), E, I)
    print("done ->", RES)


def write_report(M, S, E, I):
    L = ["# Results: model with the time feature vs model without it", "",
         "Target: `td_type` (5 classes), 61 pairs. Time feature: `time_diff_min` (minutes to fix the 3 injected bugs in the TD project minus in the clean project; values from the ground-truth time model).",
         "Accuracy / macro-F1; the repeated protocol is the mean over 20 random stratified 5-fold splits. Majority class = 0.43 accuracy.", ""]
    L += ["## Headline: best model without time vs best model with time", "", "| layout | protocol | best without time (acc) | best with time (acc) |", "|---|---|---|---|"]
    for layout in ("full", "delta_only"):
        for protocol in ("given_stratified", "repeated_stratified", "given_by_project", "leave_one_project_out"):
            e = E[(E.layout == layout) & (E.protocol == protocol)]
            a, b = e.loc[e.acc_without.idxmax()], e.loc[e.acc_with.idxmax()]
            L.append(f"| {layout} | {protocol} | {a.model} {a.acc_without:.2f} (F1 {a.f1_without:.2f}) | {b.model} {b.acc_with:.2f} (F1 {b.f1_with:.2f}) |")
    L += ["", "(`majority` below = the most frequent class of the training folds; when whole projects are held out it can be a class that is rare in the test project, hence very low values.)", ""]
    for layout in ("full", "delta_only"):
        L += [f"## Layout `{layout}`", ""]
        for protocol in ("given_stratified", "repeated_stratified", "given_by_project", "leave_one_project_out"):
            e = E[(E.layout == layout) & (E.protocol == protocol)]
            L += [f"### {protocol}", "", "| model | without time (acc / F1) | with time (acc / F1) | change in accuracy | with time better or equal in |", "|---|---|---|---|---|"]
            for _, r in e.iterrows():
                L.append(f"| {r.model} | {r.acc_without:.2f} / {r.f1_without:.2f} | {r.acc_with:.2f} / {r.f1_with:.2f} | {r.diff_acc:+.2f}" + (f" (sd {r.diff_acc_std:.2f})" if r.n > 1 else "") + f" | {r.with_better_or_equal_share:.0%} of {r.n} run(s) |")
            base = M[(M.layout == layout) & (M.protocol == protocol) & M.model.isin(["majority", "time_only"])]
            L += [""] + (["baselines: " + "; ".join(f"{r.model} acc {r.accuracy:.2f} / F1 {r.macro_f1:.2f}" for _, r in base.iterrows()), ""] if len(base) else [])
    t = I[I.feature == "time_diff_min"]
    L += ["## Where the time feature ranks in a random forest (all 61 pairs)", "", "| layout | features | rank of time_diff_min | importance |", "|---|---|---|---|"]
    for _, r in t.iterrows():
        L.append(f"| {r.layout} | {int((I.layout == r.layout).sum())} | {int(r['rank'])} | {r.importance:.3f} |")
    L += ["", "Confusion matrices of the random forest on the two project-held-out protocols: `confusion_*.csv`. All runs: `metrics.csv`; per-pair predictions: `predictions.csv`.", ""]
    open(os.path.join(RES, "report.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    main()
