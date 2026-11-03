"""06_combined: real and synthetic side by side, and pooled."""
import os, re
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi": 220, "font.size": 8.5, "legend.fontsize": 7.5})
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RES = os.path.join(ROOT, "insights", "new", "results"); OUT = os.path.join(os.path.dirname(__file__), "06_combined")
def save(fig, n): fig.tight_layout(); fig.savefig(os.path.join(OUT, n), facecolor="white"); plt.close(fig)
# ---- C1 panel as a coloured table
P = pd.read_csv(os.path.join(RES, "n7_panel.csv"), index_col=0)
cols = list(P.columns); a, b = P[cols[0]], P[cols[1]]
rel = (a - b).abs() / np.maximum(a.abs(), b.abs())
verdict = np.where(rel < 0.25, "same", np.where(rel < 0.5, "similar", "different"))
colr = {"same": "#cfe8cf", "similar": "#fff2b3", "different": "#f4c2c2"}
fig, ax = plt.subplots(figsize=(11.5, 0.33 * len(P) + 1.4)); ax.axis("off")
tab = ax.table(cellText=[[("%.3f" % v) for v in P.loc[i]] + [verdict[k]] for k, i in enumerate(P.index)], rowLabels=list(P.index), colLabels=cols + ["real vs synthetic baseline"], loc="center", cellLoc="center")
tab.auto_set_font_size(False); tab.set_fontsize(7.6); tab.scale(1, 1.35)
for k in range(len(P)):
    tab[(k + 1, 4)].set_facecolor(colr[verdict[k]])
for (r_, c_), cell in tab.get_celld().items():
    if c_ == -1: cell.set_text_props(ha="right"); cell.set_width(0.40)
ax.set_title("The same metrics on the real histories, the synthetic baseline, all synthetic and the pooled rows\n(green: same within 25 %, yellow: within 50 %, red: different)", fontsize=9)
save(fig, "C1_panel_real_vs_synthetic.png")
# ---- C2 pooled training
t = open(os.path.join(RES, "n7_combined.txt")).read()
blocks = re.split(r"\n### ", t)[1:3]
names = ["real only", "real + synthetic (all, weight 1)", "real + synthetic (all, weight 0.3)", "synthetic only"]
fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
for k, bl in enumerate(blocks):
    head = bl.split("\n")[0]; vals = [float(re.search(re.escape(n) + r" ([\d.]+)", head).group(1)) for n in names]; per = float(re.search(r"persistence ([\d.]+)", head).group(1))
    bars = ax[k].bar(range(4), vals, color=["C7", "C0", "C9", "C1"]); ax[k].axhline(per, color="k", ls="--", lw=0.9, label="persistence %.3f" % per)
    for r_, v in zip(bars, vals): ax[k].annotate("%.3f" % v, (r_.get_x() + r_.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)
    ax[k].set_ylim(0.55, 0.75); ax[k].set_xticks(range(4)); ax[k].set_xticklabels(["real\nonly", "real + synth.\nweight 1", "real + synth.\nweight 0.3", "synthetic\nonly"], fontsize=7.5); ax[k].set_ylabel("AUC on the held-out real data"); ax[k].legend(loc="upper left"); ax[k].set_title(("held-out repositories (9 folds)" if k == 0 else "temporal") + "; gradient boosting, base + shrunk-rate features")
fig.suptitle("Does adding the synthetic histories to the training data help on the real data?", fontsize=10); save(fig, "C2_pooled_training_level2.png")
# ---- C3 graph visibility
G = pd.read_csv(os.path.join(ROOT, "insights", "results", "l1_edit_graph_features.csv")); chg = ((G.e_added + G.e_removed + G.nodes_added) > 0).groupby(G.td_type).mean()
S = pd.read_csv(os.path.join(ROOT, "synthetic_dataset", "features", "pairs_delta.csv")); dcols = [c for c in S.columns if c.startswith("delta__") and any(k in c for k in ("edge", "cycle", "fan", "nodes", "scc", "density"))]
vs = (S[dcols].abs().sum(axis=1) > 0).groupby(S.ptype).mean()
types = ["complexity", "concurrency", "coupling_cohesion", "dependency_structure", "security"]
fig, ax = plt.subplots(figsize=(8, 3.3)); x = np.arange(5)
b1 = ax.bar(x - 0.19, [chg[t] * 100 for t in types], 0.38, label="real pairs (61)"); b2 = ax.bar(x + 0.19, [vs[t] * 100 for t in types], 0.38, color="C1", label="synthetic pairs (1,321)")
for bb in (b1, b2):
    for r_ in bb: ax.annotate("%.0f" % r_.get_height(), (r_.get_x() + r_.get_width() / 2, r_.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(types, fontsize=7.5); ax.set_ylabel("% of pairs whose dependency graph changes"); ax.legend(); ax.set_title("A file-level graph sees only structural debt, in both data sets")
save(fig, "C3_graph_visibility_both.png")
# ---- C4 model dependence on the real pairs, and pooling for Level 1
pp = pd.read_csv(os.path.join(RES, "n8_per_project.csv")).sort_values("n", ascending=False)
fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.6), gridspec_kw={"width_ratios": [1.5, 1]})
x = np.arange(len(pp)); w = 0.38
ax[0].bar(x - w / 2, pp["random forest (raw delta)"], w, label="random forest, raw delta"); ax[0].bar(x + w / 2, pp["logistic (direction of the delta)"], w, color="C1", label="logistic regression, direction of the delta")
ax[0].set_xticks(x); ax[0].set_xticklabels(["%s\n(n=%d)" % (a, b) for a, b in zip(pp.project, pp.n)], fontsize=6.5); ax[0].set_ylabel("accuracy when the project is held out"); ax[0].set_ylim(0, 1.25); ax[0].legend(fontsize=6.5, loc="upper right")
ax[0].set_title("Real pairs: which model generalises depends on what is missing in training")
t7 = open(os.path.join(RES, "n7_combined.txt")).read()
rows = re.findall(r"^\s+(random forest|logistic)\s+(real only|real \+ synthetic, weight 1|synthetic only)\s+accuracy ([\d.]+)", t7, re.M)
d = {(a, b): float(c) for a, b, c in rows}
labs = ["real only", "real + synthetic, weight 1", "synthetic only"]
for k, (mdl, col) in enumerate((("random forest", "C0"), ("logistic", "C1"))):
    bars = ax[1].bar(np.arange(3) + (k - 0.5) * 0.38, [d[(mdl, l)] for l in labs], 0.38, color=col, label=mdl + ", direction of the delta")
    for r_ in bars: ax[1].annotate("%.2f" % r_.get_height(), (r_.get_x() + r_.get_width() / 2, r_.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)
ax[1].axhline(0.426, color="k", ls="--", lw=0.8, label="majority 0.426"); ax[1].set_xticks(range(3)); ax[1].set_xticklabels(["real\nonly", "real +\nsynthetic", "synthetic\nonly"]); ax[1].set_ylim(0, 0.8); ax[1].set_ylabel("leave-one-project-out accuracy"); ax[1].legend(fontsize=6.5, loc="upper right"); ax[1].set_title("Adding the 1,321 synthetic pairs\ndoes not help the real classifier")
save(fig, "C4_level1_model_dependence_and_pooling.png")
print("combined figures ok")
