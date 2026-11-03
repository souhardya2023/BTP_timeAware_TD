"""Level 1 on the v2 synthetic pairs, and sim-to-real transfer; the same protocols as the talk (random / held-out project / temporal) plus a held-out template. Writes results/level1_v2.txt|csv.
Compares with v1 (../synthetic_dataset) when its feature table exists."""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True); out = []
def P(s=""):
    out.append(s); print(s)
def models():
    return {"10-best + RF (talk)": lambda: make_pipeline(SelectKBest(f_classif, k=10), RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3)),
            "random forest": lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3)}
def cv(X, y, splits, mk):
    pred = np.empty(len(y), dtype=object)
    for tr, te in splits:
        pred[te] = mk().fit(X[tr], y[tr]).predict(X[te])
    return float((pred == y).mean())
def table(path, tag):
    S = pd.read_csv(path)
    dcols = [c for c in S.columns if c.startswith("delta__")]; pcols = [c for c in S.columns if c.startswith("parent__")]
    y = S.ptype.values; rows = []
    P("%s: %d pairs, %d projects, %d templates, majority %.3f" % (tag, len(S), S.project.nunique(), S.template.nunique(), pd.Series(y).value_counts(normalize=True).max()))
    inst = S.instance.str.extract(r"D(\d+)$")[0].astype(int).values if S.instance.str.contains("-D").all() else np.arange(len(S))
    order = np.argsort(S.project.rank(method="dense").values * 1000 + inst, kind="stable")
    n_tr = int(0.6 * len(S)); tmp_tr, tmp_te = order[:n_tr], order[n_tr:]
    for inp, cols in (("delta", dcols), ("child only (parent+delta)", pcols + dcols)):
        X = S[cols].values.astype(float)
        for mn, mk in models().items():
            r = {"data": tag, "input": inp, "model": mn}
            r["random"] = cv(X, y, StratifiedKFold(5, shuffle=True, random_state=0).split(X, y), mk)
            r["held-out project"] = cv(X, y, GroupKFold(10).split(X, y, S.project.values), mk)
            r["held-out template"] = cv(X, y, GroupKFold(8).split(X, y, S.template.values), mk)
            r["temporal"] = float((mk().fit(X[tmp_tr], y[tmp_tr]).predict(X[tmp_te]) == y[tmp_te]).mean())
            rows.append(r)
    R = pd.DataFrame(rows); P(R.round(3).to_string(index=False)); return S, R
S2, R2 = table(os.path.join(HERE, "features", "pairs_delta.csv"), "v2")
allr = [R2]
v1 = os.path.join(ROOT, "synthetic_dataset", "features", "pairs_delta.csv")
if os.path.exists(v1):
    S1, R1 = table(v1, "v1"); allr.append(R1)
pd.concat(allr).to_csv(os.path.join(HERE, "results", "level1_v2.csv"), index=False)
# sim-to-real
RE = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv")); yr = RE.td_type.values; lang = (RE.language == "Python").values
P("\nreal pairs: %d, majority %.3f (Python %.3f, C/C++ %.3f)" % (len(RE), pd.Series(yr).value_counts(normalize=True).max(), pd.Series(yr[lang]).value_counts(normalize=True).max(), pd.Series(yr[~lang]).value_counts(normalize=True).max()))
sl = lambda a: np.sign(a) * np.log1p(np.abs(a))
for tag, S in (("v2", S2), ("v1", S1 if os.path.exists(v1) else None)):
    if S is None: continue
    cols = [c for c in S.columns if c.startswith("delta__") and c in RE.columns]
    for tn, tf in (("raw", lambda a: a), ("signed log", sl)):
        for mn, mk in models().items():
            m = mk().fit(tf(S[cols].values.astype(float)), S.ptype.values); p = m.predict(tf(RE[cols].values.astype(float)))
            P("train %s -> real 61 [%s, %s]: accuracy %.3f  Python %.3f  C/C++ %.3f  predicted classes %s" % (tag, tn, mn, (p == yr).mean(), (p[lang] == yr[lang]).mean(), (p[~lang] == yr[~lang]).mean(), dict(pd.Series(p).value_counts())))
    cols = [c for c in S.columns if c.startswith("delta__") and c in RE.columns]
    m = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3).fit(sl(RE[cols].values.astype(float)), yr)
    P("train real 61 -> %s: accuracy %.3f (majority %.3f)" % (tag, float((m.predict(sl(S[cols].values.astype(float))) == S.ptype.values).mean()), pd.Series(S.ptype.values).value_counts(normalize=True).max()))
open(os.path.join(HERE, "results", "level1_v2.txt"), "w").write("\n".join(out))
