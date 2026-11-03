"""02_real_results: the graphs of the real data (61 pairs, 9 histories), matplotlib defaults."""
import json, os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi": 220, "font.size": 8.5, "legend.fontsize": 7.5})
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(os.path.dirname(__file__), "02_real_results")
P = json.load(open(os.path.join(ROOT, "presentation", "data", "prio.json"))); CV = json.load(open(os.path.join(ROOT, "presentation", "data", "curve.json")))
HV = json.load(open(os.path.join(ROOT, "presentation", "data", "hurdle_vs_persistence.json")))
def save(fig, n): fig.tight_layout(); fig.savefig(os.path.join(OUT, n), facecolor="white"); plt.close(fig)
def labels(ax, bars, fmt="%.2f", fs=7.5, h=False):
    for b in bars:
        v = b.get_width() if h else b.get_height()
        ax.annotate(fmt % v, ((v, b.get_y() + b.get_height() / 2) if h else (b.get_x() + b.get_width() / 2, v)), xytext=((2, 0) if h else (0, 2)), textcoords="offset points", ha="left" if h else "center", va="center" if h else "bottom", fontsize=fs)
# 1 dataset composition
fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.2))
b = ax[0].bar(["candidates", "after audit", "final\n(+9 added)"], [102, 52, 61], color="C0"); labels(ax[0], b, "%.0f"); ax[0].set_ylabel("pairs"); ax[0].set_title("How the 61 pairs came about")
types = ["concurrency", "security", "dependency", "coupling", "complexity"]; py, c = [24, 2, 4, 6, 5], [2, 14, 3, 0, 1]
y = np.arange(5)[::-1]; ax[1].barh(y, py, color="C0", label="Python"); ax[1].barh(y, c, left=py, color="C1", label="C/C++")
for yy, p_, c_ in zip(y, py, c): ax[1].annotate(str(p_ + c_), (p_ + c_, yy), xytext=(3, 0), textcoords="offset points", va="center", fontweight="bold")
ax[1].set_yticks(y); ax[1].set_yticklabels(types); ax[1].set_xlim(0, 31); ax[1].legend(loc="lower right"); ax[1].set_title("Pairs per debt type and language")
tm = pd.DataFrame({"t": ["concurrency", "security", "complexity", "coupling", "dependency"], "m": [161.6, 92.0, 53.5, 22.7, 3.2], "f": [3.4, 2.4, 1.8, 1.4, 1.05]})
b = ax[2].bar(tm.t, tm.m, color="C2"); labels(ax[2], b, "%.0f"); ax[2].set_ylabel("extra fix minutes per pair (time model)"); ax[2].set_title("Time model: slowdown factor per type"); plt.setp(ax[2].get_xticklabels(), rotation=15, fontsize=7)
for r_, f_ in zip(b, tm.f): ax[2].annotate("x%.2f" % f_, (r_.get_x() + r_.get_width() / 2, 4), ha="center", fontsize=7, color="white")
save(fig, "R1_dataset_composition.png")
# 2 level 1 accuracy
fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
cats = ["stratified\nfolds", "20 random\nsplits", "by project\nfolds", "leave one\nproject out"]
wo, wi = [0.787, 0.840, 0.311, 0.426], [0.918, 0.938, 0.508, 0.508]
b1 = ax[0].bar(np.arange(4) - 0.19, wo, 0.38, color="C7", label="without time"); b2 = ax[0].bar(np.arange(4) + 0.19, wi, 0.38, color="C1", label="with time"); labels(ax[0], b1); labels(ax[0], b2)
ax[0].axhline(0.426, color="k", ls="--", lw=0.8, label="majority 0.426"); ax[0].set_xticks(range(4)); ax[0].set_xticklabels(cats); ax[0].set_ylim(0, 1.1); ax[0].set_ylabel("accuracy"); ax[0].legend(loc="upper right", ncol=3, fontsize=6.5); ax[0].set_title("10-best features + random forest, by protocol")
mc = ["10-best + RF", "10-best + LR", "kNN", "SVM (RBF)", "Logistic reg.", "Grad. boosting", "Random forest"]
w1 = [0.787, 0.525, 0.639, 0.705, 0.721, 0.836, 0.885]; w2 = [0.918, 0.803, 0.639, 0.705, 0.787, 0.918, 0.885]
yy = np.arange(7)[::-1]; hb1 = ax[1].barh(yy + 0.19, w1, 0.38, color="C7", label="without time"); hb2 = ax[1].barh(yy - 0.19, w2, 0.38, color="C1", label="with time"); labels(ax[1], hb1, h=True, fs=6.5); labels(ax[1], hb2, h=True, fs=6.5)
ax[1].set_yticks(yy); ax[1].set_yticklabels(mc); ax[1].set_xlim(0, 1.1); ax[1].set_xlabel("accuracy, stratified folds"); ax[1].legend(loc="center right"); ax[1].set_title("Seven classifiers")
save(fig, "R2_level1_accuracy.png")
# 3 time controls
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.2))
cc = ["no time", "real time", "shuffled", "noise 0.25", "noise 0.5", "noise 1.0"]; vv = [0.840, 0.939, 0.839, 0.926, 0.884, 0.839]
b = ax[0].bar(cc, vv, color=["C7", "C1", "C0", "C1", "C1", "C1"]); labels(ax[0], b, "%.3f"); ax[0].set_ylim(0.7, 1.0); ax[0].set_ylabel("accuracy, 20 random splits"); ax[0].set_title("The time gain: controls"); plt.setp(ax[0].get_xticklabels(), fontsize=7.5)
cfg = ["weak", "used", "strong", "near-deterministic"]; ta = [0.60, 0.96, 0.98, 1.00]; ga = [0.03, 0.11, 0.12, 0.12]
x = np.arange(4); b1 = ax[1].bar(x - 0.19, ta, 0.38, label="time alone, accuracy"); b2 = ax[1].bar(x + 0.19, ga, 0.38, label="gain of 10-best + RF"); labels(ax[1], b1); labels(ax[1], b2)
ax[1].set_xticks(x); ax[1].set_xticklabels(cfg); ax[1].legend(); ax[1].set_title("Four time models (the used one was chosen after seeing the classifiers)")
save(fig, "R3_time_feature_controls.png")
# 4 ranking
g = lambda m: [P["leave-one-repo-out|%s" % m][k] * 100 for k in ("cap10", "cap20", "cap30")]
fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.6), gridspec_kw={"width_ratios": [1.1, 1.2]})
S = [("random", [10, 20, 30], "C7"), ("persistence", g("persistence"), "C0"), ("RF regression", g("rf_pm"), "C2"), ("two-part model", g("hurdle_rf"), "C1")]
for j, (n, v, col) in enumerate(S):
    b = ax[0].bar(np.arange(3) + (j - 1.5) * 0.2, v, 0.2, color=col, label=n); labels(ax[0], b, "%.0f", 7)
ax[0].set_xticks(range(3)); ax[0].set_xticklabels(["top 10 %", "top 20 %", "top 30 %"]); ax[0].set_ylabel("% of next-release interest captured"); ax[0].legend(loc="upper left"); ax[0].set_title("Real histories: 123 repository-release groups")
k = CV["k"]
for key, lab, col, ls in (("oracle", "oracle", "k", ":"), ("hurdle_rf", "two-part model", "C1", "-"), ("persistence", "persistence", "C0", "-"), ("rf_pm", "RF regression", "C2", "-")):
    ax[1].plot(k, np.array(CV[key]) * 100, ls, color=col, label=lab, lw=1.6)
ax[1].plot(k, k, color="C7", label="random"); ax[1].set_xlabel("top k % of instances repaid"); ax[1].set_ylabel("% captured"); ax[1].legend(loc="lower right"); ax[1].set_title("Capture curve"); ax[1].grid(alpha=0.3)
save(fig, "R4_ranking_capture.png")
# 5 size vs persistence on the real histories (new)
t = open(os.path.join(ROOT, "insights", "synthetic", "results", "s2_size.txt")).read()
import re
rb = t[t.index("### REAL"):t.index("### SYNTHETIC baseline")]
def grab(k):
    seg = rb[rb.index(" top %d%%" % k):]
    nxt = seg.find(" top", 6)
    seg = seg[:nxt] if nxt > 0 else seg
    return {m.group(1).strip(): float(m.group(2)) for m in re.finditer(r"^\s{3}(.+?)\s{2,}([\d.]+)\s+[-+]", seg, re.M)}
names = ["random", "persistence + size tie-break", "size only", "shrunk events + size tie-break", "size x shrunk rate"]
fig, ax = plt.subplots(figsize=(7.4, 3.5))
for j, n in enumerate(names):
    v = [grab(k)[n] for k in (20, 30, 50)]
    b = ax.bar(np.arange(3) + (j - 2) * 0.16, v, 0.16, label=n.replace(" tie-break", " ties")); labels(ax, b, "%.0f", 6.5)
ax.set_xticks(range(3)); ax.set_xticklabels(["top 20 %", "top 30 %", "top 50 %"]); ax.set_ylabel("% captured"); ax.legend(fontsize=6.5, loc="upper left"); ax.set_title("Real histories: a rule with no history ('largest first') ties persistence")
save(fig, "R5_size_vs_persistence.png")
# 6 interest per project
sys.path.insert(0, os.path.join(ROOT, "insights", "code"))
from common import load_transitions
T = load_transitions()
pm = T.groupby("repo").pm_interest.sum().sort_values()
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.3))
b = ax[0].barh(pm.index, pm.values, color="C0"); labels(ax[0], b, "%.2f", 7, True); ax[0].set_xlabel("interest paid over 20 releases (person-months)"); ax[0].set_title("Interest per project: %.2f person-months in total" % pm.sum())
auc = [("any interest,\nnext release", 0.594, 0.71), ("function,\nnext 100 commits", 0.568, 0.625)]
x = np.arange(2); b1 = ax[1].bar(x - 0.19, [a[1] for a in auc], 0.38, label="unseen repositories"); b2 = ax[1].bar(x + 0.19, [a[2] for a in auc], 0.38, color="C1", label="later releases (temporal)"); labels(ax[1], b1); labels(ax[1], b2)
ax[1].axhline(0.5, color="k", ls="--", lw=0.8, label="chance"); ax[1].set_xticks(x); ax[1].set_xticklabels([a[0] for a in auc]); ax[1].set_ylim(0.4, 0.8); ax[1].set_ylabel("AUC"); ax[1].legend(fontsize=6.5, loc="upper left"); ax[1].set_title("What is predictable")
save(fig, "R6_interest_and_predictability.png")
print("real results ok")
