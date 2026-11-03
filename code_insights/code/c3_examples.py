#!/usr/bin/env python3
"""Pick code examples for the three code insights by a fixed rule (not by taste) and mark the lines that changed in the next release.
Rule: same repository, same release pair (next release later and within a year), lines no wider than 84 characters, raw length 20-40 lines and within 6 lines of each other; hot = paid 1-8 interest lines; cold = paid none
(insight 3: both have an 'ugly' habit, one paid and one did not). Among all such pairs the one with the shortest functions (then repository name) is taken.
-> ../examples/*.json (+ .txt for reading), ../results/c3_rates.csv (observed vs expected share with interest)"""
import json, os, re, subprocess, sys
import numpy as np, pandas as pd

PYSET = {"boltons", "click", "jinja", "werkzeug", "requests", "flask", "attrs", "rich", "httpx", "tqdm", "pyyaml", "more-itertools", "cachetools", "bottle", "jsonschema", "arrow"}
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); EX = os.path.join(HERE, "..", "examples"); BTP = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D = pd.read_csv(os.path.join(RES, "c1_features.csv")); D = D[(D.lang == "py") == D.repo.isin(PYSET)].copy(); D["lang"] = D.lang.map({"py": "python", "c": "c"}); D["raw"] = D.end - D.start + 1
D["size_bin"] = pd.cut(D.nloc0, [0, 20, 30, 40, 60, 80, 120, 200, 1e9], labels=False)
T = {}
for l in open(os.path.join(RES, "c1_texts.jsonl")):
    j = json.loads(l); T[(j["repo"], j["vi"], j["key"])] = j["text"]
D["has_text"] = [(r, v, k) in T and max(len(x.expandtabs(4)) for x in T[(r, v, k)].split("\n")[:max(int(n), 1)]) <= 84 for r, v, k, n in zip(D.repo, D.vi, D.key, D.raw)]
for c in ("n_distinct_calls", "dup_line_ratio"):
    D[c + "_q75"] = D.groupby(["repo", "size_bin"])[c].transform(lambda x: x.quantile(.75)); D[c + "_q25"] = D.groupby(["repo", "size_bin"])[c].transform(lambda x: x.quantile(.25))
import glob
REL = pd.concat([pd.read_csv(f, usecols=["repo", "vi", "d0", "d1"]) for f in glob.glob(os.path.join(HERE, "..", "..", "real_project_analysis", "data", "releases", "*.csv")) if os.path.getsize(f) > 5])
REL["gap"] = (pd.to_datetime(REL.d1, errors="coerce") - pd.to_datetime(REL.d0, errors="coerce")).dt.days
D = D.merge(REL[["repo", "vi", "gap"]], on=["repo", "vi"], how="left")
def vnum(t): return tuple(int(x) for x in re.findall(r"\d+", t)[:3])
D["forward"] = [vnum(b) > vnum(a) for a, b in zip(D.v0, D.v1)]
C = D[D.forward & D.has_text & D.raw.between(20, 40) & D.gap.between(1, 400)]


def changed_lines(r):
    d = subprocess.run(["git", "-C", os.path.join(BTP, "repos", r.repo + ".git"), "diff", "-U0", "--no-color", r.v0, r.v1, "--", r.file], capture_output=True, text=True).stdout
    ch = set()
    for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", d, re.M):
        a, b = int(m.group(1)), int(m.group(2)) if m.group(2) is not None else 1
        nb = int(m.group(4)) if m.group(4) is not None else 1
        if nb > 0: ch.update(range(a, a + b))   # modified lines only (pure deletions are not marked)
    return sorted(x - r.start for x in ch if r.start <= x <= r.end)  # 0-based offsets inside the function


USED = set()


def find(name, hot_fn, cold_fn, lang=None):
    H = C[~C.key.isin(USED) & hot_fn(C) & (C.event == 1) & C.interest_lines.between(1, 8)]; K = C[~C.key.isin(USED) & cold_fn(C) & (C.event == 0)]
    if lang: H, K = H[H.lang == lang], K[K.lang == lang]
    best = None
    for _, h in H.iterrows():
        k = K[(K.repo == h.repo) & (K.vi == h.vi) & ((K.raw - h.raw).abs() <= 6) & (K.key != h.key)]
        for _, c in k.iterrows():
            score = (h.raw + c.raw, h.repo, h.key)
            if best is None or score < best[0]: best = (score, h, c)
    if best is None: print(name, "no pair"); return
    _, h, c = best; out = {}
    for tag, r in (("hot", h), ("cold", c)):
        out[tag] = dict(repo=r.repo, file=r.file, func=r.func, tag=r.v0, next=r.v1, rule=r.rule, nloc=int(r.nloc0), ccn=int(r.ccn0), event=int(r.event), interest_lines=int(r.interest_lines),
                        text=T[(r.repo, r.vi, r.key)].split("\n")[:int(r.raw)], changed=changed_lines(r),
                        traits={k: float(r[k]) for k in ("n_distinct_calls", "dup_line_ratio", "n_goto", "n_unsafe", "n_alloc", "n_arrow", "clone_ratio") if k in r and not pd.isna(r[k])})
    USED.update([h.key, c.key])
    json.dump(out, open(os.path.join(EX, name + ".json"), "w"), indent=1)
    with open(os.path.join(EX, name + ".txt"), "w") as f:
        for tag in ("hot", "cold"):
            e = out[tag]; f.write(f"===== {tag.upper()}: {e['repo']} {e['file']} {e['func']}  ({e['tag']} -> {e['next']}) nloc {e['nloc']} ccn {e['ccn']} interest_lines {e['interest_lines']}  traits {e['traits']}\n")
            for i, ln in enumerate(e["text"]): f.write(("> " if i in e["changed"] else "  ") + ln + "\n")
            f.write("\n")
    print(name, "->", h.repo, h.func, "| vs", c.func, "| sizes", h.raw, c.raw)


find("ex1_many_callees", lambda d: (d.n_distinct_calls >= d.n_distinct_calls_q75) & (d.n_distinct_calls >= 8), lambda d: d.n_distinct_calls <= 3)
find("ex2_repeated_lines", lambda d: (d.dup_line_ratio == 0) & (d.ccn0 >= 6) & (d.shape_run_ratio < 0.3), lambda d: (d.dup_line_ratio >= d.dup_line_ratio_q75) & (d.dup_line_ratio >= 0.35))
find("ex3_ugly_habits_c", lambda d: (d.n_goto >= 1) | (d.n_unsafe >= 1), lambda d: (d.n_goto >= 1) | (d.n_unsafe >= 1), lang="c")

# observed vs expected share with interest for the three traits
