"""Evaluate interest-based prioritisation: rank debt instances in each (repo, release)
by predicted interest, measure how much of the realised next-release interest the top-k% captures."""
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

HERE = Path(__file__).parent
SRC = HERE.parent / "interest_exp/results/pm_predictions.csv"
KS = [0.05, 0.10, 0.20, 0.30]
rng = np.random.default_rng(0)
d = pd.read_csv(SRC)

def rank_order(pred, rand):
    # descending predicted; ties broken randomly (rand is a fixed random vector)
    return np.lexsort((rand, -pred))

def group_metrics(g, model):
    a = g.actual_mPM.to_numpy(); p = g.predicted_mPM.to_numpy()
    n = len(a); tot = a.sum()
    rand = rng.random(n)
    o = rank_order(p, rand)
    out = {}
    for k in KS:
        m = max(1, int(np.ceil(k * n)))
        out[f"cap{int(k*100)}"] = a[o[:m]].sum() / tot
        out[f"prec{int(k*100)}"] = (a[o[:m]] > 0).mean()
        out[f"orac{int(k*100)}"] = np.sort(a)[::-1][:m].sum() / tot
        out[f"base{int(k*100)}"] = (a > 0).mean()
    m = max(1, int(np.ceil(0.2 * n)))
    disc = 1 / np.log2(np.arange(2, m + 2))
    dcg = (a[o[:m]] * disc).sum(); idcg = (np.sort(a)[::-1][:m] * disc).sum()
    out["ndcg20"] = dcg / idcg
    out["rho"] = spearmanr(p, a)[0] if p.std() > 0 else 0.0
    out["n"] = n; out["tot"] = tot
    return out

rows = []
for (proto, model, repo, vi), g in d.groupby(["protocol", "model", "repo", "vi"]):
    if g.actual_mPM.sum() <= 0 or len(g) < 10:
        continue
    rows.append(dict(protocol=proto, model=model, repo=repo, vi=vi, **group_metrics(g, model)))
G = pd.DataFrame(rows)
G.to_csv(HERE / "data/prioritization_per_group.csv", index=False)

def boot(x, B=2000):
    x = np.asarray(x); idx = rng.integers(0, len(x), (B, len(x)))
    m = x[idx].mean(1); return np.percentile(m, [2.5, 97.5])

res = []
for (proto, model), g in G.groupby(["protocol", "model"]):
    r = dict(protocol=proto, model=model, groups=len(g))
    for k in KS:
        c = f"cap{int(k*100)}"
        r[c] = g[c].mean(); lo, hi = boot(g[c]); r[c + "_lo"], r[c + "_hi"] = lo, hi
        r[f"prec{int(k*100)}"] = g[f"prec{int(k*100)}"].mean()
        r[f"lift{int(k*100)}"] = (g[f"prec{int(k*100)}"] / g[f"base{int(k*100)}"]).mean()
        r[f"orac{int(k*100)}"] = g[f"orac{int(k*100)}"].mean()
    r["ndcg20"] = g.ndcg20.mean(); r["rho"] = g.rho.mean()
    res.append(r)
R = pd.DataFrame(res)
R.to_csv(HERE / "data/prioritization_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
print(R[["protocol","model","groups","cap10","cap10_lo","cap10_hi","cap20","cap20_lo","cap20_hi","prec20","lift20","orac20","ndcg20","rho"]].round(3).to_string())
