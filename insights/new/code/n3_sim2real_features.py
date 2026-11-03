"""N3: sim-to-real with the 133 features.  A random forest trained on the 1,321 synthetic deltas predicts the 61 real pairs (and the reverse)."""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import make_pipeline
from sload import SD, ROOT
warnings.filterwarnings("ignore")
S = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv")); R = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
cols = [c for c in S.columns if c.startswith("delta__") and c in R.columns]
print("shared delta features:", len(cols))
ys, yr = S.ptype.values, R.td_type.values
lang = (R.language == "Python").values
sl = lambda a: np.sign(a) * np.log1p(np.abs(a))
out = []
P = lambda s="": (out.append(s), print(s))
P("majority baseline on the real pairs: %.3f; real class counts %s" % (pd.Series(yr).value_counts(normalize=True).max(), pd.Series(yr).value_counts().to_dict()))
for tname, tf in (("raw delta", lambda a: a), ("signed log delta", sl)):
    for mname, mk in (("random forest", lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=2)),
                      ("10-best + RF", lambda: make_pipeline(SelectKBest(f_classif, k=10), RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=2)))):
        m = mk().fit(tf(S[cols].values), ys)
        p = m.predict(tf(R[cols].values))
        P("train synthetic -> test real  [%s, %s]: accuracy %.3f   Python %.3f (n=%d)   C/C++ %.3f (n=%d)" % (tname, mname, (p == yr).mean(), (p[lang] == yr[lang]).mean(), lang.sum(), (p[~lang] == yr[~lang]).mean(), (~lang).sum()))
        if tname == "signed log delta" and mname == "random forest":
            P(pd.crosstab(pd.Series(yr, name="true"), pd.Series(p, name="predicted")).to_string())
m = RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=2).fit(sl(R[cols].values), yr)
p = m.predict(sl(S[cols].values))
P("train real (61) -> test synthetic (1,321): accuracy %.3f (majority %.3f)" % ((p == ys).mean(), pd.Series(ys).value_counts(normalize=True).max()))
open("../results/n3_sim2real_features.txt", "w").write("\n".join(out))
