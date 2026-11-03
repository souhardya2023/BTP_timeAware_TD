"""L1-C1: natural drift versus the injected debt change.
The clean copies of each host project at 5 earlier commits (+ the base commit used in the dataset) form a time series of the 133 features.
 1. how large is the natural drift of a feature between two such versions compared with the change that the debt injection makes?
 2. 'drift-scaled' delta: divide each delta by the drift scale of ITS OWN project (computed from the clean history only, no labels) and classify again.
"""
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import balanced_accuracy_score
from sklearn.pipeline import make_pipeline

from common import ROOT

warnings.filterwarnings("ignore")
DS = pd.read_csv(f"{ROOT}/out_dataset/delta_only/dataset_without_time.csv")
FULL = pd.read_csv(f"{ROOT}/out_dataset/full/dataset_without_time.csv")
CL = pd.read_csv("../results/l1_context_clean.csv")
if "error" in CL:
    CL = CL[CL.error.isna()].drop(columns="error")
feats = [c for c in CL.columns if c not in ("project", "commit")]
dcols = ["delta__" + f for f in feats]
out = []
P = lambda s: (out.append(s), print(s))

# per project: the series = contexts (in order of the file: nearest first) and the base clean vector (one per pair, average over the project's pairs)
drift = {}
for pr, g in CL.groupby("project"):
    ctx = g[feats].values                                                 # nearest first ... oldest last
    base = FULL[FULL.project == pr][["clean__" + f for f in feats]].values.mean(0)
    series = np.vstack([base[None, :], ctx])                              # base, then going back in time
    d = np.abs(np.diff(series, axis=0))
    drift[pr] = (d.mean(0), d.std(0), series.std(0))
pairs = DS[["project"]].copy()
D = DS[dcols].values
n = len(DS)
A = np.vstack([drift[p][0] for p in DS.project])                          # mean |step| of drift of the project's own series
S = np.vstack([drift[p][2] for p in DS.project])                          # std of the project's own series
inj = np.abs(D)
eps = 1e-6
P("## 1. Size of the injected debt change against the natural drift of the same feature")
act = (inj > 0)
ratio = np.where(A > eps, inj / A, np.nan)
np.save("../results/l1_drift_ratio.npy", ratio[act & (A > eps)])
P(f"pair-feature cells where the debt injection changes the feature at all: {act.mean():.1%}")
P(f"median over those cells of |injected change| / mean |natural change between two versions|: {np.nanmedian(ratio[act]):.2f}")
P(f"share of those cells where the injected change is larger than the natural drift: {np.nanmean(ratio[act] > 1):.1%}")
P("features that change per pair at all (median): %d of 133; features whose change exceeds the natural drift (median): %d" % (np.median(act.sum(1)), np.median(np.nansum((ratio > 1) & act, 1))))
NA = pd.DataFrame({"td_type": DS.td_type, "n_changed": act.sum(1), "n_above_drift": np.nansum((ratio > 1) & act, 1)}); NA.to_csv("../results/l1_drift_per_pair.csv", index=False)
per_type = pd.DataFrame({"td_type": DS.td_type, "n_changed": act.sum(1), "n_above_drift": np.nansum((ratio > 1) & act, 1)}).groupby("td_type").median()
P("by type (median per pair):\n" + per_type.to_string())

# ---- 2. classification with raw delta and drift-scaled delta
scale = A + S * 0 + 1e-3                                                  # drift scale per (project, feature)
Z = D / scale
KB = lambda: make_pipeline(SelectKBest(f_classif, k=10), RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1))
RF = lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1)
y = DS.td_type.values
proj = DS.project.values
def cv(fn, X, split):
    folds = {"stratified": DS.fold.values, "lopo": pd.factorize(proj)[0]}[split]
    pred = np.empty(len(y), dtype=object)
    for f in np.unique(folds):
        te = folds == f
        pred[te] = fn().fit(X[~te], y[~te]).predict(X[te])
    return pred
P("\n## 2. Debt type (no time feature): raw delta against drift-scaled delta (accuracy / balanced accuracy)")
nb = proj != "boltons"
for name, X in (("raw delta", D), ("delta / drift of its own project", Z), ("signed log of the drift-scaled delta", np.sign(Z) * np.log1p(np.abs(Z)))):
    for mn, fn in (("RF", RF), ("10-best+RF", KB)):
        r = []
        for split in ("stratified", "lopo"):
            pr = cv(fn, X, split)
            r.append(f"{split}: {(pr==y).mean():.3f}/{balanced_accuracy_score(y, pr):.3f}")
            if split == "lopo":
                r.append(f"non-boltons pairs: {(pr[nb]==y[nb]).mean():.3f}")
        P(f"  {name:40s} {mn:11s} " + "   ".join(r))
open("../results/l1_drift.txt", "w").write("\n".join(out))
