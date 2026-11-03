"""L1-C2: does putting the same debt into older host versions (time windows) help?
 1. how often does the patch apply to an earlier version, and how stable is its feature signature across hosts?
 2. augmentation: extra training rows = the same pair in older contexts; test rows = the original pairs only; all copies of a pair stay on one side of the split."""
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
CL = pd.read_csv("../results/l1_context_clean.csv")
TD = pd.read_csv("../results/l1_context_td.csv")
PR = pd.read_csv(f"{ROOT}/project_dataset/properties_all_pairs.csv").set_index("id")
feats = [c for c in CL.columns if c not in ("project", "commit", "error")]
dcols = ["delta__" + f for f in feats]
out = []
P = lambda s: (out.append(s), print(s))

TD["project"] = TD.id.map(PR.project)
P("## 1. Can the debt change be moved to an older version of its project?")
P(f"attempts: {len(TD)}; patch applied and vectorised: {(TD.status=='ok').sum()} ({(TD.status=='ok').mean():.0%}); patch failed: {(TD.status=='patch_failed').sum()}; other errors: {(~TD.status.isin(['ok','patch_failed'])).sum()}")
st = TD.groupby("project").status.apply(lambda s: f"{(s=='ok').sum()}/{len(s)}")
P("applied per project: " + str(st.to_dict()))
ok = TD[TD.status == "ok"].merge(CL.drop_duplicates(["project", "commit"]), on=["project", "commit"], suffixes=("", "_clean"))
ok = ok[[c for c in ok.columns if c in feats or c in ("id", "ctx", "project", "commit") or c.endswith("_clean")]]
tdv = np.vstack([ok[f].values for f in feats]).T if all(f in ok.columns for f in feats) else None
M = TD[TD.status == "ok"].merge(CL.drop_duplicates(["project", "commit"]), on=["project", "commit"], suffixes=("", "_c"))
delta = M[feats].values - M[[f + "_c" for f in feats]].values
M["_i"] = range(len(M))
byid = M.groupby("id")["_i"].apply(list)
P(f"pairs with at least one older-context copy: {len(byid)} of {len(DS)}; contexts per such pair: median {byid.str.len().median():.0f}")
by_pair_ok = M.groupby("id").size()
# stability of the signature
base = DS.set_index("id")[["delta__" + f for f in feats]].values
idx = {k: i for i, k in enumerate(DS.id)}
cos, sg = [], []
for pid, ii in byid.items():
    b = base[idx[pid]]
    nz = np.abs(b) > 1e-9
    if nz.sum() < 3:
        continue
    for i in ii:
        d = delta[i]
        cos.append(np.dot(b[nz], d[nz]) / (np.linalg.norm(b[nz]) * np.linalg.norm(d[nz]) + 1e-12))
        sg.append(np.mean(np.sign(b[nz]) == np.sign(d[nz])))
pd.DataFrame({"cosine": cos, "sign_agreement": sg}).to_csv("../results/l1_context_stability.csv", index=False)
P(f"signature stability (features the original injection changes): cosine similarity original vs older host: median {np.median(cos):.2f}; sign agreement: median {np.median(sg):.2f}  (n={len(cos)} copies)")
rels = []
for pid, ii in byid.items():
    b = base[idx[pid]]
    nz = np.abs(b) > 1e-9
    for i in ii:
        rels.append(np.median(np.abs(delta[i][nz] - b[nz]) / (np.abs(b[nz]) + 1e-9)))
P(f"median relative change of the signature between hosts: {np.median(rels):.2f}")

# ---------------- 2. augmentation
y = DS.td_type.values
proj = DS.project.values
Xb = DS[["delta__" + f for f in feats]].values
Xa, ya, ida = delta, M.td_type if "td_type" in M else DS.set_index("id").loc[M.id].td_type.values, M.id.values
pa = DS.set_index("id").loc[M.id].project.values
folds_s = DS.set_index("id").loc[M.id].fold.values
KB = lambda: make_pipeline(SelectKBest(f_classif, k=10), RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1))
RF = lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1)
def run(fn, split, aug, n_aug=None):
    folds = DS.fold.values if split == "stratified" else pd.factorize(proj)[0]
    fa = folds_s if split == "stratified" else pd.factorize(proj)[0][[idx[i] for i in M.id]]
    pred = np.empty(len(y), dtype=object)
    for f in np.unique(folds):
        te = folds == f
        Xtr, ytr = Xb[~te], y[~te]
        if aug:
            sel = fa != f
            Xtr = np.vstack([Xtr, Xa[sel]]); ytr = np.concatenate([ytr, np.asarray(ya)[sel]])
        pred[te] = fn().fit(Xtr, ytr).predict(Xb[te])
    return pred
nb = proj != "boltons"
P("\n## 2. Augmentation by time windows (no time feature)   accuracy [balanced]   non-boltons accuracy under leave-one-project-out")
P(f"training rows: original 61; with older-context copies +{len(M)} (all copies of a held-out pair/project are removed from training)")
AUG = []
for mn, fn in (("RF", RF), ("10-best+RF", KB)):
    for aug in (False, True):
        r = []
        for split in ("stratified", "lopo"):
            pr = run(fn, split, aug)
            r.append(f"{split} {(pr==y).mean():.3f} [{balanced_accuracy_score(y, pr):.3f}]")
            if split == "lopo":
                r.append(f"non-boltons {(pr[nb]==y[nb]).mean():.3f}")
        AUG.append(dict(model=mn, augmented=aug, stratified=(run(fn, "stratified", aug) == y).mean(), lopo=(run(fn, "lopo", aug) == y).mean(), lopo_nonboltons=(run(fn, "lopo", aug)[nb] == y[nb]).mean()))
        P(f"  {mn:11s} {'with older contexts' if aug else 'original 61 only':20s} " + "   ".join(r))
open("../results/l1_context_aug.txt", "w").write("\n".join(out))
pd.DataFrame(AUG).to_csv("../results/l1_context_aug.csv", index=False)
