#!/usr/bin/env python3
"""Robustness checks and corrections of the release-level insights (reads the tables of a1 and the group captures of a3).
writes results/a3b_report.txt and a3b_numbers.json
"""
import glob, json, os, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import stats
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D, R = os.path.join(ROOT, "data"), os.path.join(ROOT, "results")
PYTHON = {"boltons","click","jinja","werkzeug","requests","flask","attrs","rich","httpx","tqdm","pyyaml","more-itertools","cachetools","bottle","jsonschema","arrow"}
OLD = {"boltons","click","jinja","werkzeug","cJSON","jansson","libpng","libyaml","zlib"}
OUT = open(os.path.join(R, "a3b_report.txt"), "w"); NUM = {}
def say(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.write(s + "\n")
def load(sub): return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(D, sub, "*.csv")))], ignore_index=True)
T = load("transitions"); REL = load("releases"); FUNCS = load("funcs")
FUNCS["smell"] = ((FUNCS.long0 + FUNCS.cx0 + FUNCS.par_smell0) > 0).astype(int)
REL["days"] = (pd.to_datetime(REL.d1) - pd.to_datetime(REL.d0)).dt.days
OBS = T[T.cls != "introduced"].copy(); OBS["event"] = (OBS.interest_lines > 0).astype(int); OBS["uid"] = OBS.repo + "|" + OBS.key
cl = lambda d: dict(groups=d.repo.astype("category").cat.codes)

say("=" * 90, "\nC1  IS DEBT REALLY AVOIDED? ENRICHMENT RESTRICTED TO FUNCTIONS THAT EXIST IN BOTH RELEASES\n" + "=" * 90)
F = FUNCS[FUNCS.nloc0 >= 1]
tot_code = F.groupby("repo").nloc0.sum(); debt_code = F[F.smell == 1].groupby("repo").nloc0.sum()
chg_all = F.groupby("repo").changed.sum(); chg_debt = F[F.smell == 1].groupby("repo").changed.sum()
E = pd.DataFrame(dict(code=tot_code, debt_code=debt_code, chg=chg_all, chg_debt=chg_debt)).fillna(0)
E["enr"] = (E.chg_debt / E.chg) / (E.debt_code / E.code)
pooled = (E.chg_debt.sum() / E.chg.sum()) / (E.debt_code.sum() / E.code.sum())
say(f"changed lines that fall in functions present (same name) at both releases: debt functions = {E.debt_code.sum() / E.code.sum():.1%} of those functions' code, receive {E.chg_debt.sum() / E.chg.sum():.1%} of the changed lines: enrichment {pooled:.2f}; per repository median {E.enr.median():.2f}, range {E.enr.min():.2f} to {E.enr.max():.2f}, below 1 in {(E.enr < 1).sum()} of {len(E)}")
rel = REL.groupby("repo").agg(all_=("chg_all", "sum"), in_funcs=("chg_all", "sum")).join(E.chg.rename("chg_matched"))
share = (E.chg / REL.groupby("repo").chg_all.sum())
say(f"share of ALL changed source lines that lie in functions present at both releases: median {share.median():.2f} (the rest is new code, deleted code, declarations and top-level code)")
NUM["enr_matched"] = dict(pooled=round(float(pooled), 2), median=round(float(E.enr.median()), 2), below1=int((E.enr < 1).sum()), n=len(E), matched_share=round(float(share.median()), 2))
E.assign(enr=E.enr).to_csv(os.path.join(R, "a3b_enrichment_matched.csv"))
by = F.assign(b=pd.cut(F.nloc0, [0, 5, 10, 20, 40, 80, 160, 1e9])).groupby(["b", "smell"]).changed.agg(lambda x: (x > 0).mean()).unstack()
say("edit probability by size (non-smell | smell) - the gap at equal size is small:\n" + by.round(3).to_string())

say("\n" + "=" * 90, "\nC2  CAN THE RELEASE CLOCK BE PREDICTED FROM WHAT IS KNOWN BEFORE THE RELEASE? (LEAVE ONE REPOSITORY OUT)\n" + "=" * 90)
G = OBS.groupby(["repo", "vi"]).agg(n=("event", "size"), ev=("event", "sum"), pm=("pm_interest", "sum")).reset_index()
RC = REL.merge(G, on=["repo", "vi"]); RC["lpm"] = np.log1p(1000 * RC.pm); RC["rate"] = RC.ev / RC.n
RC["ldays"] = np.log1p(RC.days); RC["lcommits"] = np.log1p(RC.n_commits); RC["lchg"] = np.log1p(RC.chg_all)
for c in ("lpm", "ldays", "lcommits", "lchg", "rate"):
    RC[c + "_c"] = RC[c] - RC.groupby("repo")[c].transform("mean")
RC["patch"] = (RC.step == "patch").astype(int); RC["minor"] = (RC.step == "minor").astype(int)
RC["n_c"] = np.log(RC.n) - RC.groupby("repo").n.transform(lambda x: np.log(x).mean())
def loro_r2(feats, y="lpm_c"):
    pred = pd.Series(np.nan, index=RC.index)
    for r_ in RC.repo.unique():
        tr, te = RC[RC.repo != r_], RC[RC.repo == r_]
        X1 = sm.add_constant(tr[feats]); b = sm.OLS(tr[y], X1).fit().params
        pred[te.index] = sm.add_constant(te[feats], has_constant="add").values @ b.values
    ok = pred.notna()
    return 1 - ((RC[y][ok] - pred[ok]) ** 2).sum() / (RC[y][ok] ** 2).sum()
rows = []
for name, f in [("release step only (patch / minor / major)", ["patch", "minor"]), ("days since the previous release", ["ldays_c"]), ("step + days (known before the release)", ["patch", "minor", "ldays_c"]),
                ("number of debt instances", ["n_c"]), ("step + days + instances", ["patch", "minor", "ldays_c", "n_c"]),
                ("commits since the previous release (known after)", ["lcommits_c"]), ("changed lines (known after)", ["lchg_c"])]:
    r2 = loro_r2(f); rows.append((name, round(r2, 3))); say(f"   R2 of the within-repository log release interest, {name}: {r2:.3f}")
NUM["clock_r2"] = dict(rows)
for tgt in ("rate_c",):
    say("   (target: event rate per instance) step + days: R2 %.3f" % loro_r2(["patch", "minor", "ldays_c"], "rate_c"))
NUM["clock_r2_rate"] = round(float(loro_r2(["patch", "minor", "ldays_c"], "rate_c")), 3)

say("\n" + "=" * 90, "\nC3  ROBUSTNESS: EVERY REPOSITORY WEIGHTS THE SAME; ONE ROW PER FUNCTION\n" + "=" * 90)
P = OBS[OBS.persisted == 1].copy(); P["lsize"] = np.log(P.nloc0.clip(lower=1))
P["w"] = 1.0 / P.groupby("repo").event.transform("size")
mw = smf.glm("event ~ lsize + C(repo)", P, family=sm.families.Binomial(), freq_weights=P.w * len(P) / P.w.sum()).fit(cov_type="cluster", cov_kwds=cl(P))
say(f"exposure slope (logit) with equal weight per repository: {mw.params['lsize']:.3f} (se {mw.bse['lsize']:.3f}); unweighted was 0.607")
fn = OBS.groupby(["repo", "vi", "file", "func"]).agg(ev=("event", "max"), nloc=("nloc0", "max")).reset_index(); fn["lsize"] = np.log(fn.nloc.clip(lower=1))
mf = smf.glm("ev ~ lsize + C(repo)", fn, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=cl(fn))
say(f"one row per function and release pair ({len(fn)} rows): slope {mf.params['lsize']:.3f} (se {mf.bse['lsize']:.3f})")
NUM["slope_weighted"] = round(float(mw.params["lsize"]), 3); NUM["slope_function"] = round(float(mf.params["lsize"]), 3)
seq = OBS.sort_values(["uid", "vi"]); p = seq[["uid", "vi", "event"]].copy(); p["vi"] += 1
m = seq[["uid", "vi", "event", "repo", "nloc0"]].merge(p, on=["uid", "vi"], suffixes=("", "_prev"))
m["lsize"] = np.log(m.nloc0.clip(lower=1))
mm = smf.glm("event ~ event_prev + lsize + C(repo)", m, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=cl(m))
say(f"memory with size and repository controlled: odds ratio of an event in the previous pair {np.exp(mm.params['event_prev']):.2f} (95% CI {np.exp(mm.params['event_prev'] - 1.96 * mm.bse['event_prev']):.2f} to {np.exp(mm.params['event_prev'] + 1.96 * mm.bse['event_prev']):.2f})")
NUM["memory_or_adj"] = [round(float(np.exp(mm.params["event_prev"])), 2), round(float(np.exp(mm.params["event_prev"] - 1.96 * mm.bse["event_prev"])), 2), round(float(np.exp(mm.params["event_prev"] + 1.96 * mm.bse["event_prev"])), 2)]

say("\n" + "=" * 90, "\nC4  THE SIZE x HISTORY SCORE ON THE 24 NEW REPOSITORIES ONLY (the original 9 are inside the 33)\n" + "=" * 90)
GC = pd.read_csv(os.path.join(R, "a3_group_caps.csv"))
GC["new"] = ~GC.repo.isin(OLD)
rs = np.random.RandomState(2)
rows = []
for proto in ("LORO", "temporal"):
    for sub, name in ((GC.new, "24 new repositories"), (~GC.new, "9 original repositories")):
        for top in (20, 30):
            def piv(model):
                g = GC[(GC.protocol == proto) & (GC.model == model) & (GC.top == top) & sub].set_index(["repo", "vi"]).cap
                return g
            for a, b in (("logit_base", "persist_size"), ("logit_base", "persist"), ("persist_size", "persist")):
                d = (piv(a) - piv(b)).dropna().values * 100
                if len(d) < 10: continue
                bs = [rs.choice(d, len(d)).mean() for _ in range(2000)]
                rows.append(dict(protocol=proto, subset=name, top=top, a=a, b=b, diff=round(d.mean(), 1), lo=round(np.percentile(bs, 2.5), 1), hi=round(np.percentile(bs, 97.5), 1), groups=len(d)))
SUB = pd.DataFrame(rows); SUB.to_csv(os.path.join(R, "a3b_subset_paired.csv"), index=False)
say(SUB.to_string(index=False)); NUM["subset"] = SUB.to_dict("records")
json.dump(NUM, open(os.path.join(R, "a3b_numbers.json"), "w"), indent=1, default=str); OUT.close(); print("a3b done")
