"""Insight L2-D: how much of 'does this instance pay interest in a release' is a property of the instance (hot spot) and how much is timing?
ICC (one-way random effects) of the event indicator over instances with >= 10 releases; compared with the ICC of the repository alone.
Also the distribution of per-instance event rates: one population or a mixture of frozen and hot instances?"""
import numpy as np
import pandas as pd
from common import load_transitions

T = load_transitions()
T["ev"] = T["any"]
def icc(D, by):
    g = D.groupby(by)["ev"]
    n, m = g.size(), g.mean()
    N, k, gm = len(D), len(n), D.ev.mean()
    msb = (n * (m - gm) ** 2).sum() / (k - 1)
    msw = ((D.ev - g.transform("mean")) ** 2).sum() / (N - k)
    n0 = (N - (n ** 2).sum() / N) / (k - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw), k, N
cnt = T.groupby(["repo", "key"]).size()
ok = cnt[cnt >= 10].index
D = T.set_index(["repo", "key"]).loc[ok].reset_index()
out = []
i1 = icc(D, ["repo", "key"]); i2 = icc(D, "repo"); i3 = icc(D, ["repo", "file"])
out.append(f"instances with >=10 releases: {i1[1]} ({i1[2]} instance-releases)")
out.append(f"ICC of the event indicator by instance: {i1[0]:.3f}; by file: {i3[0]:.3f}; by repository: {i2[0]:.3f}")
rate = D.groupby(["repo", "key"]).ev.mean()
bins = pd.cut(rate, [-0.001, 0, 0.05, 0.15, 0.3, 0.6, 1.0])
out.append("distribution of per-instance event rate (share of releases with interest):\n" + bins.value_counts().sort_index().to_string())
share = D.groupby(pd.cut(D.groupby(["repo", "key"]).ev.transform("mean"), [-0.001, 0, 0.05, 0.15, 0.3, 0.6, 1.0])).ev.sum()
out.append("share of all events by rate class:\n" + (share / share.sum()).round(3).to_string())
open("../results/l2_icc.txt", "w").write("\n".join(out))
print("\n".join(out))
rate.to_csv("../results/l2_instance_rates.csv")
