#!/usr/bin/env python3
"""Do clones matter for how often code is edited?  Two tests on the whole-repository near-clone data of k1_clones.py.

Test A (function level): is a function that has a near-clone partner edited more often than a function of the same size without one?
    size-matched rate ratio (same machinery as the scenario analysis), per language, repository-cluster bootstrap; variants:
    all functions / debt functions only / without test, example and vendor paths / exact copies only (J >= 0.95) / partner in another file.
Test B (the mechanism, co-change): when function A is edited in a release pair, is its clone partner B edited in the same release pair more often than a
    non-clone function of similar size (+-25 %) in the same file (else same directory, else same repository)?  co-change lift = P(B edited | A edited, clone) / P(B' edited | A edited, control).
    Pairs are used in both directions; one control per directed pair (fixed seed); pooled per language with a repository-cluster bootstrap.
-> ../results/k2_tests.csv"""
import glob, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scenario_analysis", "code"))
import s1_scenarios as S

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); DATA = os.path.join(HERE, "..", "..", "real_project_analysis", "data")
rng = np.random.default_rng(5)
F = pd.read_csv(os.path.join(RES, "k1_funcs.csv")); P = pd.read_csv(os.path.join(RES, "k1_pairs.csv"))
E = pd.concat([pd.read_csv(f, usecols=["repo", "vi", "file", "func", "nloc0", "long0", "cx0", "par_smell0", "changed"]) for f in glob.glob(os.path.join(DATA, "funcs", "*.csv")) if os.path.getsize(f) > 5])
D = F.merge(E, on=["repo", "vi", "file", "func"], how="inner")
D = D[(D.file.str.endswith(".py")) == D.repo.isin(S.PYTHON)].copy()          # files in the repository's own language
D["lang"] = np.where(D.repo.isin(S.PYTHON), "python", "c"); D["event"] = (D.changed > 0).astype(int); D["debt"] = (D.long0 + D.cx0 + D.par_smell0) > 0
D["size_bin"] = pd.cut(D.nloc0, [0, 8, 12, 16, 20, 30, 40, 60, 100, 200, 1e9], labels=False)
py, cc = set(D[D.lang == "python"].repo), set(D[D.lang == "c"].repo)
print(len(D), "functions;", D.groupby("lang").size().to_dict(), "| clone share (J>=0.6):", D.groupby("lang").apply(lambda g: round((g.jmax >= .6).mean(), 3)).to_dict())
rows = []


def add(name, kind, py_res, cc_res, extra=""):
    for lang, q in (("python", py_res), ("c", cc_res)):
        rows.append(dict(test=name, kind=kind, lang=lang, **({} if q is None else {k: round(v, 3) for k, v in q.items()}), note=extra))


# ---------------- Test A
def test_a(name, sub, mask_fn):
    sub = sub.reset_index(drop=True); m = mask_fn(sub); res = S.rr_group(sub, m, ["size_bin"])
    add(name, "A: edited more often?", S.pooled(res, py, min_exp=2, min_n=15), S.pooled(res, cc, min_exp=2, min_n=15))


test_a("A1 all functions: has a near-clone (J>=0.6)", D, lambda d: d.jmax >= .6)
test_a("A2 debt functions only", D[D.debt], lambda d: d.jmax >= .6)
test_a("A3 without test / example / vendor paths", D[D.test_path == 0], lambda d: d.jmax >= .6)
test_a("A4 exact copy (J>=0.95)", D, lambda d: d.jmax >= .95)
test_a("A5 clone partner in another file", D, lambda d: (d.jmax >= .6) & (d.partner_same_file == 0))
test_a("A6 many partners (3+)", D, lambda d: d.n_partners >= 3)

# ---------------- Test B
key = lambda r, v, f, fn: (r, v, f, fn)
byrv = {k: g for k, g in D.groupby(["repo", "vi"])}
idx = {(r.repo, r.vi, r.file, r.func): i for i, r in enumerate(D.itertuples())}
ev, nl, fl = D.event.values, D.nloc0.values, D.file.values


def directed(P_):
    A = P_.rename(columns=dict(file_a="fa", func_a="na", file_b="fb", func_b="nb"))
    return pd.concat([A, A.rename(columns=dict(fa="fb", na="nb", fb="fa", nb="na"))], ignore_index=True)


def test_b(name, Pf, label, one_per_a=False):
    DP = directed(Pf); per = {}
    if one_per_a: DP = DP.sample(frac=1, random_state=3).drop_duplicates(["repo", "vi", "fa", "na"])
    clones_of = {}
    for r in DP.itertuples(): clones_of.setdefault((r.repo, r.vi, r.fa, r.na), set()).add((r.fb, r.nb))
    for r in DP.itertuples():
        a, b = idx.get((r.repo, r.vi, r.fa, r.na)), idx.get((r.repo, r.vi, r.fb, r.nb))
        if a is None or b is None or ev[a] == 0: continue
        g = byrv[(r.repo, r.vi)]; ok = (g.jmax < 0.3) & (g.nloc0.between(0.75 * nl[b], 1.25 * nl[b])) & ~((g.file == r.fa) & (g.func == r.na))
        cand = g[ok & (g.file == r.fb)]
        if len(cand) == 0: cand = g[ok & (g.file.str.rsplit("/", n=1).str[0] == r.fb.rsplit("/", 1)[0])]
        if len(cand) == 0: cand = g[ok]
        cand = cand[[(f, n) not in clones_of.get((r.repo, r.vi, r.fa, r.na), set()) for f, n in zip(cand.file, cand.func)]]
        if len(cand) == 0: continue
        c = cand.iloc[rng.integers(len(cand))]
        d = per.setdefault(r.repo, [0, 0, 0]); d[0] += 1; d[1] += int(ev[b]); d[2] += int(c.event)
    res = {}
    for lang, rs in (("python", py), ("c", cc)):
        use = {k: v for k, v in per.items() if k in rs and v[0] >= 5}
        if len(use) < 3: add(name, label, None, None); continue
        n = np.array([v[0] for v in use.values()], float); b1 = np.array([v[1] for v in use.values()], float); b0 = np.array([v[2] for v in use.values()], float)
        est = b1.sum() / max(b0.sum(), 1e-9); bs = []
        for _ in range(1000):
            i = rng.integers(0, len(n), len(n)); bs.append(b1[i].sum() / max(b0[i].sum(), 1e-9))
        lo, hi = np.percentile(bs, [2.5, 97.5])
        rows.append(dict(test=name, kind=label, lang=lang, rr=round(est, 3), lo=round(lo, 3), hi=round(hi, 3), n_repos=len(use), agree=round(float(np.mean((b1 > b0) == (est > 1))), 3), n_pairs=int(n.sum()),
                         p_partner=round(b1.sum() / n.sum(), 3), p_control=round(b0.sum() / n.sum(), 3)))


Pn = P.copy(); Pn["test"] = Pn.file_a.str.contains(r"(?:^|/)(?:tests?|testing|examples?|docs?|contrib|deps|vendor|third_party|fuzz\w*|bench\w*|programs)(?:/|$)", case=False) | Pn.file_b.str.contains(r"(?:^|/)(?:tests?|testing|examples?|docs?|contrib|deps|vendor|third_party|fuzz\w*|bench\w*|programs)(?:/|$)", case=False)
test_b("B1 co-change: all clone pairs (J>=0.6)", P, "B: partner edited together?")
test_b("B2 co-change: close clones (J>=0.8)", P[P.jaccard >= .8], "B: partner edited together?")
test_b("B3 co-change: without test / example / vendor paths", Pn[~Pn.test], "B: partner edited together?")
test_b("B4 co-change: partner in another file", P[P.file_a != P.file_b], "B: partner edited together?")
test_b("B5 co-change: one random partner per edited function", P, "B: partner edited together?", one_per_a=True)
R = pd.DataFrame(rows); R.to_csv(os.path.join(RES, "k2_tests.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
print(R[["test", "lang", "rr", "lo", "hi", "n_repos", "agree", "n_pairs", "p_partner", "p_control"]].to_string())
