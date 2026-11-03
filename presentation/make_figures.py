"""Figures for the deck, drawn at the size they have on the slide (inches) so fonts stay readable."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for f in font_manager.findSystemFonts():
    if "LiberationSans" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"savefig.dpi": 300, "font.size": 8.5, "legend.fontsize": 7.5, "axes.titlesize": 9.5})
GREY, BLUE, GREEN, ORANGE, NAVY, LIGHT = "C7", "C0", "C2", "C1", "C0", "C7"
P = json.load(open("data/prio.json"))
CV = json.load(open("data/curve.json"))


def new(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    return fig, ax


def save(fig, name):
    fig.tight_layout(pad=0.4)
    fig.savefig(f"figs/{name}.png", facecolor="white")
    plt.close(fig)


def label_bars(ax, bars, fmt="{:.2f}", pad=2, fs=7.5, horizontal=False):
    for b in bars:
        v = b.get_width() if horizontal else b.get_height()
        if horizontal:
            ax.annotate(fmt.format(v), (v, b.get_y() + b.get_height() / 2), xytext=(pad, 0), textcoords="offset points", va="center", fontsize=fs)
        else:
            ax.annotate(fmt.format(v), (b.get_x() + b.get_width() / 2, v), xytext=(0, pad), textcoords="offset points", ha="center", fontsize=fs)


# dataset funnel
fig, ax = new(2.8, 2.3)
b = ax.bar(["Candidates", "After audit", "Final\n(+9 added)"], [102, 52, 61], color=["C0", "C0", "C0"], width=0.6)
label_bars(ax, b, "{:.0f}", fs=8.5)
ax.set_ylim(0, 120); ax.set_ylabel("pairs"); ax.set_title("Pairs along the way")
save(fig, "funnel")

# types by language
fig, ax = new(3.2, 2.6)
types = ["concurrency", "security", "dependency", "coupling", "complexity"]
py, c = [24, 2, 4, 6, 5], [2, 14, 3, 0, 1]
y = range(len(types))[::-1]
b1 = ax.barh(list(y), py, color=BLUE, label="Python", height=0.6)
b2 = ax.barh(list(y), c, left=py, color=ORANGE, label="C/C++", height=0.6)
for yy, p_, c_ in zip(y, py, c):
    ax.annotate(str(p_), (p_ / 2, yy), ha="center", va="center", color="white", fontsize=7.5)
    if c_:
        ax.annotate(str(c_), (p_ + c_ / 2, yy), ha="center", va="center", color="white" if c_ > 1 else "k", fontsize=7.5)
    ax.annotate(f"{p_ + c_}", (p_ + c_, yy), xytext=(3, 0), textcoords="offset points", va="center", fontsize=8, fontweight="bold")
ax.set_yticks(list(y)); ax.set_yticklabels(types); ax.set_xlim(0, 31); ax.set_xlabel("pairs")
ax.set_title("Pairs per debt type and language"); ax.legend(loc="lower right")
save(fig, "types_language")

# extra fix time
fig, ax = new(3.8, 2.5)
names = ["concurrency", "security", "complexity", "coupling", "dependency"]
vals = [161.6, 92.0, 53.5, 22.7, 3.2]
b = ax.bar(names, vals, color=NAVY, width=0.6)
label_bars(ax, b, "{:.1f}", fs=8)
ax.set_ylim(0, 185); ax.set_ylabel("extra minutes per pair")
ax.set_title("Extra fix time per pair, from the time model"); plt.setp(ax.get_xticklabels(), fontsize=7.5)
save(fig, "fix_time")

# result 1: accuracy by protocol
fig, ax = new(4.7, 2.95)
cats = ["Stratified\nfolds", "20 random\nsplits", "By project\nfolds", "Leave one\nproject out"]
wo, wi = [0.787, 0.840, 0.311, 0.426], [0.918, 0.938, 0.508, 0.508]
x = range(4); w = 0.36
b1 = ax.bar([i - w / 2 for i in x], wo, w, color=GREY, label="without time")
b2 = ax.bar([i + w / 2 for i in x], wi, w, color=ORANGE, label="with time")
label_bars(ax, b1); label_bars(ax, b2)
ax.axhline(0.426, color="k", lw=0.8, ls="--", label="majority baseline 0.426")
ax.set_xticks(list(x)); ax.set_xticklabels(cats); ax.set_ylim(0, 1.08); ax.set_ylabel("accuracy")
ax.set_title("10-best features + random forest, by protocol"); ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.2), fontsize=7.5)
save(fig, "acc_protocol")

# result 1: seven classifiers
fig, ax = new(4.7, 2.95)
mc = ["Random forest", "Gradient boosting", "Logistic regression", "SVM (RBF)", "kNN (k=3)", "10-best + logistic", "10-best + RF"]
wo = [0.885, 0.836, 0.721, 0.705, 0.639, 0.525, 0.787]
wi = [0.885, 0.918, 0.787, 0.705, 0.639, 0.803, 0.918]
y = list(range(len(mc)))[::-1]; h = 0.36
b1 = ax.barh([i + h / 2 for i in y], wo, h, color=GREY, label="without time")
b2 = ax.barh([i - h / 2 for i in y], wi, h, color=ORANGE, label="with time")
label_bars(ax, b1, pad=2, fs=7, horizontal=True); label_bars(ax, b2, pad=2, fs=7, horizontal=True)
ax.set_yticks(y); ax.set_yticklabels(mc); ax.set_xlim(0, 1.08); ax.set_xlabel("accuracy, stratified folds")
ax.set_title("Seven classifiers, with and without time"); ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.4, -0.17))
save(fig, "acc_classifiers")

# result 3: capture bars
fig, ax = new(5.6, 2.9)
g = lambda m: [P[f"leave-one-repo-out|{m}"][k] for k in ("cap10", "cap20", "cap30")]
series = [("Random", [0.10, 0.20, 0.30], LIGHT), ("Persistence (interest already paid)", g("persistence"), BLUE), ("RF regression", g("rf_pm"), GREEN), ("Two-part model", g("hurdle_rf"), ORANGE)]
w = 0.2
for j, (n_, v, col) in enumerate(series):
    bars = ax.bar([i + (j - 1.5) * w for i in range(3)], [t * 100 for t in v], w, color=col, label=n_)
    label_bars(ax, bars, "{:.0f}", fs=7)
ax.set_xticks(range(3)); ax.set_xticklabels(["top 10% of instances", "top 20%", "top 30%"])
ax.set_ylim(0, 62); ax.set_ylabel("% of next-release interest captured")
ax.set_title("Interest captured by the top k% of the ranking"); ax.legend(loc="upper left", fontsize=7.5)
save(fig, "capture_bars")

# result 4: capture curve
fig, ax = new(6.0, 3.9)
k = CV["k"]
ax.plot(k, [t * 100 for t in CV["oracle"]], color="k", lw=1.0, ls=":", label="Oracle (perfect order)")
ax.plot(k, k, color="C7", lw=1.4, label="Random")
ax.plot(k, [t * 100 for t in CV["persistence"]], color=BLUE, lw=1.6, label="Persistence")
ax.plot(k, [t * 100 for t in CV["rf_pm"]], color=GREEN, lw=1.6, label="RF regression")
ax.plot(k, [t * 100 for t in CV["hurdle_rf"]], color=ORANGE, lw=2.0, label="Two-part model")
i50 = k.index(50)
for key, col, dy in (("hurdle_rf", ORANGE, 8), ("persistence", BLUE, -12)):
    v = CV[key][i50] * 100
    ax.scatter([50], [v], color=col, s=14, zorder=5)
    ax.annotate(f"{v:.1f}%", (50, v), xytext=(-34 if dy > 0 else 6, dy), textcoords="offset points", fontsize=8, color=col)
ax.set_xlabel("top k% of instances repaid"); ax.set_ylabel("% of next-release interest captured")
ax.set_xlim(0, 100); ax.set_ylim(0, 102); ax.grid(alpha=0.3)
ax.set_title("Capture of next-release interest, leave-one-repo-out (123 groups)"); ax.legend(loc="lower right")
save(fig, "capture_curve")

# result 5: AUC
fig, ax = new(4.7, 2.9)
cats = ["Any interest,\nnext release", "Function,\nnext 100 commits"]
a, b_ = [0.594, 0.568], [0.71, 0.625]
w = 0.34
b1 = ax.bar([i - w / 2 for i in range(2)], a, w, color=BLUE, label="unseen repositories")
b2 = ax.bar([i + w / 2 for i in range(2)], b_, w, color=ORANGE, label="later releases (temporal)")
label_bars(ax, b1); label_bars(ax, b2)
ax.axhline(0.5, color="k", lw=0.8, ls="--", label="chance 0.5")
ax.set_xticks(range(2)); ax.set_xticklabels(cats); ax.set_ylim(0.4, 0.8); ax.set_ylabel("AUC")
ax.set_title("Can next-release interest be predicted?"); ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.2), fontsize=7.5)
save(fig, "auc")
