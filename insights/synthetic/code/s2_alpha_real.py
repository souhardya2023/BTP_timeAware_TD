"""S2c: choose the shrinkage strength alpha on the SYNTHETIC baseline projects, then test that one value on the REAL histories (never tuned on them)."""
import os, sys, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
from sload import boot_ci, capture
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))
from common import load_transitions            # real data (insights/code/common.py)

def evaluate(D, alphas, ks, min_n):
    P0 = D.ev.mean()
    res = {}
    for (repo, vi), gg in D.groupby(["repo", "vi"]):
        if len(gg) < min_n or gg.y.sum() <= 0:
            continue
        y = gg.y.values
        sc = {"persistence": (gg.past_il / (gg.age + 1)).values}
        for a in alphas:
            sc["a=%g" % a] = ((gg.past_n + a) / (gg.age + a / P0)).values
        for n, s in sc.items():
            s = s + 1e-9 * gg.nloc0.values
            for k in ks:
                res.setdefault((n, k), []).append(np.mean([capture(s, y, k, np.random.default_rng(t)) for t in range(4)]))
    return res

alphas = [0.25, 0.5, 1, 2, 4, 8, 16]
ks = [0.2, 0.3, 0.5]
out = []
P = lambda s="": (out.append(s), print(s))
S = pd.read_csv("../results/s2_rows_with_scores.csv")
Sb = S[S.regime == "baseline"]
rs = evaluate(Sb, alphas, ks, 6)
P("## synthetic baseline projects (%d groups): difference to persistence, top 20 %%" % len(rs[("persistence", 0.2)]))
best, bv = None, -9
for a in alphas:
    d = (np.array(rs[("a=%g" % a, 0.2)]) - np.array(rs[("persistence", 0.2)])) * 100
    P("  alpha %-5g %+5.1f (%+.1f, %+.1f)" % (a, d.mean(), *boot_ci(d)))
    if d.mean() > bv:
        best, bv = a, d.mean()
P("chosen on the synthetic baseline: alpha = %g" % best)
Rl = load_transitions(); Rl["ev"] = Rl["any"]
rr = evaluate(Rl, [best], ks, 10)
P("\n## real histories, 9 repositories (%d groups), alpha = %g fixed in advance" % (len(rr[("persistence", 0.2)]), best))
for k in ks:
    d = (np.array(rr[("a=%g" % best, k)]) - np.array(rr[("persistence", k)])) * 100
    P("  top %2d%%: persistence %.1f, shrunk %.1f, difference %+5.1f (%+.1f, %+.1f)" % (k * 100, np.mean(rr[("persistence", k)]) * 100, np.mean(rr[("a=%g" % best, k)]) * 100, d.mean(), *boot_ci(d)))
open("../results/s2_alpha_real.txt", "w").write("\n".join(out))
