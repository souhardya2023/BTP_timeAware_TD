#!/usr/bin/env python3
"""Share of debt functions with interest in a release pair: with the trait vs the size-matched expectation, per language (for the slides). -> ../results/c4_rates.json"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scenario_analysis", "code"))
import s1_scenarios as S
sys.argv = ["x"]
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
D = pd.read_csv(os.path.join(RES, "c1_features.csv")); D = D[(D.lang == "py") == D.repo.isin(S.PYTHON)].copy(); D["lang"] = D.lang.map({"py": "python", "c": "c"})
D["size_bin"] = pd.cut(D.nloc0, [0, 20, 30, 40, 60, 80, 120, 200, 1e9], labels=False)
out = {}
for name, col, langs, kind in (("many_callees", "n_distinct_calls", ["python", "c"], "high"), ("repeated_lines", "dup_line_ratio", ["python", "c"], "high"),
                               ("pointer_field", "n_arrow", ["c"], "high"), ("goto", "n_goto", ["c"], "present"), ("unsafe", "n_unsafe", ["c"], "present"), ("alloc", "n_alloc", ["c"], "present"),
                               ("clone", "clone_ratio", ["python", "c"], "high"), ("nesting", "max_nest", ["python", "c"], "high")):
    for lang in langs:
        sub = D[D.lang == lang].dropna(subset=[col]).reset_index(drop=True)
        if kind == "high":
            q = sub.groupby(["repo", "size_bin"])[col].transform(lambda x: x.quantile(.75)); m = (sub[col] >= q) & (sub[col] > 0)
        else: m = sub[col] > 0
        res = S.rr_group(sub, m, ["size_bin"]); ok = {k: v for k, v in res.items() if v[1] >= 2 and v[2] >= 15}
        o = sum(v[0] for v in ok.values()); e = sum(v[1] for v in ok.values()); n = sum(v[2] for v in ok.values())
        out[f"{name}|{lang}"] = dict(n=int(n), with_trait=round(o / n, 3), expected=round(e / n, 3), rr=round(o / e, 2), repos=len(ok), n_repos_above1=int(sum(v[0] / v[1] > 1 for v in ok.values())))
json.dump(out, open(os.path.join(RES, "c4_rates.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
