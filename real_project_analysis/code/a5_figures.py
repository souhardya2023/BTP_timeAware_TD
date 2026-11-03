#!/usr/bin/env python3
"""Figures of the real-project analysis (matplotlib, default colours). Reads data/ and results/, writes figures/.
usage: a5_figures.py   (run with a Python that has matplotlib and pandas)
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D, R, F = os.path.join(ROOT, "data"), os.path.join(ROOT, "results"), os.path.join(ROOT, "figures")
os.makedirs(F, exist_ok=True)
PYTHON = {"boltons", "click", "jinja", "werkzeug", "requests", "flask", "attrs", "rich", "httpx", "tqdm", "pyyaml", "more-itertools", "cachetools", "bottle", "jsonschema", "arrow"}
OLD = {"boltons", "click", "jinja", "werkzeug", "cJSON", "jansson", "libpng", "libyaml", "zlib"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150, "savefig.bbox": "tight"})
NA = json.load(open(os.path.join(R, "a3_numbers.json")))
NB = json.load(open(os.path.join(R, "a3b_numbers.json")))
N4 = json.load(open(os.path.join(R, "a4_numbers.json")))


def load(sub):
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(D, sub, "*.csv")))], ignore_index=True)


T = load("transitions")
T["uid"] = T.repo + "|" + T.key
OBS = T[T.cls != "introduced"].copy()
OBS["event"] = (OBS.interest_lines > 0).astype(int)
OBS["lang"] = np.where(OBS.repo.isin(PYTHON), "python", "c")
CORP = pd.read_csv(os.path.join(R, "a3_corpus.csv"))
col = lambda l: "tab:blue" if l == "python" else "tab:orange"


def save(name):
    plt.savefig(os.path.join(F, name), dpi=160)
    plt.close()


# P1 corpus
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.8))
c = CORP.sort_values("code_lines")
for l, g in c.groupby("lang"):
    ax[0].scatter(g.code_lines, g.instances, s=28, label=l, color=col(l))
ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("lines of code in functions (last release)"); ax[0].set_ylabel("debt instances followed"); ax[0].legend(title="language"); ax[0].set_title("33 repositories")
for l, g in c.groupby("lang"):
    ax[1].scatter(g.debt_share, g.event_rate, s=28, color=col(l))
ax[1].set_xlabel("share of code inside debt functions"); ax[1].set_ylabel("share of instance-releases with interest"); ax[1].set_title("debt share and activity")
order = CORP.sort_values("pm_total")
ax[2].barh(order.repo, order.pm_total, color=[col(l) for l in order.lang]); ax[2].set_xscale("log"); ax[2].set_xlabel("interest paid, person-months (log)"); ax[2].tick_params(axis="y", labelsize=6.5); ax[2].set_title("interest per repository")
plt.tight_layout(); save("A1_corpus.png")

# P2 concentration
inst = OBS.groupby(["repo", "uid"]).agg(pm=("pm_interest", "sum"), obs=("event", "size"), ev=("event", "sum")).reset_index()
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.8))
for name, sub, c_ in (("all 33", inst, "k"), ("python", inst[inst.repo.isin(PYTHON)], "tab:blue"), ("c", inst[~inst.repo.isin(PYTHON)], "tab:orange")):
    s = np.sort(sub.pm.values)[::-1]
    ax[0].plot(np.arange(1, len(s) + 1) / len(s) * 100, np.cumsum(s) / s.sum() * 100, label=name, color=c_)
ax[0].plot([0, 100], [0, 100], ":", color="gray"); ax[0].set_xlabel("instances, ranked by interest (%)"); ax[0].set_ylabel("share of all interest (%)"); ax[0].legend(); ax[0].set_title("concentration")
gi = []
for repo, g in inst.groupby("repo"):
    x = np.sort(g.pm.values); n = len(x)
    gi.append((repo, (2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()) if x.sum() > 0 else 0))
gi = pd.DataFrame(gi, columns=["repo", "g"]).sort_values("g")
ax[1].hist(gi.g, bins=12, color="tab:blue"); ax[1].axvline(gi.g.median(), color="k", ls="--"); ax[1].set_xlabel("Gini of interest over instances, per repository"); ax[1].set_ylabel("repositories"); ax[1].set_title("median %.2f" % gi.g.median())
ev = OBS[OBS.event == 1]
ax[2].hist(np.log10(ev.interest_lines), bins=30, color="tab:green"); ax[2].set_xlabel("log10 of interest lines per event"); ax[2].set_ylabel("events"); ax[2].set_title("median %.1f lines, p90 %.0f lines" % (ev.interest_lines.median(), ev.interest_lines.quantile(.9)))
plt.tight_layout(); save("A2_concentration.png")

# P3 memory
ml = pd.read_csv(os.path.join(R, "a3_memory_lags.csv")); md = pd.read_csv(os.path.join(R, "a3_memory_dose.csv"))
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6))
ax[0].plot(ml.lag, ml.p_after_event, "o-", label="an event at that lag"); ax[0].plot(ml.lag, ml.p_after_no_event, "s--", label="no event at that lag")
ax[0].set_ylim(0, 0.6); ax[0].set_xlabel("lag (release pairs)"); ax[0].set_ylabel("P(event in this release pair)"); ax[0].legend(); ax[0].set_title("memory does not fade")
md = md.set_index("past_bin").loc[["0", "1", "2", "3-4", "5+"]].reset_index()
ax[1].bar(md.past_bin.astype(str), md["mean"], color="tab:blue"); ax[1].set_xlabel("events so far"); ax[1].set_ylabel("P(event in this release pair)"); ax[1].set_title("more past events, more future events")
plt.tight_layout(); save("A3_memory.png")

# P4 exposure
P = OBS[OBS.persisted == 1].copy()
P["bin"] = pd.cut(P.nloc0, [0, 6, 10, 15, 22, 33, 50, 80, 130, 220, 5000])
g = P.groupby(["lang", "bin"]).agg(x=("nloc0", "median"), p=("event", "mean"), n=("event", "size")).reset_index()
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.8))
for l, d in g.groupby("lang"):
    ax[0].plot(d.x, d.p, "o-", color=col(l), label=l)
ax[0].set_xscale("log"); ax[0].set_xlabel("size of the debt region (source lines)"); ax[0].set_ylabel("P(event in a release pair)"); ax[0].legend(); ax[0].set_title("exposure: slope %.2f (logit, per log-size)" % NA["size_logit_slope"][0])
fs = pd.read_csv(os.path.join(R, "a3_function_edit_rate_by_size.csv"), header=[0, 1], index_col=0)
x = np.arange(len(fs))
ax[1].bar(x - 0.2, fs[("mean", "0")], 0.4, label="not a debt function"); ax[1].bar(x + 0.2, fs[("mean", "1")], 0.4, label="debt function")
ax[1].set_xticks(x); ax[1].set_xticklabels(fs.index, rotation=30); ax[1].set_xlabel("function size (lines)"); ax[1].set_ylabel("P(function edited in a release pair)"); ax[1].legend(); ax[1].set_title("same size, same edit rate (OR %.2f)" % NA["smell_or_same_size"][0])
inst2 = inst.merge(OBS.groupby("uid").nloc0.median().rename("nloc"), on="uid")
lv = inst2[inst2.obs >= 10]
ax[2].boxplot([lv[lv.ev == 0].nloc, lv[lv.ev > 0].nloc], tick_labels=["frozen\n(no event)", "live"], showfliers=False); ax[2].set_ylabel("median size of the debt region (lines)"); ax[2].set_title("frozen debt is smaller")
plt.tight_layout(); save("A4_exposure_size.png")

# correction: enrichment
e1 = pd.read_csv(os.path.join(R, "a3_enrichment.csv")).set_index("repo").enrichment
e2 = pd.read_csv(os.path.join(R, "a3b_enrichment_matched.csv")).set_index("repo").enr
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.8))
ax[0].boxplot([e1.values, e2.values], tick_labels=["all changed lines\n(old denominator)", "lines in functions that\nexist in both releases"], showfliers=True)
ax[0].axhline(1, color="k", ls=":"); ax[0].set_ylabel("enrichment of edits in debt (1 = proportional)"); ax[0].set_title("pooled %.2f -> %.2f" % (NA["enrichment"]["pooled"], NB["enr_matched"]["pooled"]))
d = pd.DataFrame(dict(a=e1, b=e2)).dropna()
for l in ("python", "c"):
    s = d[d.index.isin(PYTHON) == (l == "python")]
    ax[1].scatter(s.a, s.b, color=col(l), label=l, s=26)
ax[1].plot([0, 1.4], [0, 1.4], ":", color="gray"); ax[1].set_xlabel("old enrichment (all changed lines)"); ax[1].set_ylabel("enrichment among functions present in both releases"); ax[1].legend(); ax[1].set_title("'debt is avoided' was a denominator effect")
plt.tight_layout(); save("A5_enrichment_correction.png")

# P5 release clock
rc = pd.read_csv(os.path.join(R, "a3_release_clock.csv"))
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.8))
st = rc.groupby("step").agg(rate=("rate", "mean"), churn=("churn", "median"), days=("days", "median"), n=("rate", "size")).loc[["patch", "minor", "major"]]
ax[0].bar(st.index, st.rate, color=["tab:green", "tab:blue", "tab:red"]); ax[0].set_ylabel("share of instances paying interest per release pair"); ax[0].set_title("release type")
for i, (k, r) in enumerate(st.iterrows()):
    ax[0].text(i, r.rate + 0.005, "n=%d\n%.0f days" % (r.n, r.days), ha="center", fontsize=7)
ax[1].scatter(rc.lcommits_c if "lcommits_c" in rc else np.log1p(rc.n_commits), rc.lpm_c, s=8, alpha=.5)
ax[1].set_xlabel("log commits since previous release (centred per repository)"); ax[1].set_ylabel("log release interest (centred)"); ax[1].set_title("r = %.2f" % NA["clock_lcommits_c"])
cr = NB["clock_r2"]
lab = ["step only", "days only", "step + days", "commits", "changed lines"]; keys = ["release step only (patch / minor / major)", "days since the previous release", "step + days (known before the release)", "commits since the previous release (known after)", "changed lines (known after)"]
ax[2].bar(lab, [cr[k] for k in keys], color=["tab:green"] * 3 + ["tab:gray"] * 2); ax[2].set_ylabel("R2 (leave one repository out)"); ax[2].tick_params(axis="x", rotation=30); ax[2].set_title("what predicts the release total\n(grey: known only after the release)")
plt.tight_layout(); save("A6_release_clock.png")

# P6 life cycle
sv = pd.read_csv(os.path.join(R, "a3_survival.csv"))
fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.8))
ab = NA["age_bins"]
ax[0].bar(list(ab.keys()), list(ab.values()), color="tab:blue"); ax[0].set_xlabel("releases since the debt was introduced"); ax[0].set_ylabel("P(event in a release pair)"); ax[0].set_title("activity falls with age (OR %.2f per release)" % NA["age_or"][0])
ax[1].step(sv.t, sv.survival, where="post"); ax[1].set_ylim(0, 1); ax[1].set_xlabel("releases since introduction"); ax[1].set_ylabel("share still present"); ax[1].set_title("survival of new debt")
ru = NA["rule"]
ks = list(ru.keys())
ax[2].bar(ks, [100 * ru[k]["rep"] for k in ks], color="tab:red"); ax[2].set_ylabel("repayment per instance-release (%)"); ax[2].set_title("%.0f%% of new debt is born in a new function" % (100 * (1 - NA["intro_existing_share"])))
plt.tight_layout(); save("A7_life_cycle.png")

# P7 path of work
pc = pd.read_csv(os.path.join(R, "a3_path_of_work_paired.csv"))
sel = [("persist_size", "persist"), ("logit_base", "persist_size"), ("logit_prox", "logit_base"), ("logit_prox_clock", "logit_prox"), ("gb_prox_clock", "gb_base")]
lab = {"persist_size|persist": "persistence, size as tie-break\nminus persistence", "logit_base|persist_size": "size + history model\nminus persistence (size ties)", "logit_prox|logit_base": "+ path-of-work features\nminus size + history",
       "logit_prox_clock|logit_prox": "+ project clock\nminus path of work", "gb_prox_clock|gb_base": "boosting: + path of work + clock\nminus boosting base"}
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
for a_, proto in zip(ax, ("LORO", "temporal")):
    y = 0
    for (a, b) in sel:
        for top, mk in ((20, "o"), (30, "s")):
            r = pc[(pc.protocol == proto) & (pc.a == a) & (pc.b == b) & (pc.top == top)].iloc[0]
            a_.errorbar(r["diff_pts"], y, xerr=[[r["diff_pts"] - r.lo], [r.hi - r["diff_pts"]]], fmt=mk, color="tab:blue" if top == 20 else "tab:orange", capsize=2, label="top %d%%" % top if y == 0 or y == 1 else None)
            y += 1
    a_.axvline(0, color="k", ls=":"); a_.set_xlabel("difference in capture (points), 95% interval over groups"); a_.set_title("leave one repository out" if proto == "LORO" else "temporal")
ax[0].set_yticks([0.5, 2.5, 4.5, 6.5, 8.5]); ax[0].set_yticklabels([lab["%s|%s" % s] for s in sel], fontsize=7); ax[0].legend(); ax[0].invert_yaxis()
plt.tight_layout(); save("A8_path_of_work.png")

# commits
CM = load("commits")
CM["lines"] = CM.src_added + CM.src_deleted
OK = CM[CM.bulk == 0]
per = pd.read_csv(os.path.join(R, "a4_per_repo.csv"))
fig, ax = plt.subplots(2, 3, figsize=(12.5, 7))
ax[0, 0].hist(np.log10(OK.lines.clip(lower=1)), bins=40, color="tab:blue"); ax[0, 0].set_xlabel("log10 source lines changed in a commit"); ax[0, 0].set_ylabel("commits"); ax[0, 0].set_title("median %d lines, p90 %d" % (OK.lines.median(), OK.lines.quantile(.9)))
cr_ = OK.assign(kind=np.where(OK.smell_created > 0, "creates debt", np.where(OK.smell_removed > 0, "removes debt", "other")))
ax[0, 1].boxplot([np.log10(cr_[cr_.kind == k].lines.clip(lower=1)) for k in ("other", "creates debt", "removes debt")], tick_labels=["other", "creates\ndebt", "removes\ndebt"], showfliers=False); ax[0, 1].set_ylabel("log10 lines changed"); ax[0, 1].set_title("debt is created and removed in big commits")
ax[0, 2].bar(["created", "removed"], [N4["created_removed"][0], N4["created_removed"][1]], color=["tab:red", "tab:green"]); ax[0, 2].set_ylabel("smell functions (700 commits per repository)"); ax[0, 2].set_title("net %d more debt functions" % (N4["created_removed"][0] - N4["created_removed"][1]))
kw = pd.read_csv(os.path.join(R, "a4_type_keywords.csv")).set_index("group")
t = ["security", "concurrency", "dependency", "coupling", "complexity"]
x = np.arange(5)
ax[1, 0].bar(x - 0.2, kw.loc["bug-fix commits", t], 0.4, label="bug-fix commits"); ax[1, 0].bar(x + 0.2, kw.loc["other commits", t], 0.4, label="other commits")
ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels(t, rotation=25); ax[1, 0].set_ylabel("share of commits with the keyword in the subject"); ax[1, 0].legend(); ax[1, 0].set_title("the five debt types in real commit messages")
ax[1, 1].scatter(per.created, per.removed, s=16)
mx = max(per.created.max(), per.removed.max()); ax[1, 1].plot([0, mx], [0, mx], ":", color="gray"); ax[1, 1].set_xlabel("debt functions created"); ax[1, 1].set_ylabel("debt functions removed"); ax[1, 1].set_title("per repository: most grow debt")
cand = N4["candidates"]
ks = ["introduced_smell", "created_smell", "removed_smell", "deleted_smell"]
ax[1, 2].bar([k.replace("_", "\n") for k in ks], [cand[k] for k in ks], color=["tab:red", "tab:red", "tab:green", "tab:green"]); ax[1, 2].set_ylabel("small focused commits (<= 60 lines, <= 3 files)"); ax[1, 2].set_title("natural pair candidates")
plt.tight_layout(); save("A9_commits.png")
print("figures:", sorted(os.listdir(F)))
