"""L2-F: 'when' versus 'where'. Is the interest of an instance driven by the instance, or by a release-wide clock shared by all instances?
 ICC of the event indicator by (repo, release) compared with by instance; autocorrelation of the release totals within each project; and the share of
 the release clock that the number of tracked changes in the previous release explains."""
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
    return (msb - msw) / (msb + (n0 - 1) * msw), k
out = []
P = lambda s: (out.append(s), print(s))
cnt = T.groupby(["repo", "key"]).size()
D = T.set_index(["repo", "key"]).loc[cnt[cnt >= 10].index].reset_index()
P(f"ICC of the event indicator: by instance {icc(D, ['repo','key'])[0]:.3f}; by (repository, release) {icc(T, ['repo','vi'])[0]:.3f}; by repository {icc(T, 'repo')[0]:.3f}")
rel = T.groupby(["repo", "vi"]).agg(n=("ev", "size"), rate=("ev", "mean"), tot=("y", "sum")).reset_index()
rel["lag_rate"] = rel.groupby("repo").rate.shift(1)
rel["lag_tot"] = rel.groupby("repo").tot.shift(1)
r = rel.dropna().copy()
r["ltot"] = np.log1p(r.tot); r["llag"] = np.log1p(r.lag_tot)
dm = lambda s: s - r.groupby("repo")[s.name].transform("mean")
P(f"within-project correlation of the release event rate with the previous release's: {np.corrcoef(dm(r.rate), dm(r.lag_rate))[0,1]:.2f} (n={len(r)} releases)")
P(f"within-project correlation of log release total interest with the previous release's: {np.corrcoef(dm(r.ltot), dm(r.llag))[0,1]:.2f}")
open("../results/l2_release_clock.txt", "w").write("\n".join(out))
