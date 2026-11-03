#!/usr/bin/env python3
"""Which code traits (read from the function text) go with more interest, at equal size?
Group = debt functions whose trait is high (top quarter within the same repository and size bin, and > 0; for count traits that are mostly 0: present).
Effect = rate ratio of 'had interest in the release pair' against the other debt functions of the same repository and size bin; pooled per language
with a repository-cluster bootstrap (same machinery and verdict rule as the scenario analysis). -> ../results/c2_traits.csv"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scenario_analysis", "code"))
import s1_scenarios as S

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
D = pd.read_csv(os.path.join(RES, "c1_features.csv")); D = D[(D.lang == "py") == D.repo.isin(S.PYTHON)].copy(); D["lang"] = D.lang.map({"py": "python", "c": "c"})  # files in the repository's own language only (C repos hold a few .py scripts)
D["size_bin"] = pd.cut(D.nloc0, [0, 20, 30, 40, 60, 80, 120, 200, 1e9], labels=False)
COMMON = ["dup_line_ratio", "shape_run_ratio", "clone_ratio", "max_nest", "n_calls", "n_distinct_calls", "calls_per_line", "n_return", "n_locals", "magic_numbers", "comment_ratio", "n_branch_words"]
CONLY = ["n_arrow", "n_deref", "n_alloc", "n_null_check", "n_cast_ptr", "n_unsafe", "n_goto"]
PONLY = ["n_try", "n_bare_except", "n_isinstance", "n_self_attr", "n_nested_def", "n_global"]
NAMES = {"dup_line_ratio": "same line repeated inside the function", "shape_run_ratio": "runs of look-alike lines (table-like code)", "clone_ratio": "code copied in another function",
         "max_nest": "deep nesting", "n_calls": "many calls", "n_distinct_calls": "many different functions called", "calls_per_line": "dense in calls", "n_return": "many return points",
         "n_locals": "many local variables", "magic_numbers": "many bare numbers", "comment_ratio": "heavily commented", "n_branch_words": "many branches / conditions",
         "n_arrow": "many pointer field accesses (->)", "n_deref": "many pointer dereferences", "n_alloc": "manual memory (malloc / free)", "n_null_check": "many NULL checks",
         "n_cast_ptr": "pointer casts", "n_unsafe": "unsafe string / memory calls", "n_goto": "goto (cleanup jumps)", "n_try": "try / except blocks", "n_bare_except": "broad except",
         "n_isinstance": "isinstance checks (type switching)", "n_self_attr": "touches many self attributes", "n_nested_def": "nested functions", "n_global": "global state"}


def high_mask(df, col):
    g = df.groupby(["repo", "size_bin"])[col]
    q = g.transform(lambda x: x.quantile(.75))
    return ((df[col] >= q) & (df[col] > 0)).astype(bool)


rows = []
for feats, langs in ((COMMON, ["python", "c"]), (CONLY, ["c"]), (PONLY, ["python"])):
    for f in feats:
        sub = D[D.lang.isin(langs)].dropna(subset=[f]).copy().reset_index(drop=True)
        m = high_mask(sub, f)
        res = S.rr_group(sub, m, ["size_bin"])
        out = dict(trait=f, meaning=NAMES[f], n_high=int(m.sum()))
        py = S.pooled(res, set(sub[sub.lang == "python"].repo), min_exp=2, min_n=15) if "python" in langs else None
        cc = S.pooled(res, set(sub[sub.lang == "c"].repo), min_exp=2, min_n=15) if "c" in langs else None
        for tag, q in (("python", py), ("c", cc)):
            for k in ("rr", "lo", "hi", "n_repos", "agree"): out[f"{tag}_{k}"] = None if q is None else round(q[k], 3)
        if len(langs) == 2: out["verdict"] = S.classify(py, cc)
        else:
            q = py or cc
            out["verdict"] = "only in " + langs[0] + ": " + ("no data" if q is None else ("raises interest" if q["lo"] > 1 else ("lowers interest" if q["hi"] < 1 else "no clear effect")))
        rows.append(out)
R = pd.DataFrame(rows); R.to_csv(os.path.join(RES, "c2_traits.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 45)
print(len(D), D.groupby("lang").event.agg(["mean", "size"]).to_dict())
print(R[["trait", "meaning", "verdict", "python_rr", "python_lo", "python_hi", "c_rr", "c_lo", "c_hi", "python_agree", "c_agree"]].to_string())
