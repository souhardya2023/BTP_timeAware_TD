"""Figures of the synthetic-data analysis (matplotlib defaults), parsed from ../results."""
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi": 200, "font.size": 8.5})
R, F = "../results/", "../figs/"
num = r"[-+]?\d+\.?\d*"

def block(text, header):
    i = text.index(header); j = text.find("\n###", i + 5)
    return text[i:j if j > 0 else None]

# ---- 1. ranking by regime
G = pd.read_csv(R + "s2_ranking_per_group.csv")
sc = ["random", "persistence", "shrunk rate", "clock-normalised rate", "learned (GB)", "oracle (latent rate)"]
fig, ax = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [1.2, 1]})
b = G[G.regime == "baseline"].groupby("score").cap20.mean() * 100
bars = ax[0].bar(range(len(sc)), [b[s] for s in sc], color=["C7", "C0", "C1", "C2", "C4", "k"])
for r_, s in zip(bars, sc):
    ax[0].annotate("%.1f" % b[s], (r_.get_x() + r_.get_width() / 2, b[s]), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7.5)
ax[0].set_xticks(range(len(sc))); ax[0].set_xticklabels(["random", "persistence", "shrunk\nrate", "clock-\nnormalised", "learned\n(GB)", "oracle\n(latent rate)"], fontsize=7.5)
ax[0].set_ylabel("% of the interest captured, top 20 %"); ax[0].set_title("Baseline projects (391 groups)")
regs = ["baseline", "sticky", "ar_clock", "decay", "contagion"]
from sload import boot_ci
for j, reg in enumerate(regs):
    pv = G[G.regime == reg].pivot_table(index=["repo", "vi"], columns="score", values="cap20")
    for k, (s, col) in enumerate((("shrunk rate", "C1"), ("learned (GB)", "C4"), ("oracle (latent rate)", "k"))):
        d = (pv[s] - pv["persistence"]).values * 100; lo, hi = boot_ci(d)
        ax[1].errorbar(j + (k - 1) * 0.22, d.mean(), yerr=[[d.mean() - lo], [hi - d.mean()]], fmt="o", color=col, capsize=2.5, label=s if j == 0 else None)
ax[1].axhline(0, color="k", lw=0.7); ax[1].set_xticks(range(5)); ax[1].set_xticklabels(regs, fontsize=7.5)
ax[1].set_ylabel("capture minus persistence (points)"); ax[1].set_title("By regime, 95 % bootstrap interval"); ax[1].legend(fontsize=7)
fig.tight_layout(); fig.savefig(F + "sf1_ranking_regimes.png"); plt.close(fig)

# ---- 2. decomposition
t = open(R + "s2_ablation.txt").read()
bt = block(t, "### baseline")
rows = re.findall(r"^\s{2}(.+?)\s{2,}(%s)\s+(%s) \((%s), (%s)\)" % (num, num, num, num), bt, re.M)
fig, ax = plt.subplots(figsize=(7.2, 3.3))
labs = [r[0].replace("  [persistence]", "") for r in rows]
for i, r in enumerate(rows):
    m, lo, hi = float(r[2]), float(r[3]), float(r[4])
    ax.errorbar(m, len(rows) - 1 - i, xerr=[[m - lo], [hi - m]], fmt="o", color="k" if "oracle (latent" in r[0] else "C0", capsize=2.5)
ax.axvline(0, color="k", lw=0.7); ax.set_yticks(range(len(rows))); ax.set_yticklabels(labs[::-1], fontsize=7.5)
ax.set_xlabel("capture minus persistence, top 20 % (points)"); ax.set_title("The gain is shrinkage, not the clock: baseline, 391 groups")
fig.tight_layout(); fig.savefig(F + "sf2_decomposition.png"); plt.close(fig)

# ---- 3. size, real against synthetic
t = open(R + "s2_size.txt").read()
rb = block(t, "### REAL")
def grab(blk, k):
    seg = blk[blk.index(" top %d%%" % k):]
    seg = seg[:seg.find(" top", 6) if seg.find(" top", 6) > 0 else None]
    return {m.group(1).strip(): float(m.group(2)) for m in re.finditer(r"^\s{3}(.+?)\s{2,}(%s)\s+[-+]" % num, seg, re.M)}
names = ["random", "persistence + size tie-break", "size only", "shrunk events + size tie-break", "size x shrunk rate"]
fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.4), gridspec_kw={"width_ratios": [2, 1]})
for j, n in enumerate(names):
    v = [grab(rb, k)[n] for k in (20, 30, 50)]
    b_ = ax[0].bar(np.arange(3) + (j - 2) * 0.16, v, 0.16, label=n.replace(" + size tie-break", " + size ties"))
ax[0].set_xticks(range(3)); ax[0].set_xticklabels(["top 20 %", "top 30 %", "top 50 %"]); ax[0].set_ylabel("% of the interest captured")
ax[0].set_title("REAL histories (123 groups): size alone is as good as history"); ax[0].legend(fontsize=6.5, loc="upper left")
auc = re.search(r"real: (%s)\s+synthetic: (%s)" % (num, num), t)
v = [float(auc.group(1)), float(auc.group(2))]
b_ = ax[1].bar(["real", "synthetic"], v, color=["C0", "C1"])
for r_, vv in zip(b_, v):
    ax[1].annotate("%.2f" % vv, (r_.get_x() + r_.get_width() / 2, vv), xytext=(0, 2), textcoords="offset points", ha="center")
ax[1].axhline(0.5, color="k", ls="--", lw=0.7); ax[1].set_ylim(0.4, 0.75); ax[1].set_ylabel("AUC of region size alone"); ax[1].set_title("The generator has no size effect")
fig.tight_layout(); fig.savefig(F + "sf3_size_real_vs_synthetic.png"); plt.close(fig)

# ---- 4. time to identify, 5. repayment policy
t = open(R + "s3_timeseries.txt").read()
ag = re.findall(r"age (\S+)\s+n=\s*\d+\s+persistence (%s)\s+shrunk (%s)" % (num, num), t)
fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.2))
ax[0].plot([a[0] for a in ag], [float(a[1]) for a in ag], "o-", label="persistence"); ax[0].plot([a[0] for a in ag], [float(a[2]) for a in ag], "s-", label="shrunk rate")
ax[0].axhline(0.5, color="k", ls="--", lw=0.7); ax[0].set_ylim(0.45, 0.95); ax[0].set_xlabel("releases of history of the instance"); ax[0].set_ylabel("AUC for 'live, not frozen'")
ax[0].set_title("How long until a hot spot is recognised"); ax[0].legend()
pol = block(t, "## (b)")
m = re.search(r"baseline.*?top 20%%: random (%s)  persistence (%s)  shrunk rate (%s)  oracle \(latent rate\) (%s)" % (num, num, num, num), pol, re.S)
v = [float(x) for x in m.groups()]
b_ = ax[1].bar(["random", "persistence", "shrunk\nrate", "oracle\n(latent rate)"], v, color=["C7", "C0", "C1", "k"])
for r_, vv in zip(b_, v):
    ax[1].annotate("%.1f" % vv, (r_.get_x() + r_.get_width() / 2, vv), xytext=(0, 2), textcoords="offset points", ha="center")
ax[1].set_ylabel("% of future interest avoided"); ax[1].set_title("Repay the top 20 % at every release (baseline)")
fig.tight_layout(); fig.savefig(F + "sf4_time_policy.png"); plt.close(fig)

# ---- 6/7/8 Level 1
S = pd.read_csv(R + "s1_pairs_splits.csv")
fig, ax = plt.subplots(1, 3, figsize=(12.4, 3.5), gridspec_kw={"width_ratios": [1.1, 1.5, 0.9]})
splits = ["random", "project", "template", "tier"]
for j, (_, r) in enumerate(S.iterrows()):
    b_ = ax[0].bar(np.arange(4) + (j - 1) * 0.27, [r[s] for s in splits], 0.27, label=r["input"])
    for rr, s in zip(b_, splits):
        ax[0].annotate("%.2f" % r[s], (rr.get_x() + rr.get_width() / 2, r[s]), xytext=(0, 1), textcoords="offset points", ha="center", fontsize=6)
ax[0].set_xticks(range(4)); ax[0].set_xticklabels(["random\nsplit", "held-out\nproject", "held-out\ntemplate", "held-out\ntier"], fontsize=7.5); ax[0].set_ylim(0, 1.12)
ax[0].axhline(0.206, color="k", ls="--", lw=0.7); ax[0].set_ylabel("accuracy, 5 debt types"); ax[0].set_title("Type of a debt change, 1,321 pairs"); ax[0].legend(fontsize=6, loc="lower left")
t1 = open(R + "s1_pairs.txt").read()
tp = re.findall(r"^(complexity|concurrency|coupling_cohesion|dependency_structure|security)?\s+(\w+)\s+(%s)\s+(\d+)$" % num, t1[t1.index("accuracy per template"):], re.M)
cur, rows = None, []
for ty, tpl, acc, n in tp:
    cur = ty or cur
    rows.append((cur, tpl, float(acc)))
cols = {"complexity": "C0", "concurrency": "C1", "coupling_cohesion": "C2", "dependency_structure": "C3", "security": "C4"}
ax[1].barh(range(len(rows))[::-1], [r[2] for r in rows], color=[cols[r[0]] for r in rows])
ax[1].set_yticks(range(len(rows))[::-1]); ax[1].set_yticklabels([r[1] for r in rows], fontsize=6.5); ax[1].set_xlim(0, 1.05)
ax[1].set_xlabel("accuracy when this template is held out"); ax[1].set_title("Per template (colour = type)")
for ty, c in cols.items():
    ax[1].barh([], [], color=c, label=ty)
ax[1].legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
lc = re.findall(r"^\s+(\d+) pairs: (%s)" % num, t1, re.M)
ax[2].plot([int(a) for a, _ in lc], [float(b) for _, b in lc], "o-")
ax[2].set_xlabel("training pairs"); ax[2].set_ylabel("held-out-template accuracy"); ax[2].set_ylim(0.7, 0.9); ax[2].set_title("More pairs of the same templates\nstop helping")
fig.tight_layout(); fig.savefig(F + "sf5_pairs_level1.png"); plt.close(fig)
print("ok")
