#!/usr/bin/env python3
"""Plot of ../results/e2_results.csv: accuracy of each embedding model on the same experiments (mean pooling), majority share as a dash. -> ../figures/e3_models.png"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); FIG = os.path.join(HERE, "..", "figures")
INK = "#111111"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 220, "savefig.transparent": True})
R = pd.read_csv(os.path.join(RES, "e2_results.csv")); R = R[R.pooling.isin(["mean", "-"])]
exps = [("N-dual", "natural pairs\n(held-out repo)"), ("S-templ", "synthetic\n(held-out template)"), ("T-syn", "synthetic → real"), ("T-nat", "natural → real"), ("T-both", "both → real")]
order = ["tfidf (not a foundation model)", "roberta", "codebert", "graphcodebert", "unixcoder", "codet5", "qwen_coder"]
names = {"tfidf (not a foundation model)": "TF-IDF (reference)", "roberta": "RoBERTa (text)", "codebert": "CodeBERT", "graphcodebert": "GraphCodeBERT", "unixcoder": "UniXcoder", "codet5": "CodeT5", "qwen_coder": "Qwen2.5-Coder"}
order = [m for m in order if m in set(R.model)]
cols = ["#d0d0d0", "#a8a8a8", "#1f5fa8", "#4f86c6", "#7fa8d8", "#5a5a5a", "#111111"]
fig, ax = plt.subplots(figsize=(9.2, 3.6)); w = 0.8 / len(order)
for i, m in enumerate(order):
    v = [float(R[(R.model == m) & (R.experiment == e)].acc.iloc[0]) for e, _ in exps]
    ax.bar(np.arange(len(exps)) + (i - (len(order) - 1) / 2) * w, v, w, color=cols[i % len(cols)], label=names[m])
for j, (e, _) in enumerate(exps):
    mj = float(R[R.experiment == e].majority.iloc[0]); ax.plot([j - 0.42, j + 0.42], [mj, mj], color=INK, ls="--", lw=1.3)
ax.plot([], [], color=INK, ls="--", lw=1.3, label="majority class")
ax.set_xticks(range(len(exps))); ax.set_xticklabels([l for _, l in exps], fontsize=10); ax.set_ylabel("accuracy"); ax.set_ylim(0, 1.0)
ax.legend(frameon=False, fontsize=8.5, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.2))
fig.tight_layout(); fig.savefig(os.path.join(FIG, "e3_models.png")); plt.close(fig)
print(R.pivot(index="model", columns="experiment", values="acc").round(3))
