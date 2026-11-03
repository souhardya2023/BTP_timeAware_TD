"""S1c: Level 1 (type of a debt change) under the protocols of the talk: stratified random, leave-one-project-out, temporal.
 temporal = in every project the pairs introduced in the first 60 % of its history (by commit order) train, the later 40 % test (all projects pooled; the projects are seen).
 leave-one-project-out = 150 folds, one whole project (= one domain) held out.
Inputs: delta (child - parent) and child only; models: random forest, and the final model of the talk (10 best features by ANOVA F + random forest)."""
import json, os, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sload import SD, manifests
warnings.filterwarnings("ignore")
D = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv"))
I = pd.read_csv(os.path.join(SD, "instances.csv")).set_index("instance")
M = manifests()
cm = {i["id"]: i["intro_commit"] for m in M.values() for i in m["instances"]}
D["order"] = D.instance.map(cm)
D["rank_in_project"] = D.groupby("project").order.rank(method="first")
D["n_in_project"] = D.groupby("project").instance.transform("size")
D["late"] = D.rank_in_project > 0.6 * D.n_in_project
dcols = [c for c in D.columns if c.startswith("delta__")]
pcols = [c for c in D.columns if c.startswith("parent__")]
y = D.ptype.values
Xd = D[dcols].values; Xc = D[pcols].values + Xd
RF = lambda: RandomForestClassifier(200, class_weight="balanced", random_state=0, n_jobs=4)
KB = lambda: make_pipeline(SelectKBest(f_classif, k=10), RandomForestClassifier(200, class_weight="balanced", random_state=0, n_jobs=4))
def run(X, mk, proto):
    pred = np.empty(len(y), dtype=object)
    if proto == "random":
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(X, y):
            pred[te] = mk().fit(X[tr], y[tr]).predict(X[te])
        return pred, np.ones(len(y), bool)
    if proto == "temporal":
        tr, te = np.where(~D.late)[0], np.where(D.late)[0]
        pred[te] = mk().fit(X[tr], y[tr]).predict(X[te])
        return pred, D.late.values
    for p in D.project.unique():
        te = np.where(D.project == p)[0]; tr = np.where(D.project != p)[0]
        pred[te] = mk().fit(X[tr], y[tr]).predict(X[te])
    return pred, np.ones(len(y), bool)
def boot(ok, groups, B=2000):
    r = np.random.default_rng(0); u = np.unique(groups); idx = {g: np.where(groups == g)[0] for g in u}
    v = [np.concatenate([idx[g] for g in r.choice(u, len(u))]) for _ in range(B)]
    return np.percentile([ok[i].mean() for i in v], [2.5, 97.5])
rows = []
for iname, X in (("delta", Xd), ("child only (no twin)", Xc)):
    for mname, mk in (("random forest", RF), ("10-best + RF (talk)", KB)):
        for proto in ("random", "temporal", "leave-one-project-out"):
            pr, mask = run(X, mk, proto)
            ok = (pr[mask] == y[mask]); lo, hi = boot(ok, D.project.values[mask])
            rows.append(dict(input=iname, model=mname, protocol=proto, n_test=int(mask.sum()), accuracy=ok.mean(), lo=lo, hi=hi, balanced=balanced_accuracy_score(y[mask], pr[mask])))
            print(rows[-1], flush=True)
R = pd.DataFrame(rows); R.to_csv("../results/s1_protocols.csv", index=False)
maj = pd.Series(y[D.late.values]).value_counts(normalize=True).max()
out = ["majority class: %.3f (all pairs), %.3f (temporal test part)" % (pd.Series(y).value_counts(normalize=True).max(), maj), ""]
out.append(R.pivot_table(index=["input", "model"], columns="protocol", values="accuracy").round(3).to_string())
out.append("\ndifference leave-one-project-out minus temporal, minus random (accuracy points):")
pv = R.pivot_table(index=["input", "model"], columns="protocol", values="accuracy")
out.append(((pv["leave-one-project-out"] - pv["temporal"]) * 100).round(1).to_string())
open("../results/s1_protocols.txt", "w").write("\n".join(out)); print("\n".join(out))
