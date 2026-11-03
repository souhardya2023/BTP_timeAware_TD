#!/usr/bin/env python3
"""Commit-level insights: what real changes look like, how debt is created and removed, and what natural pairs are available.
reads data/commits, data/commit_funcs, data/releases; writes results/a4_*.csv, a4_report.txt, a4_numbers.json
"""
import glob, json, os, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import stats
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D, R = os.path.join(ROOT, "data"), os.path.join(R_ := os.path.join(ROOT, "results"), "") if False else os.path.join(ROOT, "results")
PYTHON = {"boltons","click","jinja","werkzeug","requests","flask","attrs","rich","httpx","tqdm","pyyaml","more-itertools","cachetools","bottle","jsonschema","arrow"}
OUT = open(os.path.join(R, "a4_report.txt"), "w"); NUM = {}
def say(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.write(s + "\n")
def load(sub): return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(D, sub, "*.csv")))], ignore_index=True)
CM = load("commits"); CF = load("commit_funcs"); REL = load("releases")
CM["lang"] = np.where(CM.repo.isin(PYTHON), "python", "c")
CM["lines"] = CM.src_added + CM.src_deleted
code = REL.groupby("repo").code1.median().rename("repo_code")
CM = CM.merge(code, on="repo", how="left")
OKC = CM[CM.bulk == 0].copy()
say("=" * 90, "\nQ1  WHAT A REAL COMMIT LOOKS LIKE\n" + "=" * 90)
say(f"{len(CM)} commits that touch source files, {CM.repo.nunique()} repositories ({OKC.shape[0]} analysed at function level, {int(CM.bulk.sum())} bulk commits with more than 40 source files)")
q = OKC.lines.quantile([.25, .5, .75, .9, .99]).round(0).to_dict()
say("source lines changed (added + deleted) per commit, quantiles:", q, "; source files per commit median %.0f, p90 %.0f" % (OKC.src_files.median(), OKC.src_files.quantile(.9)))
say("functions changed per commit: median %.0f, p90 %.0f; single-function commits %.0f%%" % (OKC.funcs_changed.median(), OKC.funcs_changed.quantile(.9), 100 * (OKC.funcs_changed == 1).mean()))
say("bug-fix commits (subject keyword): %.0f%% of commits; their median size %.0f lines vs %.0f for the others" % (100 * OKC.bugfix.mean(), OKC[OKC.bugfix == 1].lines.median(), OKC[OKC.bugfix == 0].lines.median()))
NUM["commit"] = dict(n=len(CM), analysed=len(OKC), lines_q=q, files_med=float(OKC.src_files.median()), funcs_med=float(OKC.funcs_changed.median()), single_func=round(float((OKC.funcs_changed == 1).mean()), 2),
                     bugfix_share=round(float(OKC.bugfix.mean()), 2), fix_lines=float(OKC[OKC.bugfix == 1].lines.median()), nonfix_lines=float(OKC[OKC.bugfix == 0].lines.median()))
frac = OKC.lines / OKC.repo_code
say("dilution: a commit changes a median %.3f%% of the project's code lines (p90 %.2f%%); bug-fix commits %.3f%%" % (100 * frac.median(), 100 * frac.quantile(.9), 100 * frac[OKC.bugfix == 1].median()))
NUM["dilution_pct"] = dict(median=round(float(100 * frac.median()), 3), p90=round(float(100 * frac.quantile(.9)), 2), fix=round(float(100 * frac[OKC.bugfix == 1].median()), 3))
per = OKC.groupby("repo").agg(commits=("sha", "size"), lines_med=("lines", "median"), files_med=("src_files", "median"), fix=("bugfix", "mean"), touch_smell=("smell_touched", lambda x: (x > 0).mean()),
                              created=("smell_created", "sum"), removed=("smell_removed", "sum"), sad_add=("sad_added", "sum"), sad_rm=("sad_removed", "sum")).round(3)
per.to_csv(os.path.join(R, "a4_per_repo.csv")); say(per.to_string())

say("\n" + "=" * 90, "\nQ2  HOW DEBT IS CREATED AND REMOVED\n" + "=" * 90)
ev = CF.groupby("event").agg(n=("sha", "size"), nloc1=("nloc1", "median"), nloc0=("nloc0", "median"), changed=("changed", "median"), bugfix=("bugfix", "mean")).round(2)
say(ev.to_string()); NUM["events"] = ev.to_dict("index")
c_ = OKC.smell_created.sum(); r_ = OKC.smell_removed.sum()
say(f"over {len(OKC)} commits: {c_} smell functions created or introduced, {r_} removed or deleted; net {c_ - r_}; per 100 commits {100 * c_ / len(OKC):.1f} created, {100 * r_ / len(OKC):.1f} removed")
NUM["created_removed"] = [int(c_), int(r_)]
cr = OKC.assign(creates=(OKC.smell_created > 0).astype(int), removes=(OKC.smell_removed > 0).astype(int))
say("share of commits that create debt: %.1f%%; that remove debt: %.1f%%; that touch an existing debt function: %.1f%%" % (100 * cr.creates.mean(), 100 * cr.removes.mean(), 100 * (OKC.smell_touched > 0).mean()))
NUM["commit_share"] = dict(create=round(float(cr.creates.mean()), 3), remove=round(float(cr.removes.mean()), 3), touch=round(float((OKC.smell_touched > 0).mean()), 3))
say("size of the commit that creates debt: median %.0f lines (all commits %.0f); that removes debt: median %.0f lines" % (cr[cr.creates == 1].lines.median(), cr.lines.median(), cr[cr.removes == 1].lines.median()))
NUM["creating_commit_lines"] = [float(cr[cr.creates == 1].lines.median()), float(cr[cr.removes == 1].lines.median())]
# debt creation by author
au = OKC.groupby(["repo", "author"]).agg(commits=("sha", "size"), created=("smell_created", "sum")).reset_index()
au = au[au.commits >= 1]
top = au.groupby("repo").apply(lambda g: g.sort_values("created", ascending=False).created.head(max(1, int(np.ceil(0.1 * len(g))))).sum() / max(1, g.created.sum())).dropna()
topc = au.groupby("repo").apply(lambda g: g.sort_values("commits", ascending=False).commits.head(max(1, int(np.ceil(0.1 * len(g))))).sum() / g.commits.sum()).dropna()
say("authors: the top 10%% of authors make %.0f%% of the commits and create %.0f%% of the new debt functions (medians over repositories)" % (100 * topc.median(), 100 * top.median()))
NUM["author_top10"] = [round(float(topc.median()), 2), round(float(top.median()), 2)]
au2 = au[au.commits >= 5]
rate_corr = stats.spearmanr(au2.commits, au2.created / au2.commits)[0]
say("authors with 5+ commits (%d): spearman of experience (commits) with debt created per commit %.2f" % (len(au2), rate_corr))
NUM["author_experience_corr"] = round(float(rate_corr), 2)
# bug fixes and debt
OKC["touch"] = (OKC.smell_touched > 0).astype(int); OKC["lsize"] = np.log1p(OKC.lines); OKC["lfuncs"] = np.log1p(OKC.funcs_changed)
m = smf.glm("bugfix ~ touch + lsize + lfuncs + C(repo)", OKC, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=dict(groups=OKC.repo.astype("category").cat.codes))
say("a commit that changes a debt function is a bug fix with odds ratio %.2f (95%% CI %.2f to %.2f), commit size, functions touched and repository controlled" % (np.exp(m.params["touch"]), np.exp(m.params["touch"] - 1.96 * m.bse["touch"]), np.exp(m.params["touch"] + 1.96 * m.bse["touch"])))
NUM["bugfix_or_touch"] = [round(float(np.exp(m.params["touch"])), 2), round(float(np.exp(m.params["touch"] - 1.96 * m.bse["touch"])), 2), round(float(np.exp(m.params["touch"] + 1.96 * m.bse["touch"])), 2)]
m2 = smf.glm("bugfix ~ I(smell_created>0) + lsize + lfuncs + C(repo)", OKC, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds=dict(groups=OKC.repo.astype("category").cat.codes))
k = [x for x in m2.params.index if "smell_created" in x][0]
say("a commit that creates a debt function is a bug fix with odds ratio %.2f (95%% CI %.2f to %.2f)" % (np.exp(m2.params[k]), np.exp(m2.params[k] - 1.96 * m2.bse[k]), np.exp(m2.params[k] + 1.96 * m2.bse[k])))
NUM["bugfix_or_create"] = [round(float(np.exp(m2.params[k])), 2), round(float(np.exp(m2.params[k] - 1.96 * m2.bse[k])), 2), round(float(np.exp(m2.params[k] + 1.96 * m2.bse[k])), 2)]
# self-admitted debt
sad = OKC.groupby("repo").agg(a=("sad_added", "sum"), r=("sad_removed", "sum"))
say(f"\nself-admitted debt comments (TODO/FIXME/HACK/XXX) in {len(OKC)} commits: {sad.a.sum()} added, {sad.r.sum()} removed (net {sad.a.sum() - sad.r.sum()}); added / removed per repository median {(sad.a / sad.r.clip(lower=1)).median():.2f}")
w = OKC.assign(sad=(OKC.sad_added > 0).astype(int), cr_=(OKC.smell_created > 0).astype(int))
a1_, a0_ = w[w.sad == 1].cr_.mean(), w[w.sad == 0].cr_.mean()
say(f"P(commit creates a debt function) = {a1_:.3f} when it adds a TODO/FIXME comment, {a0_:.3f} when not (ratio {a1_ / a0_:.2f}); commits adding SAD are {100 * w.sad.mean():.1f}% of all")
NUM["sad"] = dict(added=int(sad.a.sum()), removed=int(sad.r.sum()), p_create_with=round(float(a1_), 3), p_create_without=round(float(a0_), 3), share=round(float(w.sad.mean()), 3))

say("\n" + "=" * 90, "\nQ3  WHICH DEBT TYPES APPEAR IN REAL COMMITS (SUBJECT KEYWORDS; AN APPROXIMATION)\n" + "=" * 90)
kws = ["security", "concurrency", "dependency", "coupling", "complexity"]
for kname in kws: OKC["kw_" + kname] = OKC["kw_" + kname].astype(int)
OKC["nkw"] = OKC[["kw_" + k for k in kws]].sum(axis=1)
rows = []
for sel, name in ((OKC.bugfix == 1, "bug-fix commits"), (OKC.bugfix == 0, "other commits"), (OKC.lang == "python", "python repos"), (OKC.lang == "c", "c repos")):
    g = OKC[sel]
    rows.append(dict(group=name, n=len(g), **{k: round(float(g["kw_" + k].mean()), 3) for k in kws}, any_kw=round(float((g.nkw > 0).mean()), 3), two_or_more=round(float((g.nkw > 1).mean()), 3)))
KW = pd.DataFrame(rows); say(KW.to_string(index=False)); KW.to_csv(os.path.join(R, "a4_type_keywords.csv"), index=False)
tot = OKC[["kw_" + k for k in kws]].sum(); say("share of keyword hits by type: " + ", ".join(f"{k} {tot['kw_' + k] / tot.sum():.2f}" for k in kws))
NUM["type_share"] = {k: round(float(tot["kw_" + k] / tot.sum()), 3) for k in kws}
NUM["mixed_share"] = round(float((OKC.nkw > 1).sum() / max(1, (OKC.nkw > 0).sum())), 3)
sz = {k: float(OKC[OKC["kw_" + k] == 1].lines.median()) for k in kws}
say("median commit size (source lines) by type keyword: " + ", ".join(f"{k} {v:.0f}" for k, v in sz.items())); NUM["type_size"] = sz
sz2 = {k: round(float((OKC[OKC["kw_" + k] == 1].lines / OKC[OKC["kw_" + k] == 1].repo_code).median() * 100), 3) for k in kws}
say("median share of the project changed (%), by type: " + str(sz2)); NUM["type_dilution"] = sz2

say("\n" + "=" * 90, "\nQ4  NATURAL PAIRS AVAILABLE FOR A LEVEL-1 DATASET (a commit and its parent)\n" + "=" * 90)
CF["single"] = CF.groupby(["repo", "sha"]).event.transform("size") == 1
CFm = CF.drop(columns=["bugfix"]).merge(OKC[["repo", "sha", "lines", "funcs_changed", "subject", "src_files", "nkw", "bugfix"]], on=["repo", "sha"], how="inner")
small = CFm[(CFm.lines <= 60) & (CFm.src_files <= 3)]
cand = small.groupby("event").agg(commits=("sha", "nunique"), repos=("repo", "nunique")).reset_index()
say("candidate natural pairs (commit changes <= 60 source lines in <= 3 files):\n" + cand.to_string(index=False))
NUM["candidates"] = cand.set_index("event").commits.to_dict()
clean = small[(small.event.isin(["removed_smell", "deleted_smell"])) & (small.funcs_changed <= 3)]
say("   of the smell-removing commits, %d change at most 3 functions (a clean 'refactoring' pair); they come from %d repositories; with a refactoring/complexity keyword in the subject: %d" % (
    clean.sha.nunique(), clean.repo.nunique(), clean[clean.subject.str.contains("refactor|simplif|clean|split|extract|reduce", case=False, regex=True)].sha.nunique()))
NUM["clean_removals"] = [int(clean.sha.nunique()), int(clean.repo.nunique())]
intro = small[small.event.isin(["introduced_smell", "created_smell"])]
say("   debt-introducing commits that are small and focused: %d (%d repositories); of those that are bug fixes: %d" % (intro.sha.nunique(), intro.repo.nunique(), intro[intro.bugfix == 1].sha.nunique()))
NUM["clean_intro"] = [int(intro.sha.nunique()), int(intro.repo.nunique()), int(intro[intro.bugfix == 1].sha.nunique())]
sec = OKC[(OKC.kw_security == 1) & (OKC.bugfix == 1) & (OKC.lines <= 60)]; conc = OKC[(OKC.kw_concurrency == 1) & (OKC.bugfix == 1) & (OKC.lines <= 60)]
say("   small security fixes by keyword: %d commits in %d repos; small concurrency fixes: %d commits in %d repos (fix-commit pairs for the security and concurrency types; no smell detector sees them)" % (len(sec), sec.repo.nunique(), len(conc), conc.repo.nunique()))
NUM["fix_pairs"] = dict(security=[len(sec), int(sec.repo.nunique())], concurrency=[len(conc), int(conc.repo.nunique())])
ex = small[small.event == "removed_smell"].sort_values("nloc0", ascending=False).head(8)[["repo", "sha", "func", "nloc0", "nloc1", "ccn0", "ccn1", "subject"]]
say("\nexamples of smell-removing commits:\n" + ex.to_string(index=False))
ex.to_csv(os.path.join(R, "a4_examples_removals.csv"), index=False)
CFm.assign(small=lambda d: (d.lines <= 60) & (d.src_files <= 3)).query("small").drop(columns=["small"]).to_csv(os.path.join(R, "a4_natural_pair_candidates.csv"), index=False)
json.dump(NUM, open(os.path.join(R, "a4_numbers.json"), "w"), indent=1, default=str); OUT.close(); print("a4 done")
