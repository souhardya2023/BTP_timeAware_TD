#!/usr/bin/env python3
"""Extra experiments behind the results documents (everything is reproducible; seeds fixed).

x0  dataset versions   the earlier dataset (bug-free vectors, no time) vs the current one without time vs with time - same models, same splits
x1  feature blocks     which feature group carries the information (structure / code / technical debt, alone and combined), with and without time
x2  time controls      the time column replaced by: itself, a shuffled copy (negative control), multiplicative noise, additive noise
x3  time-model sweep   four settings of the fix-time model: how informative is the time alone, and how much does it add
x4  significance       paired comparison with / without time on the pooled predictions: McNemar, bootstrap CI of the accuracy difference, Wilson CI of every accuracy
x5  per class / project  precision, recall, F1 per TD type; accuracy per held-out project

usage: extra_experiments.py [--workers 3]        output ../data/x*.csv
"""
import concurrent.futures as cf
import itertools
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import f1_score, precision_recall_fscore_support

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "..", "data")
sys.path.insert(0, os.path.join(FINAL, "ml_model"))
sys.path.insert(0, os.path.join(FINAL, "pipeline", "bug_injection"))
import run_experiments as R
import sample_times as ST

CLASSES = R.CLASSES
OUT = os.path.join(FINAL, "out_dataset")
OLD = os.path.join(FINAL, "..", "td_vector", "dataset_without_bugs.csv")
META = R.META


def evalrun(D, cols, model, protocol, seed=0):
    p = R.predict(D, cols, model, R.splits(D, protocol, seed))
    return R.metrics(D.td_type, p), p


# ----------------------------------------------------------------------------------------------- x0 dataset versions
def x0_job(a):
    layout, model, protocol, seed = a
    cur = R.load(layout, False)
    old = pd.read_csv(OLD, keep_default_na=False)
    old = old.merge(cur[["id", "fold", "fold_by_project"]], on="id")
    cols = [c for c in old.columns if c.startswith("delta__")] if layout == "delta_only" else [c for c in old.columns if c.startswith(("clean__", "td__", "delta__"))]
    m, _ = evalrun(old, cols, model, protocol, seed)
    return dict(version="v1_bug_free_no_time", layout=layout, model=model, protocol=protocol, repeat=seed, **m)


# ----------------------------------------------------------------------------------------------- x1 feature blocks
BLOCKS = {"structure": ("delta__s_",), "code": ("delta__c_",), "technical_debt": ("delta__t_",), "structure+code": ("delta__s_", "delta__c_"),
          "structure+td": ("delta__s_", "delta__t_"), "code+td": ("delta__c_", "delta__t_"), "all_133": ("delta__",)}


def x1_job(a):
    block, wt, model, protocol, seed = a
    D = R.load("delta_only", True)
    cols = [c for c in D.columns if c.startswith(BLOCKS[block])]
    if wt:
        cols = cols + ["time_diff_min"]
    m, _ = evalrun(D, cols, model, protocol, seed)
    return dict(block=block, with_time=wt, model=model, protocol=protocol, repeat=seed, n_features=len(cols), **m)


# ----------------------------------------------------------------------------------------------- x2 time controls
def perturb(t, variant, seed):
    rng = np.random.default_rng(seed + 1000)
    t = t.values.astype(float)
    if variant == "real":
        return t
    if variant == "shuffled":
        return rng.permutation(t)
    kind, level = variant.split(":")
    level = float(level)
    if kind == "logmult":
        return t * np.exp(rng.normal(0, level, len(t)))
    if kind == "additive":
        return t + rng.normal(0, level * t.std(), len(t))
    raise ValueError(variant)


def x2_job(a):
    variant, model, protocol, seed = a
    D = R.load("delta_only", True)
    D["time_diff_min"] = perturb(D.time_diff_min, variant, seed)
    cols = [c for c in D.columns if c not in META]
    m, _ = evalrun(D, cols, model, protocol, seed)
    return dict(variant=variant, model=model, protocol=protocol, repeat=seed, **m)


# ----------------------------------------------------------------------------------------------- x3 time-model sweep
SWEEP = {
    "cfg0_weak": dict(F={"concurrency": 3.0, "security": 2.2, "complexity": 1.7, "coupling_cohesion": 1.35, "dependency_structure": 1.1}, bs=0.45, ns=0.12, ow=0.6),
    "cfg1_selected": dict(F={"concurrency": 3.4, "security": 2.4, "complexity": 1.8, "coupling_cohesion": 1.4, "dependency_structure": 1.05}, bs=0.30, ns=0.08, ow=0.85),
    "cfg2_strong": dict(F={"concurrency": 4.0, "security": 2.6, "complexity": 1.8, "coupling_cohesion": 1.35, "dependency_structure": 1.05}, bs=0.25, ns=0.06, ow=0.9),
    "cfg3_near_deterministic": dict(F={"concurrency": 4.0, "security": 2.6, "complexity": 1.8, "coupling_cohesion": 1.35, "dependency_structure": 1.05}, bs=0.15, ns=0.04, ow=1.0),
}


def x3_job(a):
    cfg, model, protocol, seed = a
    c = SWEEP[cfg]
    ST.FACTOR.update(c["F"])
    ST.BASE_SIGMA, ST.NOISE_SIGMA, ST.OUTSIDE_WEIGHT = c["bs"], c["ns"], c["ow"]
    D = R.load("delta_only", False)
    B = pd.read_csv(os.path.join(OUT, "bugs.csv"))
    td = []
    for _, r in D.iterrows():
        d = 0.0
        for _, b in B[B.id == r.id].iterrows():
            ct, tt = ST.sample_bug_times(r.id, b.bug, r.td_type, bool(b.in_td_file))
            d += tt - ct
        td.append(d)
    D["time_diff_min"] = td
    base = [c_ for c_ in D.columns if c_ not in META + ["time_diff_min"]]
    if model == "time_only":
        m, _ = evalrun(D, ["time_diff_min"], "random_forest", protocol, seed)
        return dict(config=cfg, model=model, with_time=True, protocol=protocol, repeat=seed, **m)
    out = []
    for wt in (False, True):
        m, _ = evalrun(D, base + (["time_diff_min"] if wt else []), model, protocol, seed)
        out.append(dict(config=cfg, model=model, with_time=wt, protocol=protocol, repeat=seed, **m))
    return out


def flat(rs):
    out = []
    for r in rs:
        out += r if isinstance(r, list) else [r]
    return out


def run(fn, jobs, workers):
    with cf.ProcessPoolExecutor(workers) as ex:
        return flat(list(ex.map(fn, jobs, chunksize=2)))


# ----------------------------------------------------------------------------------------------- x4 / x5 from predictions
def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def x4_x5():
    P = pd.read_csv(os.path.join(R.RES, "predictions.csv"))
    M = pd.read_csv(os.path.join(R.RES, "metrics.csv"))
    rng = np.random.default_rng(0)
    rows, acc_rows = [], []
    for (layout, protocol, model), g in P[P.model.isin(R.MODELS)].groupby(["layout", "protocol", "model"]):
        a = g[~g.with_time].set_index("id")
        b = g[g.with_time].set_index("id").loc[a.index]
        ca, cb = (a.true == a.pred).values, (b.true == b.pred).values
        n = len(ca)
        bb, cc = int((cb & ~ca).sum()), int((~cb & ca).sum())
        pval = stats.binomtest(bb, bb + cc, 0.5).pvalue if bb + cc else 1.0
        boots = [cb[i].mean() - ca[i].mean() for i in (rng.integers(0, n, n) for _ in range(2000))]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        wa, wb = wilson(ca.sum(), n), wilson(cb.sum(), n)
        rows.append(dict(layout=layout, protocol=protocol, model=model, n=n, acc_without=ca.mean(), acc_without_ci_low=wa[0], acc_without_ci_high=wa[1], acc_with=cb.mean(),
                         acc_with_ci_low=wb[0], acc_with_ci_high=wb[1], diff=cb.mean() - ca.mean(), diff_ci_low=lo, diff_ci_high=hi, pairs_fixed_by_time=bb, pairs_broken_by_time=cc, mcnemar_p=pval))
    X4 = pd.DataFrame(rows)
    # repeated protocol: paired over the 20 splits (descriptive: the splits overlap, so the p-value is optimistic)
    rep = []
    for (layout, model), g in M[(M.protocol == "repeated_stratified") & M.model.isin(R.MODELS)].groupby(["layout", "model"]):
        a, b = g[~g.with_time].sort_values("repeat"), g[g.with_time].sort_values("repeat")
        d = b.accuracy.values - a.accuracy.values
        try:
            w = stats.wilcoxon(d).pvalue if np.any(d != 0) else 1.0
        except ValueError:
            w = 1.0
        rep.append(dict(layout=layout, model=model, repeats=len(d), acc_without_mean=a.accuracy.mean(), acc_without_sd=a.accuracy.std(), acc_with_mean=b.accuracy.mean(), acc_with_sd=b.accuracy.std(),
                        diff_mean=d.mean(), diff_sd=d.std(), diff_min=d.min(), diff_max=d.max(), splits_with_better=int((d > 0).sum()), splits_equal=int((d == 0).sum()), splits_worse=int((d < 0).sum()), wilcoxon_p_optimistic=w))
    X4r = pd.DataFrame(rep)
    # per class and per project
    pc, pp = [], []
    for (layout, protocol, model, wt), g in P[P.model.isin(["kbest10_random_forest", "random_forest", "gradient_boosting"])].groupby(["layout", "protocol", "model", "with_time"]):
        pr, rc, f1, sup = precision_recall_fscore_support(g.true, g.pred, labels=CLASSES, zero_division=0)
        for c, a_, b_, c_, s in zip(CLASSES, pr, rc, f1, sup):
            pc.append(dict(layout=layout, protocol=protocol, model=model, with_time=wt, td_type=c, precision=a_, recall=b_, f1=c_, support=int(s)))
        if protocol == "leave_one_project_out":
            tmp = pd.read_csv(os.path.join(OUT, layout, "dataset_with_time.csv"))[["id", "project"]]
            gg = g.merge(tmp, on="id")
            for proj, h in gg.groupby("project"):
                pp.append(dict(layout=layout, model=model, with_time=wt, project=proj, pairs=len(h), accuracy=(h.true == h.pred).mean(), td_types=",".join(sorted(h.true.unique()))))
    return X4, X4r, pd.DataFrame(pc), pd.DataFrame(pp)


def main():
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
    os.makedirs(DATA, exist_ok=True)
    X4, X4r, X5c, X5p = x4_x5()
    X4.to_csv(os.path.join(DATA, "x4_significance_deterministic_splits.csv"), index=False)
    X4r.to_csv(os.path.join(DATA, "x4_significance_repeated_splits.csv"), index=False)
    X5c.to_csv(os.path.join(DATA, "x5_per_class.csv"), index=False)
    X5p.to_csv(os.path.join(DATA, "x5_per_project.csv"), index=False)
    print("x4, x5 done", flush=True)
    # x0
    jobs = [(l, m, p, s) for l in ("full", "delta_only") for m in R.MODELS for p, ss in (("given_stratified", [0]), ("given_by_project", [0]), ("leave_one_project_out", [0]), ("repeated_stratified", range(20))) for s in ss]
    pd.DataFrame(run(x0_job, jobs, workers)).to_csv(os.path.join(DATA, "x0_old_dataset_runs.csv"), index=False)
    print("x0 done", flush=True)
    # x1
    jobs = [(b, wt, m, p, s) for b in BLOCKS for wt in (False, True) for m in ("kbest10_random_forest", "random_forest") for p, ss in (("given_by_project", [0]), ("leave_one_project_out", [0]), ("repeated_stratified", range(10))) for s in ss]
    jobs += [("time_only", True, "random_forest", p, s) for p, ss in (("given_by_project", [0]), ("leave_one_project_out", [0]), ("repeated_stratified", range(10))) for s in ss]
    BLOCKS["time_only"] = ("__none__",)
    res = run(x1_job, [j for j in jobs if j[0] != "time_only"], workers)
    pd.DataFrame(res).to_csv(os.path.join(DATA, "x1_feature_blocks.csv"), index=False)
    print("x1 done", flush=True)
    # x2
    variants = ["real", "shuffled", "logmult:0.25", "logmult:0.5", "logmult:1.0", "additive:0.5", "additive:1.0", "additive:2.0"]
    jobs = [(v, m, p, s) for v in variants for m in ("kbest10_random_forest", "gradient_boosting") for p, ss in (("given_by_project", [0]), ("repeated_stratified", range(10))) for s in ss]
    pd.DataFrame(run(x2_job, jobs, workers)).to_csv(os.path.join(DATA, "x2_time_controls.csv"), index=False)
    print("x2 done", flush=True)
    # x3
    jobs = [(c, m, p, s) for c in SWEEP for m in ("random_forest", "logistic_regression", "kbest10_random_forest", "time_only") for p, ss in (("given_stratified", [0]), ("given_by_project", [0]), ("repeated_stratified", range(10))) for s in ss]
    pd.DataFrame(run(x3_job, jobs, workers)).to_csv(os.path.join(DATA, "x3_time_model_sweep.csv"), index=False)
    print("x3 done", flush=True)


if __name__ == "__main__":
    main()
