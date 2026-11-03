#!/usr/bin/env python3
"""Acceptance panel: the measurable properties of 33 real repositories (H-tests of DATASET_DESIGN_SPEC.md) computed on a data directory
produced by real_project_analysis/code/a1_release_tables.py (transitions, releases, funcs) - the SAME pipeline for real and synthetic repositories.

usage: acceptance.py DATA_DIR [--manifests DIR] [--out FILE.csv] [--min-releases N]
"""
import glob, json, os, sys, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")

def load(d, sub):
    out = []
    for f in sorted(glob.glob(os.path.join(d, sub, "*.csv"))):
        try:
            out.append(pd.read_csv(f))
        except pd.errors.EmptyDataError:
            pass
    return pd.concat(out, ignore_index=True)

def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum())) if x.sum() > 0 else 0.0

def measure(D, manifests=None, min_rel=0):
    T = load(D, "transitions"); REL = load(D, "releases"); FU = load(D, "funcs")
    if min_rel:
        n = REL.groupby("repo").vi.max() + 2
        keep = n[n >= min_rel].index
        T, REL, FU = T[T.repo.isin(keep)], REL[REL.repo.isin(keep)], FU[FU.repo.isin(keep)]
    if manifests:
        st = {}
        for f in glob.glob(os.path.join(manifests, "*.json")):
            m = json.load(open(f)); rt = m["release_table"]
            for r_ in rt:
                st[(m["id"], r_["tag"])] = (r_["step"], r_["days"])
        REL["step"] = [st.get((r, v), ("patch", 0))[0] for r, v in zip(REL.repo, REL.v1)]
        REL["days"] = [st.get((r, v), ("patch", 0))[1] for r, v in zip(REL.repo, REL.v1)]
    else:
        REL["days"] = (pd.to_datetime(REL.d1) - pd.to_datetime(REL.d0)).dt.days
    M = {}
    T["uid"] = T.repo + "|" + T.key
    O = T[T.cls != "introduced"].copy(); O["event"] = (O.interest_lines > 0).astype(int)
    M["repos"] = O.repo.nunique(); M["instances"] = O.uid.nunique(); M["inst_releases"] = len(O)
    FU["smell"] = ((FU.long0 + FU.cx0 + FU.par_smell0) > 0).astype(int)
    last = FU[FU.vi == FU.groupby("repo").vi.transform("max")]
    M["H1_func_median_lines"] = float(last.nloc0.median()); M["H1_func_p90_lines"] = float(last.nloc0.quantile(.9))
    M["H1_corr_size_ccn"] = float(np.corrcoef(last.nloc0, last.ccn0)[0, 1])
    M["H2_debt_function_share"] = float(last.smell.mean())
    M["H2_debt_line_share_median"] = float((last.assign(d=last.nloc0 * last.smell).groupby("repo").d.sum() / last.groupby("repo").nloc0.sum()).median())
    inst = O.groupby(["repo", "uid"]).agg(obs=("event", "size"), ev=("event", "sum"), pm=("pm_interest", "sum")).reset_index()
    M["H6_gini_per_repo_median"] = float(inst.groupby("repo").pm.apply(gini).median())
    long = inst[inst.obs >= 10]
    M["H6_never_pay_10plus_per_repo_median"] = float(long.groupby("repo").ev.apply(lambda x: (x == 0).mean()).median())
    ev = O[O.event == 1]
    M["H7_event_lines_median"] = float(ev.interest_lines.median()); M["H7_event_lines_p90"] = float(ev.interest_lines.quantile(.9))
    M["mean_event_rate"] = float(O.event.mean())
    # memory
    seq = O.sort_values(["uid", "vi"]); p = seq[["uid", "vi", "event"]].copy(); p["vi"] += 1
    m = seq[["uid", "vi", "event", "repo", "nloc0"]].merge(p, on=["uid", "vi"], suffixes=("", "_prev"))
    M["H5_p_after_event"] = float(m[m.event_prev == 1].event.mean()); M["H5_p_after_none"] = float(m[m.event_prev == 0].event.mean())
    M["H5_ratio"] = M["H5_p_after_event"] / max(1e-9, M["H5_p_after_none"])
    m["lsize"] = np.log(m.nloc0.clip(lower=1))
    try:
        r = smf.glm("event ~ event_prev + lsize + C(repo)", m, family=sm.families.Binomial()).fit()
        M["H5_adjusted_OR"] = float(np.exp(r.params["event_prev"]))
    except Exception:
        M["H5_adjusted_OR"] = float("nan")
    # exposure
    P = O[O.persisted == 1].copy(); P["lsize"] = np.log(P.nloc0.clip(lower=1))
    try:
        r = smf.glm("event ~ lsize + C(repo)", P, family=sm.families.Binomial()).fit(); M["H3_logit_slope"] = float(r.params["lsize"])
    except Exception:
        M["H3_logit_slope"] = float("nan")
    # debt avoidance at equal size
    F = FU[FU.nloc0 >= 3].copy(); F["chg"] = (F.changed > 0).astype(int); F["lsize"] = np.log(F.nloc0)
    try:
        r = smf.glm("chg ~ lsize + I(lsize**2) + smell + C(repo)", F, family=sm.families.Binomial()).fit(); M["H4_debt_flag_OR"] = float(np.exp(r.params["smell"]))
    except Exception:
        M["H4_debt_flag_OR"] = float("nan")
    Fm = FU[FU.nloc0 >= 1]
    M["H4_enrichment_matched"] = float((Fm[Fm.smell == 1].changed.sum() / Fm.changed.sum()) / (Fm[Fm.smell == 1].nloc0.sum() / Fm.nloc0.sum()))
    # clock
    G = O.groupby(["repo", "vi"]).agg(n=("event", "size"), ev=("event", "sum"), pm=("pm_interest", "sum")).reset_index()
    RC = REL.merge(G, on=["repo", "vi"]); RC["rate"] = RC.ev / RC.n
    for s_ in ("patch", "minor", "major"):
        M["H9_rate_" + s_] = float(RC[RC.step == s_].rate.mean()) if (RC.step == s_).any() else float("nan")
        M["H9_share_" + s_] = float((RC.step == s_).mean())
    RC["lpm"] = np.log1p(1000 * RC.pm); RC["ldays"] = np.log1p(RC.days); RC["lcom"] = np.log1p(RC.n_commits)
    for c in ("lpm", "ldays", "lcom"):
        RC[c + "_c"] = RC[c] - RC.groupby("repo")[c].transform("mean")
    RC["patch"] = (RC.step == "patch").astype(int); RC["minor"] = (RC.step == "minor").astype(int)
    pred = pd.Series(np.nan, index=RC.index)
    try:
        for r_ in RC.repo.unique():
            tr, te = RC[RC.repo != r_], RC[RC.repo == r_]
            if len(tr) < 10: continue
            cols_ = ["patch", "minor", "ldays_c"]
            b = sm.OLS(tr.lpm_c, sm.add_constant(tr[cols_])).fit().params
            pred[te.index] = sm.add_constant(te[cols_], has_constant="add").values @ b.values
        ok = pred.notna()
        M["H9_R2_step_days"] = float(1 - ((RC.lpm_c[ok] - pred[ok]) ** 2).sum() / (RC.lpm_c[ok] ** 2).sum())
    except Exception:
        M["H9_R2_step_days"] = float("nan")
    M["H9_corr_commits"] = float(np.corrcoef(RC.lpm_c, RC.lcom_c)[0, 1])
    RC = RC.sort_values(["repo", "vi"]); RC["prev"] = RC.groupby("repo").lpm_c.shift(1)
    o2 = RC.dropna(subset=["prev"]); M["H10_autocorr"] = float(np.corrcoef(o2.lpm_c, o2.prev)[0, 1])
    M["H13_churn_median_pct"] = float(100 * (REL.chg_all / REL.code0).median())
    # life cycle
    intro = T[T.cls == "introduced"][["uid", "vi", "file", "func", "repo"]].copy()
    ex = FU[["repo", "vi", "file", "func"]].drop_duplicates().assign(existed=1)
    intro = intro.merge(ex, on=["repo", "vi", "file", "func"], how="left")
    M["H11_born_in_new_function"] = float(1 - intro.existed.fillna(0).mean())
    M["H11_repayment_rate"] = float((O.persisted == 0).mean())
    i2 = intro[["uid", "vi"]].rename(columns={"vi": "vstart"}); i2["vstart"] += 1
    L = O.merge(i2, on="uid"); L["age"] = L.vi - L.vstart
    surv = L.groupby("uid").agg(dur=("age", "max"), rep=("cls", lambda x: int((x == "repayment").any()))).reset_index(); surv["dur"] += 1
    S = 1.0
    for t in range(1, 13):
        nr = (surv.dur >= t).sum()
        if nr: S *= 1 - ((surv.dur == t) & (surv.rep == 1)).sum() / nr
    M["H11_survival_12"] = float(S)
    LP = L[L.persisted == 1].copy(); LP["lsize"] = np.log(LP.nloc0.clip(lower=1))
    try:
        r = smf.glm("event ~ age + lsize + C(repo)", LP, family=sm.families.Binomial()).fit(); M["H11_age_OR"] = float(np.exp(r.params["age"]))
    except Exception:
        M["H11_age_OR"] = float("nan")
    mult = O[O.vi == 0].groupby(["repo", "file", "func"]).size(); M["H12_multi_smell_share"] = float((mult > 1).mean()) if len(mult) else float("nan")
    return M

TARGETS = [  # key, real value, low, high (acceptance), note
    ("H1_func_median_lines", 8.0, 4, 12, "functions: real Python 5, C 11"), ("H1_func_p90_lines", 34.0, 18, 50, "real Python 22, C 46"), ("H1_corr_size_ccn", 0.88, 0.7, 1.0, ""),
    ("H2_debt_function_share", 0.12, 0.05, 0.2, "real C 17 %, Python 8 %"), ("H2_debt_line_share_median", 0.41, 0.2, 0.6, ""),
    ("H3_logit_slope", 0.607, 0.45, 0.75, ""), ("H4_debt_flag_OR", 1.07, 0.85, 1.25, "no avoidance"), ("H4_enrichment_matched", 1.11, 0.9, 1.3, ""),
    ("H5_ratio", 4.0, 3.0, 5.0, "lag-1 ratio (real 0.46/0.11)"), ("H5_adjusted_OR", 4.63, 3.0, 8.0, ""),
    ("H6_gini_per_repo_median", 0.72, 0.6, 0.85, ""), ("H6_never_pay_10plus_per_repo_median", 0.22, 0.15, 0.40, ""),
    ("H7_event_lines_median", 2.5, 2, 4, ""), ("H7_event_lines_p90", 16, 12, 25, ""),
    ("H9_rate_patch", 0.089, 0.05, 0.13, ""), ("H9_rate_minor", 0.282, 0.2, 0.36, ""), ("H9_rate_major", 0.315, 0.2, 0.42, ""),
    ("H9_R2_step_days", 0.265, 0.15, 0.40, ""), ("H9_corr_commits", 0.73, 0.6, 0.85, ""), ("H10_autocorr", -0.07, -0.2, 0.1, ""),
    ("H11_born_in_new_function", 0.76, 0.6, 0.95, ""), ("H11_survival_12", 0.57, 0.45, 0.70, ""), ("H11_repayment_rate", 0.069, 0.03, 0.09, ""), ("H11_age_OR", 0.929, 0.85, 1.0, ""),
    ("H12_multi_smell_share", 0.47, 0.35, 0.6, ""), ("H13_churn_median_pct", 1.4, 1.0, 2.0, ""), ("mean_event_rate", 0.172, 0.12, 0.23, ""),
]

def panel(M):
    rows = []
    for k, real, lo, hi, note in TARGETS:
        v = M.get(k, float("nan"))
        rows.append(dict(test=k, real=real, accept_low=lo, accept_high=hi, value=round(v, 3), passed=bool(lo <= v <= hi) if v == v else False, note=note))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    D = sys.argv[1]
    man = sys.argv[sys.argv.index("--manifests") + 1] if "--manifests" in sys.argv else None
    mr = int(sys.argv[sys.argv.index("--min-releases") + 1]) if "--min-releases" in sys.argv else 0
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    M = measure(D, man, mr); P = panel(M)
    print(P.to_string(index=False)); print("passed %d of %d" % (P.passed.sum(), len(P)))
    if out: P.to_csv(out, index=False)
