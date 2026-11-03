#!/usr/bin/env python3
"""The same experiments for every embedding model (and a TF-IDF reference that is not a foundation model).
Classifier: standardised embedding + logistic regression (C=0.05, balanced classes); nothing is tuned per model.
Experiments (accuracy, balanced accuracy, majority share):
  N-all   natural pairs, 4 weak-label types, leave one repository out
  N-dual  natural pairs, dual-evidence subset, leave one repository out
  S-rand  v2 synthetic pairs, random 5 folds
  S-proj  v2 synthetic, held-out project (10 group folds)
  S-templ v2 synthetic, held-out code template (8 group folds)
  T-syn   train synthetic -> test the 61 real pairs
  T-nat   train natural (dual) -> test the real pairs of the same 4 types
  T-both  train synthetic + natural (dual) -> test the 61 real pairs
Pooling 'mean' is the pre-declared main setting; 'cls' is reported as a second setting.
-> ../results/e2_results.csv"""
import os, pickle, warnings
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); EMB = os.path.join(HERE, "..", "embeddings"); RES = os.path.join(HERE, "..", "results"); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MODELS = ["codebert", "graphcodebert", "unixcoder", "codet5", "roberta", "qwen_coder"]

T = pickle.load(open(os.path.join(EMB, "texts.pkl"), "rb"))
B = pd.read_csv(os.path.join(ROOT, "real_project_analysis", "results", "b1_pairs.csv")); B["key"] = B.repo + "|" + B.sha
B["idx"] = B.key.map({k: i for i, k in enumerate(T["natural_keys"])}); B["y"] = B.label.replace({"dependency": "dependency_structure"})
S = pd.read_csv(os.path.join(ROOT, "synthetic_dataset_v2", "features", "pairs_delta.csv"))[["instance", "project", "ptype", "template"]].set_index("instance").loc[T["synthetic_keys"]].reset_index()
RE = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv")); yr = RE.td_type.values
NN, NS = len(T["natural"]), len(T["synthetic"])
Ball = B[B.label != "coupling"]; Bdual = B[B.dual_ok]


class Clf:
    def __init__(self, tfidf=False): self.tfidf = tfidf
    def fit(self, X, y):
        if self.tfidf:
            self.v = TfidfVectorizer(token_pattern=r"[A-Za-z_]{2,}", min_df=3, max_features=4000, sublinear_tf=True).fit(X); self.m = LogisticRegression(C=3.0, max_iter=500, class_weight="balanced").fit(self.v.transform(X), y)
        else:
            self.sc = StandardScaler().fit(X); self.m = LogisticRegression(C=0.05, max_iter=800, class_weight="balanced").fit(self.sc.transform(X), y)
        return self
    def predict(self, X): return self.m.predict(self.v.transform(X) if self.tfidf else self.sc.transform(X))


def cv(X, y, splits, tfidf):
    X = np.asarray(X, dtype=object) if tfidf else np.asarray(X); y = np.asarray(y); p = np.empty(len(y), dtype=object)
    for tr, te in splits: p[te] = Clf(tfidf).fit(X[tr], y[tr]).predict(X[te])
    return (p == y).mean(), balanced_accuracy_score(y, p)


def tr_te(Xtr, ytr, Xte, yte, tfidf):
    Xtr = np.asarray(Xtr, dtype=object) if tfidf else np.asarray(Xtr); Xte = np.asarray(Xte, dtype=object) if tfidf else np.asarray(Xte)
    p = Clf(tfidf).fit(Xtr, ytr).predict(Xte); yte = np.asarray(yte)
    return (p == yte).mean(), balanced_accuracy_score(yte, p)


def maj(y): return pd.Series(y).value_counts(normalize=True).max()


def experiments(nat, syn, real, tfidf):
    """nat, syn, real: feature arrays (or text lists) of the natural, synthetic and real sets"""
    nat, syn, real = (np.asarray(a, dtype=object) if tfidf else np.asarray(a) for a in (nat, syn, real)); out = []
    for nm, sub in (("N-all", Ball), ("N-dual", Bdual)):
        X, y, g = nat[sub.idx.values], sub.y.values, sub.repo.values
        out.append((nm, *cv(X, y, GroupKFold(len(set(g))).split(X, y, g), tfidf), maj(y), len(y)))
    y = S.ptype.values
    out.append(("S-rand", *cv(syn, y, StratifiedKFold(5, shuffle=True, random_state=0).split(syn, y), tfidf), maj(y), len(y)))
    out.append(("S-proj", *cv(syn, y, GroupKFold(10).split(syn, y, S.project.values), tfidf), maj(y), len(y)))
    out.append(("S-templ", *cv(syn, y, GroupKFold(8).split(syn, y, S.template.values), tfidf), maj(y), len(y)))
    out.append(("T-syn", *tr_te(syn, y, real, yr, tfidf), maj(yr), len(yr)))
    Xn, yn = nat[Bdual.idx.values], Bdual.y.values; keep = np.isin(yr, np.unique(yn))
    out.append(("T-nat", *tr_te(Xn, yn, real[keep], yr[keep], tfidf), maj(yr[keep]), int(keep.sum())))
    Xb = np.concatenate([syn, Xn]) if not tfidf else np.concatenate([syn, Xn]); yb = np.concatenate([y, yn])
    out.append(("T-both", *tr_te(Xb, yb, real, yr, tfidf), maj(yr), len(yr)))
    return out


def main():
    rows = []
    for nm, e, a, b, m, n in experiments(T["natural"], T["synthetic"], T["real"], True): rows.append(dict(model="tfidf (not a foundation model)", pooling="-", experiment=nm, acc=a, bal_acc=b, majority=m, n=n))
    for model in MODELS:
        f = os.path.join(EMB, model + ".npz")
        if not os.path.exists(f): continue
        E = np.load(f)
        for pool in ("mean", "cls"):
            X = E[pool]; nat, syn, real = X[:NN], X[NN:NN + NS], X[NN + NS:]
            for nm, a, b, m, n in [(r[0], *r[1:]) for r in experiments(nat, syn, real, False)]: rows.append(dict(model=model, pooling=pool, experiment=nm, acc=a, bal_acc=b, majority=m, n=n))
        print("done", model, flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(RES, "e2_results.csv"), index=False)
    pd.set_option("display.width", 220)
    print(R[R.pooling.isin(["mean", "-"])].pivot(index="model", columns="experiment", values="acc").round(3)[["N-all", "N-dual", "S-rand", "S-proj", "S-templ", "T-syn", "T-nat", "T-both"]])
    print(R[R.model.str.startswith("tfidf")][["experiment", "majority"]].set_index("experiment").T.round(3))


if __name__ == "__main__":
    main()
