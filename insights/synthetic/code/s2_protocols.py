"""S2f: Level 2 (ranking debt inside a release) under the protocols of the talk, on the synthetic AND the real histories.
 leave-one-project-out: one whole project held out (150 folds synthetic, 9 real); temporal: releases up to the 60th percentile of each project train, later releases test (all projects pooled).
 Scores: persistence + size ties | size only | shrunk events + size ties | size x shrunk rate | learned (gradient boosting, trained under the protocol) | oracle latent rate (synthetic only).
 Metrics: capture of the interest of the release pair in the top 20 % and 30 % (paired bootstrap against persistence + size ties) and the AUC of the learned model for 'interest in this release pair'."""
import os, sys, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))
from common import load_transitions, boot_ci, capture

def prep(D):
    D = D.copy(); P0 = D.ev.mean()
    D["persist"] = D.past_il / (D.age + 1)
    D["shr"] = (D.past_n + 2) / (D.age + 2 / P0)
    D["size_shr"] = D.nloc0 * D.shr
    return D
FE = ["nloc0", "ccn0", "past_n", "past_il", "age", "shr", "principal_pm"]
def learn(D, proto):
    D = D.copy(); D["learned"] = np.nan
    mk = lambda: GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, subsample=0.8, random_state=0)
    if proto == "temporal":
        cut = D.groupby("repo").vi.transform(lambda s: s.quantile(0.6))
        tr, te = D[D.vi <= cut], D[D.vi > cut]
        D.loc[te.index, "learned"] = mk().fit(tr[FE], tr.ev).predict_proba(te[FE])[:, 1]
        D["is_test"] = D.vi > cut
    else:
        for r in D.repo.unique():
            tr, te = D[D.repo != r], D[D.repo == r]
            D.loc[te.index, "learned"] = mk().fit(tr[FE], tr.ev).predict_proba(te[FE])[:, 1]
        D["is_test"] = True
    return D
def evaluate(D, min_n, label, out, oracle=False):
    V = {"random": lambda g: np.random.default_rng(3).random(len(g)), "persistence + size ties": lambda g: g.persist.values + 1e-9 * g.nloc0.values,
         "size only": lambda g: g.nloc0.values.astype(float), "shrunk events + size ties": lambda g: g.shr.values + 1e-9 * g.nloc0.values,
         "size x shrunk rate": lambda g: g.size_shr.values, "learned (GB)": lambda g: g.learned.values}
    if oracle:
        V["oracle (latent rate)"] = lambda g: g.latent.values
    ks = [0.2, 0.3]; res = {}
    T = D[D.is_test]
    for (repo, vi), g in T.groupby(["repo", "vi"]):
        if len(g) < min_n or g.y.sum() <= 0:
            continue
        y = g.y.values
        for n, f in V.items():
            for k in ks:
                res.setdefault((n, k), []).append(np.mean([capture(f(g), y, k, np.random.default_rng(t)) for t in range(3)]))
    auc = roc_auc_score(T.ev, T.learned)
    out.append("\n### %s: %d groups; learned AUC for 'interest in this release pair' %.3f" % (label, len(res[("random", 0.2)]), auc))
    for k in ks:
        out.append(" top %d%%: capture (difference to persistence + size ties, points, 95 %% interval)" % (k * 100))
        base = np.array(res[("persistence + size ties", k)])
        for n in V:
            a = np.array(res[(n, k)]); d = (a - base) * 100
            out.append("   %-28s %5.1f   %+5.1f (%+.1f, %+.1f)" % (n, a.mean() * 100, d.mean(), *boot_ci(d)))
out = []
S = pd.read_csv("../results/s2_rows_with_scores.csv"); S["latent"] = S.latent.astype(float)
S = prep(S)
Rl = load_transitions(); Rl["ev"] = Rl["any"]; Rl["y"] = Rl.pm_interest * 1000
Rl = prep(Rl)
for label, D, mn, orc in (("SYNTHETIC, all regimes", S, 6, True), ("SYNTHETIC, baseline regime", S[S.regime == "baseline"], 6, True), ("REAL, 9 repositories", Rl, 10, False)):
    for proto in ("leave-one-project-out", "temporal"):
        Dl = learn(D if not label.endswith("regime") else D, "temporal" if proto == "temporal" else "lopo")
        evaluate(Dl, mn, "%s, %s" % (label, proto), out, orc)
open("../results/s2_protocols.txt", "w").write("\n".join(out)); print("\n".join(out))
