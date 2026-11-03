"""03_synthetic_dataset: composition and checks of the 150-project synthetic benchmark."""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi": 220, "font.size": 8.5, "legend.fontsize": 7.5})
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SD = os.path.join(ROOT, "synthetic_dataset"); OUT = os.path.join(os.path.dirname(__file__), "03_synthetic_dataset")
P = pd.read_csv(os.path.join(SD, "projects.csv")); I = pd.read_csv(os.path.join(SD, "instances.csv")); PR = pd.read_csv(os.path.join(SD, "pairs.csv")); IC = pd.read_csv(os.path.join(SD, "insight_check.csv"), index_col=0)
def save(fig, n): fig.tight_layout(); fig.savefig(os.path.join(OUT, n), facecolor="white"); plt.close(fig)
tiers = ["S", "M", "L", "X"]; tn = {"S": "small", "M": "medium", "L": "large", "X": "xlarge"}
fig, ax = plt.subplots(1, 4, figsize=(12, 3.2))
for a, (col, lab, lg) in zip(ax, (("python_files", "python files", False), ("loc", "lines of code", True), ("releases", "releases (tags)", False), ("commits", "commits", True))):
    a.boxplot([P[P.tier == t][col] for t in tiers], tick_labels=["%s\n(n=%d)" % (tn[t], (P.tier == t).sum()) for t in tiers], showfliers=True)
    if lg: a.set_yscale("log")
    a.set_title(lab)
fig.suptitle("The 150 synthetic projects by size tier", fontsize=10); save(fig, "S1_tiers.png")
# types and templates
tt = I.groupby(["ptype", "template"]).size().reset_index(name="n")
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw={"width_ratios": [1, 1.6]})
types = ["complexity", "security", "coupling_cohesion", "concurrency", "dependency_structure"]
cnt = I.ptype.value_counts()
b = ax[0].barh(types[::-1], [cnt[t] for t in types][::-1], color="C0")
for r_ in b: ax[0].annotate("%d" % r_.get_width(), (r_.get_width(), r_.get_y() + r_.get_height() / 2), xytext=(2, 0), textcoords="offset points", va="center")
maj = I[I.major == 1].ptype.value_counts()
ax[0].set_title("1,321 debt instances by type\n(major-type instances: %d, minor: %d)" % (I.major.sum(), (1 - I.major).sum()))
yy, lab = 0, []
for ty in types:
    s = tt[tt.ptype == ty].sort_values("n", ascending=False)
    for _, r in s.iterrows():
        ax[1].barh(yy, r.n, color="C%d" % types.index(ty)); ax[1].annotate("%d" % r.n, (r.n, yy), xytext=(2, 0), textcoords="offset points", va="center", fontsize=7); lab.append(r.template); yy += 1
    yy += 0.6
ys = []; 
pos = 0
for ty in types:
    k = (tt.ptype == ty).sum(); ys += [pos + i for i in range(k)]; pos += k + 0.6
ax[1].set_yticks(ys); ax[1].set_yticklabels(lab, fontsize=6.8); ax[1].invert_yaxis(); ax[1].set_title("23 templates (colour = type)")
for i, ty in enumerate(types): ax[1].barh([], [], color="C%d" % i, label=ty)
ax[1].legend(loc="lower right"); save(fig, "S2_types_templates.png")
# balance
fig, ax = plt.subplots(1, 3, figsize=(12, 3.3))
ct = P.groupby(["tier", "major_type"]).size().unstack(fill_value=0).loc[tiers]
ct.plot(kind="bar", stacked=True, ax=ax[0], width=0.7, legend=False, color=["C0", "C3", "C2", "C4", "C1"] if False else None); ax[0].set_title("Major type by tier"); ax[0].set_xticklabels([tn[t] for t in tiers], rotation=0)
cr = P.groupby(["regime", "major_type"]).size().unstack(fill_value=0).loc[["baseline", "sticky", "ar_clock", "decay", "contagion"]]
cr.plot(kind="bar", stacked=True, ax=ax[1], width=0.7); ax[1].set_title("Major type by regime"); ax[1].legend(fontsize=6, loc="upper right"); plt.setp(ax[1].get_xticklabels(), rotation=15)
ax[2].bar(["baseline", "sticky", "ar_clock", "decay", "contagion"], P.regime.value_counts()[["baseline", "sticky", "ar_clock", "decay", "contagion"]], color="C7")
for k, v in enumerate(P.regime.value_counts()[["baseline", "sticky", "ar_clock", "decay", "contagion"]]): ax[2].annotate(v, (k, v), xytext=(0, 2), textcoords="offset points", ha="center")
ax[2].set_title("Projects per regime"); plt.setp(ax[2].get_xticklabels(), rotation=15)
save(fig, "S3_balance.png")
# pairs
fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.2))
ax[0].hist(PR.lines_added.clip(upper=100), bins=40, color="C0"); ax[0].set_xlabel("lines added by the debt commit (clipped at 100)"); ax[0].set_title("Size of a debt introduction (median %d)" % PR.lines_added.median())
ax[1].bar(["pure", "mixed"], [(~PR.mixed).sum(), PR.mixed.sum()], color=["C0", "C1"]); ax[1].set_title("Mixed commits: %.0f %%" % (100 * PR.mixed.mean()))
ax[2].bar(PR.granularity.value_counts().index, PR.granularity.value_counts().values, color="C2"); ax[2].set_title("Granularity of the debt region")
save(fig, "S4_pairs.png")
# insight check per regime against the real values
metrics = [("event rate", 0.078), ("gini", 0.83), ("never pay", 0.46), ("P(ev|ev,lag1)", 0.227), ("enrichment", 0.39), ("neighbour ratio", 1.1), ("ICC release", 0.28), ("ICC instance", 0.13)]
regs = ["baseline", "sticky", "ar_clock", "decay", "contagion"]
fig, ax = plt.subplots(2, 4, figsize=(12.5, 5.2))
for a, (m, real) in zip(ax.ravel(), metrics):
    v = [IC.loc[r, m] for r in regs]
    b = a.bar(range(5), v, color=["C0", "C1", "C2", "C4", "C3"]); a.axhline(real, color="k", ls="--", lw=1, label="real data" if m == "event rate" else None)
    a.set_xticks(range(5)); a.set_xticklabels(regs, rotation=30, fontsize=6.5); a.set_title(m, fontsize=8.5)
    for r_, vv in zip(b, v): a.annotate("%.2f" % vv, (r_.get_x() + r_.get_width() / 2, vv), xytext=(0, 1), textcoords="offset points", ha="center", fontsize=6)
ax[0, 0].legend(fontsize=7)
fig.suptitle("Do the real-data patterns appear in the synthetic histories?  (dashed line = the 9 real repositories)", fontsize=10); save(fig, "S5_patterns_vs_real_by_regime.png")
# interest
T = pd.concat([pd.read_csv(f) for f in sorted(__import__("glob").glob(os.path.join(SD, "transitions", "*.csv")))])
T["ev"] = T.interest_lines > 0; T = T.merge(I[["instance", "ptype", "template"]], left_on="key", right_on="instance")
fig, ax = plt.subplots(1, 2, figsize=(11, 3.3))
er = T.groupby("ptype").ev.mean().loc[types]; b = ax[0].bar(types, er.values * 100, color="C1")
for r_, vv in zip(b, er.values * 100): ax[0].annotate("%.1f" % vv, (r_.get_x() + r_.get_width() / 2, vv), xytext=(0, 2), textcoords="offset points", ha="center")
ax[0].set_ylabel("% of instance-releases with interest"); ax[0].set_title("Event rate by type (all %d instance-releases)" % len(T)); plt.setp(ax[0].get_xticklabels(), rotation=15, fontsize=7)
pm = T.groupby("ptype").pm_interest.sum().loc[types]; b = ax[1].bar(types, pm.values, color="C0")
for r_, vv in zip(b, pm.values): ax[1].annotate("%.2f" % vv, (r_.get_x() + r_.get_width() / 2, vv), xytext=(0, 2), textcoords="offset points", ha="center")
ax[1].set_ylabel("person-months"); ax[1].set_title("Interest by type (%.2f person-months in total)" % pm.sum()); plt.setp(ax[1].get_xticklabels(), rotation=15, fontsize=7)
save(fig, "S6_interest_by_type.png")
print("synthetic figures ok")
