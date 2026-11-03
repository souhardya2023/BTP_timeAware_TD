"""S3: the time dimension, with the generator's truth.
 (a) how many releases does it take to tell a hot instance from a frozen one?  AUC of the history score for 'latent rate > 0', by age of the instance
 (b) a repayment policy: at every release repay the top k % of the live instances; interest AVOIDED = what they would have paid in all later releases
 (c) can the interest of a release be predicted from the previous releases and from what git shows (commits, lines added)?  R2 by regime, leave-one-project-out"""
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score
from sload import boot_ci, capture, manifests, releases
warnings.filterwarnings("ignore")
T = pd.read_csv("../results/s2_rows_with_scores.csv")
out = []
P = lambda s="": (out.append(s), print(s))
# ---- (a)
T["live"] = (T.latent > 0).astype(int)
T["age_bin"] = pd.cut(T.age, [-1, 0, 1, 2, 4, 8, 30], labels=["0", "1", "2", "3-4", "5-8", "9+"])
P("## (a) AUC of the history score for 'this instance is live (latent rate > 0)', baseline regime, by age (releases of history)")
B = T[T.regime == "baseline"]
for ab, g in B.groupby("age_bin", observed=True):
    if g.live.nunique() < 2:
        continue
    P("  age %-4s n=%5d   persistence %.3f   shrunk %.3f" % (ab, len(g), roc_auc_score(g.live, g.persist + 1e-9 * g.nloc0), roc_auc_score(g.live, g.shrunk + 1e-9 * g.nloc0)))
P("  share of live instances among all: %.2f" % B.live.mean())
# ---- (b)
T = T.sort_values(["repo", "key", "vi"])
T["fut"] = T.groupby(["repo", "key"]).y.transform(lambda s: s[::-1].cumsum()[::-1])         # interest of this release pair and all later ones
P("\n## (b) repayment policy: share of all FUTURE interest of the live instances avoided by repaying the top k % (by score) at each release")
rows = []
for (repo, vi), g in T.groupby(["repo", "vi"]):
    if len(g) < 6 or g.fut.sum() <= 0:
        continue
    y = g.fut.values
    for name, col in (("persistence", "persist"), ("shrunk rate", "shrunk"), ("oracle (latent rate)", "latent")):
        s = g[col].values + 1e-9 * g.nloc0.values
        for k in (0.1, 0.2, 0.3):
            rows.append(dict(repo=repo, vi=vi, regime=g.regime.iloc[0], score=name, k=k, cap=np.mean([capture(s, y, k, np.random.default_rng(t)) for t in range(3)])))
    for k in (0.1, 0.2, 0.3):
        rows.append(dict(repo=repo, vi=vi, regime=g.regime.iloc[0], score="random", k=k, cap=np.mean([capture(np.random.default_rng(t).random(len(y)), y, k, np.random.default_rng(t + 5)) for t in range(3)])))
G = pd.DataFrame(rows)
for reg in ("baseline", "ALL"):
    gr = G if reg == "ALL" else G[G.regime == reg]
    P("  %s (%d groups)" % (reg, gr.groupby(["repo", "vi"]).ngroups))
    for k in (0.1, 0.2, 0.3):
        pv = gr[gr.k == k].pivot_table(index=["repo", "vi"], columns="score", values="cap")
        line = "    top %d%%: " % (k * 100) + "  ".join("%s %.1f" % (s, pv[s].mean() * 100) for s in ("random", "persistence", "shrunk rate", "oracle (latent rate)"))
        d = (pv["shrunk rate"] - pv["persistence"]).values * 100
        P(line + "   shrunk - persistence %+.1f (%+.1f, %+.1f)" % (d.mean(), *boot_ci(d)))
# ---- (c)
M = manifests(); R = releases()
rows = []
for pid, m in M.items():
    cnt = pd.Series([c["release"] for c in m["commits"]]).value_counts()
    tot = T[T.repo == pid].groupby("vi").y.sum()
    ra = R[R.repo == pid].set_index("vi")
    for vi in range(len(m["release_table"]) - 1):
        rows.append(dict(repo=pid, regime=m["regime"], vi=vi, tot=tot.get(vi, 0.0), commits=cnt.get(vi + 2, 0), added=ra.total_added.get(vi, np.nan), true_act=m["activity"][vi + 1]))
C = pd.DataFrame(rows).sort_values(["repo", "vi"])
for c in ("tot", "commits", "added"):
    C["l" + c] = C.groupby("repo")[c].shift(1)
C["ltot_log"] = np.log1p(C.tot); C["lprev_log"] = np.log1p(C.ltot)
C = C.dropna(subset=["ltot", "lcommits", "ladded"])
P("\n## (c) predicting the total interest of a release pair (log scale) from the previous release pair; R2, leave-one-project-out (rows %d)" % len(C))
def r2(Xcols, sub):
    ys, ps = [], []
    for repo in sub.repo.unique():
        tr, te = sub[sub.repo != repo], sub[sub.repo == repo]
        m = Ridge(1.0).fit(tr[Xcols], tr.ltot_log); ps += list(m.predict(te[Xcols])); ys += list(te.ltot_log)
    ys, ps = np.array(ys), np.array(ps)
    return 1 - ((ys - ps) ** 2).sum() / ((ys - ys.mean()) ** 2).sum()
C["lprev_log"] = np.log1p(C.ltot); C["lcommits_log"] = np.log1p(C.lcommits); C["ladded_log"] = np.log1p(C.ladded)
for reg in ("baseline", "ar_clock", "ALL"):
    sub = C if reg == "ALL" else C[C.regime == reg]
    P("  %-9s n=%4d   previous interest %+.3f   previous commits %+.3f   previous lines added %+.3f   all three %+.3f" % (reg, len(sub), r2(["lprev_log"], sub), r2(["lcommits_log"], sub), r2(["ladded_log"], sub), r2(["lprev_log", "lcommits_log", "ladded_log"], sub)))
open("../results/s3_timeseries.txt", "w").write("\n".join(out))
