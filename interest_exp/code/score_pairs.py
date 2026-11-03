#!/usr/bin/env python3
"""Score the dataset pairs with the interest model.

For every pair: the functions touched by td.patch are located on the clean and on the TD side. A touched function that is a smell
on a side gets features (its own static metrics on that side + its real git history up to base_commit) and the model predicts
how much interest it will absorb in the next 100 commits. A function that is not a smell on a side carries no debt there (0).
pair score = sum of the predicted interest lines of the touched functions;  delta = TD - clean.
Each pair is scored by a model trained WITHOUT the repo the pair comes from (leave-one-project-out).

usage: score_pairs.py DATASET_DIR REPOS_DIR DATA_DIR RESULTS_DIR      (DATASET_DIR = ../../project_dataset, REPOS_DIR = bare clones, DATA_DIR/snapshots = training snapshots)
"""
import glob
import os
import re
import sys

import lizard
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

sys.path.insert(0, os.path.dirname(__file__))
import history as H
from model_snapshots import FEATS, load


def hunks(patch):
    """{path: (clean_lines, td_lines)} line numbers touched on each side."""
    res, cur = {}, None
    for l in patch.split("\n"):
        m = re.match(r"diff --git a/(\S+) b/(\S+)", l)
        if m:
            cur = m.group(2)
            res[cur] = (set(), set())
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", l)
        if m and cur:
            a, ac, b, bc = int(m.group(1)), int(m.group(2) or 1), int(m.group(3)), int(m.group(4) or 1)
            res[cur][0].update(range(a, a + max(ac, 1)))
            res[cur][1].update(range(b, b + max(bc, 1)))
    return res


def side_functions(folder, path):
    fp = os.path.join(folder, path)
    if not os.path.isfile(fp):
        return {}
    return H.functions(path, open(fp, encoding="utf-8", errors="ignore").read())


def prop(t, k):
    m = re.search(rf"(?m)^{k}: (.*)$", t)
    return m.group(1).strip() if m else ""


def main():
    ds, repos, data, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    snaps = load(data)
    models = {}

    def model_without(repo):
        if repo not in models:
            tr = snaps[snaps.repo != repo + ".git"] if (snaps.repo == repo + ".git").any() else snaps
            clf = RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=0, n_jobs=-1, class_weight="balanced_subsample").fit(tr[FEATS], tr["any"])
            reg = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=0, n_jobs=-1).fit(tr[FEATS], tr["ly"])
            models[repo] = (clf, reg)
        return models[repo]

    walks = {}
    rows = []
    for lang in ("Python", "C_C++"):
        for p in sorted(os.listdir(os.path.join(ds, lang)), key=lambda x: int(x[1:]) if x[1:].isdigit() else 0):
            if not re.fullmatch(r"P\d+", p):
                continue
            pdir = os.path.join(ds, lang, p)
            t = open(os.path.join(pdir, f"{p}_prop", "properties.txt")).read()
            name = os.path.basename(prop(t, "repository"))
            base = prop(t, "base_commit")
            repo = os.path.join(repos, name + ".git")
            patch = open(os.path.join(pdir, f"{p}_prop", "td.patch"), errors="ignore").read()
            if (name, base) not in walks:
                _, _, n, state, meta = H.walk(repo, 700, ref=base, full=True)
                walks[(name, base)] = (n - 1, state, meta)
            idx, state, meta = walks[(name, base)]
            clf, reg = model_without(name)
            res = {"clean": [], "TD": []}
            for path, (cl, tl) in hunks(patch).items():
                if not H.is_src(path):
                    continue
                for side, lines in (("clean", cl), ("TD", tl)):
                    fs = side_functions(os.path.join(pdir, f"{p}_{side}"), path)
                    nsm = sum(1 for f in fs.values() if H.is_smell(f))
                    for fn, f in fs.items():
                        if not any(f["s"] <= ln <= f["e"] for ln in lines) or not H.is_smell(f):
                            continue
                        res[side].append(H.features(name + ".git", idx, path, fn, f, fs, nsm, meta.get((path, fn))))
            score = {}
            for side, feats in res.items():
                if feats:
                    X = pd.DataFrame(feats)
                    X["lang_c"] = (X.lang == "c").astype(int)
                    pa = clf.predict_proba(X[FEATS])[:, 1]
                    pl = np.expm1(reg.predict(X[FEATS]))
                    score[side] = (len(X), float(pl.sum()), float(pa.max()))
                else:
                    score[side] = (0, 0.0, 0.0)
            rows.append(dict(lang=lang, pair=p, project=name, td_type=prop(t, "td_type"), td_subtype=prop(t, "td_subtype"),
                             smells_clean=score["clean"][0], smells_TD=score["TD"][0],
                             interest_lines_clean=round(score["clean"][1], 2), interest_lines_TD=round(score["TD"][1], 2),
                             delta_lines=round(score["TD"][1] - score["clean"][1], 2),
                             p_any_clean=round(score["clean"][2], 3), p_any_TD=round(score["TD"][2], 3), delta_p=round(score["TD"][2] - score["clean"][2], 3)))
            print(rows[-1]["lang"], p, name, rows[-1]["td_subtype"], "smells", score["clean"][0], "->", score["TD"][0], "delta lines", rows[-1]["delta_lines"], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out, "pair_scores.csv"), index=False)
    pd.set_option("display.width", 200)
    print("\nby TD type (delta = TD - clean):")
    g = df.groupby("td_type").agg(pairs=("pair", "count"), with_smell=("smells_TD", lambda s: int((s > 0).sum())),
                                  mean_delta_lines=("delta_lines", "mean"), share_positive=("delta_lines", lambda s: round((s > 0).mean(), 2)),
                                  mean_delta_p=("delta_p", "mean")).round(3)
    print(g.to_string())
    print(f"\npairs where a touched function is a smell on neither side (no interest can be assigned): {int(((df.smells_clean == 0) & (df.smells_TD == 0)).sum())} of {len(df)}")


if __name__ == "__main__":
    main()
