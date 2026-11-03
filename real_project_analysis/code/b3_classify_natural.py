#!/usr/bin/env python3
"""Level 1 on natural pairs: type of a real change from its diff, leave one repository out. Compares majority, keyword counts + random forest, TF-IDF + logistic regression,
frozen CodeBERT (mean / CLS) + logistic regression, on all weakly labelled pairs and on the 'dual evidence' subset. writes results/b3_*.csv, b3_report.txt"""
import json, os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, recall_score
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = os.path.join(ROOT, "results")
D = pd.read_csv(os.path.join(R, "b1_pairs.csv")); T = {}
for l in open(os.path.join(R, "b1_diffs.jsonl")):
    j = json.loads(l); T[j["repo"] + "|" + j["sha"]] = j["text"]
D["key"] = D.repo + "|" + D.sha; D["text"] = D.key.map(T)
E = np.load(os.path.join(R, "b2_codebert.npz")); idx = {k: i for i, k in enumerate(E["keys"])}
D["ei"] = D.key.map(idx)
kcols = [c for c in D.columns if c.startswith("k_")] + ["lines", "added", "removed", "files", "funcs_changed", "imp_frac"]
out = open(os.path.join(R, "b3_report.txt"), "w")
def say(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")
rows = []
def run(sub, name):
    S = sub.reset_index(drop=True); y = S.label.values; classes = sorted(set(y)); g = S.repo.values
    maj = pd.Series(y).value_counts(normalize=True).max()
    res = {}
    for model in ("keywords_rf", "tfidf_lr", "codebert_mean_lr", "codebert_cls_lr", "codebert_mean+keywords"):
        pred = np.empty(len(S), dtype=object)
        for r in sorted(set(g)):
            te = g == r; tr = ~te
            if len(set(y[tr])) < 2 or te.sum() == 0:
                pred[te] = pd.Series(y[tr]).mode()[0]; continue
            if model == "keywords_rf":
                m = RandomForestClassifier(300, class_weight="balanced", random_state=0, min_samples_leaf=2).fit(S.loc[tr, kcols].values, y[tr]); pred[te] = m.predict(S.loc[te, kcols].values)
            elif model == "tfidf_lr":
                v = TfidfVectorizer(token_pattern=r"[A-Za-z_]{2,}", lowercase=True, min_df=3, max_features=4000, sublinear_tf=True).fit(S.loc[tr, "text"])
                m = LogisticRegression(C=3.0, max_iter=500, class_weight="balanced").fit(v.transform(S.loc[tr, "text"]), y[tr]); pred[te] = m.predict(v.transform(S.loc[te, "text"]))
            else:
                key = "cls" if "cls" in model else "mean"
                X = E[key][S.ei.values.astype(int)]
                if "+keywords" in model:
                    K = np.log1p(S[kcols].values.astype(float)); X = np.hstack([X, K])
                sc = StandardScaler().fit(X[tr]); m = LogisticRegression(C=0.05, max_iter=800, class_weight="balanced").fit(sc.transform(X[tr]), y[tr]); pred[te] = m.predict(sc.transform(X[te]))
        res[model] = pred
        rows.append(dict(subset=name, n=len(S), repos=len(set(g)), model=model, acc=accuracy_score(y, pred), bal_acc=balanced_accuracy_score(y, pred), macro_f1=f1_score(y, pred, average="macro"), majority=maj,
                         **{"recall_" + c: recall_score(y, pred, labels=[c], average="macro") for c in classes}))
    rows.append(dict(subset=name, n=len(S), repos=len(set(g)), model="majority", acc=maj, bal_acc=1 / len(classes), macro_f1=np.nan, majority=maj))
    return S
all_ = D[D.label != "coupling"]; dual = D[D.dual_ok]
run(all_, "all weak labels (4 types)"); run(dual, "dual evidence")
R_ = pd.DataFrame(rows); R_.to_csv(os.path.join(R, "b3_results.csv"), index=False)
say(R_.round(3).to_string(index=False))
out.close()
