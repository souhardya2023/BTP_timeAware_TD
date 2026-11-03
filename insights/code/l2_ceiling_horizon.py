"""Insight L2-C: is the ranking limited by what we know (estimation) or by chance (intrinsic)?
 (a) ceiling: rank instances by their TRUE long-run interest rate (the mean over all OTHER releases; this uses the future, so no real method can have it) and
     measure capture of the next release. Whatever is left to the oracle sorted by the realised value is randomness.
 (b) horizon: capture of the interest over the next h releases instead of the next one.
"""
import numpy as np
import pandas as pd
from common import boot_ci, capture, load_transitions

T = load_transitions().sort_values(["repo", "key", "vi"])
P0 = (T.interest_lines > 0).mean()
T["persist"] = T.past_il / (T.age + 1)
T["rate"] = (T.past_n + 2) / (T.age + 2 / P0)
# interest of the instance in every release pair, wide table
W = T.pivot_table(index=["repo", "key"], columns="vi", values="y", aggfunc="sum")
cols = sorted(W.columns)
T["tot_other"] = [np.nan] * len(T)
tot = W.sum(axis=1)
cnt = W.notna().sum(axis=1)
Y = {(r, k): W.loc[(r, k)] for (r, k) in W.index}
tt = T.set_index(["repo", "key"])
T["tot_other"] = (tot.reindex(tt.index).values - T.y.values)
T["n_other"] = (cnt.reindex(tt.index).values - 1)
T["oracle_rate"] = T.tot_other / T.n_other.clip(lower=1)

key_all = {(r, k, v): y for r, k, v, y in zip(T.repo, T.key, T.vi, T.y)}
def oracle_h(T, h):
    """long-run rate of the instance over the releases OUTSIDE the target window [vi, vi+h-1] (clean ceiling: nothing of the target period is used)."""
    res = []
    for r, k, v, tot_, n_ in zip(T.repo, T.key, T.vi, tot.reindex(tt.index).values, cnt.reindex(tt.index).values):
        inside = [key_all[(r, k, v + j)] for j in range(h) if (r, k, v + j) in key_all]
        res.append((tot_ - sum(inside)) / max(1, n_ - len(inside)))
    return np.array(res)

def target(T, h):
    out = np.zeros(len(T))
    key = {(r, k, v): y for r, k, v, y in zip(T.repo, T.key, T.vi, T.y)}
    return np.array([sum(key.get((r, k, v + j), 0.0) for j in range(h)) for r, k, v in zip(T.repo, T.key, T.vi)])

KS = [0.1, 0.2, 0.3, 0.5]
rows = []
for h in (1, 2, 3, 5):
    T[f"y{h}"] = target(T, h)
    T["oracle_rate"] = oracle_h(T, h)
    for (repo, vi), g in T.groupby(["repo", "vi"]):
        # complete horizon only: the last releases have no full future
        if vi + h - 1 > T[T.repo == repo].vi.max() or len(g) < 10 or g[f"y{h}"].sum() <= 0:
            continue
        y = g[f"y{h}"].values
        for name, s in (("persistence", g.persist.values), ("shrunk rate", g.rate.values), ("oracle long-run rate", g.oracle_rate.values), ("random", np.random.default_rng(0).random(len(g)))):
            caps = [np.mean([capture(s, y, k, np.random.default_rng(t)) for t in range(5)]) for k in KS]
            rows.append(dict(h=h, repo=repo, vi=vi, score=name, **{f"cap{int(k*100)}": c for k, c in zip(KS, caps)}))
        caps = [np.sort(y)[::-1][:max(1, int(np.ceil(k * len(y))))].sum() / y.sum() for k in KS]
        rows.append(dict(h=h, repo=repo, vi=vi, score="oracle (realised value)", **{f"cap{int(k*100)}": c for k, c in zip(KS, caps)}))
R = pd.DataFrame(rows)
R.to_csv("../results/l2_ceiling_horizon_per_group.csv", index=False)
S = R.groupby(["h", "score"])[[f"cap{int(k*100)}" for k in KS]].mean().mul(100).round(1)
S["groups"] = R.groupby(["h", "score"]).size().values
S.to_csv("../results/l2_ceiling_horizon.csv")
print(S.to_string())
open("../results/l2_ceiling_horizon.txt", "w").write(S.to_string())
