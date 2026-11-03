"""05_new_experiments: code-to-image CNN, sim-to-real, time-series features, patterns.  Reads ../../insights/new/results."""
import os, re
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi": 220, "font.size": 8.5, "legend.fontsize": 7.5})
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RES = os.path.join(ROOT, "insights", "new", "results"); OUT = os.path.join(os.path.dirname(__file__), "05_new_experiments")
def save(fig, n): fig.tight_layout(); fig.savefig(os.path.join(OUT, n), facecolor="white"); plt.close(fig)
def lab(ax, bars, fmt="%.2f", fs=7):
    for b in bars:
        v = b.get_height(); ax.annotate(fmt % v, (b.get_x() + b.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=fs)
# ---- E1 code image CNN against the other representations (synthetic pairs)
cnn = pd.read_csv(os.path.join(RES, "n2_cnn_code.csv")).set_index("split").accuracy
s1 = pd.read_csv(os.path.join(ROOT, "insights", "synthetic", "results", "s1_pairs_splits.csv")).set_index("input")
words = {"random": 0.964, "project": 0.979, "template": 0.584}
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [1.25, 1]})
splits = ["random", "project", "template"]; nm = ["random split", "held-out project", "held-out template"]
rows = [("133 features, delta, random forest", [s1.loc["delta (child - parent)", s] for s in splits], "C0"), ("code image, CNN", [cnn[s] for s in splits], "C1"), ("patch words, logistic regression", [words[s] for s in splits], "C2")]
for j, (n, v, c) in enumerate(rows):
    b = ax[0].bar(np.arange(3) + (j - 1) * 0.27, v, 0.27, color=c, label=n); lab(ax[0], b)
ax[0].axhline(0.206, color="k", ls="--", lw=0.8); ax[0].set_xticks(range(3)); ax[0].set_xticklabels(nm); ax[0].set_ylim(0, 1.1); ax[0].set_ylabel("accuracy, 5 debt types"); ax[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=6.5); ax[0].set_title("Code as an image does not generalise to a new template")
conf = pd.read_csv(os.path.join(RES, "n2_cnn_sim2real_confusion.csv"), index_col=0)
cls = ["complexity", "concurrency", "coupling_cohesion", "dependency_structure", "security"]; conf = conf.reindex(index=cls, columns=cls, fill_value=0)
im = ax[1].imshow(conf.values, cmap="Blues"); ax[1].set_xticks(range(5)); ax[1].set_yticks(range(5)); ax[1].set_xticklabels([c[:6] for c in cls], rotation=30); ax[1].set_yticklabels(cls, fontsize=7)
for i in range(5):
    for k in range(5): ax[1].text(k, i, int(conf.values[i, k]), ha="center", va="center", fontsize=8, color="white" if conf.values[i, k] > conf.values.max() / 2 else "black")
ax[1].set_xlabel("predicted"); ax[1].set_title("Trained on synthetic images, tested on the\n61 real pairs: accuracy 0.164 (majority 0.426)")
save(fig, "E1_code_image_cnn.png")
# ---- E2 sim-to-real with the features
t = open(os.path.join(RES, "n3b_scale_free.txt")).read()
rows = re.findall(r"^\s{2}(.+?)\s{2,}(RF|logistic)\s+sim->real ([\d.]+) \(Python ([\d.]+), C/C\+\+ ([\d.]+)\)\s+real->sim ([\d.]+)", t, re.M)
rf = {r[0].strip(): r for r in rows if r[1] == "RF"}
names = ["raw", "sign", "unit length", "signed rank within the pair"]
fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
b1 = ax[0].bar(np.arange(4) - 0.19, [float(rf[n][2]) for n in names], 0.38, label="synthetic -> real (61 pairs)"); b2 = ax[0].bar(np.arange(4) + 0.19, [float(rf[n][5]) for n in names], 0.38, color="C1", label="real -> synthetic (1,321)")
lab(ax[0], b1); lab(ax[0], b2); ax[0].axhline(0.426, color="k", ls="--", lw=0.8, label="majority on real 0.426"); ax[0].axhline(0.206, color="C7", ls="--", lw=0.8, label="majority on synthetic 0.206")
ax[0].set_xticks(range(4)); ax[0].set_xticklabels(["raw delta", "sign", "unit length", "signed rank\nwithin the pair"]); ax[0].set_ylabel("accuracy, random forest"); ax[0].set_ylim(0, 0.68); ax[0].legend(fontsize=6, loc="upper left", ncol=1); ax[0].set_title("Does a model transfer between the two data sets?")
S = pd.read_csv(os.path.join(ROOT, "synthetic_dataset", "features", "pairs_delta.csv")); R = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv"))
cols = [c for c in S.columns if c.startswith("delta__") and c in R.columns]
nr, ns = np.linalg.norm(R[cols].values, axis=1), np.linalg.norm(S[cols].values, axis=1)
ax[1].hist(np.log10(nr + 1e-6), bins=25, alpha=0.7, label="real pairs (median %.2f)" % np.median(nr)); ax[1].hist(np.log10(ns + 1e-6), bins=25, alpha=0.7, label="synthetic pairs (median %.1f)" % np.median(ns))
ax[1].set_xlabel("log10 of the length of the delta vector"); ax[1].set_ylabel("pairs"); ax[1].legend(); ax[1].set_title("The same number of features move, 44 times less")
save(fig, "E2_sim_to_real_features.png")
# ---- E3 time-series features
t = open(os.path.join(RES, "n4b_ts_models.txt")).read() if os.path.exists(os.path.join(RES, "n4b_ts_models.txt")) else open(os.path.join(RES, "n4b.log")).read()
blocks = re.split(r"\n### ", t)[1:]
sets = ["base (size, age, past events)", "+ instance time series", "+ project clock", "+ neighbours", "all"]
fig, ax = plt.subplots(1, 4, figsize=(13, 3.4), sharey=False)
sel = [b for b in blocks if b.startswith("REAL, held-out") or b.startswith("REAL, temporal") or b.startswith("SYNTHETIC all regimes, held-out") or b.startswith("SYNTHETIC all regimes, temporal")]
for a, b in zip(ax, sel):
    head = b.split("\n")[0]; line = [l for l in b.split("\n") if l.startswith("AUC")][0]
    vals = [float(re.search(re.escape(s) + r" ([\d.]+)", line).group(1)) for s in sets]; per = float(re.search(r"persistence ([\d.]+)", line).group(1))
    bars = a.bar(range(5), vals, color=["C7", "C0", "C1", "C2", "C4"]); lab(a, bars, "%.3f", 6.5); a.axhline(per, color="k", ls="--", lw=0.9, label="persistence %.3f" % per)
    a.set_ylim(min(vals + [per]) - 0.05, max(vals + [per]) + 0.03); a.set_xticks(range(5)); a.set_xticklabels(["base", "+ instance\nseries", "+ project\nclock", "+ neigh-\nbours", "all"], fontsize=6.5); a.set_title(head.replace("held-out projects", "held-out\nprojects").replace(", ", "\n", 1) if False else head, fontsize=7.5); a.legend(fontsize=6.5, loc="upper left"); a.set_ylabel("AUC")
fig.suptitle("Adding the time series of the git history to the features: AUC for 'interest in this release pair'", fontsize=9.5); save(fig, "E3_time_series_features.png")
# ---- E4 patterns
IR = pd.read_csv(os.path.join(RES, "n5_archetypes_real.csv")); IS = pd.read_csv(os.path.join(RES, "n5_archetypes_synthetic.csv"))
bins = [-0.001, 0, 0.15, 0.3, 0.6, 1.01]; bl = ["never (frozen)", "<= 15 %", "15-30 %", "30-60 %", "> 60 %"]
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.5), gridspec_kw={"width_ratios": [1, 1, 1]})
sh = pd.DataFrame({"real (n=%d)" % len(IR): pd.cut(IR.rate, bins, labels=bl).value_counts(normalize=True), "synthetic baseline (n=%d)" % len(IS): pd.cut(IS.rate, bins, labels=bl).value_counts(normalize=True)}).loc[bl]
sh.T.plot(kind="bar", stacked=True, ax=ax[0], width=0.6, colormap="viridis"); ax[0].set_ylabel("share of instances (>= 10 releases)"); ax[0].set_title("Lifecycle shapes: share of releases\nwith interest, per instance"); ax[0].legend(fontsize=6, title="events in", title_fontsize=6); plt.setp(ax[0].get_xticklabels(), rotation=0, fontsize=7)
for k, (nm, I, c) in enumerate((("real", IR, "C0"), ("synthetic", IS, "C1"))):
    d = [I[I.live == 0]["size"].values, I[I.live == 1]["size"].values]
    bp = ax[1].boxplot(d, positions=[k * 3, k * 3 + 1], widths=0.8, showfliers=False, patch_artist=True)
    for p_ in bp["boxes"]: p_.set_facecolor(c); p_.set_alpha(0.6)
ax[1].set_xticks([0, 1, 3, 4]); ax[1].set_xticklabels(["real\nfrozen", "real\nlive", "synthetic\nfrozen", "synthetic\nlive"], fontsize=7); ax[1].set_yscale("log"); ax[1].set_ylabel("lines of the debt region"); ax[1].set_title("Frozen debt is small debt (real),\nnot in the generator")
for k, (nm, I) in enumerate((("real", IR), ("synthetic", IS))):
    L = I[I.k > 0]; v = [L.early.mean(), L.late.mean()]
    b = ax[2].bar(np.arange(2) + k * 2.6, v, 0.8, color=["C0", "C1"][k], alpha=0.8); lab(ax[2], b, "%.3f")
ax[2].set_xticks([0, 1, 2.6, 3.6]); ax[2].set_xticklabels(["real\nfirst half", "real\nsecond half", "synth.\nfirst half", "synth.\nsecond half"], fontsize=7); ax[2].set_ylabel("event rate per release"); ax[2].set_title("Real debt gets busier late in its life\n(p = 0.04); synthetic does not")
save(fig, "E4_patterns_real_vs_synthetic.png")
# ---- E5 sequence CNN
p = os.path.join(RES, "n4d_seq_cnn.txt")
if os.path.exists(p):
    rows = []
    for l in open(p).read().splitlines():
        m = re.match(r"(\w+)\s+([\w -]+?)\s+AUC cnn ([\d.]+) persistence ([\d.]+) \| top 20%: persistence ([\d.]+), cnn ([-+][\d.]+) \(([-+][\d.]+), ([-+][\d.]+)\)", l)
        if m: rows.append(m.groups())
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.3))
    lb = ["%s\n%s" % (r[0], r[1].replace("held-out projects", "held-out\nprojects")) for r in rows]
    x = np.arange(len(rows)); b1 = ax[0].bar(x - 0.19, [float(r[3]) for r in rows], 0.38, color="C0", label="persistence"); b2 = ax[0].bar(x + 0.19, [float(r[2]) for r in rows], 0.38, color="C1", label="CNN on the 12-release history image"); lab(ax[0], b1, "%.3f", 6.5); lab(ax[0], b2, "%.3f", 6.5)
    ax[0].set_ylim(0.5, 0.9); ax[0].set_xticks(x); ax[0].set_xticklabels(lb, fontsize=7); ax[0].set_ylabel("AUC"); ax[0].legend(fontsize=6.5); ax[0].set_title("Git history as a time-series image")
    for k, r in enumerate(rows):
        m_, lo, hi = float(r[5]), float(r[6]), float(r[7]); ax[1].errorbar(k, m_, yerr=[[m_ - lo], [hi - m_]], fmt="o", color="C1", capsize=3)
    ax[1].axhline(0, color="k", lw=0.8); ax[1].set_xticks(range(len(rows))); ax[1].set_xticklabels(lb, fontsize=7); ax[1].set_ylabel("capture minus persistence, top 20 % (points)"); ax[1].set_title("Ranking inside a release (95 % interval)")
    save(fig, "E5_sequence_cnn.png")
# ---- E6 size prior and the product, real histories, both protocols
t = open(os.path.join(RES, "n6_size_prior.txt")).read()
real = re.split(r"\n### ", "\n" + t)[1:3]
names = ["size only", "shrunk events + size ties", "size x shrunk rate", "size prior + history (posterior)"]
fig, ax = plt.subplots(1, 2, figsize=(11, 3.4), sharey=True)
for a, blk in zip(ax, real):
    head = blk.split("\n")[0].split(":")[0]
    for q, col in ((20, "C0"), (30, "C1")):
        line = [l for l in blk.split("\n") if l.startswith(" top %d%%" % q)][0]
        for k, n in enumerate(names):
            m = re.search(re.escape(n) + r" ([-+][\d.]+) \(([-+][\d.]+), ([-+][\d.]+)\)", line)
            v, lo, hi = (float(x) for x in m.groups())
            a.errorbar(k + (0.12 if q == 30 else -0.12), v, yerr=[[v - lo], [hi - v]], fmt="o", color=col, capsize=3, label=("top %d%%" % q) if k == 0 else None)
    a.axhline(0, color="k", lw=0.8); a.set_xticks(range(4)); a.set_xticklabels(["size\nonly", "shrunk\nevents", "size x\nshrunk rate", "size prior +\nhistory"], fontsize=7.5); a.set_title("REAL, " + head.replace("REAL, ", ""), fontsize=9); a.legend(fontsize=7)
ax[0].set_ylabel("capture minus persistence (points, 95 % interval)")
fig.suptitle("Size and history together: the one candidate that is positive under both protocols (123 and 48 groups)", fontsize=9.5); save(fig, "E6_size_and_history.png")
# ---- E7 CodeBERT
pt = pd.read_csv(os.path.join(RES, "n9c_fusion_per_template.csv"))
fig, ax = plt.subplots(1, 3, figsize=(14, 5.2), gridspec_kw={"width_ratios": [1.5, 1, 0.8]})
y = np.arange(len(pt))[::-1]
ax[0].barh(y + 0.27, pt["features RF"], 0.27, color="C0", label="133 features, random forest"); ax[0].barh(y, pt["CodeBERT"], 0.27, color="C1", label="CodeBERT embedding, logistic regression"); ax[0].barh(y - 0.27, pt["fusion"], 0.27, color="C2", label="average of both (exploratory)")
ax[0].set_yticks(y); ax[0].set_yticklabels(pt.template, fontsize=6.5); ax[0].set_xlabel("accuracy when this template is held out"); ax[0].legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=1); ax[0].set_title("Per template: complementary, not better")
splits = ["random\nsplit", "held-out\nproject", "held-out\ntemplate", "temporal"]
vals = {"133 features (RF)": [0.942, 0.960, 0.828, 0.915], "CodeBERT (frozen)": [0.969, 0.977, 0.618, 0.949], "code-image CNN": [0.970, 0.977, 0.561, np.nan], "patch words": [0.964, 0.979, 0.584, np.nan]}
for j, (n, v) in enumerate(vals.items()):
    b = ax[1].bar(np.arange(4) + (j - 1.5) * 0.2, v, 0.2, label=n)
ax[1].axhline(0.206, color="k", ls="--", lw=0.8); ax[1].set_xticks(range(4)); ax[1].set_xticklabels(splits, fontsize=7.5); ax[1].set_ylim(0, 1.35); ax[1].set_ylabel("accuracy, 5 debt types"); ax[1].legend(fontsize=6, loc="upper center", ncol=2); ax[1].set_title("Synthetic pairs, by split")
sr = [("133 features\nRF", 0.148), ("code image\nCNN", 0.164), ("CodeBERT\nmean-pooled", 0.295), ("CodeBERT\n[CLS]", 0.344)]
b = ax[2].bar(range(4), [v for _, v in sr], color=["C0", "C3", "C1", "C1"])
for r_, (_, v) in zip(b, sr): ax[2].annotate("%.2f" % v, (r_.get_x() + r_.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)
ax[2].axhline(0.426, color="k", ls="--", lw=0.8, label="majority 0.426"); ax[2].set_xticks(range(4)); ax[2].set_xticklabels([n for n, _ in sr], fontsize=6.5); ax[2].set_ylim(0, 0.6); ax[2].set_ylabel("accuracy on the 61 real pairs"); ax[2].legend(fontsize=6.5); ax[2].set_title("Trained on synthetic,\ntested on real")
save(fig, "E7_codebert_embeddings.png")
print("experiment figures ok")
