"""N9c (EXPLORATORY, decided after seeing N9b): do the 133 features and the CodeBERT embedding complement each other?  Late fusion = average of the class probabilities of
the random forest on the 133 delta features and the logistic regression on the mean-pooled CodeBERT embedding (C = 0.1).  Held-out template, held-out project, temporal."""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sload import SD, manifests
warnings.filterwarnings("ignore")
Z = np.load("../results/n9_codebert.npz"); E = Z["ms"]
D = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv")); X = D[[c for c in D.columns if c.startswith("delta__")]].values
y = D.ptype.values; cls = np.unique(y)
M = manifests(); cm = {i["id"]: i["intro_commit"] for m in M.values() for i in m["instances"]}
D["order"] = D.instance.map(cm); late = (D.groupby("project").order.rank(method="first") > 0.6 * D.groupby("project").instance.transform("size")).values
def probs(tr, te):
    rf = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=4).fit(X[tr], y[tr])
    lr = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=4000, class_weight="balanced")).fit(E[tr], y[tr])
    def full(m, Xt):
        P = np.zeros((len(Xt), len(cls))); P[:, [list(cls).index(c) for c in m.classes_]] = m.predict_proba(Xt); return P
    return full(rf, X[te]), full(lr, E[te])
out = []
P = lambda s="": (out.append(s), print(s, flush=True))
for how in ("template", "project", "temporal"):
    pa = {k: np.empty(len(y), dtype=object) for k in ("features RF", "CodeBERT", "fusion")}; mask = np.ones(len(y), bool)
    if how == "template": folds = [(np.where(D.template != t)[0], np.where(D.template == t)[0]) for t in D.template.unique()]
    elif how == "project": folds = list(GroupKFold(5).split(X, y, D.project))
    else: folds = [(np.where(~late)[0], np.where(late)[0])]; mask = late
    for tr, te in folds:
        a, b = probs(tr, te)
        for k, p in (("features RF", a), ("CodeBERT", b), ("fusion", (a + b) / 2)): pa[k][te] = cls[p.argmax(1)]
    P("held-out %-9s " % how + "  ".join("%s %.3f" % (k, (v[mask] == y[mask]).mean()) for k, v in pa.items()))
    if how == "template":
        pt = pd.DataFrame({"type": D.ptype, "template": D.template, **{k: (v == y).astype(float) for k, v in pa.items()}}).groupby(["type", "template"]).mean()
        P(pt.round(2).to_string()); pt.to_csv("../results/n9c_fusion_per_template.csv")
open("../results/n9c_fusion.txt", "w").write("\n".join(out))
