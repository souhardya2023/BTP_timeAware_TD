#!/usr/bin/env python3
"""Figures of the second synthetic dataset, the natural pairs and the new experiments (matplotlib, default colours). Run with a Python that has matplotlib + pandas."""
import glob, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RP = os.path.join(ROOT, "real_project_analysis")
F = os.path.join(HERE, "figures"); os.makedirs(F, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "savefig.bbox": "tight"})
def save(n): plt.savefig(os.path.join(F, n), dpi=160); plt.close()
a1 = pd.read_csv(os.path.join(HERE, "acceptance_v1.csv")); a2 = pd.read_csv(os.path.join(HERE, "acceptance_v2.csv"))
M = a1.merge(a2[["test", "value", "passed"]], on="test", suffixes=("_v1", "_v2"))
# 1 acceptance panel (normalised: 0 = lower bound, 1 = upper bound of the acceptance band)
fig, ax = plt.subplots(figsize=(8.2, 8.5)); n = len(M)
for i, r in M.iterrows():
    y = n - 1 - i; w = r.accept_high - r.accept_low
    ax.add_patch(plt.Rectangle((0, y - 0.35), 1, 0.7, color="tab:green", alpha=0.18, lw=0))
    ax.plot([(r.real - r.accept_low) / w], [y], "k|", ms=12, mew=2, label="real corpus" if i == 0 else None)
    for v, ok, mk, c, lab in ((r.value_v1, r.passed_v1, "s", "tab:orange", "first synthetic dataset"), (r.value_v2, r.passed_v2, "o", "tab:blue", "second synthetic dataset")):
        if v == v:
            ax.plot([min(max((v - r.accept_low) / w, -1.2), 2.2)], [y], mk, color=c, mfc=c if ok else "white", ms=6, label=lab if i == 0 else None)
ax.set_yticks(range(n)); ax.set_yticklabels(list(M.test)[::-1], fontsize=7); ax.set_xlim(-1.3, 2.3); ax.set_xticks([0, 1]); ax.set_xticklabels(["lower bound", "upper bound"])
ax.set_title("acceptance panel: %d / %d tests passed (second dataset), %d / %d (first)" % (a2.passed.sum(), len(a2), a1.passed.sum(), len(a1))); ax.legend(loc="lower right", fontsize=7, title="filled = passed")
save("V1_acceptance_panel.png")
# 2 overview of v2
P = pd.read_csv(os.path.join(HERE, "projects.csv")); I = pd.read_csv(os.path.join(HERE, "instances.csv"))
fig, ax = plt.subplots(1, 4, figsize=(14, 3.6))
order = ["S", "M", "L", "X", "H"]
ax[0].boxplot([P[P.tier == t]["loc"] for t in order], tick_labels=["%s\n(%d)" % (t, (P.tier == t).sum()) for t in order], showfliers=False); ax[0].set_ylabel("lines of code (last release)"); ax[0].set_title("150 projects by size tier")
ax[1].boxplot([P[P.tier == t].releases for t in order], tick_labels=order, showfliers=False); ax[1].set_ylabel("releases"); ax[1].set_title("history length")
real = pd.concat([pd.read_csv(f, usecols=["repo", "vi", "nloc0"]) for f in glob.glob(os.path.join(RP, "data", "funcs", "*.csv"))]); real = real[real.vi == real.groupby("repo").vi.transform("max")]
syn = pd.concat([pd.read_csv(f, usecols=["repo", "vi", "nloc0"]) for f in glob.glob(os.path.join(HERE, "real_pipeline_data", "funcs", "*.csv"))]); syn = syn[syn.vi == syn.groupby("repo").vi.transform("max")]
bins = np.logspace(0, 2.4, 30)
ax[2].hist(real.nloc0.clip(lower=1), bins=bins, density=True, alpha=.55, label="real, 33 repositories"); ax[2].hist(syn.nloc0.clip(lower=1), bins=bins, density=True, alpha=.55, label="second dataset"); ax[2].set_xscale("log"); ax[2].set_xlabel("function size (source lines)"); ax[2].set_ylabel("density"); ax[2].legend(fontsize=7); ax[2].set_title("function sizes")
cnt = I.ptype.value_counts(); ax[3].bar([c.replace("_", "\n") for c in cnt.index], cnt.values, color="tab:blue"); ax[3].set_ylabel("typed debt instances"); ax[3].set_title("%d typed instances, %d templates" % (len(I), I.template.nunique())); ax[3].tick_params(axis="x", labelsize=7)
plt.tight_layout(); save("V2_dataset_overview.png")
# 3 Level 1 v1 vs v2 and sim-to-real
L = pd.read_csv(os.path.join(HERE, "results", "level1_v2.csv")); L = L[(L.input == "delta") & (L.model == "random forest")].set_index("data")
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8)); prot = ["random", "held-out project", "held-out template", "temporal"]; x = np.arange(4)
ax[0].bar(x - 0.2, [L.loc["v1", p] for p in prot], 0.4, label="first dataset"); ax[0].bar(x + 0.2, [L.loc["v2", p] for p in prot], 0.4, label="second dataset")
ax[0].axhline(0.459, color="k", ls="--", lw=1); ax[0].text(3.45, 0.47, "real pairs, leave one project out 0.46", ha="right", fontsize=7); ax[0].axhline(0.21, color="gray", ls=":"); ax[0].set_xticks(x); ax[0].set_xticklabels(prot, rotation=12); ax[0].set_ylim(0, 1.05); ax[0].set_ylabel("accuracy, random forest on the delta"); ax[0].legend(loc="lower left"); ax[0].set_title("type of debt on synthetic pairs")
labs = ["first dataset\n(raw)", "second dataset\n(raw)", "second, relative\ndelta", "second, tier H\nonly", "second, sign\nof delta"]; vals = [0.148, 0.148, 0.148, 0.180, 0.344]
ax[1].bar(labs, vals, color="tab:orange"); ax[1].axhline(0.426, color="k", ls="--"); ax[1].text(4.4, 0.435, "majority 0.426", ha="right", fontsize=7); ax[1].set_ylim(0, 0.6); ax[1].set_ylabel("accuracy on the 61 real pairs"); ax[1].set_title("trained on synthetic pairs, tested on real"); ax[1].tick_params(axis="x", labelsize=7)
plt.tight_layout(); save("V3_level1_synthetic_versions.png")
# 4 natural pairs
B = pd.read_csv(os.path.join(RP, "results", "b1_pairs.csv")); R3 = pd.read_csv(os.path.join(RP, "results", "b3_results.csv"))
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
types = ["security", "concurrency", "dependency", "complexity", "coupling"]; w = B.label.value_counts(); d = B[B.dual_ok].label.value_counts()
ax[0].bar(np.arange(5) - 0.2, [w.get(t, 0) for t in types], 0.4, label="weak label (subject)"); ax[0].bar(np.arange(5) + 0.2, [d.get(t, 0) for t in types], 0.4, label="dual evidence"); ax[0].set_xticks(range(5)); ax[0].set_xticklabels(types, rotation=20); ax[0].set_ylabel("natural pairs"); ax[0].legend(fontsize=7); ax[0].set_title("%d pairs from %d repositories" % (len(B), B.repo.nunique()))
mods = ["keywords_rf", "tfidf_lr", "codebert_mean_lr", "codebert_cls_lr", "codebert_mean+keywords"]; nm = ["keyword\ncounts+RF", "TF-IDF\n+LR", "CodeBERT\nmean+LR", "CodeBERT\nCLS+LR", "CodeBERT+\nkeywords"]
for a_, sub, t in ((ax[1], "all weak labels (4 types)", "weak labels (subject only)"), (ax[2], "dual evidence", "dual evidence (subject and diff agree)")):
    s = R3[(R3.subset == sub)].set_index("model"); a_.bar(nm, [s.loc[m, "acc"] for m in mods], color="tab:blue"); a_.axhline(s.loc["majority", "acc"], color="k", ls="--"); a_.set_ylim(0, 1); a_.set_ylabel("accuracy, leave one repository out"); a_.set_title("%s, n=%d" % (t, s.n.iloc[0])); a_.tick_params(axis="x", labelsize=7)
plt.tight_layout(); save("V4_natural_pairs.png")
# 5 CodeBERT
fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.8))
lab = ["first dataset\nmean", "second dataset\nmean", "second dataset\nCLS"]; r = [(0.969, 0.977, 0.618), (0.955, 0.967, 0.741), (0.952, 0.967, 0.684)]
for k, nm_ in enumerate(["random split", "held-out project", "held-out template"]):
    ax[0].bar(np.arange(3) + (k - 1) * 0.27, [v[k] for v in r], 0.27, label=nm_)
ax[0].set_xticks(range(3)); ax[0].set_xticklabels(lab); ax[0].set_ylim(0, 1.05); ax[0].set_ylabel("accuracy"); ax[0].legend(fontsize=7, loc="lower left"); ax[0].set_title("frozen CodeBERT on synthetic pairs")
t = ["synthetic v2 ->\nreal 61", "synthetic v2 ->\nnatural", "natural ->\nreal (4 types)", "natural ->\nsynthetic v2", "synthetic v2 +\nnatural -> real 61"]
ax[1].bar(np.arange(5) - 0.2, [0.197, 0.260, 0.545, 0.616, 0.443], 0.4, label="mean-pooled"); ax[1].bar(np.arange(5) + 0.2, [0.344, 0.220, 0.564, 0.563, 0.623], 0.4, label="CLS")
for i, m_ in enumerate([0.426, 0.426, 0.473, 0.260, 0.426]): ax[1].plot([i - 0.4, i + 0.4], [m_, m_], "k--", lw=1)
ax[1].set_xticks(range(5)); ax[1].set_xticklabels(t, fontsize=7); ax[1].set_ylim(0, 0.8); ax[1].set_ylabel("accuracy (dashed: majority class)"); ax[1].legend(fontsize=7); ax[1].set_title("transfer between data sets")
plt.tight_layout(); save("V5_codebert_transfer.png")
# 6 Level 2: real versus v2
rr = pd.read_csv(os.path.join(RP, "results", "a3_path_of_work_models.csv")); sv = pd.read_csv(os.path.join(HERE, "results_level2", "a3_path_of_work_models.csv"))
mm = ["size", "persist", "persist_size", "logit_base"]; ml = ["size only", "persistence", "persistence,\nsize ties", "size + history\n(logistic)"]
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
for a_, col, t in ((ax[0], "auc", "AUC, leave one repository out"), (ax[1], "cap20", "capture, top 20 %, leave one repository out")):
    for k, (d_, nm_) in enumerate(((rr, "real, 33 repositories"), (sv, "second dataset"))):
        s = d_[d_.protocol.str.startswith("leave")].set_index("model"); a_.bar(np.arange(4) + (k - .5) * 0.38, [s.loc[m, col] for m in mm], 0.38, label=nm_)
    a_.set_xticks(range(4)); a_.set_xticklabels(ml, fontsize=7); a_.set_title(t); a_.legend(fontsize=7)
ax[0].set_ylim(0.5, 0.85)
pr = pd.read_csv(os.path.join(RP, "results", "a3_path_of_work_paired.csv"))
ax[2].axis("off"); ax[2].text(0, 0.95, "size + history minus persistence\n(size ties), leave one repository out\n\nreal, top 30 %%: %+.1f points (+0.8 to +5.2)\nreal, top 20 %%: %+.1f points (-0.1 to +4.6)\nsecond dataset, top 30 %%: +0.9 (-1.3 to +3.2)\nsecond dataset, top 20 %%: +0.4 (-2.0 to +2.7)" % (3.0, 2.3), va="top", fontsize=9)
plt.tight_layout(); save("V6_level2_real_vs_synthetic.png")
# 7 J5 nested
fig, ax = plt.subplots(figsize=(7, 3.6)); lab = ["random forest", "linear model, nested\nchoice", "hybrid", "linear model, earlier\n(optimistic)"]; x = np.arange(4)
ov = [0.459, 0.311, 0.459, 0.66]; bo = [0.0, 0.0, 0.0, 0.917]; ot = [0.757, 0.514, 0.757, 0.51]
ax.bar(x - 0.27, ov, 0.27, label="overall (61)"); ax.bar(x, bo, 0.27, label="boltons (24)"); ax.bar(x + 0.27, ot, 0.27, label="other 37 pairs"); ax.axhline(0.426, color="k", ls="--"); ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=8); ax.set_ylabel("accuracy, leave one project out"); ax.legend(fontsize=7); ax.set_title("the direction-only linear model does not survive nested validation")
save("V7_nested_linear.png")
print(sorted(os.listdir(F)))
