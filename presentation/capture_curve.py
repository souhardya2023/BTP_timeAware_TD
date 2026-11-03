"""Capture curve: share of next-release interest found in the top k% (k = 5..100), averaged over groups."""
import numpy as np, pandas as pd
from pathlib import Path
HERE = Path(__file__).parent
d = pd.read_csv(HERE.parent / "interest_exp/results/pm_predictions.csv")
rng = np.random.default_rng(0)
ks = np.arange(5, 101, 5)
rows = []
for (proto, model, repo, vi), g in d.groupby(["protocol", "model", "repo", "vi"]):
    a = g.actual_mPM.to_numpy(); p = g.predicted_mPM.to_numpy(); n = len(a)
    if a.sum() <= 0 or n < 10: continue
    o = np.lexsort((rng.random(n), -p)); cs = np.cumsum(a[o]) / a.sum()
    oc = np.cumsum(np.sort(a)[::-1]) / a.sum()
    for k in ks:
        m = max(1, int(np.ceil(k / 100 * n)))
        rows.append((proto, model, repo, vi, k, cs[m - 1], oc[m - 1]))
C = pd.DataFrame(rows, columns=["protocol", "model", "repo", "vi", "k", "capture", "oracle"])
out = C.groupby(["protocol", "model", "k"])[["capture", "oracle"]].mean().reset_index()
out.to_csv(HERE / "data/capture_curve.csv", index=False)
x = out[(out.protocol == "leave-one-repo-out")].pivot(index="k", columns="model", values="capture")
x["oracle"] = out[(out.protocol == "leave-one-repo-out") & (out.model == "zero")].set_index("k").oracle
print(x.round(3).to_string())
import json
json.dump({m: x[m].round(4).tolist() for m in x.columns} | {"k": ks.tolist()}, open(HERE / "data/curve.json", "w"))
