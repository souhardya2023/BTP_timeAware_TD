"""N8: the surprising 0.656 of a logistic regression on direction-only deltas, leave-one-project-out, 61 real pairs: per project, per C, and against the random forest."""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sload import ROOT
warnings.filterwarnings("ignore")
RP = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
cols = [c for c in RP.columns if c.startswith("delta__")]
unit = lambda a: a / np.where(np.linalg.norm(a, axis=1, keepdims=True) > 0, np.linalg.norm(a, axis=1, keepdims=True), 1)
X = {"raw": RP[cols].values.astype(float), "unit length": unit(RP[cols].values.astype(float)), "sign": np.sign(RP[cols].values.astype(float))}
y, proj = RP.td_type.values, RP.project.values
out = []
P = lambda s="": (out.append(s), print(s))
def lopo(Xm, mk):
    pred = np.empty(len(y), dtype=object)
    for p in np.unique(proj):
        te = proj == p; pred[te] = mk().fit(Xm[~te], y[~te]).predict(Xm[te])
    return pred
P("leave-one-project-out accuracy on the 61 real pairs (majority 0.426; non-boltons majority 0.432)")
for tn, Xm in X.items():
    for name, mk in (("RF", lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=2)),) + tuple(("logistic C=%g" % c, (lambda c=c: make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=5000, class_weight="balanced")))) for c in (0.005, 0.05, 0.5)):
        p = lopo(Xm, mk); nb = proj != "boltons"
        P("  %-12s %-16s overall %.3f   non-boltons %.3f   boltons (24 concurrency) %.3f" % (tn, name, (p == y).mean(), (p[nb] == y[nb]).mean(), (p[~nb] == y[~nb]).mean()))
pl = lopo(X["unit length"], lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=5000, class_weight="balanced")))
prf = lopo(X["raw"], lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=2))
pd.DataFrame([{"project": q, "n": int((proj == q).sum()), "random forest (raw delta)": float((prf[proj == q] == y[proj == q]).mean()), "logistic (direction of the delta)": float((pl[proj == q] == y[proj == q]).mean())} for q in sorted(set(proj))]).to_csv("../results/n8_per_project.csv", index=False)
p = pl
P("\nlogistic, unit length, C=0.05: per project accuracy")
for q in sorted(set(proj)): P("  %-14s n=%2d  %.2f" % (q, (proj == q).sum(), (p[proj == q] == y[proj == q]).mean()))
P("per type recall: " + str({t: round(float((p[y == t] == t).mean()), 2) for t in np.unique(y)}))
open("../results/n8_logistic_check.txt", "w").write("\n".join(out))
