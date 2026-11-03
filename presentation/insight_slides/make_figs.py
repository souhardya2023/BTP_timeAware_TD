"""Plots for the added slides (matplotlib only, simple style). Numbers come from real_project_analysis/results and presentation/data."""
import glob, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "figs"); os.makedirs(FD, exist_ok=True)
RES = os.path.join(HERE, "..", "..", "real_project_analysis", "results")
RAW = os.path.join(HERE, "..", "..", "real_project_analysis", "data")
PRES = os.path.join(HERE, "..", "data")
ML = os.path.join(HERE, "..", "..", "ml_model", "results", "summary.csv")

INK, GREY, ACC = "#111111", "#b5b5b5", "#1f5fa8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 1.0, "savefig.dpi": 220, "savefig.transparent": True})


def bars_label(ax, bars, fmt="{:.2f}", dy=0.01):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy, fmt.format(b.get_height()), ha="center", va="bottom", fontsize=11)


# ---------- result 1: debt type accuracy by protocol --------------------------------------------------------------------------------
d = pd.read_csv(ML)
d = d[(d.layout == "delta_only") & (d.model == "kbest10_random_forest")]
order = [("given_stratified", "stratified\nfolds"), ("repeated_stratified", "20 random\nsplits"), ("given_by_project", "by project\nfolds"), ("leave_one_project_out", "leave one\nproject out")]
wo = [float(d[(d.protocol == p) & (~d.with_time)].accuracy_mean.iloc[0]) for p, _ in order]
wt = [float(d[(d.protocol == p) & (d.with_time)].accuracy_mean.iloc[0]) for p, _ in order]
fig, ax = plt.subplots(figsize=(6.2, 3.3))
x = np.arange(4); w = 0.36
b1 = ax.bar(x - w / 2, wo, w, color=GREY, label="without fix time"); b2 = ax.bar(x + w / 2, wt, w, color=ACC, label="with fix time")
bars_label(ax, b1); bars_label(ax, b2)
ax.axhline(0.426, color=INK, ls="--", lw=1); ax.text(-0.45, 0.445, "majority 0.43", ha="left", fontsize=10)
ax.set_xticks(x); ax.set_xticklabels([l for _, l in order]); ax.set_ylim(0, 1.12); ax.set_ylabel("accuracy")
ax.legend(frameon=False, loc="upper right", fontsize=10, bbox_to_anchor=(1.0, 1.08), ncol=2)
fig.tight_layout(); fig.savefig(f"{FD}/r1_type_accuracy.png"); plt.close(fig)

# ---------- result 2: ranking, capture in the top k% (9 repositories, 123 groups) ---------------------------------------------------------
s = pd.read_csv(f"{PRES}/prioritization_summary.csv"); s = s[s.protocol == "leave-one-repo-out"].set_index("model")
rows = [("random", [10, 20, 30]), ("persistence", [100 * s.loc["persistence", c] for c in ("cap10", "cap20", "cap30")]), ("two-part model", [100 * s.loc["hurdle_rf", c] for c in ("cap10", "cap20", "cap30")])]
fig, ax = plt.subplots(figsize=(5.4, 3.3))
x = np.arange(3); w = 0.26; cols = [GREY, "#6b6b6b", ACC]
for i, (n, v) in enumerate(rows):
    b = ax.bar(x + (i - 1) * w, v, w, color=cols[i], label=n); bars_label(ax, b, "{:.0f}", 0.8)
ax.set_xticks(x); ax.set_xticklabels(["top 10%", "top 20%", "top 30%"]); ax.set_ylabel("% of next-release interest\ncaptured"); ax.set_ylim(0, 62)
ax.legend(frameon=False, fontsize=10, loc="upper left")
fig.tight_layout(); fig.savefig(f"{FD}/r2_capture_9repos.png"); plt.close(fig)

# ---------- result 3: capture on 33 repositories, top 20% / 30% ---------------------------------------------------------------------------
g = pd.read_csv(f"{RES}/a3_group_caps.csv"); g = g[g.protocol == "LORO"]
m = g.groupby(["model", "top"]).cap.mean() * 100
names = [("random", None, "random"), ("size", "size", "size only"), ("persist", "persist", "persistence"), ("logit_base", "logit_base", "size + history")]
fig, ax = plt.subplots(figsize=(5.4, 3.3))
vals = []
for lab, key, nm in names:
    vals.append([20.0, 30.0] if key is None else [m[(key, 20)], m[(key, 30)]])
x = np.arange(2); w = 0.2; cols = [GREY, "#8a8a8a", "#5a5a5a", ACC]
for i, (lab, key, nm) in enumerate(names):
    b = ax.bar(x + (i - 1.5) * w, vals[i], w, color=cols[i], label=nm); bars_label(ax, b, "{:.1f}", 0.8)
ax.set_xticks(x); ax.set_xticklabels(["top 20%", "top 30%"]); ax.set_ylabel("% of next-release interest\ncaptured"); ax.set_ylim(0, 66)
ax.legend(frameon=False, fontsize=9, loc="upper left", ncol=2)
fig.tight_layout(); fig.savefig(f"{FD}/r3_capture_33repos.png"); plt.close(fig)
print("capture 33:", {k: [round(v, 1) for v in vals[i]] for i, (k, _, _) in enumerate(names)})

# ---------- insight 1: concentration + memory ---------------------------------------------------------------------------------------------
pm = []
for f in glob.glob(f"{RAW}/transitions/*.csv"):
    t = pd.read_csv(f)
    if len(t): pm.append(t[t.cls != "introduced"].groupby(["repo", "key"]).pm_interest.sum())
pm = pd.concat(pm).values; pm = np.sort(pm)[::-1]
cum = np.cumsum(pm) / pm.sum(); fr = np.arange(1, len(pm) + 1) / len(pm)
print("instances", len(pm), "top10%", cum[int(.1 * len(pm)) - 1], "top20%", cum[int(.2 * len(pm)) - 1])
fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.2))
ax = axs[0]
ax.plot(np.r_[0, fr] * 100, np.r_[0, cum] * 100, color=ACC, lw=2.2); ax.plot([0, 100], [0, 100], color=GREY, lw=1.5, ls="--")
ax.set_xlabel("% of debt instances (largest interest first)"); ax.set_ylabel("% of all interest"); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.annotate("top 10% hold 80%", xy=(10, 80), xytext=(28, 62), arrowprops=dict(arrowstyle="-", color=INK), fontsize=11)
ax = axs[1]
dose = pd.read_csv(f"{RES}/a3_memory_dose.csv")
b = ax.bar(["0", "1", "2", "3-4", "5+"], 100 * dose["mean"], color=[GREY, ACC, ACC, ACC, ACC]); bars_label(ax, b, "{:.0f}%", 1)
ax.set_xlabel("events in earlier releases"); ax.set_ylabel("% paying interest\nin the next release"); ax.set_ylim(0, 52)
fig.tight_layout(); fig.savefig(f"{FD}/i1_concentration_memory.png"); plt.close(fig)

# ---------- insight 2: debt is not avoided ------------------------------------------------------------------------------------------------
er = pd.read_csv(f"{RES}/a3_function_edit_rate_by_size.csv", header=[0, 1], index_col=0).iloc[1:].reset_index()
er.columns = ["bin", "clean", "debt", "n0", "n1"]; er = er[er.bin.isin(["6-10", "11-20", "21-40", "41-80"])]
fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.2))
ax = axs[0]
b = ax.bar(["all changed\nlines", "functions in\nboth releases"], [0.33, 1.11], color=[GREY, ACC], width=0.5); bars_label(ax, b, "{:.2f}", 0.03)
ax.axhline(1, color=INK, ls="--", lw=1); ax.set_ylabel("edit share / code share\n(1 = no avoidance)"); ax.set_ylim(0, 1.45)
ax = axs[1]
x = np.arange(len(er)); w = 0.36
b1 = ax.bar(x - w / 2, 100 * er.clean.astype(float), w, color=GREY, label="clean function"); b2 = ax.bar(x + w / 2, 100 * er.debt.astype(float), w, color=ACC, label="debt function")
bars_label(ax, b1, "{:.0f}", 0.4); bars_label(ax, b2, "{:.0f}", 0.4)
ax.set_xticks(x); ax.set_xticklabels(er.bin); ax.set_xlabel("function size (lines)"); ax.set_ylabel("% edited in a release pair"); ax.set_ylim(0, 29)
ax.legend(frameon=False, fontsize=10, loc="upper left")
fig.tight_layout(); fig.savefig(f"{FD}/i2_not_avoided.png"); plt.close(fig)

# ---------- insight 3: the release type is the clock ---------------------------------------------------------------------------------------
rc = pd.read_csv(f"{RES}/a3_release_clock.csv")
rate = rc.groupby("step").rate.mean().reindex(["patch", "minor", "major"]); n = rc.groupby("step").size().reindex(["patch", "minor", "major"])
fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.2))
ax = axs[0]
b = ax.bar(rate.index, 100 * rate.values, color=[GREY, ACC, ACC], width=0.55); bars_label(ax, b, "{:.0f}%", 0.8)
ax.set_xticklabels([f"{k}\n(n={v})" for k, v in zip(rate.index, n.values)])
ax.set_ylabel("% of debt instances\npaying in a release"); ax.set_ylim(0, 38)
ax = axs[1]
lab = ["release type\n+ days", "commits", "changed\nlines"]; r2 = [0.265, 0.535, 0.705]
b = ax.bar(lab, r2, color=[ACC, GREY, GREY], width=0.55); bars_label(ax, b, "{:.2f}", 0.015)
ax.set_ylabel("R$^2$ of release interest"); ax.set_ylim(0, 0.85)
ax.text(0, 0.40, "known\nbefore", ha="center", fontsize=10); ax.text(1.5, 0.80, "known only after the release", ha="center", fontsize=10)
fig.tight_layout(); fig.savefig(f"{FD}/i3_release_clock.png"); plt.close(fig)
