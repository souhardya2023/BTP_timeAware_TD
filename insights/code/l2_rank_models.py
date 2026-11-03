"""Insight set L2-B: can hand-made 'hotness' scores built from the time series of an instance beat the persistence baseline?
Scores are rules (no training) or a small learned model; all are evaluated with the same groups and the same capture@k as the talk.
Interest is persistent in time (see l2_temporal_structure.py: no decay with lag), so every rule keeps the whole history, but
 - pools evidence with a Beta-binomial shrinkage (an instance seen for 1 release with 1 event is not hotter than one with 6 events in 20),
 - uses change-proneness (any change in the region, not only interest lines),
 - breaks the many ties of persistence (instances with no history) with the size of the region (exposure).
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

from common import ROOT, boot_ci, capture, load_transitions

warnings.filterwarnings("ignore")
rng0 = 7
T = load_transitions()
T = T.sort_values(["repo", "key", "vi"])
g = T.groupby(["repo", "key"])
T["expo_w"] = g.cumcount()                                       # releases of history inside the 20-release window
T["expo"] = T.age                                                # releases of history before this one (whole life of the instance)
T["ev"] = (T.interest_lines > 0).astype(int)
T["chg"] = (T.changed > 0).astype(int)
T["ev_cnt"] = T.past_n                                           # interest events before this release pair
T["chg_cnt"] = g.chg.cumsum() - T.chg
T["il_sum"] = T.past_il
T["chd_sum"] = g.changed.cumsum() - T.changed
last = T.vi.where(T.ev == 1)
T["last_ev_vi"] = last.groupby([T.repo, T.key]).transform(lambda s: s.shift(1).ffill())
T["since_ev"] = (T.vi - T.last_ev_vi).fillna(99)
T["ev_last3"] = g.ev.transform(lambda s: s.shift(1).rolling(3, min_periods=1).sum()).fillna(0)
T["mean_il_ev"] = (T.il_sum / T.ev_cnt.replace(0, np.nan))

P0 = T.ev.mean()
PC = T.chg.mean()


def shrunk(cnt, expo, p0, a):
    return (cnt + a) / (expo + a / p0)


# ---- the rows and groups of the talk
pm = pd.read_csv(f"{ROOT}/interest_exp/results/pm_predictions.csv")
base = pm[pm.model == "zero"].drop(columns=["model", "predicted_mPM"])
M = base.merge(T, on=["repo", "vi", "key"], how="left", suffixes=("", "_t"))
assert M.nloc0.notna().all()
M["persist"] = M.il_sum / (M.expo + 1)                          # the baseline of the talk (average interest lines so far)
SC = {}
SC["persistence (talk)"] = M.persist
SC["persistence + size tie-break"] = M.persist + 1e-6 * M.nloc0
SC["event count"] = M.ev_cnt + 1e-6 * M.nloc0
SC["event rate, shrunk (a=2)"] = shrunk(M.ev_cnt, M.expo, P0, 2) + 1e-9 * M.nloc0
SC["event rate, shrunk (a=6)"] = shrunk(M.ev_cnt, M.expo, P0, 6) + 1e-9 * M.nloc0
SC["change-proneness (any change)"] = shrunk(M.chg_cnt, M.expo_w, PC, 2) + 1e-9 * M.nloc0
SC["events + change-proneness"] = shrunk(M.ev_cnt, M.expo, P0, 2) + 0.5 * shrunk(M.chg_cnt, M.expo_w, PC, 2) + 1e-9 * M.nloc0
mag = M.mean_il_ev.fillna(M.il_sum.replace(0, np.nan)).fillna(T.interest_lines[T.ev == 1].mean())
SC["rate x magnitude"] = shrunk(M.ev_cnt, M.expo, P0, 2) * mag
SC["recent event (last 3 releases)"] = M.ev_last3 + 0.1 * shrunk(M.ev_cnt, M.expo, P0, 2) + 1e-9 * M.nloc0
M["random"] = np.random.default_rng(1).random(len(M))
SC["random"] = M.random

# ---- learned model on the new features (leave-one-repo-out and temporal protocol follow the talk)
FE = ["expo", "expo_w", "ev_cnt", "chg_cnt", "il_sum", "chd_sum", "since_ev", "ev_last3", "mean_il_ev", "nloc0", "ccn0", "principal_pm", "age"]
M["rate_s"] = shrunk(M.ev_cnt, M.expo, P0, 2)
M["rate_c"] = shrunk(M.chg_cnt, M.expo_w, PC, 2)
FE += ["rate_s", "rate_c"]
Xall = M[FE].fillna(-1)
M["rep"] = M.repo
learn = {}
for proto, tr_mask_fn in (("leave-one-repo-out", None), ("temporal", None)):
    pass
# training data: all rows of T (not only the evaluated ones) with the same feature construction
T["rate_s"] = shrunk(T.ev_cnt, T.expo, P0, 2)
T["rate_c"] = shrunk(T.chg_cnt, T.expo_w, PC, 2)
Tf = T.copy()
pred_loro = pd.Series(np.nan, index=M.index)
for r in M.repo.unique():
    tr = Tf[Tf.repo != r]
    clf = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0)
    clf.fit(tr[FE].fillna(-1), tr.ev)
    idx = (M.protocol == "leave-one-repo-out") & (M.repo == r)
    pred_loro[idx] = clf.predict_proba(Xall[idx])[:, 1]
pred_tmp = pd.Series(np.nan, index=M.index)
cut = Tf.groupby("repo").vi.transform(lambda s: s.quantile(0.6))
for r in M.repo.unique():
    tr = Tf[(cut.loc[Tf.index] >= Tf.vi) & (Tf.repo == r) | (Tf.repo != r) & (cut.loc[Tf.index] >= Tf.vi)]
    clf = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0).fit(tr[FE].fillna(-1), tr.ev)
    idx = (M.protocol == "temporal") & (M.repo == r)
    if idx.any():
        pred_tmp[idx] = clf.predict_proba(Xall[idx])[:, 1]
SC["learned (GB, new features)"] = pred_loro.fillna(pred_tmp)

# ---- evaluate
KS = [0.1, 0.2, 0.3, 0.5]
rows = []
for proto, mp in M.groupby("protocol"):
    for (repo, vi), gg in mp.groupby(["repo", "vi"]):
        if len(gg) < 10 or gg.actual_mPM.sum() <= 0:
            continue
        y = gg.actual_mPM.values
        for name, s in SC.items():
            sv = s.loc[gg.index].values
            rr = np.random.default_rng(rng0)
            caps = [np.mean([capture(sv, y, k, np.random.default_rng(rng0 + t)) for t in range(5)]) for k in KS]
            rows.append(dict(protocol=proto, repo=repo, vi=vi, score=name, **{f"cap{int(k*100)}": c for k, c in zip(KS, caps)}))
R = pd.DataFrame(rows)
R.to_csv("../results/l2_rank_models_per_group.csv", index=False)
out = []
for proto, rp in R.groupby("protocol"):
    out.append(f"\n### {proto}: {rp.groupby(['repo','vi']).ngroups} groups")
    summ = rp.groupby("score")[[f"cap{int(k*100)}" for k in KS]].mean() * 100
    pv = rp.pivot_table(index=["repo", "vi"], columns="score", values="cap20")
    ref = pv["persistence (talk)"]
    d = []
    for name in summ.index:
        diff = (pv[name] - ref).values * 100
        lo, hi = boot_ci(diff)
        d.append((diff.mean(), lo, hi))
    summ["d20_vs_persistence"] = [x[0] for x in d]
    summ["ci_lo"] = [x[1] for x in d]
    summ["ci_hi"] = [x[2] for x in d]
    summ = summ.sort_values("cap20", ascending=False)
    out.append(summ.round(1).to_string())
    summ.to_csv(f"../results/l2_rank_models_{proto}.csv")
txt = "\n".join(out)
open("../results/l2_rank_models.txt", "w").write(txt)
print(txt)
