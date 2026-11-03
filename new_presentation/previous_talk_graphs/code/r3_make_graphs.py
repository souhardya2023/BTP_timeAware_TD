"""Draws the graphs of the previous talk from the FRESH model outputs in ../results (matplotlib defaults).
Not drawn on purpose: the fix-time graph (extra minutes per type) and the time-feature controls.
Level 1 graphs read results/level1/summary.csv; Level 2 graphs are computed from results/level2/pm_predictions.csv (groups = repository x release with >= 10 instances and some real interest)
and results/level2/next_release_model_results.csv, snapshot_model_results.csv.   Run with a Python that has pandas, numpy, scipy, matplotlib."""
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
plt.rcParams.update({"savefig.dpi": 220, "font.size": 8.5, "legend.fontsize": 7.5})
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); FIG = os.path.join(HERE, "..", "figures")
FF = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
rng = np.random.default_rng(0)
def save(fig, n): fig.tight_layout(); fig.savefig(os.path.join(FIG, n), facecolor="white"); plt.close(fig)
def lab(ax, bars, fmt="%.2f", fs=7.5, h=False):
    for b in bars:
        v = b.get_width() if h else b.get_height()
        ax.annotate(fmt % v, ((v, b.get_y() + b.get_height() / 2) if h else (b.get_x() + b.get_width() / 2, v)), xytext=((2, 0) if h else (0, 2)), textcoords="offset points", ha="left" if h else "center", va="center" if h else "bottom", fontsize=fs)
# ------------------------------------------------------------------ dataset graphs
DS = pd.read_csv(os.path.join(FF, "out_dataset", "delta_only", "dataset_without_time.csv"))
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.2))
b = ax[0].bar(["candidates", "after audit", "final\n(+9 added)"], [102, 52, len(DS)], color="C0"); lab(ax[0], b, "%.0f"); ax[0].set_ylabel("pairs"); ax[0].set_title("Pairs along the way (102 and 52 from the audit record)")
types = ["concurrency", "security", "dependency_structure", "coupling_cohesion", "complexity"]
ct = pd.crosstab(DS.td_type, DS.language).reindex(types)
y = np.arange(5)[::-1]; ax[1].barh(y, ct["Python"], color="C0", label="Python"); ax[1].barh(y, ct["C/C++"], left=ct["Python"], color="C1", label="C/C++")
for yy, t in zip(y, types): ax[1].annotate(str(int(ct.loc[t].sum())), (ct.loc[t].sum(), yy), xytext=(3, 0), textcoords="offset points", va="center", fontweight="bold")
ax[1].set_yticks(y); ax[1].set_yticklabels([t.replace("_", " ") for t in types]); ax[1].set_xlim(0, 31); ax[1].legend(loc="lower right"); ax[1].set_title("Pairs per debt type and language (counted from the data set)")
save(fig, "G1_dataset_pairs.png")
# ------------------------------------------------------------------ Level 1
S = pd.read_csv(os.path.join(RES, "level1", "summary.csv"))
def acc(model, protocol, wt, layout="delta_only"):
    r = S[(S.layout == layout) & (S.model == model) & (S.protocol == protocol) & (S.with_time == wt)]
    return float(r.accuracy_mean.iloc[0])
protos = ["given_stratified", "repeated_stratified", "given_by_project", "leave_one_project_out"]
cats = ["stratified\nfolds", "20 random\nsplits", "by project\nfolds", "leave one\nproject out"]
maj = float(DS.td_type.value_counts(normalize=True).max())      # share of the most common class overall (concurrency, 26 of 61), as in the talk
fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.6))
wo = [acc("kbest10_random_forest", p, False) for p in protos]; wi = [acc("kbest10_random_forest", p, True) for p in protos]
b1 = ax[0].bar(np.arange(4) - 0.19, wo, 0.38, color="C7", label="without time"); b2 = ax[0].bar(np.arange(4) + 0.19, wi, 0.38, color="C1", label="with time"); lab(ax[0], b1); lab(ax[0], b2)
ax[0].axhline(maj, color="k", ls="--", lw=0.8, label="always the most common class: %.3f" % maj); ax[0].set_xticks(range(4)); ax[0].set_xticklabels(cats); ax[0].set_ylim(0, 1.1); ax[0].set_ylabel("accuracy"); ax[0].legend(loc="upper right", ncol=3, fontsize=6.5); ax[0].set_title("10-best features + random forest, by protocol")
models = [("kbest10_random_forest", "10-best + RF"), ("kbest10_logistic_regression", "10-best + LR"), ("knn", "kNN"), ("svm_rbf", "SVM (RBF)"), ("logistic_regression", "Logistic reg."), ("gradient_boosting", "Grad. boosting"), ("random_forest", "Random forest")]
yy = np.arange(7)[::-1]
h1 = ax[1].barh(yy + 0.19, [acc(m, "given_stratified", False) for m, _ in models], 0.38, color="C7", label="without time"); h2 = ax[1].barh(yy - 0.19, [acc(m, "given_stratified", True) for m, _ in models], 0.38, color="C1", label="with time")
lab(ax[1], h1, h=True, fs=6.5); lab(ax[1], h2, h=True, fs=6.5); ax[1].set_yticks(yy); ax[1].set_yticklabels([n for _, n in models]); ax[1].set_xlim(0, 1.1); ax[1].set_xlabel("accuracy, stratified folds"); ax[1].legend(loc="center right"); ax[1].set_title("Seven classifiers")
save(fig, "G2_level1_accuracy.png")
# ------------------------------------------------------------------ Level 2: ranking
d = pd.read_csv(os.path.join(RES, "level2", "pm_predictions.csv"))
KS = [0.05, 0.10, 0.20, 0.30]
def group_metrics(g):
    a = g.actual_mPM.to_numpy(); p = g.predicted_mPM.to_numpy(); n = len(a); tot = a.sum(); r = rng.random(n)
    o = np.lexsort((r, -p)); out = {}
    for k in KS:
        m = max(1, int(np.ceil(k * n))); out["cap%d" % round(k * 100)] = a[o[:m]].sum() / tot; out["prec%d" % round(k * 100)] = (a[o[:m]] > 0).mean(); out["base%d" % round(k * 100)] = (a > 0).mean()
    m = max(1, int(np.ceil(0.2 * n))); disc = 1 / np.log2(np.arange(2, m + 2)); out["ndcg20"] = (a[o[:m]] * disc).sum() / (np.sort(a)[::-1][:m] * disc).sum()
    out["rho"] = spearmanr(p, a)[0] if p.std() > 0 else 0.0
    return out
rows = []
for (proto, model, repo, vi), g in d.groupby(["protocol", "model", "repo", "vi"]):
    if g.actual_mPM.sum() <= 0 or len(g) < 10: continue
    rows.append(dict(protocol=proto, model=model, repo=repo, vi=vi, **group_metrics(g)))
G = pd.DataFrame(rows); G.to_csv(os.path.join(RES, "level2", "capture_per_group.csv"), index=False)
def boot(x, B=2000): x = np.asarray(x); return np.percentile(x[rng.integers(0, len(x), (B, len(x)))].mean(1), [2.5, 97.5])
R = []
for (proto, model), g in G.groupby(["protocol", "model"]):
    r = dict(protocol=proto, model=model, groups=len(g))
    for k in (10, 20, 30):
        r["cap%d" % k] = g["cap%d" % k].mean(); r["cap%d_lo" % k], r["cap%d_hi" % k] = boot(g["cap%d" % k]); r["lift%d" % k] = (g["prec%d" % k] / g["base%d" % k]).mean()
    r["ndcg20"] = g.ndcg20.mean(); r["rho"] = g.rho.mean(); R.append(r)
R = pd.DataFrame(R); R.to_csv(os.path.join(RES, "level2", "capture_summary.csv"), index=False)
def cap(proto, model, k): return float(R[(R.protocol == proto) & (R.model == model)]["cap%d" % k].iloc[0]) * 100
names = [("random", None, "C7"), ("persistence", "persistence", "C0"), ("RF regression", "rf_pm", "C2"), ("two-part model", "hurdle_rf", "C1")]
fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.6), sharey=True)
for a, proto, title in ((ax[0], "leave-one-repo-out", "leave one repository out"), (ax[1], "temporal", "temporal")):
    ng = int(R[(R.protocol == proto)].groups.iloc[0])
    for j, (n, m, col) in enumerate(names):
        v = [10, 20, 30] if m is None else [cap(proto, m, k) for k in (10, 20, 30)]
        b = a.bar(np.arange(3) + (j - 1.5) * 0.2, v, 0.2, color=col, label=n); lab(a, b, "%.0f", 7)
    a.set_xticks(range(3)); a.set_xticklabels(["top 10 %", "top 20 %", "top 30 %"]); a.set_title("%s (%d groups)" % (title, ng))
ax[0].set_ylabel("% of next-release interest captured"); ax[0].legend(loc="upper left")
save(fig, "G3_ranking_capture_bars.png")
# capture curve
ks = np.arange(5, 101, 5); crow = []
for (proto, model, repo, vi), g in d.groupby(["protocol", "model", "repo", "vi"]):
    a = g.actual_mPM.to_numpy(); p = g.predicted_mPM.to_numpy(); n = len(a)
    if a.sum() <= 0 or n < 10: continue
    o = np.lexsort((rng.random(n), -p)); cs = np.cumsum(a[o]) / a.sum(); oc = np.cumsum(np.sort(a)[::-1]) / a.sum()
    for k in ks:
        m = max(1, int(np.ceil(k / 100 * n))); crow.append((proto, model, k, cs[m - 1], oc[m - 1]))
C = pd.DataFrame(crow, columns=["protocol", "model", "k", "capture", "oracle"]).groupby(["protocol", "model", "k"]).mean().reset_index(); C.to_csv(os.path.join(RES, "level2", "capture_curve.csv"), index=False)
fig, ax = plt.subplots(1, 2, figsize=(11.5, 3.8), sharey=True)
for a, proto, title in ((ax[0], "leave-one-repo-out", "leave one repository out"), (ax[1], "temporal", "temporal")):
    c = C[C.protocol == proto]
    a.plot(ks, c[c.model == "zero"].set_index("k").oracle * 100, ":", color="k", label="oracle")
    for m, n, col in (("hurdle_rf", "two-part model", "C1"), ("persistence", "persistence", "C0"), ("rf_pm", "RF regression", "C2")): a.plot(ks, c[c.model == m].set_index("k").capture * 100, color=col, lw=1.6, label=n)
    a.plot(ks, ks, color="C7", label="random"); a.set_xlabel("top k % of instances repaid"); a.grid(alpha=0.3); a.set_title(title)
ax[0].set_ylabel("% of next-release interest captured"); ax[0].legend(loc="lower right")
save(fig, "G4_capture_curve.png")
# paired difference two-part - persistence
def paired(proto, ks_=(10, 20, 30, 50), B=3000):
    A = d[(d.protocol == proto) & d.model.isin(["hurdle_rf", "persistence"])]; out = {k: [] for k in ks_}
    for (repo, vi), g in A.groupby(["repo", "vi"]):
        gh, gp = g[g.model == "hurdle_rf"], g[g.model == "persistence"]
        if gh.actual_mPM.sum() <= 0 or len(gh) < 10: continue
        a = gh.actual_mPM.to_numpy(); n = len(a); rr = rng.random(n)
        for k in ks_:
            m = max(1, int(np.ceil(k / 100 * n)))
            ch = a[np.lexsort((rr, -gh.predicted_mPM.to_numpy()))[:m]].sum() / a.sum(); cp = a[np.lexsort((rr, -gp.predicted_mPM.to_numpy()))[:m]].sum() / a.sum(); out[k].append(ch - cp)
    return {k: (np.mean(v) * 100, *np.percentile(np.array(v)[rng.integers(0, len(v), (B, len(v)))].mean(1) * 100, [2.5, 97.5]), len(v)) for k, v in out.items()}
fig, ax = plt.subplots(figsize=(7.2, 3.4)); pdif = {}
for j, proto in enumerate(("leave-one-repo-out", "temporal")):
    pdif[proto] = paired(proto)
    for i, (k, (m, lo, hi, n)) in enumerate(pdif[proto].items()):
        ax.errorbar(i + (j - 0.5) * 0.25, m, yerr=[[m - lo], [hi - m]], fmt="o", color=["C1", "C0"][j], capsize=3, label=("%s (%d groups)" % (proto, n)) if i == 0 else None)
ax.axhline(0, color="k", lw=0.8); ax.set_xticks(range(4)); ax.set_xticklabels(["top 10 %", "top 20 %", "top 30 %", "top 50 %"]); ax.set_ylabel("two-part model minus persistence (points)"); ax.legend(); ax.set_title("Is the model better than the simple rule? (paired bootstrap)")
save(fig, "G5_paired_difference.png")
json.dump({p: {str(k): [round(x, 2) for x in v] for k, v in dd.items()} for p, dd in pdif.items()}, open(os.path.join(RES, "level2", "paired_difference.json"), "w"), indent=1)
# ------------------------------------------------------------------ Level 2: predictability
A = pd.read_csv(os.path.join(RES, "level2", "next_release_model_results.csv")); B = pd.read_csv(os.path.join(RES, "level2", "snapshot_model_results.csv"))
def mauc(df, proto, model): return df[(df.protocol == proto) & (df.model == model)].AUC.mean()
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.4), sharey=True)
for a, df, pr, title in ((ax[0], A, ("leave-one-repo-out", "temporal"), "any interest in the next release"), (ax[1], B, ("leave-one-project-out", "temporal"), "function edited in the next 100 commits")):
    ms = [("all_features", "all features", "C1"), ("size_only", "size only", "C0"), ("history_only", "history only", "C2")]
    for j, (m, n, col) in enumerate(ms):
        v = [mauc(df, p, m) for p in pr]; bb = a.bar(np.arange(2) + (j - 1) * 0.26, v, 0.26, color=col, label=n); lab(a, bb, "%.2f", 7)
    a.axhline(0.5, color="k", ls="--", lw=0.8); a.set_xticks(range(2)); a.set_xticklabels(["unseen repositories", "later releases (temporal)"]); a.set_ylim(0.4, 0.8); a.set_title(title)
ax[0].set_ylabel("AUC (mean over folds)"); ax[0].legend(loc="upper left", fontsize=6.5)
save(fig, "G6_auc_predictability.png")
# ------------------------------------------------------------------ the two result tables of the talk, as images
def table_img(name, head, rows, widths, hl=None):
    fig, ax = plt.subplots(figsize=(sum(widths) * 1.0, 0.33 * (len(rows) + 1) + 0.2)); ax.axis("off")
    t = ax.table(cellText=rows, colLabels=head, loc="center", cellLoc="left", colWidths=[w / sum(widths) for w in widths]); t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1, 1.4)
    for (r, c), cell in t.get_celld().items():
        cell.set_linewidth(0); cell.set_edgecolor("white")
        if r == 0: cell.set_text_props(fontweight="bold"); cell.set_facecolor("white")
        if hl and (r - 1, c) in hl: cell.set_facecolor("#fde0c2")
    save(fig, name)
rows = []
lab_ = {"zero": "Zero model (= random)", "persistence": "Persistence", "rf_pm": "RF regression", "hurdle_rf": "Two-part model"}
for m in ("zero", "persistence", "rf_pm", "hurdle_rf"):
    r = R[(R.protocol == "leave-one-repo-out") & (R.model == m)].iloc[0]; rows.append([lab_[m], "%.1f%% (%.0f-%.0f)" % (r.cap20 * 100, r.cap20_lo * 100, r.cap20_hi * 100), "%.2f" % r.lift20, "%.2f" % r.ndcg20])
table_img("T1_ranking_table_top20.png", ["Model, top 20 %", "Capture (95% CI)", "Lift", "NDCG@20"], rows, [2.2, 2.0, 0.8, 1.0], {(3, 1)})
rows = [[k + " %", "%+.1f pts" % v[0], "%+.1f to %+.1f" % (v[1], v[2])] for k, v in ((str(k), pdif["leave-one-repo-out"][k]) for k in (10, 20, 30, 50))]
table_img("T2_paired_difference_table.png", ["Budget k", "Two-part - persistence", "95% CI"], rows, [1.0, 2.0, 1.8])
print("graphs ok")
