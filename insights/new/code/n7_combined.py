"""N7: real and synthetic together.
 (A) panel: the same metrics computed on the real histories, the synthetic baseline, all synthetic, and the pooled rows; 'agree' = the two data sets give the same qualitative answer
 (B) pooling for Level 2: train on real + synthetic and test on the held-out real repository (and temporal): does the synthetic data help?
 (C) pooling for Level 1: train on the other real projects + the 1,321 synthetic deltas (direction of the delta only), test on the held-out real project."""
import os, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sload import SD, ROOT, boot_ci, capture
warnings.filterwarnings("ignore")
R = pd.read_csv("../results/n4_rows_real.csv").fillna(0); S = pd.read_csv("../results/n4_rows_synthetic.csv").fillna(0)
R["ds"] = "real"; S["ds"] = "synthetic"; R["regime"] = "real"
SB = S[S.regime == "baseline"]
out = []
P = lambda s="": (out.append(s), print(s, flush=True))
# ------------------------------------------------------------------ (A) panel
def gini(x):
    x = np.sort(np.asarray(x, float)); return 1 - 2 * np.sum(np.cumsum(x) - x / 2) / (len(x) * x.sum()) if x.sum() > 0 else np.nan
def icc(D, by):
    g = D.groupby(by)["ev"]; n, m = g.size(), g.mean(); N, k, gm = len(D), len(n), D.ev.mean()
    msb = (n * (m - gm) ** 2).sum() / (k - 1); msw = ((D.ev - g.transform("mean")) ** 2).sum() / (N - k); n0 = (N - (n ** 2).sum() / N) / (k - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw)
def metrics(D):
    m = {}
    m["event rate"] = D.ev.mean()
    inst = D.groupby(["repo", "key"]).y.sum(); m["Gini of interest over instances"] = gini(inst.values)
    cnt = D.groupby(["repo", "key"]).size(); L = D.set_index(["repo", "key"]).loc[cnt[cnt >= 10].index].reset_index()
    m["share of instances that never pay (>= 10 releases)"] = (L.groupby(["repo", "key"]).ev.sum() == 0).mean()
    dd = D[["repo", "key", "vi", "ev"]]
    for lag in (1, 3):
        s = dd.copy(); s["vi"] += lag; mm = dd.merge(s.rename(columns={"ev": "prev"}), on=["repo", "key", "vi"])
        m["P(event | event %d releases ago)" % lag] = mm[mm.prev == 1].ev.mean()
        if lag == 1: m["P(event | no event 1 release ago)"] = mm[mm.prev == 0].ev.mean()
    m["lift of a past event (lag 1)"] = m["P(event | event 1 releases ago)"] / m["P(event | no event 1 release ago)"]
    fp = D.groupby(["repo", "file", "vi"]).ev.sum().rename("fe").reset_index(); fp["vi"] += 1
    own = D[["repo", "key", "vi", "ev"]].copy(); own["vi"] += 1
    mm = D[["repo", "file", "key", "vi", "ev"]].merge(fp, on=["repo", "file", "vi"], how="inner").merge(own.rename(columns={"ev": "own"}), on=["repo", "key", "vi"], how="left").fillna({"own": 0})
    mm["nb"] = mm.fe - mm.own; sub = mm[(mm.own == 0)]
    a_, b_ = sub[sub.nb > 0].ev.mean(), sub[sub.nb == 0].ev.mean(); m["same-file neighbour ratio"] = a_ / b_
    m["AUC of region size alone for an event"] = roc_auc_score(D.ev, D.nloc0)
    I = D.groupby(["repo", "key"]).agg(k=("ev", "sum"), n=("ev", "size"), size=("nloc0", "mean")); I = I[I.n >= 10]
    m["Spearman(size, event rate per instance)"] = stats.spearmanr(I["size"], I.k / I.n)[0]
    m["median size, frozen / live instances"] = I[I.k == 0]["size"].median() / I[I.k > 0]["size"].median()
    Lv = I[I.k > 0]; pooled = Lv.k.sum() / Lv.n.sum(); m["dispersion of event counts (1 = binomial)"] = Lv.k.var() / (Lv.n * pooled * (1 - pooled)).mean()
    m["share of instances with an event in > 30 % of releases"] = ((I.k / I.n) > 0.3).mean()
    m["ICC of events by instance"] = icc(L, ["repo", "key"]); m["ICC of events by release (the clock)"] = icc(D, ["repo", "vi"])
    ec = D.groupby(["repo", "key"]).apply(lambda g: pd.Series({"early": g.sort_values("vi").ev.values[: len(g) // 2].mean(), "late": g.sort_values("vi").ev.values[len(g) // 2:].mean(), "k": g.ev.sum(), "n": len(g)}))
    ec = ec[(ec.n >= 10) & (ec.k > 0)]; m["event rate, second half / first half of life"] = ec.late.mean() / ec.early.mean()
    rng = np.random.default_rng(0); res = {"persistence + size ties": [], "size only": [], "shrunk events + size ties": [], "random": []}
    P0 = D.ev.mean()
    for (repo, vi), g in D.groupby(["repo", "vi"]):
        if len(g) < 8 or g.y.sum() <= 0: continue
        y = g.y.values; sc = {"persistence + size ties": g.past_il / (g.age + 1) + 1e-9 * g.nloc0, "size only": g.nloc0.astype(float), "shrunk events + size ties": (g.past_n + 2) / (g.age + 2 / P0) + 1e-9 * g.nloc0, "random": pd.Series(rng.random(len(g)))}
        for n, s in sc.items(): res[n].append(np.mean([capture(s.values, y, 0.2, np.random.default_rng(t)) for t in range(3)]))
    for n, v in res.items(): m["capture top 20 %%: %s" % n] = np.mean(v)
    return m
panel = pd.DataFrame({"real (9 repositories)": metrics(R), "synthetic baseline (90)": metrics(SB), "synthetic, all regimes (150)": metrics(S), "pooled real + synthetic": metrics(pd.concat([R, S], ignore_index=True))})
panel.to_csv("../results/n7_panel.csv")
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 70)
P("## (A) the same metrics on real, synthetic and pooled rows"); P(panel.round(3).to_string())
# ------------------------------------------------------------------ (B) pooled training, Level 2
BASE = ["nloc0", "ccn0", "past_n", "past_il", "age", "principal_pm", "ts_shr"]
mk = lambda: GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, subsample=0.8, random_state=0)
R["persist"] = R.past_il / (R.age + 1) + 1e-9 * R.nloc0
def fit(tr, w=None): return mk().fit(tr[BASE], tr.ev, sample_weight=w)
variants = {"real only": lambda trR: (trR, None), "real + synthetic (all, weight 1)": lambda trR: (pd.concat([trR, S]), None),
            "real + synthetic (all, weight 0.3)": lambda trR: (pd.concat([trR, S]), np.r_[np.ones(len(trR)), 0.3 * np.ones(len(S))]), "synthetic only": lambda trR: (S, None)}
P("\n## (B) Level 2, pooled training, tested on the real data (capture: difference to persistence + size ties, points, 95 % interval)")
for proto in ("held-out repositories (9 folds)", "temporal"):
    pred = {k: np.zeros(len(R)) for k in variants}
    if proto.startswith("temporal"):
        cut = R.groupby("repo").vi.transform(lambda s: s.quantile(0.6)); trI, teI = np.where(R.vi <= cut)[0], np.where(R.vi > cut)[0]
        for k, f in variants.items():
            tr, w = f(R.iloc[trI]); pred[k][teI] = fit(tr, w).predict_proba(R.iloc[teI][BASE])[:, 1]
        test = np.zeros(len(R), bool); test[teI] = True
    else:
        for r in R.repo.unique():
            te = R.repo == r
            for k, f in variants.items():
                tr, w = f(R[~te]); pred[k][np.where(te)[0]] = fit(tr, w).predict_proba(R[te][BASE])[:, 1]
        test = np.ones(len(R), bool)
    T = R[test].copy()
    for k in variants: T["p_" + k] = pred[k][test]
    P("\n### " + proto + ": AUC " + "; ".join("%s %.3f" % (k, roc_auc_score(T.ev, T["p_" + k])) for k in variants) + "; persistence %.3f" % roc_auc_score(T.ev, T.persist))
    res = {k: {0.2: [], 0.3: []} for k in list(variants) + ["persistence"]}
    for (repo, vi), g in T.groupby(["repo", "vi"]):
        if len(g) < 10 or g.y.sum() <= 0: continue
        for k in res:
            s = g.persist.values if k == "persistence" else g["p_" + k].values + 1e-9 * g.nloc0.values
            for q in (0.2, 0.3): res[k][q].append(np.mean([capture(s, g.y.values, q, np.random.default_rng(t)) for t in range(3)]))
    for q in (0.2, 0.3):
        b = np.array(res["persistence"][q]); P(" top %d%% (%d groups): persistence %.1f; " % (q * 100, len(b), b.mean() * 100) + "; ".join("%s %+.1f (%+.1f, %+.1f)" % ((k,) + ((np.array(res[k][q]) - b).mean() * 100, *boot_ci((np.array(res[k][q]) - b) * 100))) for k in variants))
# ------------------------------------------------------------------ (C) pooled training, Level 1
SP = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv")); RP = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
cols = [c for c in SP.columns if c.startswith("delta__") and c in RP.columns]
unit = lambda a: a / np.where(np.linalg.norm(a, axis=1, keepdims=True) > 0, np.linalg.norm(a, axis=1, keepdims=True), 1)
XS, XR = unit(SP[cols].values.astype(float)), unit(RP[cols].values.astype(float)); ys, yr = SP.ptype.values, RP.td_type.values
proj = RP.project.values; py = (RP.language == "Python").values; nb = proj != "boltons"
P("\n## (C) Level 1: leave-one-project-out on the 61 real pairs; training = other real projects (+ the 1,321 synthetic deltas, direction only)")
for mname, mk1 in (("random forest", lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=2)), ("logistic", lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=3000, class_weight="balanced")))):
    for vname, wsyn in (("real only", None), ("real + synthetic, weight 1", 1.0), ("real + synthetic, weight 0.1", 0.1), ("synthetic only", -1)):
        pred = np.empty(len(yr), dtype=object)
        for p in np.unique(proj):
            te = proj == p; trX, trY, w = XR[~te], yr[~te], np.ones((~te).sum())
            if wsyn == -1: trX, trY, w = XS, ys, np.ones(len(ys))
            elif wsyn: trX = np.vstack([trX, XS]); trY = np.r_[trY, ys]; w = np.r_[w, wsyn * np.ones(len(ys))]
            m = mk1()
            try: m.fit(trX, trY, **({"randomforestclassifier__sample_weight": w} if mname == "logistic" else {"sample_weight": w}))
            except Exception: m.fit(trX, trY)
            pred[te] = m.predict(XR[te])
        P("  %-14s %-30s accuracy %.3f   non-boltons %.3f   Python %.3f   C/C++ %.3f" % (mname, vname, (pred == yr).mean(), (pred[nb] == yr[nb]).mean(), (pred[py] == yr[py]).mean(), (pred[~py] == yr[~py]).mean()))
P("  majority: %.3f overall, %.3f non-boltons, %.3f Python, %.3f C/C++" % (pd.Series(yr).value_counts(normalize=True).max(), pd.Series(yr[nb]).value_counts(normalize=True).max(), pd.Series(yr[py]).value_counts(normalize=True).max(), pd.Series(yr[~py]).value_counts(normalize=True).max()))
open("../results/n7_combined.txt", "w").write("\n".join(out))
