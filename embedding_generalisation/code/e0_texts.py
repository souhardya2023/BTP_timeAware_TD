#!/usr/bin/env python3
"""Collect the three text sets once, so every model embeds exactly the same text.
  natural   1,247 diffs of real commits (real_project_analysis/results/b1_diffs.jsonl)
  synthetic diffs parent -> child of the v2 benchmark's debt introductions
  real      the 61 real clean/debt pairs (td.patch)
-> ../embeddings/texts.pkl  (dict of lists + keys)"""
import json, os, pickle, subprocess, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "insights", "new", "code"))
from n1_images import parse_diff
SD = os.path.join(ROOT, "synthetic_dataset_v2")
nat = [json.loads(l) for l in open(os.path.join(ROOT, "real_project_analysis", "results", "b1_diffs.jsonl"))]
P = pd.read_csv(os.path.join(SD, "pairs.csv")); I = pd.read_csv(os.path.join(SD, "instances.csv")).set_index("instance")
F = pd.read_csv(os.path.join(SD, "features", "pairs_delta.csv"))[["instance"]]; P = F.merge(P, on="instance")
syn = []
for _, r in P.iterrows():
    t = subprocess.run(["git", "-C", os.path.join(SD, "repos", r.project + ".git"), "diff", "-U0", r.parent, r.child], capture_output=True, text=True).stdout
    syn.append("\n".join(("+" if s > 0 else "-") + l for s, l in parse_diff(t, I.loc[r.instance].file)))
DS = pd.read_csv(os.path.join(ROOT, "out_dataset", "delta_only", "dataset_without_time.csv")); real = []
for pid in DS.id:
    l, n = pid.split("/")
    patch = os.path.join(ROOT, "project_dataset", "Python" if l == "Python" else "C_C++", n, n + "_prop", "td.patch")
    real.append("\n".join(("+" if s > 0 else "-") + x for s, x in parse_diff(open(patch, errors="ignore").read())))
out = dict(natural=[j["text"] for j in nat], natural_keys=[j["repo"] + "|" + j["sha"] for j in nat], synthetic=syn, synthetic_keys=list(P.instance), real=real, real_keys=list(DS.id))
pickle.dump(out, open(os.path.join(HERE, "..", "embeddings", "texts.pkl"), "wb"))
print({k: len(v) for k, v in out.items()}, "empty:", {k: sum(1 for t in out[k] if not t.strip()) for k in ("natural", "synthetic", "real")})
