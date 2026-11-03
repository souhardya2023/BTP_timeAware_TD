"""N6: size as the prior, history as the evidence.
 prior of an instance with no events yet: p0(size) = logistic regression of 'event' on log size, fitted on the training projects (rows with no past event)
 posterior score = (events so far + a * p0) / (releases so far + a)     a = 3 fixed in advance
Compared with persistence + size ties, size only, shrunk events + size ties, size x shrunk rate.  Real and synthetic; held-out projects and temporal; AUC by age of the instance."""
import warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sload import boot_ci, capture
warnings.filterwarnings("ignore")
A = 3.0
def run(D, name, min_n):
    D = D.copy().fillna(0); P0 = D.ev.mean()
    D["persist"] = D.past_il / (D.age + 1) + 1e-9 * D.nloc0
    D["shr"] = (D.past_n + 2) / (D.age + 2 / P0) + 1e-9 * D.nloc0
    D["lsize"] = np.log1p(D.nloc0)
    D["size_shr"] = D.nloc0 * (D.past_n + 2) / (D.age + 2 / P0)
    out = []
    for proto in ("held-out projects", "temporal"):
        D["prior"] = np.nan
        if proto == "temporal":
            cut = D.groupby("repo").vi.transform(lambda s: s.quantile(0.6)); tr = D[D.vi <= cut]; te = D[D.vi > cut]
            m = LogisticRegression(C=1.0).fit(tr[tr.past_n == 0][["lsize"]], tr[tr.past_n == 0].ev); D.loc[te.index, "prior"] = m.predict_proba(te[["lsize"]])[:, 1]; test = D.index.isin(te.index)
        else:
            for r in D.repo.unique():
                tr, te = D[D.repo != r], D[D.repo == r]
                m = LogisticRegression(C=1.0).fit(tr[tr.past_n == 0][["lsize"]], tr[tr.past_n == 0].ev); D.loc[te.index, "prior"] = m.predict_proba(te[["lsize"]])[:, 1]
            test = np.ones(len(D), bool)
        T = D[test].copy()
        T["post"] = (T.past_n + A * T.prior) / (T.age + A)
        V = {"persistence + size ties": lambda g: g.persist.values, "size only": lambda g: g.nloc0.values.astype(float), "shrunk events + size ties": lambda g: g.shr.values,
             "size x shrunk rate": lambda g: g.size_shr.values, "size prior + history (posterior)": lambda g: g.post.values + 1e-9 * g.nloc0.values}
        res = {}
        for (repo, vi), g in T.groupby(["repo", "vi"]):
            if len(g) < min_n or g.y.sum() <= 0: continue
            for n, f in V.items():
                for q in (0.2, 0.3):
                    res.setdefault((n, q), []).append(np.mean([capture(f(g), g.y.values, q, np.random.default_rng(t)) for t in range(3)]))
        out.append("\n### %s, %s: %d groups; AUC: persistence %.3f, size %.3f, shrunk %.3f, posterior %.3f" % (name, proto, len(res[("size only", 0.2)]), roc_auc_score(T.ev, T.persist), roc_auc_score(T.ev, T.nloc0), roc_auc_score(T.ev, T.shr), roc_auc_score(T.ev, T.post)))
        for q in (0.2, 0.3):
            base = np.array(res[("persistence + size ties", q)])
            out.append(" top %d%% persistence %.1f; " % (q * 100, base.mean() * 100) + "; ".join("%s %+.1f (%+.1f, %+.1f)" % ((n,) + ((np.array(res[(n, q)]) - base).mean() * 100, *boot_ci((np.array(res[(n, q)]) - base) * 100))) for n in V if n != "persistence + size ties"))
        if proto == "held-out projects":
            T["ab"] = pd.cut(T.age, [-1, 1, 4, 30], labels=["age 0-1", "age 2-4", "age 5+"])
            out.append(" AUC by age of the instance: " + "; ".join("%s: persistence %.3f, size %.3f, posterior %.3f" % (a, roc_auc_score(g.ev, g.persist), roc_auc_score(g.ev, g.nloc0), roc_auc_score(g.ev, g.post)) for a, g in T.groupby("ab", observed=True) if g.ev.nunique() > 1))
    return out
R = pd.read_csv("../results/n4_rows_real.csv"); S = pd.read_csv("../results/n4_rows_synthetic.csv")
lines = run(R, "REAL", 10) + run(S[S.regime == "baseline"], "SYNTHETIC baseline", 6)
print("\n".join(lines)); open("../results/n6_size_prior.txt", "w").write("\n".join(lines))
