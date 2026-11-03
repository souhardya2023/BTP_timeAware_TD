"""S1: the type of a debt change from the 133 features, on 1,321 synthetic pairs, with the splits that matter.
 splits: random (stratified 5-fold by pair) | held-out project (5-fold by project = by domain) | leave-one-template-out | held-out tier
 inputs: delta (child - parent) | child only (a single snapshot, no clean twin) | parent + child + delta
 plus: mixed against pure commits; drift-scaled delta; a learning curve under leave-one-template-out"""
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sload import SD
import glob, os
warnings.filterwarnings("ignore")
D = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv"))
dcols = [c for c in D.columns if c.startswith("delta__")]
pcols = [c for c in D.columns if c.startswith("parent__")]
y = D.ptype.values
RF = lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1, min_samples_leaf=1)
X_delta = D[dcols].values
X_parent = D[pcols].values
X_child = X_parent + X_delta
out = []
P = lambda s="": (out.append(s), print(s))
P("pairs %d, types %s, majority %.3f" % (len(D), D.ptype.value_counts().to_dict(), D.ptype.value_counts(normalize=True).max()))

def cv(X, split, groups=None, sub=None):
    pred = np.empty(len(y), dtype=object)
    if split == "random":
        it = StratifiedKFold(5, shuffle=True, random_state=0).split(X, y)
    elif split == "project":
        it = GroupKFold(5).split(X, y, D.project)
    elif split == "template":
        it = ((np.where(D.template != t)[0], np.where(D.template == t)[0]) for t in D.template.unique())
    elif split == "tier":
        it = ((np.where(D.tier != t)[0], np.where(D.tier == t)[0]) for t in D.tier.unique())
    for tr, te in it:
        if sub is not None:
            tr = tr[np.isin(tr, sub)]
        pred[te] = RF().fit(X[tr], y[tr]).predict(X[te])
    return pred
res = []
for name, X in (("delta (child - parent)", X_delta), ("child only (no twin)", X_child), ("parent + child + delta", np.hstack([X_parent, X_child, X_delta]))):
    r = {"input": name}
    for split in ("random", "project", "template", "tier"):
        p = cv(X, split)
        r[split] = (p == y).mean(); r[split + "_bal"] = balanced_accuracy_score(y, p)
        if name.startswith("delta") and split in ("project", "template"):
            globals()["PRED_" + split] = p
    res.append(r)
R = pd.DataFrame(res)
R.to_csv("../results/s1_pairs_splits.csv", index=False)
P("\n## accuracy by split and input (balanced accuracy in the csv)")
P(R[["input", "random", "project", "template", "tier"]].round(3).to_string(index=False))
P("\n## delta, held-out template: accuracy per template (a template is the code pattern of the injection)")
pt = pd.DataFrame({"template": D.template, "ptype": D.ptype, "ok": PRED_template == y}).groupby(["ptype", "template"]).ok.agg(["mean", "size"])
P(pt.round(2).to_string())
P("\n## delta, held-out project: mixed commits (other edits in the same commit) against pure")
for m in (False, True):
    s = D.mixed.astype(str) == str(m)
    P("  mixed=%s: n=%d accuracy %.3f" % (m, s.sum(), (PRED_project[s] == y[s]).mean()))
P("  by tier (held-out project): " + str({t: round(float((PRED_project[D.tier == t] == y[D.tier == t]).mean()), 3) for t in "SMLX"}))
P("  by regime (held-out project): " + str({t: round(float((PRED_project[D.regime == t] == y[D.regime == t]).mean()), 3) for t in D.regime.unique()}))
# drift-scaled delta
drift = {}
for f in glob.glob(os.path.join(SD, "features", "releases", "*.csv")):
    Rr = pd.read_csv(f).sort_values("release")
    feats = [c[7:] for c in dcols]
    drift[Rr.project.iloc[0]] = np.abs(np.diff(Rr[feats].values, axis=0)).mean(0)
A = np.vstack([drift[p] for p in D.project])
Z = X_delta / (A + 1e-3)
Zs = np.sign(Z) * np.log1p(np.abs(Z))
P("\n## drift-scaled delta (each delta divided by the mean release-to-release change of the same feature in the same project)")
for name, X in (("raw delta", X_delta), ("delta / drift", Z), ("signed log of delta / drift", Zs)):
    P("  %-30s random %.3f   held-out project %.3f   held-out template %.3f" % (name, (cv(X, "random") == y).mean(), (cv(X, "project") == y).mean(), (cv(X, "template") == y).mean()))
# learning curve under leave-one-template-out
P("\n## learning curve, delta, leave-one-template-out accuracy against the number of training pairs")
rng = np.random.default_rng(0)
for n in (60, 150, 300, 600, 1000, 1321):
    accs = []
    for rep in range(3):
        sub = rng.choice(len(D), min(n, len(D)), replace=False) if n < len(D) else np.arange(len(D))
        p = cv(X_delta, "template", sub=sub)
        accs.append((p == y).mean())
    P("  %4d pairs: %.3f" % (n, np.mean(accs)))
open("../results/s1_pairs.txt", "w").write("\n".join(out))
