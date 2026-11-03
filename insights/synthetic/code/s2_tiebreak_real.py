"""S2d: on the REAL histories, how much of the earlier 'hotness beats persistence' gain is only the tie-break by region size?"""
import os, sys, warnings
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))
from common import load_transitions, boot_ci, capture
warnings.filterwarnings("ignore")
R = load_transitions(); R["ev"] = R["any"]
P0 = R.ev.mean()
V = {"persistence, ties at random": lambda g: (g.past_il / (g.age + 1)).values,
     "persistence + size tie-break": lambda g: (g.past_il / (g.age + 1)).values + 1e-9 * g.nloc0.values,
     "shrunk events (a=2) + size tie-break": lambda g: ((g.past_n + 2) / (g.age + 2 / P0)).values + 1e-9 * g.nloc0.values,
     "size only (largest region first)": lambda g: g.nloc0.values.astype(float),
     "random": lambda g: np.random.default_rng(1).random(len(g))}
ks = [0.2, 0.3, 0.5]
res = {}
for (repo, vi), g in R.groupby(["repo", "vi"]):
    if len(g) < 10 or g.y.sum() <= 0:
        continue
    y = g.y.values
    for n, f in V.items():
        for k in ks:
            res.setdefault((n, k), []).append(np.mean([capture(f(g), y, k, np.random.default_rng(t)) for t in range(6)]))
out = ["real histories, %d groups; capture in the top k %% (difference to 'persistence, ties at random', points, 95 %% interval)" % len(res[("random", 0.2)])]
for k in ks:
    out.append("top %d%%" % (k * 100))
    base = np.array(res[("persistence, ties at random", k)])
    for n in V:
        a = np.array(res[(n, k)]); d = (a - base) * 100
        out.append("  %-40s %5.1f   %+5.1f (%+.1f, %+.1f)" % (n, a.mean() * 100, d.mean(), *boot_ci(d)))
open("../results/s2_tiebreak_real.txt", "w").write("\n".join(out)); print("\n".join(out))
