"""Figures of the insight report, from the CSV files in ../results (matplotlib defaults)."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import load_transitions

plt.rcParams.update({"savefig.dpi": 200, "font.size": 9})
R = "../results/"
F = "../figs/"
T = load_transitions()

# ---- 1. concentration: Lorenz curve of interest over instances + frozen share
inst = T.groupby(["repo", "key"]).y.sum().sort_values(ascending=False)
cum = inst.cumsum() / inst.sum()
x = np.arange(1, len(inst) + 1) / len(inst) * 100
fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.2))
ax[0].plot(x, cum * 100, label="interest held by the top x% of instances"); ax[0].plot([0, 100], [0, 100], "k--", lw=0.8, label="equal share")
for q in (10, 20):
    v = cum.iloc[int(q / 100 * len(inst)) - 1] * 100
    ax[0].scatter([q], [v], zorder=5); ax[0].annotate(f"{v:.0f}%", (q, v), xytext=(6, -12), textcoords="offset points")
ax[0].set_xlabel("instances, ranked by interest paid (%)"); ax[0].set_ylabel("share of all interest (%)"); ax[0].set_title("Interest is concentrated (Gini 0.83)"); ax[0].legend(loc="lower right")
rate = pd.read_csv(R + "l2_instance_rates.csv").iloc[:, -1]
cls = pd.cut(rate, [-0.001, 0, 0.15, 0.3, 0.6, 1.0], labels=["never\n(frozen)", "up to 15%", "15-30%", "30-60%", "over 60%"]).value_counts().sort_index()
b = ax[1].bar(cls.index.astype(str), cls.values, color=["C7", "C0", "C0", "C0", "C0"])
for r_, v in zip(b, cls.values):
    ax[1].annotate(f"{v}", (r_.get_x() + r_.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center")
ax[1].set_ylabel("instances with >= 10 releases"); ax[1].set_xlabel("share of releases in which the instance pays interest"); ax[1].set_title("Almost half of the debt is never touched")
fig.tight_layout(); fig.savefig(F + "i1_concentration.png"); plt.close(fig)

# ---- 2. memory and dose-response
mem = pd.read_csv(R + "l2_memory_lags.csv")
dose = pd.read_csv(R + "l2_hazard_pastn.csv")
fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.2))
ax[0].plot(mem.lag, mem.p_given_event * 100, "o-", label="interest at t-lag"); ax[0].plot(mem.lag, mem.p_given_none * 100, "s-", label="no interest at t-lag")
ax[0].set_ylim(0, 30); ax[0].set_xlabel("lag (releases)"); ax[0].set_ylabel("P(interest in release t) (%)"); ax[0].set_title("Memory does not fade with lag"); ax[0].legend()
b = ax[1].bar(dose.pn_b.astype(str), dose["mean"] * 100, color="C0")
for r_, v in zip(b, dose["mean"] * 100):
    ax[1].annotate(f"{v:.0f}%", (r_.get_x() + r_.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center")
ax[1].set_xlabel("interest events already paid by the instance"); ax[1].set_ylabel("P(interest next release) (%)"); ax[1].set_title("Dose-response: the more, the likelier")
fig.tight_layout(); fig.savefig(F + "i2_memory.png"); plt.close(fig)

# ---- 3. enrichment
E = pd.read_csv(R + "l2_enrichment.csv").set_index("repo").sort_values("enrichment")
fig, ax = plt.subplots(figsize=(6.4, 3.3))
y = np.arange(len(E))
ax.barh(y + 0.2, E.share_of_code_in_debt_regions * 100, 0.4, label="share of the code in debt regions"); ax.barh(y - 0.2, E.share_of_changes_in_debt_regions * 100, 0.4, label="share of added/modified lines in debt regions")
for i, (a, b_) in enumerate(zip(E.share_of_code_in_debt_regions * 100, E.share_of_changes_in_debt_regions * 100)):
    ax.annotate(f"{a:.0f}%", (a, i + 0.2), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7); ax.annotate(f"{b_:.0f}%", (b_, i - 0.2), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7)
ax.set_yticks(y); ax.set_yticklabels(E.index); ax.set_xlabel("%"); ax.set_title("Developers avoid debt: 32% of the code, 12% of the edits"); ax.set_xlim(0, 75); ax.legend(loc="center right", fontsize=7)
fig.tight_layout(); fig.savefig(F + "i3_enrichment.png"); plt.close(fig)

# ---- 4. ceiling
C = pd.read_csv(R + "l2_ceiling_horizon.csv")
c1 = C[C.h == 1].set_index("score")
fig, ax = plt.subplots(figsize=(6.2, 3.8))
ks = [10, 20, 30, 50]; w = 0.2
names = [("random", "random"), ("persistence", "persistence"), ("oracle long-run rate", "oracle: true long-run rate of each instance (uses the future)"), ("oracle (realised value)", "oracle: sorted by the realised value")]
for j, (key, lab) in enumerate(names):
    v = [c1.loc[key, f"cap{k}"] for k in ks]
    b = ax.bar(np.arange(4) + (j - 1.5) * w, v, w, label=lab)
    for r_, vv in zip(b, v):
        ax.annotate(f"{vv:.0f}", (r_.get_x() + r_.get_width() / 2, vv), xytext=(0, 1), textcoords="offset points", ha="center", fontsize=6.5)
ax.set_xticks(range(4)); ax.set_xticklabels([f"top {k}%" for k in ks]); ax.set_ylabel("% of next-release interest captured")
ax.set_title("Persistence reaches the hotness ceiling"); ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
ax.set_ylim(0, 105)
fig.tight_layout(); fig.savefig(F + "i4_ceiling.png"); plt.close(fig)

# ---- 5. where vs when
fig, ax = plt.subplots(figsize=(5.4, 3.0))
lab = ["repository", "instance (where)", "file", "release clock (when)"]
val = [0.091, 0.134, 0.125, 0.280]
b = ax.bar(lab, val, color=["C7", "C0", "C0", "C1"])
for r_, v in zip(b, val):
    ax.annotate(f"{v:.2f}", (r_.get_x() + r_.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center")
ax.set_ylabel("share of variance (ICC)"); ax.set_title("Which release it is matters twice as much as which instance")
plt.setp(ax.get_xticklabels(), fontsize=8)
fig.tight_layout(); fig.savefig(F + "i5_where_when.png"); plt.close(fig)

# ---- 6. hotness rules against persistence (paired, leave-one-repo-out)
Pd = pd.read_csv(R + "l2_rank_models_paired.csv")
Pd = Pd[(Pd.protocol == "leave-one-repo-out") & Pd.score.isin(["change-proneness (any change)", "event rate, shrunk (a=2)", "learned (GB, new features)"])]
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ks = ["cap10", "cap20", "cap30", "cap50"]
for j, (s, g) in enumerate(Pd.groupby("score")):
    g = g.set_index("k").loc[ks]
    xx = np.arange(4) + (j - 1) * 0.2
    ax.errorbar(xx, g.diff_pts, yerr=[g.diff_pts - g.lo, g.hi - g.diff_pts], fmt="o", capsize=3, label=s)
ax.axhline(0, color="k", lw=0.8); ax.set_xticks(range(4)); ax.set_xticklabels(["top 10%", "top 20%", "top 30%", "top 50%"])
ax.set_ylabel("capture minus persistence (points)"); ax.set_title("Hotness scores vs persistence, 123 groups, 95% bootstrap interval"); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(F + "i6_hotness_vs_persistence.png"); plt.close(fig)

# ---- 7. Level 1: leave-one-project-out per project and by origin
L = pd.read_csv(R + "l1_lopo_per_project.csv", index_col=0)
cnt = pd.read_csv("../../out_dataset/delta_only/dataset_without_time.csv").project.value_counts()
sel = ["whole-project delta, RF", "LOCAL delta (touched files), RF", "PATCH WORDS (added/removed identifiers), LR"]
fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.4), gridspec_kw={"width_ratios": [1.5, 1]})
order = list(cnt.sort_values(ascending=False).index)
for j, s in enumerate(sel):
    ax[0].bar(np.arange(len(order)) + (j - 1) * 0.27, L.loc[s, order], 0.27, label=s)
ax[0].set_xticks(range(len(order))); ax[0].set_xticklabels([f"{p}\n(n={cnt[p]})" for p in order], fontsize=6.5)
ax[0].set_ylabel("accuracy when the project is held out"); ax[0].set_title("Only boltons fails: its concurrency pairs have no twin"); ax[0].set_ylim(0, 1.35); ax[0].legend(fontsize=6.5, loc="upper right"); ax[0].annotate("0.00", (0, 0.01), ha="center", fontsize=7)
O = pd.read_csv(R + "l1_lopo_by_origin.csv").set_index("method").loc[["whole-project delta, RF", "LOCAL delta (touched files), 10-best + RF"]]
cols = ["scripted injection", "SmellBench"]
for j, (m, row) in enumerate(O.iterrows()):
    b = ax[1].bar(np.arange(2) + (j - 0.5) * 0.35, row[cols].values, 0.35, label=m.replace("whole-project delta, RF", "whole project").replace("LOCAL delta (touched files), 10-best + RF", "touched files only"))
    for r_, v in zip(b, row[cols].values):
        ax[1].annotate(f"{v:.2f}", (r_.get_x() + r_.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)
ax[1].set_xticks(range(2)); ax[1].set_xticklabels(["scripted injection\n(21 pairs)", "LLM-written\n(SmellBench, 15 pairs)"], fontsize=7)
ax[1].set_ylim(0, 1.1); ax[1].set_title("Unseen projects, boltons excluded"); ax[1].legend(fontsize=6.5)
fig.tight_layout(); fig.savefig(F + "i7_level1_generalisation.png"); plt.close(fig)

# ---- 8. dilution and drift
ratio = np.load(R + "l1_drift_ratio.npy")
per = pd.read_csv(R + "l1_drift_per_pair.csv")
fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.2))
ax[0].hist(np.log10(np.clip(ratio, 1e-6, None)), bins=40, color="C0"); ax[0].axvline(0, color="k", ls="--", lw=0.8)
ax[0].set_xlabel("log10( injected change / natural change between versions )"); ax[0].set_ylabel("pair-feature cells"); ax[0].set_title("The debt is ~100x smaller than natural drift")
ax[1].scatter(per.n_changed + np.random.default_rng(0).uniform(-0.3, 0.3, len(per)), per.n_above_drift + np.random.default_rng(1).uniform(-0.15, 0.15, len(per)), c=[f"C{i}" for i in pd.factorize(per.td_type)[0]], s=14)
for i, t in enumerate(pd.factorize(per.td_type)[1]):
    ax[1].scatter([], [], c=f"C{i}", s=14, label=t)
ax[1].set_xlabel("features (of 133) that the debt changes at all"); ax[1].set_ylabel("... that exceed natural drift"); ax[1].set_title("Per pair: 1 feature rises above the noise"); ax[1].legend(fontsize=6)
fig.tight_layout(); fig.savefig(F + "i8_drift.png"); plt.close(fig)

# ---- 9. context shift: stable signature, no gain from augmentation
S = pd.read_csv(R + "l1_context_stability.csv"); A = pd.read_csv(R + "l1_context_aug.csv")
fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.2))
ax[0].hist(S.cosine, bins=20, color="C0"); ax[0].set_xlabel("cosine similarity: signature in an older host vs the original"); ax[0].set_ylabel("copies (188)"); ax[0].set_title("Same edit, other host: same signature")
x = np.arange(2)
for j, (aug, lab) in enumerate(((False, "original 61 pairs"), (True, "+ 188 older-host copies"))):
    v = [A[(A.model == m) & (A.augmented == aug)].lopo_nonboltons.iloc[0] for m in ("RF", "10-best+RF")]
    b = ax[1].bar(x + (j - 0.5) * 0.35, v, 0.35, label=lab)
    for r_, vv in zip(b, v):
        ax[1].annotate(f"{vv:.2f}", (r_.get_x() + r_.get_width() / 2, vv), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)
ax[1].set_xticks(x); ax[1].set_xticklabels(["RF", "10-best + RF"]); ax[1].set_ylim(0, 1); ax[1].set_ylabel("leave-one-project-out accuracy, non-boltons pairs"); ax[1].set_title("More copies, no more information"); ax[1].legend(fontsize=7)
fig.tight_layout(); fig.savefig(F + "i9_context_augmentation.png"); plt.close(fig)

# ---- 10. graph: what changes
G = pd.read_csv(R + "l1_edit_graph_features.csv")
chg = ((G.e_added + G.e_removed + G.nodes_added) > 0).groupby(G.td_type).agg(["mean", "size"])
fig, ax = plt.subplots(figsize=(5.8, 3.0))
b = ax.bar(chg.index, chg["mean"] * 100, color="C0")
for r_, (m, n) in zip(b, zip(chg["mean"], chg["size"])):
    ax.annotate(f"{m*100:.0f}%  (n={n})", (r_.get_x() + r_.get_width() / 2, m * 100), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)
ax.set_ylabel("pairs whose dependency graph changes (%)"); ax.set_ylim(0, 115); ax.set_title("The dependency graph sees only 14 of 61 debt changes")
plt.setp(ax.get_xticklabels(), fontsize=7, rotation=12)
fig.tight_layout(); fig.savefig(F + "i10_graph_visibility.png"); plt.close(fig)
print("figures done")
