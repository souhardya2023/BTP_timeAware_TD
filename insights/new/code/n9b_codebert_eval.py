"""N9b: do frozen CodeBERT embeddings of the changed lines generalise better than the other representations?
Same splits as before.  Head: logistic regression on standardised embeddings (C fixed in advance: 0.1; 1.0 reported too).
 synthetic (1,321 pairs): random 5-fold, held-out project, held-out template (leave one template out), temporal (first 60 % of each project's pairs train)
 real (61 pairs): leave one project out;  sim-to-real: train on all synthetic, test the real pairs;  real -> synthetic;  pooled
Reference values: 133 features RF: 0.942 / 0.960 / 0.828 / 0.915;  CNN on the code image: 0.970 / 0.977 / 0.561;  patch words: 0.964 / 0.979 / 0.584;  real LOPO majority 0.426."""
import os, warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sload import SD, ROOT, manifests
warnings.filterwarnings("ignore")
Z = np.load("../results/n9_codebert.npz")
S = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv"))[["instance", "project", "ptype", "template", "tier"]]
M = manifests(); cm = {i["id"]: i["intro_commit"] for m in M.values() for i in m["instances"]}
S["order"] = S.instance.map(cm); S["late"] = S.groupby("project").order.rank(method="first") > 0.6 * S.groupby("project").instance.transform("size")
R = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
ys, yr = S.ptype.values, R.td_type.values; proj = R.project.values; py = (R.language == "Python").values; nb = proj != "boltons"
out = []
P = lambda s="": (out.append(s), print(s, flush=True))
def lr(C): return lambda: make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=4000, class_weight="balanced"))
def split_pred(X, y, mk, how):
    pred = np.empty(len(y), dtype=object)
    if how == "random": it = StratifiedKFold(5, shuffle=True, random_state=0).split(X, y)
    elif how == "project": it = GroupKFold(5).split(X, y, S.project)
    elif how == "template": it = ((np.where(S.template != t)[0], np.where(S.template == t)[0]) for t in S.template.unique())
    elif how == "temporal": tr, te = np.where(~S.late)[0], np.where(S.late)[0]; pred[te] = mk().fit(X[tr], y[tr]).predict(X[te]); return pred, S.late.values
    for tr, te in it: pred[te] = mk().fit(X[tr], y[tr]).predict(X[te])
    return pred, np.ones(len(y), bool)
for emb in ("mean-pooled", "[CLS]"):
    XS = Z["ms"] if emb == "mean-pooled" else Z["cs"]; XR = Z["mr"] if emb == "mean-pooled" else Z["cr"]
    for C in (0.1, 1.0):
        P("\n## CodeBERT %s embedding, logistic regression C=%g" % (emb, C))
        res = {}
        for how in ("random", "project", "template", "temporal"):
            p, mask = split_pred(XS, ys, lr(C), how); res[how] = (p[mask] == ys[mask]).mean()
            if how == "template": pt = pd.DataFrame({"t": S.template, "ty": S.ptype, "ok": p == ys}).groupby(["ty", "t"]).ok.mean()
        P("  synthetic accuracy: random %.3f   held-out project %.3f   held-out template %.3f   temporal %.3f" % (res["random"], res["project"], res["template"], res["temporal"]))
        if emb == "mean-pooled" and C == 0.1: P("  per held-out template:\n" + pt.round(2).to_string()); pt.to_csv("../results/n9_codebert_per_template.csv")
        pr = np.empty(len(yr), dtype=object)
        for q in np.unique(proj):
            te = proj == q; pr[te] = lr(C)().fit(XR[~te], yr[~te]).predict(XR[te])
        P("  real pairs, leave one project out: %.3f   non-boltons %.3f   (majority 0.426 / 0.432)" % ((pr == yr).mean(), (pr[nb] == yr[nb]).mean()))
        m = lr(C)().fit(XS, ys); p = m.predict(XR)
        P("  sim-to-real (train synthetic, test the 61 real pairs): %.3f   Python %.3f (majority 0.585)   C/C++ %.3f (majority 0.700)" % ((p == yr).mean(), (p[py] == yr[py]).mean(), (p[~py] == yr[~py]).mean()))
        if emb == "mean-pooled" and C == 0.1:
            P(pd.crosstab(pd.Series(yr, name="true"), pd.Series(p, name="predicted")).to_string()); np.save("../results/n9_simreal_pred.npy", p.astype(str))
        m2 = lr(C)().fit(XR, yr); q2 = m2.predict(XS); P("  real -> synthetic: %.3f (majority 0.206)" % (q2 == ys).mean())
        pr2 = np.empty(len(yr), dtype=object)
        for q in np.unique(proj):
            te = proj == q; pr2[te] = lr(C)().fit(np.vstack([XR[~te], XS]), np.r_[yr[~te], ys]).predict(XR[te])
        P("  pooled (other real projects + all synthetic), real leave one project out: %.3f   non-boltons %.3f" % ((pr2 == yr).mean(), (pr2[nb] == yr[nb]).mean()))
open("../results/n9_codebert_eval.txt", "w").write("\n".join(out))
