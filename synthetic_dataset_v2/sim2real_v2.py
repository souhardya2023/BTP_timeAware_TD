"""Does a model trained on the v2 synthetic pairs work on the 61 real pairs when the representation removes the scale (relative delta = delta / (|parent| + 1)), and when only the hosts of realistic dilution (tier H) are used? writes results/sim2real_v2.txt"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
out = []
def P(s=""):
    out.append(s); print(s)
S = pd.read_csv(os.path.join(HERE, "features", "pairs_delta.csv")); R = pd.read_csv(os.path.join(ROOT, "out_dataset", "full", "dataset_without_time.csv"))
names = [c[7:] for c in S.columns if c.startswith("delta__") and ("clean__" + c[7:]) in R.columns and ("parent__" + c[7:]) in S.columns]
def rep(df, kind, real):
    d = df[["delta__" + n for n in names]].values.astype(float); par = df[[("clean__" if real else "parent__") + n for n in names]].values.astype(float)
    if kind == "raw": return d
    if kind == "relative": return d / (np.abs(par) + 1.0)
    if kind == "sign": return np.sign(d)
    if kind == "signed log": return np.sign(d) * np.log1p(np.abs(d))
yr = R.td_type.values; lang = (R.language == "Python").values
P("shared features %d; real majority %.3f; v2 pairs %d (tier H %d, median relative change of sloc: all %.3f %%, H %.3f %%)" % (len(names), pd.Series(yr).value_counts(normalize=True).max(), len(S), (S.tier == "H").sum(),
  100 * (S.delta__c_sloc / S.parent__c_sloc).abs().median(), 100 * (S[S.tier == "H"].delta__c_sloc / S[S.tier == "H"].parent__c_sloc).abs().median()))
for subset, mask in (("all v2 pairs", np.ones(len(S), bool)), ("tier H hosts only (realistic dilution)", (S.tier == "H").values)):
    T = S[mask]
    for kind in ("raw", "signed log", "relative", "sign"):
        m = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3).fit(rep(T, kind, False), T.ptype.values)
        p = m.predict(rep(R, kind, True))
        P("train %-40s [%-10s] -> real 61: accuracy %.3f  Python %.3f  C/C++ %.3f  predicted %s" % (subset, kind, (p == yr).mean(), (p[lang] == yr[lang]).mean(), (p[~lang] == yr[~lang]).mean(), dict(pd.Series(p).value_counts())))
# within v2 held-out project, relative representation
y = S.ptype.values
for kind in ("raw", "relative"):
    X = rep(S, kind, False); pred = np.empty(len(S), dtype=object)
    for tr, te in GroupKFold(10).split(X, y, S.project.values):
        pred[te] = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3).fit(X[tr], y[tr]).predict(X[te])
    P("v2 held-out project, %s delta: %.3f" % (kind, (pred == y).mean()))
Hh = S[S.tier == "H"]; X = rep(Hh, "relative", False); pred = np.empty(len(Hh), dtype=object)
for tr, te in GroupKFold(min(8, Hh.project.nunique())).split(X, Hh.ptype.values, Hh.project.values):
    pred[te] = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3).fit(X[tr], Hh.ptype.values[tr]).predict(X[te])
P("v2 tier H only (%d pairs, %d projects), held-out project, relative delta: %.3f (majority %.3f)" % (len(Hh), Hh.project.nunique(), (pred == Hh.ptype.values).mean(), Hh.ptype.value_counts(normalize=True).max()))
Xr = rep(R, "relative", True)
m = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3).fit(Xr, yr); p = m.predict(rep(S, "relative", False))
P("train real 61 (relative) -> v2 all: %.3f (majority %.3f)" % ((p == y).mean(), pd.Series(y).value_counts(normalize=True).max()))
open(os.path.join(HERE, "results", "sim2real_v2.txt"), "w").write("\n".join(out))
