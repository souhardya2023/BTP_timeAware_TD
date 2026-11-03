"""N3b: does a scale-free description of the change transfer from synthetic to real?  (direction of the change, not its size)
transforms: sign of each delta (-1, 0, +1) | the delta vector divided by its own length | the sign x log-rank of |delta| within the pair (relative importance of features)"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from scipy.stats import rankdata
from sload import SD, ROOT
warnings.filterwarnings("ignore")
S = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv")); R = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
cols = [c for c in S.columns if c.startswith("delta__") and c in R.columns]
ys, yr = S.ptype.values, R.td_type.values; py = (R.language == "Python").values
def sign(a): return np.sign(a)
def unit(a): n = np.linalg.norm(a, axis=1, keepdims=True); return a / np.where(n > 0, n, 1)
def rankt(a): return np.sign(a) * np.array([rankdata(np.abs(r)) / a.shape[1] for r in a])
out = []
P = lambda s="": (out.append(s), print(s))
P("train synthetic -> test real (61 pairs, majority 0.426); and the reverse")
for tname, tf in (("raw", lambda a: a), ("sign", sign), ("unit length", unit), ("signed rank within the pair", rankt)):
    A, B = tf(S[cols].values.astype(float)), tf(R[cols].values.astype(float))
    for mname, mk in (("RF", lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=2)),
                      ("logistic", lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=3000, class_weight="balanced")))):
        p = mk().fit(A, ys).predict(B)
        q = mk().fit(B, yr).predict(A)
        P("  %-28s %-8s sim->real %.3f (Python %.3f, C/C++ %.3f)   real->sim %.3f" % (tname, mname, (p == yr).mean(), (p[py] == yr[py]).mean(), (p[~py] == yr[~py]).mean(), (q == ys).mean()))
# the size of the real and synthetic deltas
nr = np.linalg.norm(R[cols].values, axis=1); ns = np.linalg.norm(S[cols].values, axis=1)
P("\nmedian length of the delta vector: real %.3f, synthetic %.3f (ratio %.1f)" % (np.median(nr), np.median(ns), np.median(ns) / np.median(nr)))
nzr, nzs = (np.abs(R[cols].values) > 0).sum(1), (np.abs(S[cols].values) > 0).sum(1)
P("features changed per pair (median): real %d, synthetic %d" % (np.median(nzr), np.median(nzs)))
open("../results/n3b_scale_free.txt", "w").write("\n".join(out))
