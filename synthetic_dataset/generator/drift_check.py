"""Insight B on the synthetic data: the change that a debt introduction makes in the 133 features against the natural change of the same feature
between two consecutive releases of the same project.   python drift_check.py <dataset dir>   (needs features/)"""
import glob, os, sys
import numpy as np, pandas as pd
out = sys.argv[1]
D = pd.read_csv(os.path.join(out, "features", "pairs_delta.csv"))
dcols = [c for c in D.columns if c.startswith("delta__")]
feats = [c[7:] for c in dcols]
drift = {}
for f in glob.glob(os.path.join(out, "features", "releases", "*.csv")):
    R = pd.read_csv(f).sort_values("release")
    drift[R.project.iloc[0]] = np.abs(np.diff(R[feats].values, axis=0)).mean(0)
rows = []
for _, r in D.iterrows():
    if r.project not in drift:
        continue
    inj = np.abs(r[dcols].values.astype(float)); a = drift[r.project]
    act = inj > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(a > 1e-9, inj / a, np.nan)
    rows.append(dict(project=r.project, ptype=r.ptype, changed=int(act.sum()), above=int(np.nansum((ratio > 1) & act)), med_ratio=np.nanmedian(ratio[act & (a > 1e-9)]) if (act & (a > 1e-9)).any() else np.nan, mixed=r.mixed))
T = pd.DataFrame(rows)
txt = ["pairs: %d" % len(T), "features changed per pair (median): %d of %d" % (T.changed.median(), len(feats)),
       "features whose change exceeds the natural release-to-release drift (median per pair): %d" % T.above.median(),
       "median over pairs of the median ratio |injected change| / mean |natural change|: %.2f" % T.med_ratio.median(),
       "by type, features above drift (median): " + str(T.groupby("ptype").above.median().to_dict())]
print("\n".join(txt))
open(os.path.join(out, "drift_check.txt"), "w").write("\n".join(txt))
