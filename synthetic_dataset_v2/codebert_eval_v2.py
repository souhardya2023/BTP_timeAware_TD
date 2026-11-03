"""CodeBERT (frozen) on the v2 synthetic pairs and transfer between v2, the 61 real pairs and the natural pairs. writes results/codebert_v2_eval.txt"""
import json, os, warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); NAT = os.path.join(ROOT, "real_project_analysis", "results")
out = []
def P(s=""):
    out.append(s); print(s)
E2 = np.load(os.path.join(HERE, "results", "codebert_v2.npz"), allow_pickle=True)
S = pd.read_csv(os.path.join(HERE, "features", "pairs_delta.csv"))[["instance", "project", "ptype", "template"]]
S = S.set_index("instance").loc[E2["instance"]].reset_index()
ER = np.load(os.path.join(ROOT, "insights", "new", "results", "n9_codebert.npz"))
RE = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv")); yr = RE.td_type.values
B = pd.read_csv(os.path.join(NAT, "b1_pairs.csv")); EN = np.load(os.path.join(NAT, "b2_codebert.npz")); B["ei"] = B.apply(lambda r: list(EN["keys"]).index(r.repo + "|" + r.sha), axis=1)
B["y"] = B.label.map({"dependency": "dependency_structure"}).fillna(B.label)
Bd = B[B.dual_ok]
def fit(Xtr, ytr, C=0.1):
    sc = StandardScaler().fit(Xtr); m = LogisticRegression(C=C, max_iter=1000, class_weight="balanced").fit(sc.transform(Xtr), ytr)
    return lambda X: m.predict(sc.transform(X))
def cv(X, y, splits):
    p = np.empty(len(y), dtype=object)
    for tr, te in splits:
        p[te] = fit(X[tr], y[tr])(X[te])
    return float((p == y).mean())
for key in ("mean", "cls"):
    X = E2[key]; y = S.ptype.values
    P("== CodeBERT %s embedding, logistic regression C=0.1" % key)
    P("v2 synthetic (%d pairs): random %.3f  held-out project %.3f  held-out template %.3f   majority %.3f" % (
        len(S), cv(X, y, StratifiedKFold(5, shuffle=True, random_state=0).split(X, y)), cv(X, y, GroupKFold(10).split(X, y, S.project.values)), cv(X, y, GroupKFold(8).split(X, y, S.template.values)), pd.Series(y).value_counts(normalize=True).max()))
    f = fit(X, y)
    p = f(ER["m" + ("r" if key == "mean" else "r")] if False else ER[("mr" if key == "mean" else "cr")])
    P("train v2 -> real 61 pairs: %.3f (majority %.3f); predicted %s" % ((p == yr).mean(), pd.Series(yr).value_counts(normalize=True).max(), dict(pd.Series(p).value_counts())))
    for nm, sub in (("natural pairs, all weak labels (4 types)", B[B.label != "coupling"]), ("natural pairs, dual evidence", Bd)):
        keep = sub.y.isin(set(y)); sub = sub[keep]
        p = f(EN[key][sub.ei.values])
        P("train v2 -> %s (n=%d): %.3f (majority %.3f)" % (nm, len(sub), (p == sub.y.values).mean(), sub.y.value_counts(normalize=True).max()))
    g = fit(EN[key][Bd.ei.values], Bd.y.values)
    p = g(ER[("mr" if key == "mean" else "cr")]); keep = np.isin(yr, Bd.y.unique())
    P("train natural (dual, %d pairs) -> real 61 pairs of the same 4 types (n=%d): %.3f (majority %.3f)" % (len(Bd), keep.sum(), (p[keep] == yr[keep]).mean(), pd.Series(yr[keep]).value_counts(normalize=True).max()))
    keep2 = S.ptype.isin(Bd.y.unique()).values
    p = g(X[keep2]); P("train natural (dual) -> v2 synthetic of the same 4 types (n=%d): %.3f (majority %.3f)" % (keep2.sum(), (p == y[keep2]).mean(), pd.Series(y[keep2]).value_counts(normalize=True).max()))
    # pooled: natural + v2 -> real
    Xp = np.vstack([X, EN[key][Bd.ei.values]]); yp = np.concatenate([y, Bd.y.values]); h = fit(Xp, yp)
    p = h(ER[("mr" if key == "mean" else "cr")]); P("train v2 + natural -> real 61: %.3f" % (p == yr).mean())
open(os.path.join(HERE, "results", "codebert_v2_eval.txt"), "w").write("\n".join(out))
