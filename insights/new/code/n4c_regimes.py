"""N4c: do the time-series features help in the regimes that contain the signal they are built for?
 decay -> recency features; ar_clock -> project clock features; contagion -> neighbour features.  GB with base features against base + the matching group,
 15-fold by project, trained on ALL synthetic projects (all regimes), evaluated per regime; AUC and capture in the top 20 % (paired bootstrap)."""
import warnings
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sload import boot_ci, capture
warnings.filterwarnings("ignore")
D = pd.read_csv("../results/n4_rows_synthetic.csv").fillna(0)
BASE = ["nloc0", "ccn0", "past_n", "past_il", "age", "principal_pm"]
TS = ["ts_ev", "ts_shr", "ts_l1", "ts_l3", "ts_l5", "ts_gap", "ts_gap_mean", "ts_gap_cv", "ts_run", "ts_maxrun", "ts_trend", "ts_ew", "ts_first", "ts_il_per_ev", "ts_ac1", "ts_chg_share"]
CLK = ["clk_a1", "clk_a3", "clk_trend", "clk_pshare1", "clk_pshare3"]; NBR = ["nbr_1", "nbr_3"]
SETS = {"base": BASE, "+ time series": BASE + TS, "+ clock": BASE + CLK, "+ neighbours": BASE + NBR, "all": BASE + TS + CLK + NBR}
mk = lambda: GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, subsample=0.8, random_state=0)
pred = {k: np.zeros(len(D)) for k in SETS}
for tr, te in GroupKFold(15).split(D, groups=D.repo):
    for k, c in SETS.items():
        pred[k][te] = mk().fit(D.iloc[tr][c], D.iloc[tr].ev).predict_proba(D.iloc[te][c])[:, 1]
for k in SETS:
    D["p_" + k] = pred[k]
D["persist"] = D.past_il / (D.age + 1) + 1e-9 * D.nloc0
out = []
P = lambda s="": (out.append(s), print(s, flush=True))
P("regime      AUC: " + "  ".join("%s" % k for k in SETS) + "  persistence | top 20 %: difference to base (points, 95 % interval)")
for reg in ["baseline", "decay", "ar_clock", "contagion", "sticky"]:
    G = D[D.regime == reg]
    auc = "  ".join("%.3f" % roc_auc_score(G.ev, G["p_" + k]) for k in SETS) + "  %.3f" % roc_auc_score(G.ev, G.persist)
    res = {k: [] for k in SETS}
    for (repo, vi), g in G.groupby(["repo", "vi"]):
        if len(g) < 6 or g.y.sum() <= 0:
            continue
        for k in SETS:
            res[k].append(np.mean([capture(g["p_" + k].values + 1e-9 * g.nloc0.values, g.y.values, 0.2, np.random.default_rng(t)) for t in range(3)]))
    b = np.array(res["base"])
    cap = "  ".join("%s %+.1f (%+.1f, %+.1f)" % ((k, ) + ((np.array(res[k]) - b).mean() * 100, *boot_ci((np.array(res[k]) - b) * 100))) for k in SETS if k != "base")
    P("%-10s %s | %d groups, base %.1f | %s" % (reg, auc, len(b), b.mean() * 100, cap))
open("../results/n4c_regimes.txt", "w").write("\n".join(out))
