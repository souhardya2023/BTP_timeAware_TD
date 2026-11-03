"""N4b: does the time-series signal of the git history help?  Gradient boosting with feature groups added one by one, on the real and the synthetic histories,
under held-out projects (real: leave one repository out, 9 folds; synthetic: 15 folds by project) and the temporal protocol (first 60 % of each project's releases train).
Metrics: AUC for 'interest in this release pair', and capture in the top 20 / 30 % against persistence with size ties (paired bootstrap)."""
import os, sys, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sload import boot_ci, capture
warnings.filterwarnings("ignore")
BASE = ["nloc0", "ccn0", "past_n", "past_il", "age", "principal_pm"]
TS = [c for c in ["ts_ev", "ts_shr", "ts_l1", "ts_l3", "ts_l5", "ts_gap", "ts_gap_mean", "ts_gap_cv", "ts_run", "ts_maxrun", "ts_trend", "ts_ew", "ts_first", "ts_il_per_ev", "ts_ac1", "ts_chg_share"]]
CLK = ["clk_a1", "clk_a3", "clk_trend", "clk_pshare1", "clk_pshare3"]
NBR = ["nbr_1", "nbr_3"]
SETS = {"base (size, age, past events)": BASE, "+ instance time series": BASE + TS, "+ project clock": BASE + CLK, "+ neighbours": BASE + NBR, "all": BASE + TS + CLK + NBR}
mk = lambda: GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, subsample=0.8, random_state=0)
out = []
P = lambda s="": (out.append(s), print(s, flush=True))
def run(D, name, min_n, folds):
    D = D.copy().fillna(0)
    D["persist"] = D.past_il / (D.age + 1) + 1e-9 * D.nloc0
    for proto in ("held-out projects", "temporal"):
        pred = {k: np.full(len(D), np.nan) for k in SETS}
        if proto == "temporal":
            cut = D.groupby("repo").vi.transform(lambda s: s.quantile(0.6))
            tr, te = np.where(D.vi <= cut)[0], np.where(D.vi > cut)[0]
            for k, cols in SETS.items():
                pred[k][te] = mk().fit(D.iloc[tr][cols], D.iloc[tr].ev).predict_proba(D.iloc[te][cols])[:, 1]
            test = np.zeros(len(D), bool); test[te] = True
        else:
            for tr, te in GroupKFold(folds).split(D, groups=D.repo):
                for k, cols in SETS.items():
                    pred[k][te] = mk().fit(D.iloc[tr][cols], D.iloc[tr].ev).predict_proba(D.iloc[te][cols])[:, 1]
            test = np.ones(len(D), bool)
        res = {}
        T = D[test]
        for k in SETS:
            T = T.assign(**{"p_" + k: pred[k][test]})
        P("\n### %s, %s" % (name, proto))
        P("AUC for 'interest in this release pair': " + "; ".join("%s %.3f" % (k, roc_auc_score(T.ev, T["p_" + k])) for k in SETS) + "; persistence %.3f" % roc_auc_score(T.ev, T.persist))
        for (repo, vi), g in T.groupby(["repo", "vi"]):
            if len(g) < min_n or g.y.sum() <= 0:
                continue
            y = g.y.values
            for k in list(SETS) + ["persistence"]:
                s = g.persist.values if k == "persistence" else g["p_" + k].values + 1e-9 * g.nloc0.values
                for q in (0.2, 0.3):
                    res.setdefault((k, q), []).append(np.mean([capture(s, y, q, np.random.default_rng(t)) for t in range(3)]))
        for q in (0.2, 0.3):
            base = np.array(res[("persistence", q)])
            P("top %d%% (%d groups): persistence %.1f" % (q * 100, len(base), base.mean() * 100) + "; " + "; ".join("%s %+.1f (%+.1f, %+.1f)" % ((k, ) + ((np.array(res[(k, q)]) - base).mean() * 100, *(boot_ci((np.array(res[(k, q)]) - base) * 100)))) for k in SETS))
        if proto == "held-out projects":
            m = mk().fit(D[BASE + TS + CLK + NBR], D.ev)
            imp = pd.Series(m.feature_importances_, index=BASE + TS + CLK + NBR).sort_values(ascending=False)
            P("most used features (all data): " + ", ".join("%s %.2f" % (k, v) for k, v in imp.head(8).items()))
R = pd.read_csv("../results/n4_rows_real.csv"); S = pd.read_csv("../results/n4_rows_synthetic.csv")
run(R, "REAL", 10, 9)
run(S[S.regime == "baseline"], "SYNTHETIC baseline", 6, 15)
run(S, "SYNTHETIC all regimes", 6, 15)
open("../results/n4b_ts_models.txt", "w").write("\n".join(out))
