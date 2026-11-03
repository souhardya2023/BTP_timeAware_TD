"""J5: the direction-only linear model validated properly. Nested leave-one-project-out on the 61 real pairs: the transform (raw / signed log / sign / unit length / within-row rank) and the regularisation C
are chosen INSIDE the training projects by an inner leave-one-project-out; the outer fold only tests. Also a hybrid (random forest where the training set has >= 6 pairs of a class, the linear model otherwise)."""
import os, warnings
import numpy as np, pandas as pd
from scipy.stats import rankdata
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings("ignore")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
D = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
cols = [c for c in D.columns if c.startswith("delta__") or c.startswith("d_")] or [c for c in D.columns if c not in ("id", "td_type", "language", "project", "fold", "fold_by_project", "time_diff_min")]
cols = [c for c in cols if D[c].dtype.kind in "fi"]
proj = D.id.str.split("/").str[1].str.split("_").str[0].values if "id" in D else D.project.values
if "project" in D: proj = D.project.values
y = D.td_type.values; X = D[cols].values.astype(float); X = np.nan_to_num(X)
TR = {"raw": lambda a: a, "signed log": lambda a: np.sign(a) * np.log1p(np.abs(a)), "sign": np.sign,
      "unit length": lambda a: a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-9), "rank": lambda a: np.apply_along_axis(rankdata, 1, a) / a.shape[1]}
def lr(Xtr, ytr, Xte, C):
    sc = StandardScaler().fit(Xtr); m = LogisticRegression(C=C, max_iter=1000, class_weight="balanced").fit(sc.transform(Xtr), ytr); return m.predict(sc.transform(Xte))
def inner_choice(Xa, ya, ga):
    best, bs = None, -1
    for tn, tf in TR.items():
        Z = tf(Xa)
        for C in (0.01, 0.1, 1.0, 10.0):
            ok = 0
            for g in sorted(set(ga)):
                te = ga == g; tr = ~te
                if len(set(ya[tr])) < 2: continue
                ok += (lr(Z[tr], ya[tr], Z[te], C) == ya[te]).sum()
            if ok > bs: best, bs = (tn, C), ok
    return best
pred = np.empty(len(y), dtype=object); chosen = {}
for g in sorted(set(proj)):
    te = proj == g; tr = ~te
    tn, C = inner_choice(X[tr], y[tr], proj[tr]); chosen[g] = (tn, C)
    Z = TR[tn](X); pred[te] = lr(Z[tr], y[tr], Z[te], C)
rf = np.empty(len(y), dtype=object); hyb = np.empty(len(y), dtype=object)
for g in sorted(set(proj)):
    te = proj == g; tr = ~te
    m = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=3).fit(X[tr], y[tr]); rf[te] = m.predict(X[te])
    cnt = pd.Series(y[tr]).value_counts(); rare = set(cnt[cnt < 6].index)
    hyb[te] = rf[te]
    if rare:
        tn, C = chosen[g]; Z = TR[tn](X); lp = lr(Z[tr], y[tr], Z[te], C)
        hyb[te] = np.where(np.isin(lp, list(rare)), lp, rf[te])
non = proj != "boltons"
maj = pd.Series(y).value_counts(normalize=True).max()
lines = ["nested leave-one-project-out, 61 real pairs, %d projects; majority %.3f (non-boltons %.3f)" % (len(set(proj)), maj, pd.Series(y[non]).value_counts(normalize=True).max())]
for nm, p in (("random forest (raw delta)", rf), ("linear model, transform + C chosen inside the training projects", pred), ("hybrid: forest, linear model for rare classes", hyb)):
    lines.append("%-62s overall %.3f   boltons %.3f   other 37 pairs %.3f" % (nm, (p == y).mean(), (p[~non] == y[~non]).mean(), (p[non] == y[non]).mean()))
lines.append("transforms chosen per held-out project: " + str(pd.Series([v[0] for v in chosen.values()]).value_counts().to_dict()) + "; C: " + str(pd.Series([v[1] for v in chosen.values()]).value_counts().to_dict()))
print("\n".join(lines)); open(os.path.join("..", "results", "j5_nested.txt"), "w").write("\n".join(lines))
