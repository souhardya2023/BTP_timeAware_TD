"""S2e: size (exposure) against history. Real histories and synthetic histories.
 rules: size only | persistence + size tie-break | shrunk events + size tie-break | size x shrunk rate | learned (GB on size, ccn, past events, age; leave-one-project-out)
 For the synthetic data the same rules, per regime group."""
import os, sys, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GroupKFold
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))
from common import load_transitions, boot_ci, capture

def prep(D):
    D = D.copy()
    P0 = D.ev.mean()
    D["persist"] = D.past_il / (D.age + 1)
    D["shr"] = (D.past_n + 2) / (D.age + 2 / P0)
    D["size_shr"] = D.nloc0 * D.shr
    D["lsize"] = np.log1p(D.nloc0)
    FE = ["nloc0", "ccn0", "past_n", "past_il", "age", "shr", "principal_pm"]
    D["learned"] = np.nan
    for tr, te in GroupKFold(5).split(D, groups=D.repo):
        m = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0).fit(D.iloc[tr][FE], D.iloc[tr].ev)
        D.loc[D.index[te], "learned"] = m.predict_proba(D.iloc[te][FE])[:, 1]
    return D
def run(D, min_n, label, out):
    V = {"persistence + size tie-break": lambda g: g.persist.values + 1e-9 * g.nloc0.values, "size only": lambda g: g.nloc0.values.astype(float),
         "shrunk events + size tie-break": lambda g: g.shr.values + 1e-9 * g.nloc0.values, "size x shrunk rate": lambda g: g.size_shr.values,
         "learned (GB, other projects)": lambda g: g.learned.values, "random": lambda g: np.random.default_rng(2).random(len(g))}
    ks = [0.2, 0.3, 0.5]
    res = {}
    for (repo, vi), g in D.groupby(["repo", "vi"]):
        if len(g) < min_n or g.y.sum() <= 0:
            continue
        y = g.y.values
        for n, f in V.items():
            for k in ks:
                res.setdefault((n, k), []).append(np.mean([capture(f(g), y, k, np.random.default_rng(t)) for t in range(4)]))
    out.append("\n### %s: %d groups; capture (difference to 'persistence + size tie-break', points, 95 %% interval)" % (label, len(res[("random", 0.2)])))
    for k in ks:
        out.append(" top %d%%" % (k * 100))
        base = np.array(res[("persistence + size tie-break", k)])
        for n in V:
            a = np.array(res[(n, k)]); d = (a - base) * 100
            out.append("   %-34s %5.1f   %+5.1f (%+.1f, %+.1f)" % (n, a.mean() * 100, d.mean(), *boot_ci(d)))
out = []
R = load_transitions(); R["ev"] = R["any"]; R["y"] = R.pm_interest * 1000
run(prep(R), 10, "REAL histories", out)
S = pd.read_csv("../results/s2_rows_with_scores.csv")
Sp = prep(S)
run(Sp[Sp.regime == "baseline"], 6, "SYNTHETIC baseline", out)
run(Sp, 6, "SYNTHETIC all regimes", out)
# does size predict events at all?  AUC of size alone
from sklearn.metrics import roc_auc_score
out.append("\n### AUC of region size alone for 'interest in this release pair'")
out.append("  real: %.3f   synthetic: %.3f" % (roc_auc_score(R.ev, R.nloc0), roc_auc_score(S.ev, S.nloc0)))
Rg = R.groupby(["repo", "key"]).agg(n=("ev", "sum"), s=("nloc0", "mean"), e=("ev", "size")).reset_index()
Sg = S.groupby(["repo", "key"]).agg(n=("ev", "sum"), s=("nloc0", "mean"), e=("ev", "size")).reset_index()
from scipy.stats import spearmanr
out.append("  Spearman(size, events per release) over instances: real %.3f   synthetic %.3f" % (spearmanr(Rg.s, Rg.n / Rg.e)[0], spearmanr(Sg.s, Sg.n / Sg.e)[0]))
open("../results/s2_size.txt", "w").write("\n".join(out)); print("\n".join(out))
