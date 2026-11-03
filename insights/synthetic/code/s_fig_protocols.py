"""Figure: the two protocols of the talk (leave-one-project-out, temporal) side by side."""
import re
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi": 200, "font.size": 8.5})
R = pd.read_csv("../results/s1_protocols.csv")
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1, 1.5]})
protos = ["random", "leave-one-project-out", "temporal"]
for j, (inp, mod) in enumerate((("delta", "random forest"), ("delta", "10-best + RF (talk)"), ("child only (no twin)", "random forest"))):
    sub = R[(R.input == inp) & (R.model == mod)].set_index("protocol").loc[protos]
    b = ax[0].bar(np.arange(3) + (j - 1) * 0.27, sub.accuracy, 0.27, yerr=[sub.accuracy - sub.lo, sub.hi - sub.accuracy], capsize=2, label="%s, %s" % (inp, mod))
    for r_, v in zip(b, sub.accuracy):
        ax[0].annotate("%.2f" % v, (r_.get_x() + r_.get_width() / 2, 0.02), ha="center", fontsize=7, color="white")
ax[0].axhline(0.206, color="k", ls="--", lw=0.7); ax[0].set_xticks(range(3)); ax[0].set_xticklabels(["random split", "leave one\nproject out", "temporal"])
ax[0].set_ylim(0, 1.05); ax[0].set_ylabel("accuracy, 5 debt types (95 % interval over projects)"); ax[0].set_title("Type of a debt change (1,321 synthetic pairs)"); ax[0].legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1)
t = open("../results/s2_protocols.txt").read()
blocks = re.split(r"\n### ", "\n" + t)[1:]
names = ["shrunk events + size ties", "size x shrunk rate", "learned (GB)"]
cols = ["C1", "C4", "C2"]
labels, data = [], []
for b in blocks:
    head = b.split(":")[0]
    seg = b[b.index("top 20%"):b.index("top 30%")]
    d = {}
    for n in names:
        m = re.search(r"^\s+%s\s+[\d.]+\s+([-+][\d.]+) \(([-+][\d.]+), ([-+][\d.]+)\)" % re.escape(n), seg, re.M)
        d[n] = tuple(float(x) for x in m.groups())
    who = "REAL" if head.startswith("REAL") else ("synth.\nbaseline" if "baseline" in head else "synth.\nall regimes")
    labels.append(who + "\n" + ("LOPO" if "leave-one" in head else "temporal"))
    data.append(d)
for i, d in enumerate(data):
    for k, n in enumerate(names):
        m, lo, hi = d[n]
        ax[1].errorbar(i + (k - 1) * 0.2, m, yerr=[[m - lo], [hi - m]], fmt="o", color=cols[k], capsize=2.5, label=n if i == 0 else None)
ax[1].axhline(0, color="k", lw=0.7); ax[1].set_xticks(range(len(labels))); ax[1].set_xticklabels(labels, fontsize=6.5)
ax[1].set_ylabel("capture minus persistence, top 20 % (points)"); ax[1].set_title("Ranking inside a release: gains over persistence under the two protocols"); ax[1].legend(fontsize=6.5)
fig.tight_layout(); fig.savefig("../figs/sf6_protocols.png"); print("ok")
