"""Insight set L1-B: the project as a graph / an image.
 1. the dependency graph of every pair (clean and debt copy): what does a debt change do to it? ('edit subgraph' features)
 2. the adjacency matrix as an image (32x32), the debt copy and the DIFFERENCE image, saved for a CNN (l1_cnn.py)
 3. classical models on the edit-graph features and on the flattened images
"""
import os
import sys
import warnings

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from common import src_files  # noqa: E402
from f_structure import c_graph, py_graph  # noqa: E402

DS = pd.read_csv(f"{ROOT}/out_dataset/delta_only/dataset_without_time.csv")
y = DS.td_type.values
proj = DS.project.values
out = []
P = lambda s: (out.append(s), print(s))
S = 32


def pair_dirs(pid):
    lang, n = pid.split("/")
    b = f"{ROOT}/project_dataset/{'Python' if lang == 'Python' else 'C_C++'}/{n}"
    return f"{b}/{n}_clean", f"{b}/{n}_TD", lang


def graph(root, lang):
    files = src_files(root)
    return (py_graph if lang == "Python" else c_graph)(root, files)


def adj_image(g, order, size=S):
    n = len(order)
    idx = {f: i for i, f in enumerate(order)}
    A = np.zeros((n, n))
    for a, b in g.edges():
        if a in idx and b in idx:
            A[idx[a], idx[b]] = 1
    # block-sum onto a size x size grid
    bins = np.minimum((np.arange(n) * size / max(n, 1)).astype(int), size - 1)
    img = np.zeros((size, size))
    for i in range(n):
        for j in range(n):
            if A[i, j]:
                img[bins[i], bins[j]] += 1
    return img


rows, imgs_td, imgs_dl = [], [], []
for pid in DS.id:
    c, t, lang = pair_dirs(pid)
    gc, gt = graph(c, lang), graph(t, lang)
    order = sorted(set(gc.nodes) | set(gt.nodes))
    ec, et = set(gc.edges), set(gt.edges)
    add, rem = et - ec, ec - et
    touched = {n for e in add | rem for n in e}
    def nontriv(g):
        return sum(len(s) for s in nx.strongly_connected_components(g) if len(s) > 1)
    rows.append(dict(id=pid, nodes=len(order), edges=len(et), e_added=len(add), e_removed=len(rem), touched_nodes=len(touched),
                     cyc_nodes_delta=nontriv(gt) - nontriv(gc), nodes_added=len(set(gt.nodes) - set(gc.nodes)),
                     indeg_max_delta=(max([d for _, d in gt.in_degree()] or [0]) - max([d for _, d in gc.in_degree()] or [0]))))
    imgs_td.append(adj_image(gt, order))
    imgs_dl.append(adj_image(gt, order) - adj_image(gc, order))
G = pd.DataFrame(rows)
G["td_type"] = y
G["project"] = proj
G.to_csv("../results/l1_edit_graph_features.csv", index=False)
np.savez_compressed("../results/l1_images.npz", td=np.array(imgs_td), delta=np.array(imgs_dl), y=y, proj=proj, fold=DS.fold.values)

P("## 1. What a debt change does to the dependency graph")
P(f"pairs whose dependency graph changes at all: {(G.e_added + G.e_removed + G.nodes_added > 0).sum()} of {len(G)}")
P(G.groupby("td_type")[["e_added", "e_removed", "cyc_nodes_delta", "touched_nodes"]].agg(["mean"]).round(2).to_string())
chg = (G.e_added + G.e_removed + G.nodes_added) > 0
P("share of pairs with a changed graph, by type: " + str(chg.groupby(G.td_type).mean().round(2).to_dict()))
P("number of graph pixels that differ (of the 32x32 delta image), median: " + str(int(np.median([(np.abs(d) > 0).sum() for d in imgs_dl]))))

FE = ["e_added", "e_removed", "touched_nodes", "cyc_nodes_delta", "nodes_added", "indeg_max_delta"]
Xg = G[FE].values
def cv(model_fn, X, split):
    folds = DS.fold.values if split == "stratified" else pd.factorize(proj)[0]
    pred = np.empty(len(y), dtype=object)
    for f in np.unique(folds):
        te = folds == f
        pred[te] = model_fn().fit(X[~te], y[~te]).predict(X[te])
    return (pred == y).mean()
RF = lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0, n_jobs=-1)
LR = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=3000, class_weight="balanced"))
P("\n## 2. Classical models (accuracy, no time feature; majority = 0.426)")
Xi_td = np.array(imgs_td).reshape(len(y), -1)
Xi_dl = np.array(imgs_dl).reshape(len(y), -1)
for name, X, fn in (("edit-graph features (6 numbers), RF", Xg, RF), ("flattened adjacency image of the debt copy, LR", Xi_td, LR), ("flattened DIFFERENCE image, LR", Xi_dl, LR)):
    P(f"  {name:52s} stratified {cv(fn, X, 'stratified'):.3f}   leave-one-project-out {cv(fn, X, 'lopo'):.3f}")
# dependency_structure vs rest, AUC with leave-one-project-out
yb = (y == "dependency_structure").astype(int)
pr = np.zeros(len(y))
folds = pd.factorize(proj)[0]
for f in np.unique(folds):
    te = folds == f
    m = RandomForestClassifier(300, class_weight="balanced", random_state=0).fit(Xg[~te], yb[~te])
    pr[te] = m.predict_proba(Xg[te])[:, 1]
P(f"\nDependency-structure vs the rest from the 6 edit-graph numbers: AUC {roc_auc_score(yb, pr):.2f} (leave-one-project-out, 7 positive pairs)")
open("../results/l1_graph_image.txt", "w").write("\n".join(out))
