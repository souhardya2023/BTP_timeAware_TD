"""Insight set L1-A: 'the debt is local, the project is the noise'.
 1. dilution: how small is the debt change compared with the project vector it is buried in?
 2. local view: describe the EDIT instead of the project:
      (a) the 133 features of only the files that the patch touched (debt copy minus clean copy)
      (b) the words of the patch itself (added and removed identifiers)
    and test them with the project-held-out protocols that the whole-project vector fails.
"""
import os
import re
import shutil
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from common import src_files  # noqa: E402
from extract import extract  # noqa: E402

DS = pd.read_csv(f"{ROOT}/out_dataset/delta_only/dataset_without_time.csv")
PR = pd.read_csv(f"{ROOT}/project_dataset/properties_all_pairs.csv").set_index("id")
FEAT = [c for c in DS.columns if c.startswith("delta__")]
y = DS.td_type.values
proj = DS.project.values
out = []
P = lambda s: (out.append(s), print(s))


def pair_dir(pid):
    lang, n = pid.split("/")
    sub = "Python" if lang == "Python" else "C_C++"
    b = f"{ROOT}/project_dataset/{sub}/{n}"
    return f"{b}/{n}_clean", f"{b}/{n}_TD", f"{b}/{n}_prop/td.patch"


# ---------------------------------------------------------------- 1. dilution
rows = []
for pid in DS.id:
    clean, td, patch = pair_dir(pid)
    files = src_files(clean)
    loc = 0
    for rel, p, lang in files:
        try:
            loc += sum(1 for _ in open(p, errors="ignore"))
        except OSError:
            pass
    r = PR.loc[pid]
    rows.append(dict(id=pid, files=len(files), nloc=loc, touched=int(r.files_changed), changed_lines=int(r.lines_added + r.lines_deleted)))
dl = pd.DataFrame(rows)
dl["file_frac"] = dl.touched / dl.files
dl["line_frac"] = dl.changed_lines / dl.nloc
dl.to_csv("../results/l1_dilution.csv", index=False)
P("## 1. Dilution of the debt change inside the project")
P(f"files touched per pair: median {dl.touched.median():.0f}; changed lines (added + deleted): median {dl.changed_lines.median():.0f}, mean {dl.changed_lines.mean():.0f}")
P(f"share of the project's files that the patch touches: median {dl.file_frac.median():.2%}, max {dl.file_frac.max():.1%}")
P(f"share of the project's lines that the patch changes: median {dl.line_frac.median():.3%}, max {dl.line_frac.max():.2%}")

X_all = DS[FEAT].values
sd_between = X_all.std(0) + 1e-9
P(f"mean |delta| / std of the delta column over pairs: see results/04; here: mean |delta| in units of the BETWEEN-project std of the clean vector is computed in l1_drift.py")

# ---------------------------------------------------------------- 2a. local features (only the touched files)
def local_vector(pid, side):
    clean, td, patch = pair_dir(pid)
    root = clean if side == "clean" else td
    changed = [f.strip() for f in str(PR.loc[pid].changed_files).replace(";", ",").split(",") if f.strip()]
    tmp = tempfile.mkdtemp()
    try:
        for f in changed:
            src = os.path.join(root, f)
            if os.path.exists(src):
                dst = os.path.join(tmp, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst)
        return extract(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

cache = "../results/l1_local_features.csv"
if os.path.exists(cache):
    L = pd.read_csv(cache, index_col=0)
else:
    recs = {}
    for pid in DS.id:
        try:
            a, b = local_vector(pid, "clean"), local_vector(pid, "td")
            recs[pid] = {k: b[k] - a[k] for k in a}
        except Exception as e:
            print("local extraction failed", pid, e)
    L = pd.DataFrame(recs).T
    L.to_csv(cache)
L = L.reindex(DS.id).fillna(0.0)
XL = L.values
# ---------------------------------------------------------------- 2b. patch words
def patch_text(pid):
    t = open(pair_dir(pid)[2], errors="ignore").read()
    add, rem = [], []
    for line in t.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        toks = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", line[1:])
        sp = []
        for w in toks:
            sp += [x.lower() for x in re.split(r"_+|(?<=[a-z])(?=[A-Z])", w) if len(x) > 1]
        if line.startswith("+"):
            add += ["a_" + x for x in sp]
        elif line.startswith("-"):
            rem += ["r_" + x for x in sp]
    return " ".join(add + rem)
TXT = [patch_text(p) for p in DS.id]

# ---------------------------------------------------------------- protocols
def run(model_fn, kind, X, split):
    pred = np.empty(len(y), dtype=object)
    if split == "stratified":
        folds = DS.fold.values
    elif split == "by_project":
        folds = DS.fold_by_project.values
    else:                                   # leave one project out
        folds = pd.factorize(proj)[0]
    for f in np.unique(folds):
        te = folds == f
        m = model_fn()
        if kind == "text":
            vec = TfidfVectorizer(token_pattern=r"\S+", sublinear_tf=True, min_df=2)
            Xtr = vec.fit_transform(np.array(X, dtype=object)[~te]); Xte = vec.transform(np.array(X, dtype=object)[te])
            m.fit(Xtr, y[~te]); pred[te] = m.predict(Xte)
        else:
            m.fit(X[~te], y[~te]); pred[te] = m.predict(X[te])
    return (pred == y).mean(), balanced_accuracy_score(y, pred), f1_score(y, pred, average="macro"), pred

RF = lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1)
KB = lambda: make_pipeline(SelectKBest(f_classif, k=10), RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1))
LR = lambda: LogisticRegression(C=10, max_iter=2000, class_weight="balanced")
LRs = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced"))

methods = [
    ("whole-project delta, 10-best + RF (talk)", "num", X_all, KB),
    ("whole-project delta, RF", "num", X_all, RF),
    ("LOCAL delta (touched files), RF", "num", XL, RF),
    ("LOCAL delta (touched files), 10-best + RF", "num", XL, KB),
    ("PATCH WORDS (added/removed identifiers), LR", "text", TXT, LR),
]
res = []
preds = {}
P("\n## 2. Debt type from the whole project, from the touched files, and from the patch words (no time feature)")
for name, kind, X, fn in methods:
    r = {"method": name}
    for split in ("stratified", "by_project", "leave_one_project_out"):
        a, b, f, pr = run(fn, kind, X, split)
        r[split + "_acc"] = a; r[split + "_bal"] = b
        preds[(name, split)] = pr
    res.append(r)
R = pd.DataFrame(res)
R.to_csv("../results/l1_local_signal.csv", index=False)
P(R.round(3).to_string(index=False))
P(f"majority baseline {pd.Series(y).value_counts(normalize=True).max():.3f}")

# per-origin check for the patch-word model under leave-one-project-out
src = PR.loc[DS.id].source.str.split(" ").str[0].values
pr = preds[("PATCH WORDS (added/removed identifiers), LR", "leave_one_project_out")]
P("\nPatch-word model, leave-one-project-out, accuracy by origin of the change:")
for s in np.unique(src):
    m = src == s
    P(f"  {s:12s} n={m.sum():2d}  acc={(pr[m]==y[m]).mean():.3f}")
P("Patch-word model, per type (leave-one-project-out):")
for t in np.unique(y):
    m = y == t
    P(f"  {t:20s} n={m.sum():2d}  recall={(pr[m]==t).mean():.3f}")
# train on scripted injections only, test on the LLM-written (SmellBench) ones and the natural pair
sc = np.array([s.startswith("scripted") or s.startswith("scripted/hand") for s in PR.loc[DS.id].source.values])
test = ~sc
vec = TfidfVectorizer(token_pattern=r"\S+", sublinear_tf=True, min_df=2)
Xtr = vec.fit_transform(np.array(TXT, dtype=object)[sc]); Xte = vec.transform(np.array(TXT, dtype=object)[test])
m = LR().fit(Xtr, y[sc]); p2 = m.predict(Xte)
P(f"\nTrain on scripted injections (n={sc.sum()}), test on LLM-written SmellBench + natural pair (n={test.sum()}): accuracy {(p2==y[test]).mean():.3f}")
P("  test types: " + str(pd.Series(y[test]).value_counts().to_dict()))
P("  per-type: " + str({t: f"{(p2[y[test]==t]==t).mean():.2f} (n={(y[test]==t).sum()})" for t in np.unique(y[test])}))
# top words per class
vec = TfidfVectorizer(token_pattern=r"\S+", sublinear_tf=True, min_df=2)
Xa = vec.fit_transform(TXT); lr = LR().fit(Xa, y)
P("\nMost indicative patch words per type (logistic-regression weights):")
for i, c in enumerate(lr.classes_):
    top = np.argsort(-lr.coef_[i])[:8]
    P(f"  {c:20s} " + ", ".join(vec.get_feature_names_out()[top]))
open("../results/l1_local_signal.txt", "w").write("\n".join(out))

# ---------------------------------------------------------------- 3. where does leave-one-project-out fail?
P("\n## 3. Leave-one-project-out accuracy per held-out project (no time feature)")
tab = {}
for name, kind, X, fn in methods:
    pr = preds[(name, "leave_one_project_out")]
    tab[name] = {p: (pr[proj == p] == y[proj == p]).mean() for p in np.unique(proj)}
T3 = pd.DataFrame(tab).T
T3["n_pairs"] = None
cnt = pd.Series(proj).value_counts()
T3.drop(columns="n_pairs").to_csv("../results/l1_lopo_per_project.csv")
P(T3.drop(columns="n_pairs").round(2).to_string())
P("pairs per project: " + str(cnt.to_dict()))
nb = proj != "boltons"
P("\nAccuracy on the 37 pairs of the 9 projects other than boltons (boltons stays in the training data):")
for name, kind, X, fn in methods:
    pr = preds[(name, "leave_one_project_out")]
    P(f"  {name:48s} {(pr[nb]==y[nb]).mean():.3f}   (majority among these pairs: {pd.Series(y[nb]).value_counts(normalize=True).max():.3f})")
P("Concurrency training examples when each project is held out: " + str({p: int(((y == 'concurrency') & (proj != p)).sum()) for p in ['boltons', 'zlib']}))
open("../results/l1_local_signal.txt", "w").write("\n".join(out))

P("\n## 4. Leave-one-project-out accuracy by how the debt change was made (boltons excluded from the count)")
ORI = []
srcs = PR.loc[DS.id].source.str.replace(r" \(.*", "", regex=True).str.replace(r"scripted/hand-authored injection", "scripted injection").values
for name in ("whole-project delta, RF", "LOCAL delta (touched files), 10-best + RF", "PATCH WORDS (added/removed identifiers), LR"):
    pr = preds[(name, "leave_one_project_out")]
    line = []
    for s in np.unique(srcs):
        m = (srcs == s) & nb
        if m.sum():
            line.append(f"{s[:22]} n={m.sum()} acc={(pr[m]==y[m]).mean():.2f}")
    P(f"  {name:48s} " + "; ".join(line))
    ORI.append({"method": name, **{s2[:22]: (preds[(name, "leave_one_project_out")][(srcs == s2) & nb] == y[(srcs == s2) & nb]).mean() for s2 in np.unique(srcs) if ((srcs == s2) & nb).sum()}})
open("../results/l1_local_signal.txt", "w").write("\n".join(out))
pd.DataFrame(ORI).to_csv("../results/l1_lopo_by_origin.csv", index=False)
