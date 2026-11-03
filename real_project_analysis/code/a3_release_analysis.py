#!/usr/bin/env python3
"""Release-level insights of the 34 real repositories (debt instances followed over up to 20 releases).

reads  data/{transitions,releases,files,funcs}/<repo>.csv     writes  results/a3_*.csv|txt and results/a3_numbers.json
usage: a3_release_analysis.py
"""
import glob
import json
import os
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D, R = os.environ.get("RPA_DATA", os.path.join(ROOT, "data")), os.environ.get("RPA_RES", os.path.join(ROOT, "results"))
os.makedirs(R, exist_ok=True)
PYTHON = {"boltons", "click", "jinja", "werkzeug", "requests", "flask", "attrs", "rich", "httpx", "tqdm", "pyyaml", "more-itertools", "cachetools", "bottle", "jsonschema", "arrow"}
OLD = {"boltons", "click", "jinja", "werkzeug", "cJSON", "jansson", "libpng", "libyaml", "zlib"}
NUM = {}
OUT = open(os.path.join(R, "a3_report.txt"), "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")


def load(sub):
    out = []
    for f in sorted(glob.glob(os.path.join(D, sub, "*.csv"))):
        try:
            out.append(pd.read_csv(f))
        except pd.errors.EmptyDataError:
            pass
    return pd.concat(out, ignore_index=True)


def gini(x):
    x = np.sort(np.asarray(x, float))
    if x.sum() == 0:
        return 0.0
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


T = load("transitions")
if os.environ.get("RPA_ALLPY"):
    PYTHON = set(pd.concat([pd.read_csv(f, usecols=["repo"]) for f in glob.glob(os.path.join(D, "releases", "*.csv"))]).repo)
T["lang"] = np.where(T.repo.isin(PYTHON), "python", "c")
T["old"] = T.repo.isin(OLD)
T["uid"] = T.repo + "|" + T.key
OBS = T[T.cls != "introduced"].copy()              # an instance present at V0 and observed over the pair
OBS["event"] = (OBS.interest_lines > 0).astype(int)
REL = load("releases")
REL["lang"] = np.where(REL.repo.isin(PYTHON), "python", "c")
REL["days"] = (pd.to_datetime(REL.d1) - pd.to_datetime(REL.d0)).dt.days
FILES = load("files")
FUNCS = load("funcs")
FUNCS["smell"] = ((FUNCS.long0 + FUNCS.cx0 + FUNCS.par_smell0) > 0).astype(int)
FUNCS["lang"] = np.where(FUNCS.repo.isin(PYTHON), "python", "c")


# ------------------------------------------------------------------ P1 corpus
say("=" * 100, "\nP1  THE CORPUS\n" + "=" * 100)
rows = []
for repo, g in OBS.groupby("repo"):
    r = REL[REL.repo == repo]
    inst = g.uid.nunique()
    ev = g.event.sum()
    rows.append(dict(repo=repo, lang=g.lang.iloc[0], original=repo in OLD, releases=len(r) + 1, first=r.d0.min(), last=r.d1.max(), code_lines=int(r.code1.iloc[-1]),
                     debt_share=round(r.debt1.iloc[-1] / r.code1.iloc[-1], 3), instances=inst, obs=len(g), events=int(ev), event_rate=round(ev / len(g), 4),
                     pm_total=round(g.pm_interest.sum(), 3), never_pay=round(float((g.groupby("uid").event.sum() == 0).mean()), 3)))
CORP = pd.DataFrame(rows)
CORP.to_csv(os.path.join(R, "a3_corpus.csv"), index=False)
say(CORP.to_string(index=False))
NUM["repos"] = len(CORP)
NUM["repos_python"] = int((CORP.lang == "python").sum())
NUM["instances"] = int(CORP.instances.sum()); NUM["obs"] = int(CORP.obs.sum()); NUM["events"] = int(CORP.events.sum())
NUM["pm_total"] = round(float(CORP.pm_total.sum()), 2)
say(f"\n{NUM['repos']} repositories ({NUM['repos_python']} Python), {NUM['instances']} instances, {NUM['obs']} instance-releases, {NUM['events']} events, {NUM['pm_total']} person-months")

# ------------------------------------------------------------------ P2 concentration
say("\n" + "=" * 100, "\nP2  CONCENTRATION AND FROZEN DEBT\n" + "=" * 100)
inst = OBS.groupby(["repo", "uid"]).agg(obs=("event", "size"), ev=("event", "sum"), pm=("pm_interest", "sum"), nloc=("nloc0", "median")).reset_index()
res = []
for name, sub in [("all", inst), ("python", inst[inst.repo.isin(PYTHON)]), ("c", inst[~inst.repo.isin(PYTHON)]), ("original 9", inst[inst.repo.isin(OLD)]), ("new 24", inst[~inst.repo.isin(OLD)])]:
    long = sub[sub.obs >= 10]
    s = np.sort(sub.pm.values)[::-1]
    tot = s.sum()
    res.append(dict(group=name, instances=len(sub), gini=round(gini(sub.pm), 3), never_pay_10plus=round(float((long.ev == 0).mean()), 3),
                    top10=round(float(s[:max(1, len(s) // 10)].sum() / tot), 3), top20=round(float(s[:max(1, len(s) // 5)].sum() / tot), 3)))
CC = pd.DataFrame(res)
say(CC.to_string(index=False))
NUM["conc"] = CC.set_index("group").to_dict("index")
per = inst.groupby("repo").apply(lambda g: pd.Series(dict(gini=gini(g.pm), never=float((g[g.obs >= 10].ev == 0).mean()) if (g.obs >= 10).any() else np.nan)))
say("\nper repository: Gini min / median / max = %.2f / %.2f / %.2f ; never-pay (10+ releases) = %.2f / %.2f / %.2f" % (per.gini.min(), per.gini.median(), per.gini.max(), per.never.min(), per.never.median(), per.never.max()))
NUM["gini_repo"] = [round(per.gini.min(), 2), round(per.gini.median(), 2), round(per.gini.max(), 2)]
# heavy tail of the event size
ev = OBS[OBS.event == 1]
say("interest lines per event: median %.1f, mean %.1f, p90 %.1f, max %d; share of all interest in the largest 10%% of events %.2f" % (
    ev.interest_lines.median(), ev.interest_lines.mean(), ev.interest_lines.quantile(.9), ev.interest_lines.max(), np.sort(ev.pm_interest.values)[::-1][:max(1, len(ev) // 10)].sum() / ev.pm_interest.sum()))
NUM["event_lines"] = dict(median=float(ev.interest_lines.median()), p90=float(ev.interest_lines.quantile(.9)))

# ------------------------------------------------------------------ P3 memory
say("\n" + "=" * 100, "\nP3  MEMORY: DOES AN INSTANCE THAT PAID PAY AGAIN?\n" + "=" * 100)
seq = OBS.sort_values(["uid", "vi"])
mem = []
for lag in range(1, 7):
    s = seq[["uid", "vi", "event"]].copy()
    p = s.copy(); p["vi"] = p.vi + lag
    m = s.merge(p, on=["uid", "vi"], suffixes=("", "_prev"))
    mem.append(dict(lag=lag, p_after_event=m[m.event_prev == 1].event.mean(), n_after=int((m.event_prev == 1).sum()), p_after_no_event=m[m.event_prev == 0].event.mean()))
MEM = pd.DataFrame(mem)
MEM.to_csv(os.path.join(R, "a3_memory_lags.csv"), index=False)
say(MEM.round(3).to_string(index=False))
seq["past_bin"] = pd.cut(seq.past_n, [-1, 0, 1, 2, 4, 1e9], labels=["0", "1", "2", "3-4", "5+"])
dose = seq.groupby("past_bin").event.agg(["mean", "size"]).reset_index()
say("\nP(event) by number of past events:", dict(zip(dose.past_bin, dose["mean"].round(3))))
NUM["memory"] = dict(lags=[round(x, 3) for x in MEM.p_after_event], no_event=round(float(MEM.p_after_no_event.mean()), 3), dose={str(k): round(v, 3) for k, v in zip(dose.past_bin, dose["mean"])})
dose.to_csv(os.path.join(R, "a3_memory_dose.csv"), index=False)
# macro view: every repository counts once
lag1 = []
for repo, g in seq.groupby("repo"):
    p = g[["uid", "vi", "event"]].copy(); p["vi"] += 1
    m = g[["uid", "vi", "event"]].merge(p, on=["uid", "vi"], suffixes=("", "_prev"))
    if (m.event_prev == 1).sum() >= 10 and (m.event_prev == 0).sum() >= 10:
        lag1.append((m[m.event_prev == 1].event.mean(), m[m.event_prev == 0].event.mean()))
lag1 = np.array(lag1)
say("per repository (%d repos), lag 1: P(event | event before) median %.2f vs P(event | no event before) median %.2f; ratio > 1 in %d repos" % (len(lag1), np.median(lag1[:, 0]), np.median(lag1[:, 1]), int((lag1[:, 0] > lag1[:, 1]).sum())))
NUM["memory_macro"] = dict(n=len(lag1), after_event=round(float(np.median(lag1[:, 0])), 3), after_none=round(float(np.median(lag1[:, 1])), 3), higher_in=int((lag1[:, 0] > lag1[:, 1]).sum()))
# contagion inside a file: did ANOTHER instance of the same file pay in the previous release pair?
S = OBS[["repo", "file", "vi", "uid", "event"]].copy()
fprevtab = S.assign(vi=S.vi + 1).groupby(["repo", "file", "vi"]).agg(n_prev=("event", "size"), ev_prev=("event", "sum")).reset_index()
own = S.assign(vi=S.vi + 1)[["uid", "vi", "event"]].rename(columns={"event": "own_prev"})
cg = S.merge(fprevtab, on=["repo", "file", "vi"]).merge(own, on=["uid", "vi"], how="left")
cg["own_prev"] = cg.own_prev.fillna(0)
cg["own_present"] = cg.uid.isin(own.uid).astype(int)
cg["others_n"] = cg.n_prev - cg.merge(own, on=["uid", "vi"], how="left", suffixes=("", "_o")).event_prev if False else cg.n_prev
cg["others_ev"] = cg.ev_prev - cg.own_prev
cg = cg[cg.n_prev - (cg.own_prev.notna() & cg.uid.isin(own.uid)).astype(int) > 0]
cg = cg[cg.n_prev > 1]
a1 = cg[cg.others_ev > 0].event.mean(); a0 = cg[cg.others_ev == 0].event.mean()
say(f"\nsame-file contagion: P(event) {a1:.3f} when ANOTHER instance of the file paid in the previous release pair vs {a0:.3f} when none did: ratio {a1 / a0:.2f} (n = {len(cg)}); size and own history not controlled")
NUM["contagion_ratio"] = round(float(a1 / a0), 2)
cg["lsize"] = np.log(1 + cg.uid.map(OBS.groupby("uid").nloc0.median()))
cg["oth"] = (cg.others_ev > 0).astype(int)
cg["own"] = cg.own_prev
mc = smf.glm("event ~ oth + own + lsize + C(repo)", cg, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=dict(groups=cg.repo.astype("category").cat.codes))
say(f"   adjusted for the instance's own previous event, its size and the repository: odds ratio of another instance having paid {np.exp(mc.params['oth']):.2f} (95% CI {np.exp(mc.params['oth'] - 1.96 * mc.bse['oth']):.2f} to {np.exp(mc.params['oth'] + 1.96 * mc.bse['oth']):.2f})")
NUM["contagion_or_adj"] = [round(float(np.exp(mc.params["oth"])), 2), round(float(np.exp(mc.params["oth"] - 1.96 * mc.bse["oth"])), 2), round(float(np.exp(mc.params["oth"] + 1.96 * mc.bse["oth"])), 2)]

# ------------------------------------------------------------------ P4 exposure law and debt avoidance
say("\n" + "=" * 100, "\nP4  EXPOSURE LAW (SIZE) AND DEBT AVOIDANCE\n" + "=" * 100)
P = OBS[OBS.persisted == 1].copy()
P["lsize"] = np.log(P.nloc0.clip(lower=1))
m = smf.glm("event ~ lsize + C(repo)", P, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=dict(groups=P.repo.astype("category").cat.codes))
b, se = m.params["lsize"], m.bse["lsize"]
say(f"instance level, logit of 'event in this release pair' on log(size of the debt region) with repository fixed effects: slope {b:.3f} (se {se:.3f}); odds ratio per doubling {np.exp(b * np.log(2)):.2f}")
NUM["size_logit_slope"] = [round(b, 3), round(se, 3)]
pm_ = smf.glm("interest_lines ~ lsize + C(repo)", P, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds=dict(groups=P.repo.astype("category").cat.codes))
say(f"interest lines per release pair, Poisson with log link: exponent beta (lines ~ size^beta) = {pm_.params['lsize']:.3f} (se {pm_.bse['lsize']:.3f}); beta = 1 would be pure exposure")
NUM["beta_lines"] = [round(pm_.params["lsize"], 3), round(pm_.bse["lsize"], 3)]
for lang in ("python", "c"):
    s = P[P.lang == lang]
    if s.repo.nunique() < 2:
        continue
    mm_ = smf.glm("event ~ lsize + C(repo)", s, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=dict(groups=s.repo.astype("category").cat.codes))
    say(f"   {lang}: logit slope {mm_.params['lsize']:.3f} (se {mm_.bse['lsize']:.3f})")
    NUM[f"size_logit_slope_{lang}"] = [round(mm_.params["lsize"], 3), round(mm_.bse["lsize"], 3)]
rho = []
for repo, g in inst.groupby("repo"):
    if len(g) >= 20:
        rho.append(stats.spearmanr(g.nloc, g.ev / g.obs)[0])
say("Spearman of size and event rate per instance, per repository: median %.2f, range %.2f to %.2f (%d repos)" % (np.median(rho), np.min(rho), np.max(rho), len(rho)))
NUM["spearman_size_rate"] = [round(float(np.median(rho)), 2), round(float(np.min(rho)), 2), round(float(np.max(rho)), 2)]
# frozen debt is small
fr = inst[inst.obs >= 10]
say("frozen (no event in 10+ releases) median size %.0f lines vs live %.0f lines (Mann-Whitney p = %.1e)" % (fr[fr.ev == 0].nloc.median(), fr[fr.ev > 0].nloc.median(), stats.mannwhitneyu(fr[fr.ev == 0].nloc, fr[fr.ev > 0].nloc).pvalue))
NUM["frozen_live_size"] = [float(fr[fr.ev == 0].nloc.median()), float(fr[fr.ev > 0].nloc.median())]
# function level: debt versus non-debt functions of the same size
F = FUNCS[(FUNCS.nloc0 >= 3)].copy()
F["chg"] = (F.changed > 0).astype(int)
F["lsize"] = np.log(F.nloc0)
F["smell"] = F.smell.astype(int)
mf = smf.glm("chg ~ lsize + I(lsize**2) + smell + C(repo)", F, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=dict(groups=F.repo.astype("category").cat.codes))
say(f"\nfunction level ({len(F)} function-releases): same size, same repository, a function that is a smell is edited with odds ratio {np.exp(mf.params['smell']):.2f} "
    f"(95%% CI {np.exp(mf.params['smell'] - 1.96 * mf.bse['smell']):.2f} to {np.exp(mf.params['smell'] + 1.96 * mf.bse['smell']):.2f}) against a non-smell function")
NUM["smell_or_same_size"] = [round(float(np.exp(mf.params["smell"])), 2), round(float(np.exp(mf.params["smell"] - 1.96 * mf.bse["smell"])), 2), round(float(np.exp(mf.params["smell"] + 1.96 * mf.bse["smell"])), 2)]
F["bin"] = pd.cut(F.nloc0, [2, 5, 10, 20, 40, 80, 160, 1e9], labels=["3-5", "6-10", "11-20", "21-40", "41-80", "81-160", ">160"])
tab = F.groupby(["bin", "smell"]).chg.agg(["mean", "size"]).unstack()
tab.to_csv(os.path.join(R, "a3_function_edit_rate_by_size.csv"))
say("edit probability by size bin (non-smell | smell):\n" + tab.round(3).to_string())
# enrichment: share of code in debt vs share of edits in debt
ENR = REL.groupby("repo").apply(lambda g: pd.Series(dict(debt_share_code=g.debt0.sum() / g.code0.sum(), debt_share_edits=g.chg_in_debt_pre.sum() / g.chg_all.sum()))).reset_index()
ENR["enrichment"] = ENR.debt_share_edits / ENR.debt_share_code
ENR["lang"] = np.where(ENR.repo.isin(PYTHON), "python", "c")
ENR.to_csv(os.path.join(R, "a3_enrichment.csv"), index=False)
tot_code = REL.debt0.sum() / REL.code0.sum(); tot_ed = REL.chg_in_debt_pre.sum() / REL.chg_all.sum()
say(f"\nenrichment (share of edits in debt / share of code in debt): pooled {tot_ed / tot_code:.2f} (debt = {tot_code:.1%} of code, receives {tot_ed:.1%} of edits); per repository median {ENR.enrichment.median():.2f}, "
    f"range {ENR.enrichment.min():.2f} to {ENR.enrichment.max():.2f}; below 1 in {int((ENR.enrichment < 1).sum())} of {len(ENR)} repositories")
say("   Python median %.2f, C median %.2f" % (ENR[ENR.lang == "python"].enrichment.median(), ENR[ENR.lang == "c"].enrichment.median()))
NUM["enrichment"] = dict(pooled=round(tot_ed / tot_code, 2), debt_share_code=round(tot_code, 3), debt_share_edits=round(tot_ed, 3), median=round(float(ENR.enrichment.median()), 2),
                         below1=int((ENR.enrichment < 1).sum()), n=len(ENR), python=round(float(ENR[ENR.lang == "python"].enrichment.median()), 2), c=round(float(ENR[ENR.lang == "c"].enrichment.median()), 2))

# ------------------------------------------------------------------ P5 release clock
say("\n" + "=" * 100, "\nP5  THE RELEASE CLOCK\n" + "=" * 100)
G = OBS.groupby(["repo", "vi"]).agg(n=("event", "size"), ev=("event", "sum"), pm=("pm_interest", "sum")).reset_index()
RC = REL.merge(G, on=["repo", "vi"])
RC["rate"] = RC.ev / RC.n
RC["churn"] = RC.chg_all / RC.code0
RC["lchurn"] = np.log(RC.chg_all + 1)
say("release pairs:", len(RC), "; mean event rate per instance-release %.3f" % RC.rate.mean())
st = RC.groupby("step").agg(pairs=("rate", "size"), rate=("rate", "mean"), churn_pct=("churn", lambda x: 100 * x.median()), days=("days", "median"), commits=("n_commits", "median")).round(3)
say("by release step:\n" + st.to_string())
NUM["step"] = st.to_dict("index")
pa, mi = RC[RC.step == "patch"].rate, RC[RC.step.isin(["minor", "major"])].rate
say("patch vs minor/major event rate: %.3f vs %.3f (Mann-Whitney p = %.2g)" % (pa.mean(), mi.mean(), stats.mannwhitneyu(pa, mi).pvalue))
NUM["patch_vs_minor_p"] = float(stats.mannwhitneyu(pa, mi).pvalue)
# within-repository predictors of the release total
RC = RC.sort_values(["repo", "vi"])
RC["lpm"] = np.log1p(RC.pm * 1000)
for c in ("lpm", "lchurn"):
    RC[c + "_c"] = RC[c] - RC.groupby("repo")[c].transform("mean")
RC["lpm_prev"] = RC.groupby("repo").lpm_c.shift(1)
RC["lchurn_prev"] = RC.groupby("repo").lchurn_c.shift(1)
RC["ldays_c"] = np.log1p(RC.days) - RC.groupby("repo").days.transform(lambda x: np.log1p(x).mean())
RC["lcommits_c"] = np.log1p(RC.n_commits) - RC.groupby("repo").n_commits.transform(lambda x: np.log1p(x).mean())
ok = RC.dropna(subset=["lpm_prev"])
ac = stats.pearsonr(ok.lpm_c, ok.lpm_prev)[0]
say("within-repository correlation of the log release interest with the previous release: %.2f" % ac)
NUM["clock_autocorr"] = round(float(ac), 2)
for x in ("ldays_c", "lcommits_c", "lchurn_prev"):
    o = ok.dropna(subset=[x])
    say(f"   within-repo correlation of log release interest with {x}: {stats.pearsonr(o.lpm_c, o[x])[0]:.2f}  (n={len(o)})")
    NUM["clock_" + x] = round(float(stats.pearsonr(o.lpm_c, o[x])[0]), 2)
# ICC of the event indicator
def icc(df, grp):
    g = df.groupby(grp).event
    k = g.size().values; ybar = g.mean().values; N = len(df); mean = df.event.mean()
    ssb = (k * (ybar - mean) ** 2).sum(); ssw = ((df.event - g.transform("mean")) ** 2).sum()
    msb = ssb / (len(k) - 1); msw = ssw / (N - len(k)); n0 = (N - (k ** 2).sum() / N) / (len(k) - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw)
OBS["rel"] = OBS.repo + "|" + OBS.vi.astype(str)
say("ICC of the event indicator: by instance %.3f, by release %.3f" % (icc(OBS, "uid"), icc(OBS, "rel")))
NUM["icc"] = dict(instance=round(float(icc(OBS, "uid")), 3), release=round(float(icc(OBS, "rel")), 3))
RC.to_csv(os.path.join(R, "a3_release_clock.csv"), index=False)

# ------------------------------------------------------------------ P6 life cycle
say("\n" + "=" * 100, "\nP6  LIFE CYCLE OF A DEBT INSTANCE\n" + "=" * 100)
intro = T[T.cls == "introduced"][["uid", "vi"]].rename(columns={"vi": "vi_intro"}); intro["vi_intro"] += 1       # present from the next pair on
L = OBS.merge(intro, on="uid")
L["age_in"] = L.vi - L.vi_intro
L["lsize"] = np.log(L.nloc0.clip(lower=1))
LP = L[L.persisted == 1]
ml = smf.glm("event ~ age_in + lsize + C(repo)", LP, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=dict(groups=LP.repo.astype("category").cat.codes))
say(f"instances introduced inside the window ({L.uid.nunique()}): event odds ratio per release of age {np.exp(ml.params['age_in']):.3f} (95% CI {np.exp(ml.params['age_in'] - 1.96 * ml.bse['age_in']):.3f} to {np.exp(ml.params['age_in'] + 1.96 * ml.bse['age_in']):.3f}), size controlled")
NUM["age_or"] = [round(float(np.exp(ml.params["age_in"])), 3), round(float(np.exp(ml.params["age_in"] - 1.96 * ml.bse["age_in"])), 3), round(float(np.exp(ml.params["age_in"] + 1.96 * ml.bse["age_in"])), 3)]
ab = LP.groupby(pd.cut(LP.age_in, [-1, 0, 1, 3, 6, 100], labels=["0", "1", "2-3", "4-6", "7+"])).event.agg(["mean", "size"])
say("P(event) by age since introduction:", dict(ab["mean"].round(3)), " n:", dict(ab["size"]))
NUM["age_bins"] = {str(k): round(float(v), 3) for k, v in ab["mean"].items()}
# survival
last = OBS.sort_values("vi").groupby("uid").tail(1)
surv = L.groupby("uid").agg(dur=("age_in", "max"), rep=("cls", lambda x: int((x == "repayment").any()))).reset_index()
surv["dur"] += 1
tt = np.arange(1, 13)
at_risk = [(surv.dur >= t).sum() for t in tt]
km, S = [], 1.0
for t in tt:
    d = ((surv.dur == t) & (surv.rep == 1)).sum(); n_ = (surv.dur >= t).sum()
    S *= 1 - d / n_ if n_ else 1
    km.append(S)
say("share of debt introduced inside the window still alive after 1, 3, 6, 12 releases (Kaplan-Meier): " + ", ".join("%.2f" % km[i] for i in (0, 2, 5, 11)))
NUM["survival"] = [round(float(km[i]), 3) for i in (0, 2, 5, 11)]
pd.DataFrame(dict(t=tt, survival=km, at_risk=at_risk)).to_csv(os.path.join(R, "a3_survival.csv"), index=False)
# how is it introduced: a new function or a function that crossed a threshold
INT = T[T.cls == "introduced"][["repo", "vi", "file", "func", "rule", "nloc1"]]
ex = FUNCS[["repo", "vi", "file", "func"]].drop_duplicates()
INT = INT.merge(ex.assign(existed=1), on=["repo", "vi", "file", "func"], how="left")
INT["existed"] = INT.existed.fillna(0)
say("\ndebt introduced during a release pair (%d instances): in a function that already existed (grew past a threshold) %.0f%%, in a new function %.0f%%" % (len(INT), 100 * INT.existed.mean(), 100 * (1 - INT.existed.mean())))
NUM["intro_existing_share"] = round(float(INT.existed.mean()), 2)
for rule, g in INT.groupby("rule"):
    say(f"   {rule}: {len(g)} introduced, {g.existed.mean():.0%} in an existing function, median size {g.nloc1.median():.0f}")
# repayment
rp = OBS[OBS.persisted == 0]
rr = OBS.groupby("rule").agg(obs=("event", "size"), rep=("persisted", lambda x: float((x == 0).mean())), ev=("event", "mean"), size=("nloc0", "median")).round(3)
say("by smell kind:\n" + rr.to_string())
NUM["rule"] = rr.to_dict("index")
say("repayment rate per instance-release: %.3f overall; python %.3f, c %.3f" % ((OBS.persisted == 0).mean(), (OBS[OBS.lang == "python"].persisted == 0).mean(), (OBS[OBS.lang == "c"].persisted == 0).mean()))
NUM["repay_rate"] = round(float((OBS.persisted == 0).mean()), 3)
# several smells in one function
mult = OBS[OBS.vi == 0].groupby(["repo", "file", "func"]).size()
say("share of debt functions that carry 2 or 3 smells (first release pair): %.0f%%" % (100 * (mult > 1).mean()))
NUM["multi_smell_share"] = round(float((mult > 1).mean()), 2)

# ------------------------------------------------------------------ P7 path of work (proximity features) and the ranking test
say("\n" + "=" * 100, "\nP7  PATH OF WORK: DOES NEARBY RECENT ACTIVITY ADD TO SIZE AND HISTORY? (LEAVE ONE REPOSITORY OUT)\n" + "=" * 100)
FI = FILES.copy()
FI["dir"] = FI.file.map(lambda p: os.path.dirname(p))
fprev = FI.assign(vi=FI.vi + 1)[["repo", "vi", "file", "changed", "file_code"]].rename(columns={"changed": "file_prev", "file_code": "file_code_prev"})
dprev = FI.assign(vi=FI.vi + 1).groupby(["repo", "vi", "dir"]).agg(dir_prev=("changed", "sum"), dir_code=("file_code", "sum")).reset_index()
rprev = REL.assign(vi=REL.vi + 1)[["repo", "vi", "chg_all", "code0"]].rename(columns={"chg_all": "repo_prev", "code0": "repo_code_prev"})
X = OBS.copy()
X["dir"] = X.file.map(os.path.dirname)
X = X.merge(fprev, on=["repo", "vi", "file"], how="left").merge(dprev, on=["repo", "vi", "dir"], how="left").merge(rprev, on=["repo", "vi"], how="left")
X = X.dropna(subset=["repo_prev"])                                             # drop the first pair of each repository (no previous pair)
X["file_prev"] = X.file_prev.fillna(0); X["dir_prev"] = X.dir_prev.fillna(0)
X["f_file"] = np.log1p(X.file_prev); X["f_dir"] = np.log1p(X.dir_prev - X.file_prev.clip(upper=X.dir_prev)); X["f_repo"] = np.log1p(X.repo_prev) - np.log1p(X.repo_code_prev)
X["f_file_rel"] = X.file_prev / X.file_code_prev.fillna(1).clip(lower=1)
X["lsize"] = np.log(X.nloc0.clip(lower=1)); X["lccn"] = np.log(X.ccn0.clip(lower=1))
X["lpast_il"] = np.log1p(X.past_il); X["lpast_n"] = np.log1p(X.past_n); X["lage"] = np.log1p(X.age)
X["is_py"] = (X.lang == "python").astype(int)
for r_ in ("long_method", "complex_method", "many_params"):
    X["r_" + r_] = (X.rule == r_).astype(int)
BASE = ["lsize", "lccn", "lpast_il", "lpast_n", "lage", "is_py", "r_long_method", "r_complex_method"]
PROX = ["f_file", "f_dir", "f_file_rel"]
CLOCK = ["f_repo"]
say("rows for the test: %d instance-releases, %d repositories, %d events" % (len(X), X.repo.nunique(), X.event.sum()))


def cap(df, score, k, w="interest_lines"):
    out = []
    for (r_, v_), g in df.groupby(["repo", "vi"]):
        tot = g[w].sum()
        if len(g) < 5 or tot <= 0:
            continue
        s = g.assign(_s=score.loc[g.index], _t=np.random.RandomState(0).rand(len(g)))
        s = s.sort_values(["_s", "_t"], ascending=[False, False])
        n = max(1, int(np.ceil(k * len(g))))
        out.append((r_, v_, s[w].iloc[:n].sum() / tot))
    return pd.DataFrame(out, columns=["repo", "vi", "cap"]).set_index(["repo", "vi"]).cap


def fit_predict(feats, tr, te, model):
    if model == "logit":
        sc = StandardScaler().fit(tr[feats]); m_ = LogisticRegression(C=0.3, max_iter=400).fit(sc.transform(tr[feats]), tr.event)
        return m_.predict_proba(sc.transform(te[feats]))[:, 1]
    m_ = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=150, l2_regularization=1.0).fit(tr[feats], tr.event)
    return m_.predict_proba(te[feats])[:, 1]


def protocol(name, splits):
    preds = {k: pd.Series(np.nan, index=X.index) for k in ("size", "persist", "persist_size", "logit_base", "logit_prox", "logit_prox_clock", "gb_base", "gb_prox_clock")}
    for tr, te in splits:
        te = X.loc[te]; tr = X.loc[tr]
        preds["size"].loc[te.index] = te.lsize.values
        preds["persist"].loc[te.index] = te.past_il.values + 1e-9 * te.lsize.values * 0              # random ties
        preds["persist_size"].loc[te.index] = te.past_il.values + 1e-6 * te.lsize.values              # ties broken by size
        preds["logit_base"].loc[te.index] = fit_predict(BASE, tr, te, "logit")
        preds["logit_prox"].loc[te.index] = fit_predict(BASE + PROX, tr, te, "logit")
        preds["logit_prox_clock"].loc[te.index] = fit_predict(BASE + PROX + CLOCK, tr, te, "logit")
        preds["gb_base"].loc[te.index] = fit_predict(BASE, tr, te, "gb")
        preds["gb_prox_clock"].loc[te.index] = fit_predict(BASE + PROX + CLOCK, tr, te, "gb")
    rows, caps = [], {}
    for k_, s_ in preds.items():
        d = X[s_.notna()]
        auc = roc_auc_score(d.event, s_[d.index])
        for kk in (0.2, 0.3, 0.5):
            caps[(k_, kk)] = cap(d, s_[d.index], kk)
        rows.append(dict(protocol=name, model=k_, auc=round(auc, 3), cap20=round(100 * caps[(k_, .2)].mean(), 1), cap30=round(100 * caps[(k_, .3)].mean(), 1), cap50=round(100 * caps[(k_, .5)].mean(), 1), groups=len(caps[(k_, .2)])))
    return pd.DataFrame(rows), caps


def paired(caps, a, b, k, B=2000):
    d = (caps[(a, k)] - caps[(b, k)]).dropna().values * 100
    rs = np.random.RandomState(1)
    bs = [rs.choice(d, len(d)).mean() for _ in range(B)]
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(d)


repos = sorted(X.repo.unique())
loro = [(X.index[X.repo != r_], X.index[X.repo == r_]) for r_ in repos]
mx = X.groupby("repo").vi.transform("max")
test_mask = X.vi > 0.6 * mx
temporal = [(X.index[~test_mask], X.index[test_mask])]
res_l, caps_l = protocol("leave-one-repository-out", loro)
res_t, caps_t = protocol("temporal (last 40% of each repository)", temporal)
RES = pd.concat([res_l, res_t])
RES.to_csv(os.path.join(R, "a3_path_of_work_models.csv"), index=False)
pd.concat([pd.DataFrame({"protocol": pn, "model": k_[0], "top": int(k_[1] * 100), "cap": v_}).reset_index() for pn, cs in (("LORO", caps_l), ("temporal", caps_t)) for k_, v_ in cs.items()]).to_csv(os.path.join(R, "a3_group_caps.csv"), index=False)
say(RES.to_string(index=False))
cmp_rows = []
for pname, caps in (("LORO", caps_l), ("temporal", caps_t)):
    for a, b in (("persist_size", "persist"), ("size", "persist"), ("logit_base", "persist_size"), ("logit_prox", "logit_base"), ("logit_prox_clock", "logit_prox"), ("logit_prox_clock", "persist_size"), ("gb_prox_clock", "gb_base"), ("gb_base", "persist_size")):
        for k in (0.2, 0.3):
            m_, lo, hi, n_ = paired(caps, a, b, k)
            cmp_rows.append(dict(protocol=pname, a=a, b=b, top=int(k * 100), diff_pts=round(m_, 1), lo=round(lo, 1), hi=round(hi, 1), groups=n_))
CMP = pd.DataFrame(cmp_rows)
CMP.to_csv(os.path.join(R, "a3_path_of_work_paired.csv"), index=False)
say("\npaired differences of capture (percentage points, 95% bootstrap interval over groups):\n" + CMP.to_string(index=False))
NUM["pow"] = dict(models=RES.to_dict("records"), paired=CMP.to_dict("records"))

# coefficients of the proximity features (full fit, standardised logit)
sc = StandardScaler().fit(X[BASE + PROX + CLOCK]); lr = LogisticRegression(C=0.3, max_iter=400).fit(sc.transform(X[BASE + PROX + CLOCK]), X.event)
coef = pd.Series(lr.coef_[0], index=BASE + PROX + CLOCK).round(3)
say("\nstandardised logit coefficients (all repositories): " + dict(coef).__repr__())
NUM["pow_coef"] = coef.to_dict()
# simple univariate checks
for c in PROX + CLOCK:
    a_ = roc_auc_score(X.event, X[c])
    say(f"   univariate AUC of {c}: {a_:.3f}")
    NUM["auc_" + c] = round(float(a_), 3)
say("   univariate AUC of size %.3f ; of interest paid so far %.3f" % (roc_auc_score(X.event, X.lsize), roc_auc_score(X.event, X.past_il)))
NUM["auc_size"] = round(float(roc_auc_score(X.event, X.lsize)), 3); NUM["auc_past"] = round(float(roc_auc_score(X.event, X.past_il)), 3)

# ------------------------------------------------------------------ P8 size distributions (for the generator)
say("\n" + "=" * 100, "\nP8  SIZE AND COMPLEXITY OF REAL FUNCTIONS (GENERATOR PARAMETERS)\n" + "=" * 100)
V = FUNCS[FUNCS.vi == FUNCS.groupby("repo").vi.transform("max")]
for lang, g in V.groupby("lang"):
    ln = np.log(g.nloc0.clip(lower=1))
    say(f"{lang}: {len(g)} functions in the last release; nloc median {g.nloc0.median():.0f}, p90 {g.nloc0.quantile(.9):.0f}, p99 {g.nloc0.quantile(.99):.0f}; lognormal mu {ln.mean():.2f} sigma {ln.std():.2f}; "
        f"smell share {g.smell.mean():.1%}; long {g.long0.mean():.1%} complex {g.cx0.mean():.1%} params {g.par_smell0.mean():.1%}; corr(nloc, ccn) {np.corrcoef(g.nloc0, g.ccn0)[0, 1]:.2f}")
    NUM["funcs_" + lang] = dict(n=len(g), med=float(g.nloc0.median()), p90=float(g.nloc0.quantile(.9)), mu=round(float(ln.mean()), 2), sigma=round(float(ln.std()), 2), smell_share=round(float(g.smell.mean()), 3))
sr = V.groupby("repo").agg(code=("nloc0", "sum"), funcs=("nloc0", "size"), smell=("smell", "mean"), dsh=("smell", lambda x: 0)).reset_index()
sr["debt_code_share"] = V.assign(d=V.nloc0 * V.smell).groupby("repo").d.sum().values / sr.code
say("share of code lines inside debt functions per repository: median %.2f, range %.2f to %.2f" % (sr.debt_code_share.median(), sr.debt_code_share.min(), sr.debt_code_share.max()))
NUM["debt_code_share"] = [round(float(sr.debt_code_share.median()), 2), round(float(sr.debt_code_share.min()), 2), round(float(sr.debt_code_share.max()), 2)]
# growth of the project
gr = REL.groupby("repo").apply(lambda g: pd.Series(dict(growth=g.code1.iloc[-1] / g.code0.iloc[0], churn_med=float((g.chg_all / g.code0).median()))))
say("code growth over the window: median x%.2f; median churn per release pair (changed lines / code) %.1f%%" % (gr.growth.median(), 100 * gr.churn_med.median()))
NUM["growth"] = round(float(gr.growth.median()), 2); NUM["churn_median_pct"] = round(float(100 * gr.churn_med.median()), 1)

json.dump(NUM, open(os.path.join(R, "a3_numbers.json"), "w"), indent=1, default=str)
OUT.close()
print("a3 done")
