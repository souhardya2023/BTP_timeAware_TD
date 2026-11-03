#!/usr/bin/env python3
"""Named scenarios (patterns) tested for repetition across languages, repositories and sources.

A scenario = a group of debt instance-releases (or functions, or commits) defined by a condition. Its effect is the size-adjusted rate ratio
RR = observed events in the group / events expected from the rest of the same repository at the same size (strata = size bins).
Replication: pooled RR with a repository-cluster bootstrap interval in Python repos, in C/C++ repos and in the synthetic benchmark (a third source),
plus the share of eligible repositories whose RR has the same direction.
  REPEATS    interval excludes 1 in the same direction in both languages and >= 65 % of eligible repositories agree
  LANGUAGE   interval excludes 1 in one language only, or in opposite directions
  NOISE      interval includes 1 in both languages
  (REPEATS is STRONG when the pooled RR is >= 1.3 or <= 0.77, otherwise WEAK)
usage: s1_scenarios.py   (reads real_project_analysis/data and synthetic_dataset_v2/real_pipeline_data; writes ../results/s1_*.csv)
"""
import glob, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REAL = os.path.join(ROOT, "real_project_analysis", "data"); SYN = os.path.join(ROOT, "synthetic_dataset_v2", "real_pipeline_data")
OUT = os.path.join(HERE, "..", "results")
PYTHON = {"boltons", "click", "jinja", "werkzeug", "requests", "flask", "attrs", "rich", "httpx", "tqdm", "pyyaml", "more-itertools", "cachetools", "bottle", "jsonschema", "arrow"}
rng = np.random.default_rng(7)


def load(d, sub):
    out = []
    for f in sorted(glob.glob(os.path.join(d, sub, "*.csv"))):
        try:
            x = pd.read_csv(f)
            if len(x): out.append(x)
        except pd.errors.EmptyDataError:
            pass
    return pd.concat(out, ignore_index=True)


def build(d, source):
    T = load(d, "transitions"); R = load(d, "releases")
    T = T[T.cls != "introduced"].copy()
    T["event"] = (T.interest_lines > 0).astype(int)
    T = T.merge(R[["repo", "vi", "step", "d0", "d1", "n_commits"]], on=["repo", "vi"], how="left")
    T["days"] = (pd.to_datetime(T.d1, errors="coerce") - pd.to_datetime(T.d0, errors="coerce")).dt.days
    T["uid"] = T.repo + "|" + T.key
    T = T.sort_values(["uid", "vi"]).reset_index(drop=True)
    g = T.groupby("uid")
    T["prev_event"] = g.event.shift(1).fillna(0)
    T["past_events"] = g.event.cumsum() - T.event
    T["n_obs_before"] = g.cumcount()
    # sibling: another instance of the same file paid in the previous release pair
    fe = T.groupby(["repo", "file", "vi"]).event.sum().rename("file_ev").reset_index(); fe["vi"] += 1
    T = T.merge(fe, on=["repo", "file", "vi"], how="left"); T["file_ev"] = T.file_ev.fillna(0)
    T["sibling_prev"] = ((T.file_ev - T.prev_event) > 0).astype(int)
    T["file_n"] = T.groupby(["repo", "file", "vi"]).uid.transform("size")
    T["func_smells"] = T.groupby(["repo", "file", "func", "vi"]).uid.transform("size")
    T["size_bin"] = pd.cut(T.nloc0, [0, 5, 10, 20, 30, 40, 60, 80, 120, 200, 1e9], labels=False)
    T["rel_size"] = T.groupby(["repo", "vi"]).nloc0.rank(pct=True)
    T["source"] = source
    T["lang"] = np.where(T.repo.isin(PYTHON), "python", "c") if source == "real" else "python"
    return T, R


def rr_group(df, mask, strata):
    """per repo: observed, expected (from the rest at the same strata), group n"""
    res = {}
    for repo, x in df.groupby("repo"):
        m = mask.loc[x.index]
        a, b = x[m], x[~m]
        if len(a) == 0 or len(b) == 0: continue
        s_b = b.groupby(strata).event.agg(["sum", "size"]); s_a = a.groupby(strata).event.agg(["sum", "size"])
        j = s_a.join(s_b, lsuffix="_a", rsuffix="_b", how="inner"); j = j[j.size_b >= 5]
        if len(j) == 0: continue
        exp = float((j.size_a * j.sum_b / j.size_b).sum()); obs = float(j.sum_a.sum()); n = int(j.size_a.sum())
        res[repo] = (obs, exp, n)
    return res


def pooled(res, repos, nboot=1000, min_exp=3, min_n=30):
    r = {k: v for k, v in res.items() if k in repos and v[1] >= min_exp and v[2] >= min_n}
    if len(r) < 3: return None
    k = list(r); o = np.array([r[i][0] for i in k]); e = np.array([r[i][1] for i in k])
    est = o.sum() / e.sum()
    bs = []
    for _ in range(nboot):
        ix = rng.integers(0, len(k), len(k)); bs.append(o[ix].sum() / max(e[ix].sum(), 1e-9))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    rep = o / e
    agree = float(np.mean((rep > 1) == (est > 1)))
    return dict(rr=est, lo=lo, hi=hi, n_repos=len(k), agree=agree)


def classify(pl, pc):
    if pl is None or pc is None: return "too few repositories"
    sig = lambda p: "up" if p["lo"] > 1 else ("down" if p["hi"] < 1 else "none")
    a, b = sig(pl), sig(pc)
    if a == b and a != "none" and pl["agree"] >= .65 and pc["agree"] >= .65:
        rr = np.exp((np.log(pl["rr"]) + np.log(pc["rr"])) / 2)
        return "REPEATS strong" if (rr >= 1.3 or rr <= .77) else "REPEATS weak"
    if a == "none" and b == "none": return "NOISE"
    return "LANGUAGE-SPECIFIC"


def main():
    T, R = build(REAL, "real"); S, _ = build(SYN, "syn")
    py = set(T[T.lang == "python"].repo); cc = set(T[T.lang == "c"].repo); sy = set(S.repo)
    rows = []

    def add(name, family, adjust, df, mask_fn, strata, srcmask=None):
        mask = mask_fn(df)
        res = rr_group(df, mask, strata)
        p, c = pooled(res, py), pooled(res, cc)
        sres = None
        if name in SYNMASK:
            sm = SYNMASK[name](S); sres = pooled(rr_group(S, sm, strata), sy)
        row = dict(scenario=name, family=family, adjusted_for=adjust, verdict=classify(p, c))
        for tag, q in (("python", p), ("c", c), ("synthetic", sres)):
            for kk in ("rr", "lo", "hi", "n_repos", "agree"): row[f"{tag}_{kk}"] = None if q is None else round(q[kk], 3)
        rows.append(row)

    SYNMASK = {}
    sc = [  # name, family, adjust label, mask fn, strata
        ("paid in the previous release pair", "history", "size", lambda d: d.prev_event == 1, ["size_bin"]),
        ("paid 2+ times before", "history", "size", lambda d: d.past_events >= 2, ["size_bin"]),
        ("has never paid, observed 5+ releases", "history", "size", lambda d: (d.past_events == 0) & (d.n_obs_before >= 5), ["size_bin"]),
        ("large for its repository (top third)", "size", "none", lambda d: d.rel_size > .67, ["vi"]),
        ("small for its repository (bottom third)", "size", "none", lambda d: d.rel_size <= .33, ["vi"]),
        ("Long Method", "type", "size", lambda d: d.rule == "long_method", ["size_bin"]),
        ("Complex Method", "type", "size", lambda d: d.rule == "complex_method", ["size_bin"]),
        ("Many Parameters", "type", "size", lambda d: d.rule == "many_params", ["size_bin"]),
        ("very complex (ccn >= 20)", "type", "size", lambda d: d.ccn0 >= 20, ["size_bin"]),
        ("two or more smells in the same function", "type", "size", lambda d: d.func_smells >= 2, ["size_bin"]),
        ("new debt (age 0-1 releases)", "age", "size", lambda d: d.age <= 1, ["size_bin"]),
        ("old debt (age 7+ releases)", "age", "size", lambda d: d.age >= 7, ["size_bin"]),
        ("minor or major release", "release", "none", lambda d: d.step.isin(["minor", "major"]), ["repo"]),
        ("long gap since last tag (above repo median)", "release", "none", lambda d: d.days > d.groupby("repo").days.transform("median"), ["repo"]),
        ("busy release (commits above repo median)", "release", "none", lambda d: d.n_commits > d.groupby("repo").n_commits.transform("median"), ["repo"]),
        ("a sibling in the file paid before", "file", "size", lambda d: d.sibling_prev == 1, ["size_bin", "prev_event"]),
        ("file holds 3+ debt instances", "file", "size", lambda d: d.file_n >= 3, ["size_bin"]),
    ]
    SYNMASK.update({n: f for n, _, _, f, _ in sc})
    for name, fam, adj, f, strata in sc:
        add(name, fam, adj, T, f, strata)

    # function level: is a debt function edited more than a clean one at the same size?
    def fun(d):
        F = load(d, "funcs"); F["event"] = (F.changed > 0).astype(int); F["debt"] = ((F.long0 + F.cx0 + F.par_smell0) > 0)
        F["size_bin"] = pd.cut(F.nloc0, [0, 5, 10, 20, 30, 40, 60, 80, 120, 200, 1e9], labels=False)
        return F
    F = fun(REAL); FS = fun(SYN)
    F["lang"] = np.where(F.repo.isin(PYTHON), "python", "c")
    mask = F.debt; res = rr_group(F, mask, ["size_bin"]); p, c = pooled(res, py), pooled(res, cc); s_ = pooled(rr_group(FS, FS.debt, ["size_bin"]), sy)
    row = dict(scenario="debt function is edited more than a clean one", family="avoidance", adjusted_for="size", verdict=classify(p, c))
    for tag, q in (("python", p), ("c", c), ("synthetic", s_)):
        for kk in ("rr", "lo", "hi", "n_repos", "agree"): row[f"{tag}_{kk}"] = None if q is None else round(q[kk], 3)
    rows.append(row)

    # commit level: what creates debt (real repositories only; the benchmark has no commit table)
    C = load(REAL, "commits"); C = C[C.bulk == 0].copy()
    C["lang"] = np.where(C.repo.isin(PYTHON), "python", "c")
    C["event"] = (C.smell_created > 0).astype(int); C["rem"] = (C.smell_removed > 0).astype(int)
    C["size_bin"] = pd.cut(C.code_lines_changed, [-1, 2, 5, 10, 20, 40, 80, 160, 1e9], labels=False)
    C["big"] = C.groupby("repo").code_lines_changed.transform(lambda x: x > x.quantile(.75))
    cs = [("a bug-fix commit creates debt more often", "commit", "size of change", C.bugfix == 1, "event"),
          ("a big commit (top quarter) creates debt more often", "commit", "none", C.big, "event"),
          ("a 'refactor/simplify' commit removes debt more often", "commit", "size of change", C.kw_complexity == 1, "rem"),
          ("a commit that adds TODO/FIXME creates debt more often", "commit", "size of change", C.sad_added > 0, "event"),
          ("a commit with many files (>=5 source) creates debt more often", "commit", "size of change", C.src_files >= 5, "event")]
    for name, fam, adj, mask, tgt in cs:
        D = C.copy(); D["event"] = D[tgt]
        strata = ["size_bin"] if adj != "none" else ["repo"]
        res = rr_group(D, mask, strata); p, c = pooled(res, py, min_exp=1, min_n=10), pooled(res, cc, min_exp=1, min_n=10)
        row = dict(scenario=name, family=fam, adjusted_for=adj, verdict=classify(p, c))
        for tag, q in (("python", p), ("c", c), ("synthetic", None)):
            for kk in ("rr", "lo", "hi", "n_repos", "agree"): row[f"{tag}_{kk}"] = None if q is None else round(q[kk], 3)
        rows.append(row)

    out = pd.DataFrame(rows); out.to_csv(os.path.join(OUT, "s1_scenarios.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    print(out[["scenario", "verdict", "python_rr", "python_lo", "python_hi", "c_rr", "c_lo", "c_hi", "synthetic_rr", "python_agree", "c_agree"]].to_string())
    print(out.verdict.value_counts())


if __name__ == "__main__":
    main()
