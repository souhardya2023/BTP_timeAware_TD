#!/usr/bin/env python3
"""Reverse engineering: let the data propose the scenarios, then see which repeat.
A shallow decision tree is fitted on the DISCOVERY repositories; every leaf with a high or low event rate is a scenario (a rule of conditions).
Each rule is then measured on VALIDATION repositories it never saw: lift = event rate inside the rule / event rate of the repository.
A rule REPEATS if the pooled validation lift has the same direction, the repository-cluster bootstrap interval excludes 1 and >= 65 % of eligible
repositories agree. Otherwise it is NOISE for that split. A permutation control (event labels shuffled within repository x release x size bin)
gives the replication rate expected from chance.
splits: python->c, c->python, 20 random half/half repository splits (stratified by language), real->synthetic benchmark
"""
import os, sys, itertools
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
import s1_scenarios as S

OUT = S.OUT
FEATS_ALL = ["rel_size", "nloc0", "ccn0", "age", "prev_event", "past_events", "n_obs_before", "is_long", "is_complex", "is_params", "minor_major", "ldays", "commits_rel", "file_n", "func_smells", "sibling_prev", "pos"]


FEATS_INST = ["rel_size", "nloc0", "ccn0", "age", "prev_event", "past_events", "n_obs_before", "is_long", "is_complex", "is_params", "file_n", "func_smells", "sibling_prev"]
MODE = {"all features, lift vs repository rate": (FEATS_ALL, "rate_repo", 1.5, 0.5), "instance features only, lift vs the same release": (FEATS_INST, "rate_rel", 1.4, 0.6)}


def prep(T):
    T = T.copy()
    T["is_long"] = (T.rule == "long_method").astype(int); T["is_complex"] = (T.rule == "complex_method").astype(int); T["is_params"] = (T.rule == "many_params").astype(int)
    T["minor_major"] = T.step.isin(["minor", "major"]).astype(int)
    T["ldays"] = np.log1p(T.days.fillna(T.days.median()))
    T["commits_rel"] = T.n_commits / T.groupby("repo").n_commits.transform("median").clip(lower=1)
    T["pos"] = T.vi / T.groupby("repo").vi.transform("max").clip(lower=1)
    T["ccn0"] = T.ccn0.fillna(0)
    T["rate_repo"] = T.groupby("repo").event.transform("mean")
    T["rate_rel"] = T.groupby(["repo", "vi"]).event.transform("mean")
    return T


def leaves(tree, X, names):
    """return {leaf id: text rule}"""
    t = tree.tree_; out = {}

    def walk(n, conds):
        if t.children_left[n] == -1:
            out[n] = " AND ".join(conds) if conds else "all"; return
        f, th = names[t.feature[n]], t.threshold[n]
        walk(t.children_left[n], conds + [f"{f} <= {th:.3g}"]); walk(t.children_right[n], conds + [f"{f} > {th:.3g}"])
    walk(0, []); return out


def discover(D, feats, expcol, hot, cold, depth=4, leaf=150):
    clf = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=leaf, random_state=0).fit(D[feats], D.event)
    lid = clf.apply(D[feats]); txt = leaves(clf, D[feats], feats)
    rules = []
    for l in np.unique(lid):
        m = lid == l; rate = D.event.values[m].mean(); lift = D.event.values[m].sum() / D[expcol].values[m].sum()
        if lift >= hot or lift <= cold: rules.append(dict(leaf=l, rule=txt[l], n_disc=int(m.sum()), rate_disc=rate, lift_disc=lift, dir="hot" if lift >= hot else "cold"))
    return clf, rules


def validate(clf, rules, V, feats, expcol, nboot=300, rng=np.random.default_rng(3)):
    lid = clf.apply(V[feats]); out = []
    for r in rules:
        m = lid == r["leaf"]; per = []
        for repo, x in V.assign(m=m).groupby("repo"):
            a = x[x.m]
            if len(a) >= 20: per.append((repo, a.event.sum(), a[expcol].sum(), len(a)))
        if len(per) < 3: out.append(dict(r, verdict="too few repositories", val_lift=np.nan)); continue
        o = np.array([p[1] for p in per], float); e = np.array([p[2] for p in per], float)
        est = o.sum() / e.sum(); bs = []
        for _ in range(nboot):
            ix = rng.integers(0, len(per), len(per)); bs.append(o[ix].sum() / max(e[ix].sum(), 1e-9))
        lo, hi = np.percentile(bs, [2.5, 97.5]); sign_up = r["dir"] == "hot"
        agree = float(np.mean((o / np.maximum(e, 1e-9) > 1) == sign_up))
        ok = (lo > 1 if sign_up else hi < 1) and agree >= .65
        out.append(dict(r, val_lift=est, val_lo=lo, val_hi=hi, val_repos=len(per), agree=agree, verdict="REPEATS" if ok else "NOISE"))
    return out


def run_split(name, disc, val, mode, perm=False, rng=None):
    feats, expcol, hot, cold = MODE[mode]
    D, V = disc.copy(), val
    if perm:
        D["event"] = D.groupby(["repo", "vi", "size_bin"]).event.transform(lambda x: rng.permutation(x.values))
        D["rate_repo"] = D.groupby("repo").event.transform("mean"); D["rate_rel"] = D.groupby(["repo", "vi"]).event.transform("mean")
    clf, rules = discover(D, feats, expcol, hot, cold)
    res = validate(clf, rules, V, feats, expcol)
    return pd.DataFrame(res).assign(split=name, perm=perm, mode=mode), clf


def main():
    T, R = S.build(S.REAL, "real"); T = prep(T); SY, _ = S.build(S.SYN, "syn"); SY = prep(SY)
    py = T[T.lang == "python"]; cc = T[T.lang == "c"]
    allr = []; show = {}
    rng = np.random.default_rng(11); repos_py = sorted(py.repo.unique()); repos_c = sorted(cc.repo.unique())
    for mode in MODE:
        r1, _ = run_split("python -> c", py, cc, mode); r2, _ = run_split("c -> python", cc, py, mode); r3, _ = run_split("real -> synthetic", T, SY, mode)
        allr += [r1, r2, r3]; show[mode] = [("python -> c", r1), ("c -> python", r2), ("real -> synthetic", r3)]
        for k in range(20):
            a = set(rng.permutation(repos_py)[: len(repos_py) // 2]) | set(rng.permutation(repos_c)[: len(repos_c) // 2])
            r, _ = run_split("random repo halves", T[T.repo.isin(a)], T[~T.repo.isin(a)], mode); allr.append(r.assign(rep=k))
            rp, _ = run_split("random repo halves (labels shuffled)", T[T.repo.isin(a)], T[~T.repo.isin(a)], mode, perm=True, rng=rng); allr.append(rp.assign(rep=k))
    A = pd.concat(allr, ignore_index=True); A.to_csv(os.path.join(OUT, "s2_rules.csv"), index=False)
    summ = []
    for (md, sp), g in A.groupby(["mode", "split"]):
        g = g[g.verdict != "too few repositories"]
        summ.append(dict(mode=md, split=sp, rules=len(g), repeat=int((g.verdict == "REPEATS").sum()), noise=int((g.verdict == "NOISE").sum()), share_repeat=round(float((g.verdict == "REPEATS").mean()), 3),
                         hot_repeat=round(float((g[g.dir == "hot"].verdict == "REPEATS").mean()), 3), cold_repeat=round(float((g[g.dir == "cold"].verdict == "REPEATS").mean()), 3)))
    summ = pd.DataFrame(summ); summ.to_csv(os.path.join(OUT, "s2_summary.csv"), index=False); print(summ.to_string())
    with open(os.path.join(OUT, "s2_rules_text.txt"), "w") as f:
        for md, lst in show.items():
            for nm, c in lst:
                f.write(f"== {md} | {nm}\n")
                for _, x in c.sort_values("lift_disc", ascending=False).iterrows():
                    f.write(f"{x.verdict:20s} {x.dir:4s} disc lift {x.lift_disc:.2f} (n={x.n_disc})  val lift {x.val_lift:.2f}  :: {x.rule}\n")
    


if __name__ == "__main__":
    main()
