#!/usr/bin/env python3
"""Example for the clone insight: a near-clone pair (J >= 0.8) in which BOTH functions were edited in the same release pair.
Rule: next release later and within a year, both functions 10-22 lines and no line wider than 80 characters; the pair with the smallest total length (then repo name) is taken.
The lines edited in the next release are marked. -> ../examples/ex4_clone_cochange.json / .txt"""
import glob, json, os, re, subprocess, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); BTP = os.path.dirname(ROOT); RES = os.path.join(HERE, "..", "results")
sys.path.insert(0, os.path.join(ROOT, "interest_exp", "code"))
import interest_versions as IV
P = pd.read_csv(os.path.join(RES, "k1_pairs.csv")); P = P[P.jaccard >= .8]
E = pd.concat([pd.read_csv(f, usecols=["repo", "vi", "file", "func", "changed"]) for f in glob.glob(os.path.join(ROOT, "real_project_analysis", "data", "funcs", "*.csv")) if os.path.getsize(f) > 5])
R = pd.concat([pd.read_csv(f, usecols=["repo", "vi", "v0", "v1", "d0", "d1"], dtype={"v0": str, "v1": str}) for f in glob.glob(os.path.join(ROOT, "real_project_analysis", "data", "releases", "*.csv")) if os.path.getsize(f) > 5]).dropna()
R["gap"] = (pd.to_datetime(R.d1, errors="coerce") - pd.to_datetime(R.d0, errors="coerce")).dt.days
vnum = lambda t: tuple(int(x) for x in re.findall(r"\d+", t)[:3])
R = R[np.array([vnum(b) > vnum(a) for a, b in zip(R.v0, R.v1)]) & R.gap.between(1, 400).values]
P = P.merge(R[["repo", "vi", "v0", "v1"]], on=["repo", "vi"])
for s in ("a", "b"):
    P = P.merge(E.rename(columns=dict(file="file_" + s, func="func_" + s, changed="ch_" + s)), on=["repo", "vi", "file_" + s, "func_" + s])
P = P[(P.ch_a > 0) & (P.ch_b > 0)]


def body(r, f, fn):
    repo = os.path.join(BTP, "repos", r.repo + ".git"); code = IV.show(repo, r.v0, f); d = IV.funcs(repo, r.v0, f).get(fn)
    if code is None or d is None: return None
    return code.split("\n")[d["s"] - 1:d["e"]], d


def changed(r, f, d):
    t = subprocess.run(["git", "-C", os.path.join(BTP, "repos", r.repo + ".git"), "diff", "-U0", "--no-color", r.v0, r.v1, "--", f], capture_output=True, text=True).stdout; ch = set()
    for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", t, re.M):
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) is not None else 1; nb = int(m.group(4)) if m.group(4) is not None else 1
        if nb > 0: ch.update(range(a, a + b))
    return sorted(x - d["s"] for x in ch if d["s"] <= x <= d["e"])


best = None
for r in P.itertuples():
    ba, bb = body(r, r.file_a, r.func_a), body(r, r.file_b, r.func_b)
    if not ba or not bb: continue
    la, lb = ba[0], bb[0]
    if not (10 <= len(la) <= 22 and 10 <= len(lb) <= 22): continue
    if max(len(x.expandtabs(4)) for x in la + lb) > 80: continue
    ca, cb = changed(r, r.file_a, ba[1]), changed(r, r.file_b, bb[1])
    if not ca or not cb: continue
    sc = (len(la) + len(lb), r.repo, r.func_a)
    if best is None or sc < best[0]: best = (sc, r, la, lb, ca, cb)
_, r, la, lb, ca, cb = best
out = {"a": dict(repo=r.repo, file=r.file_a, func=r.func_a, tag=r.v0, next=r.v1, text=la, changed=ca), "b": dict(repo=r.repo, file=r.file_b, func=r.func_b, tag=r.v0, next=r.v1, text=lb, changed=cb), "jaccard": float(r.jaccard)}
json.dump(out, open(os.path.join(HERE, "..", "examples", "ex4_clone_cochange.json"), "w"), indent=1)
with open(os.path.join(HERE, "..", "examples", "ex4_clone_cochange.txt"), "w") as f:
    for k in ("a", "b"):
        e = out[k]; f.write(f"===== {k.upper()}: {e['repo']} {e['file']} {e['func']} ({e['tag']} -> {e['next']})  J={out['jaccard']}\n")
        for i, ln in enumerate(e["text"]): f.write(("> " if i in e["changed"] else "  ") + ln + "\n")
        f.write("\n")
print(r.repo, r.func_a, r.func_b, r.jaccard, r.v0, r.v1)
