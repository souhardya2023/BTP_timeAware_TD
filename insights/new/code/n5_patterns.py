"""N5: patterns in the histories (no model).  Real (9 repositories) against synthetic baseline.
 (1) overdispersion: is the number of events of an instance more variable than chance (Fano factor, instances with >= 10 releases)?
 (2) gaps between events: geometric (memoryless) or not?  runs of consecutive events against what chance gives
 (3) lifecycle archetypes: k-means on per-instance shape features (event rate, early/late rates, burstiness, first-event delay) -> the shapes that exist
 (4) active window: do events of an instance cluster in one window of its life?
 (5) which static properties relate to the archetype (size, rule)"""
import warnings
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import stats
warnings.filterwarnings("ignore")
R = pd.read_csv("../results/n4_rows_real.csv"); S = pd.read_csv("../results/n4_rows_synthetic.csv"); S = S[S.regime == "baseline"]
out = []
P = lambda s="": (out.append(s), print(s))
def instances(D, minlen=10):
    rows = []
    for (repo, key), g in D.sort_values("vi").groupby(["repo", "key"]):
        e = g.ev.values
        if len(e) < minlen:
            continue
        n = len(e); k = e.sum()
        idx = np.where(e == 1)[0]
        half = n // 2
        gaps = np.diff(idx)
        runs = []; c = 0
        for v in e:
            if v: c += 1
            else:
                if c: runs.append(c)
                c = 0
        if c: runs.append(c)
        rows.append(dict(repo=repo, key=key, n=n, k=int(k), rate=k / n, early=e[:half].mean(), late=e[half:].mean(), first=(idx[0] / n if k else 1.0), span=((idx[-1] - idx[0]) / n if k > 1 else 0.0),
                         maxrun=max(runs) if runs else 0, nruns=len(runs), gaps_mean=gaps.mean() if len(gaps) else np.nan, size=g.nloc0.mean(), rule=g.rule.iloc[0] if "rule" in g else "", live=int(k > 0)))
    return pd.DataFrame(rows)
IR, IS = instances(R), instances(S)
P("instances with >= 10 releases: real %d, synthetic baseline %d" % (len(IR), len(IS)))
# (1) overdispersion among instances that have any event
for nm, I in (("real", IR), ("synthetic", IS)):
    L = I[I.k > 0]
    p = (L.k / L.n)
    expected_var = (L.n * p * (1 - p)).mean()          # binomial variance given each instance's own rate would be... use pooled rate instead
    pooled = L.k.sum() / L.n.sum()
    obs = L.k.var(); exp = (L.n * pooled * (1 - pooled)).mean()
    P("(1) %-9s events per instance (instances with an event): mean %.2f, variance %.2f, binomial variance at the pooled rate %.2f -> dispersion %.2f" % (nm, L.k.mean(), obs, exp, obs / exp))
# (2) run lengths: observed number of runs against expected under independence given k and n
def runs_test(I):
    z = []
    for _, r in I[(I.k >= 3) & (I.k <= I.n - 3)].iterrows():
        n, k, nr = r.n, r.k, r.nruns
        mu = 1 + 2 * k * (n - k) / n; var = 2 * k * (n - k) * (2 * k * (n - k) - n) / (n ** 2 * (n - 1))
        # runs of events: the Wald-Wolfowitz runs of both symbols is 2*nruns (+-1)
        if var > 0:
            z.append((2 * nr - mu) / np.sqrt(var))
    return np.array(z)
for nm, I in (("real", IR), ("synthetic", IS)):
    z = runs_test(I)
    P("(2) %-9s Wald-Wolfowitz z of the number of event runs (negative = events clumped): mean %.2f, share with z < -1.64: %.2f (n=%d)" % (nm, z.mean(), (z < -1.64).mean(), len(z)))
# gap distribution: geometric?  compare mean gap with 1/p
for nm, I in (("real", IR), ("synthetic", IS)):
    L = I[I.k >= 3]
    P("    %-9s median max run of consecutive events %.0f; mean gap between events %.2f releases; implied mean gap if memoryless %.2f" % (nm, L.maxrun.median(), L.gaps_mean.mean(), (1 / (L.k / L.n)).mean()))
# (4) active window: span of events relative to life, among instances with >= 3 events
for nm, I in (("real", IR), ("synthetic", IS)):
    L = I[I.k >= 3]
    exp_span = np.mean([(L.k.iloc[i] - 1) / (L.k.iloc[i] + 1) for i in range(len(L))])
    P("(4) %-9s events span %.2f of the life (instances with >= 3 events, n=%d); uniformly placed events would span about %.2f" % (nm, L.span.mean(), len(L), exp_span))
# early against late
for nm, I in (("real", IR), ("synthetic", IS)):
    L = I[I.k > 0]
    P("    %-9s event rate in the first half of the life %.3f, in the second half %.3f (Wilcoxon p=%.3g, n=%d)" % (nm, L.early.mean(), L.late.mean(), stats.wilcoxon(L.early, L.late).pvalue, len(L)))
# (3) archetypes
P("\n(3) lifecycle archetypes (k-means, k=4, on rate, early, late, first-event position, span, longest run), instances with >= 10 releases")
feat = ["rate", "early", "late", "first", "span", "maxrun"]
for nm, I in (("real", IR), ("synthetic", IS)):
    Z = StandardScaler().fit_transform(I[feat]); km = KMeans(4, n_init=10, random_state=0).fit(Z)
    I = I.assign(c=km.labels_)
    g = I.groupby("c").agg(n=("key", "size"), rate=("rate", "mean"), early=("early", "mean"), late=("late", "mean"), first=("first", "mean"), maxrun=("maxrun", "mean"), size=("size", "median"))
    g["share"] = g.n / g.n.sum()
    g = g.sort_values("rate")
    names = []
    for c, r in g.iterrows():
        names.append("frozen" if r.rate == 0 else ("dormant after activity" if r.early > 2 * r.late + 0.02 else ("late awakening" if r.late > 2 * r.early + 0.02 else ("hot, persistent" if r.rate > 0.3 else "occasional"))))
    g["archetype"] = names
    P("  " + nm); P(g.round(3).to_string())
    I.to_csv("../results/n5_archetypes_%s.csv" % nm, index=False)
# (5) static properties of archetypes: frozen against size
for nm, I in (("real", IR), ("synthetic", IS)):
    P("(5) %-9s size of frozen instances (median) %.0f, of live instances %.0f; Mann-Whitney p=%.3g" % (nm, I[I.live == 0]["size"].median(), I[I.live == 1]["size"].median(), stats.mannwhitneyu(I[I.live == 0]["size"], I[I.live == 1]["size"]).pvalue))
open("../results/n5_patterns.txt", "w").write("\n".join(out))
