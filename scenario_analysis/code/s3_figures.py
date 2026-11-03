"""Plots for the scenario slides (matplotlib, simple). Reads ../results/s1_scenarios.csv and s2_summary.csv."""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); FIG = os.path.join(HERE, "..", "figures")
INK, GREY, ACC = "#111111", "#8a8a8a", "#1f5fa8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 220, "savefig.transparent": True})
d = pd.read_csv(os.path.join(RES, "s1_scenarios.csv"))
show = [("large for its repository (top third)", "function is large for its repository"), ("minor or major release", "release is minor or major"), ("busy release (commits above repo median)", "release has many commits"),
        ("a big commit (top quarter) creates debt more often", "big commit creates debt"), ("a 'refactor/simplify' commit removes debt more often", "refactor commit removes debt"),
        ("Long Method", "Long Method (weak, size-adjusted)"),
        ("paid in the previous release pair", "paid in the previous release"), ("Many Parameters", "Many Parameters"), ("new debt (age 0-1 releases)", "new debt (age 0-1)"),
        ("long gap since last tag (above repo median)", "long gap since last tag"), ("file holds 3+ debt instances", "file holds 3+ debt instances"),
        ("Complex Method", "Complex Method"), ("a sibling in the file paid before", "sibling in the file paid before"), ("debt function is edited more than a clean one", "debt function edited more than clean"),
        ("a bug-fix commit creates debt more often", "bug-fix commit creates debt"), ("old debt (age 7+ releases)", "old debt (age 7+)"), ("two or more smells in the same function", "2+ smells in one function")]
d = d.set_index("scenario").loc[[s for s, _ in show]]
fig, ax = plt.subplots(figsize=(6.7, 4.4))
y = np.arange(len(show))[::-1]
for i, (s, lab) in enumerate(show):
    r = d.loc[s]
    for off, tag, col, mk in ((0.17, "python", GREY, "o"), (-0.17, "c", ACC, "s")):
        rr, lo, hi = r[f"{tag}_rr"], r[f"{tag}_lo"], r[f"{tag}_hi"]
        ax.plot([lo, hi], [y[i] + off] * 2, color=col, lw=1.6); ax.plot(rr, y[i] + off, mk, color=col, ms=5)
ax.axvline(1, color=INK, lw=1, ls="--"); ax.set_xscale("log"); ax.set_xlim(0.3, 20)
ax.set_xticks([0.5, 1, 2, 5, 10]); ax.set_xticklabels(["0.5", "1", "2", "5", "10"])
ax.set_yticks(y); ax.set_yticklabels([l for _, l in show], fontsize=9)
for b in (10.5, 5.5):
    ax.axhline(b, color=GREY, lw=0.6)
# group labels (verdict) on the right
ax.text(21, 13.5, "REPEATS", rotation=-90, va="center", ha="left", fontsize=10, fontweight="bold", clip_on=False)
ax.text(21, 8, "LANGUAGE-\nSPECIFIC", rotation=-90, va="center", ha="left", fontsize=9, fontweight="bold", clip_on=False)
ax.text(21, 2.5, "NOISE", rotation=-90, va="center", ha="left", fontsize=10, fontweight="bold", clip_on=False)
ax.set_xlabel("rate ratio (1 = no effect)")
ax.plot([], [], "o", color=GREY, label="Python repositories"); ax.plot([], [], "s", color=ACC, label="C/C++ repositories"); ax.legend(frameon=False, fontsize=9, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "s1_forest.png")); plt.close(fig)

# replication of rules found by the data
s = pd.read_csv(os.path.join(RES, "s2_summary.csv")); s = s[s["mode"].str.startswith("instance")].set_index("split")
labs = [("python -> c", "found in Python,\ntested on C/C++"), ("c -> python", "found in C/C++,\ntested on Python"), ("random repo halves", "random halves\n(20 splits)"), ("real -> synthetic", "found in real,\ntested on benchmark")]
fig, ax = plt.subplots(figsize=(6.0, 3.4))
vals = [100 * s.loc[k, "share_repeat"] for k, _ in labs]; cnt = [f"{int(s.loc[k,'repeat'])}/{int(s.loc[k,'rules'])}" for k, _ in labs]
b = ax.bar([l for _, l in labs], vals, color=[ACC, GREY, ACC, ACC], width=0.55)
for r, v, c in zip(b, vals, cnt): ax.text(r.get_x() + r.get_width() / 2, v + 2, f"{v:.0f}%\n({c} rules)", ha="center", fontsize=10)
ax.set_ylim(0, 128); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_ylabel("% of discovered rules that repeat"); plt.xticks(fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "s2_rules_replication.png")); plt.close(fig)

# agreement of the benchmark with real direction
x = pd.read_csv(os.path.join(RES, "s1_scenarios.csv")).dropna(subset=["synthetic_rr"])
real_dir = np.sign(np.log((x.python_rr * x.c_rr) ** .5)); syn_dir = np.sign(np.log(x.synthetic_rr))
print("benchmark direction agrees with real in", int((real_dir == syn_dir).sum()), "of", len(x), "scenarios;", "on REPEATS only:",
      int(((real_dir == syn_dir) & x.verdict.str.startswith("REPEATS")).sum()), "of", int(x.verdict.str.startswith("REPEATS").sum()))
print(pd.read_csv(os.path.join(RES, "s1_scenarios.csv")).verdict.value_counts().to_dict())
