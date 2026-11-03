"""S1b: (1) the words of the patch (identifiers added and removed) as the only input; (2) host invariance of the feature signature of a template;
(3) which debt types change the import graph (visibility of a file-level graph)."""
import os, re, subprocess, warnings
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sload import SD
warnings.filterwarnings("ignore")
D = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv"))
Pp = pd.read_csv(os.path.join(SD, "pairs.csv")).set_index("instance")
y = D.ptype.values
out = []
P = lambda s="": (out.append(s), print(s))
# ---- (1) patch words
def words(inst):
    r = Pp.loc[inst]
    t = subprocess.run(["git", "-C", os.path.join(SD, "repos", r.project + ".git"), "diff", "-U0", r.parent, r.child], capture_output=True, text=True).stdout
    add, rem = [], []
    for l in t.splitlines():
        if l.startswith(("+++", "---", "@@", "diff", "index")):
            continue
        toks = [x.lower() for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", l[1:]) for x in re.split(r"_+|(?<=[a-z])(?=[A-Z])", w) if len(x) > 1]
        if l.startswith("+"):
            add += ["a_" + x for x in toks]
        elif l.startswith("-"):
            rem += ["r_" + x for x in toks]
    return " ".join(add + rem)
TXT = np.array([words(i) for i in D.instance], dtype=object)
def cvtext(split):
    pred = np.empty(len(y), dtype=object)
    if split == "random":
        it = StratifiedKFold(5, shuffle=True, random_state=0).split(TXT, y)
    elif split == "project":
        it = GroupKFold(5).split(TXT, y, D.project)
    else:
        it = ((np.where(D.template != t)[0], np.where(D.template == t)[0]) for t in D.template.unique())
    for tr, te in it:
        v = TfidfVectorizer(token_pattern=r"\S+", sublinear_tf=True, min_df=2)
        m = LogisticRegression(C=10, max_iter=3000, class_weight="balanced").fit(v.fit_transform(TXT[tr]), y[tr])
        pred[te] = m.predict(v.transform(TXT[te]))
    return pred
P("## patch words only (logistic regression on added / removed identifiers)")
for s in ("random", "project", "template"):
    P("  %-22s accuracy %.3f" % ({"random": "random split", "project": "held-out project", "template": "held-out template"}[s], (cvtext(s) == y).mean()))
# ---- (2) host invariance of the signature
dcols = [c for c in D.columns if c.startswith("delta__")]
X = D[dcols].values.astype(float)
Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
pure = ~D.mixed.astype(bool)
def mean_cos(a, b, same=False):
    A, B = Xs[a], Xs[b]
    A = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9); B = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-9)
    C = A @ B.T
    if same:
        np.fill_diagonal(C, np.nan)
    return np.nanmean(C)
rng = np.random.default_rng(0)
P("\n## host invariance: cosine similarity of the (standardised) delta vectors of PURE commits")
tt = D.template.values; ty = D.ptype.values; pj = D.project.values
same_t, same_ty, diff_ty = [], [], []
for _ in range(20000):
    i, j = rng.integers(0, len(D), 2)
    if i == j or not (pure[i] and pure[j]) or pj[i] == pj[j]:
        continue
    c = float(Xs[i] @ Xs[j] / (np.linalg.norm(Xs[i]) * np.linalg.norm(Xs[j]) + 1e-9))
    (same_t if tt[i] == tt[j] else same_ty if ty[i] == ty[j] else diff_ty).append(c)
P("  same template, different project:                    %.2f (n=%d)" % (np.mean(same_t), len(same_t)))
P("  same type, different template, different project:    %.2f (n=%d)" % (np.mean(same_ty), len(same_ty)))
P("  different type:                                      %.2f (n=%d)" % (np.mean(diff_ty), len(diff_ty)))
# ---- (3) visibility to the import graph
names = [c for c in dcols if any(k in c for k in ("edge", "cycle", "fan", "nodes", "scc", "density"))]
vis = (D[names].abs().sum(axis=1) > 0)
P("\n## graph features that exist: %s" % [c[7:] for c in names][:14])
P("share of pairs in which a graph feature changes, by type: " + str(vis.groupby(D.ptype).mean().round(2).to_dict()))
open("../results/s1_words_invariance.txt", "w").write("\n".join(out))
