"""S2: ranking debt instances inside a release, on the synthetic histories, per regime.
Scores (all use only what is known at the start of the release pair):
  persistence            interest lines paid so far / (age + 1)             (the baseline of the talk)
  shrunk rate            (events + 2) / (releases + 2 / base rate)           Beta-binomial shrinkage
  clock-normalised rate  (events + a) / (sum of release activity over the releases the instance was exposed to + a / h0)
                         release activity = lines added in the release pair, normalised by the project's mean (observable from git)
  recency                events weighted 0.5 ** (releases since the event)    (for self-exciting debt)
  neighbours             events of the other instances of the same file in the previous release pair
  learned (GB)           gradient boosting on all of the above + size + age, trained on other projects (5-fold by project)
  oracle (latent rate)   the generator's latent rate of the instance  -> the ceiling of ANY history-based method (evaluation only)
Evaluation: capture of the interest of the release pair in the top k %, groups = (project, release) with >= 6 instances and some interest; paired bootstrap against persistence."""
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GroupKFold

from sload import SD, boot_ci, capture, latent, releases, transitions

warnings.filterwarnings("ignore")
T = transitions()
R = releases()
L = latent()
T["latent"] = T.key.map(L.latent_rate)
# release activity proxy: lines added in the release pair (known after the release; used for the PAST releases only)
R["act"] = R.total_added / R.groupby("repo").total_added.transform("mean").replace(0, np.nan)
act = R.set_index(["repo", "vi"]).act.fillna(1.0)
cum = {}
for repo, g in R.sort_values("vi").groupby("repo"):
    cum[repo] = np.concatenate([[0.0], np.cumsum(g.act.values)])           # cum[repo][v] = activity of release pairs 0..v-1
T["intro"] = T.vi - T.age
T["A_exp"] = [cum[r][v] - cum[r][max(i, 0)] for r, v, i in zip(T.repo, T.vi, T.intro)]
T["A_prev"] = [act.get((r, v - 1), np.nan) for r, v in zip(T.repo, T.vi)]
P0 = T.ev.mean()
T["persist"] = T.past_il / (T.age + 1)
T["shrunk"] = (T.past_n + 2) / (T.age + 2 / P0)
H0 = P0                                          # mean events per exposed release at activity 1
T["clock"] = (T.past_n + 2) / (T.A_exp + 2 / H0)
g = T.groupby(["repo", "key"])
T["last_vi"] = T.vi.where(T.ev == 1)
T["last_vi"] = g.last_vi.transform(lambda s: s.shift(1).ffill())
T["gap"] = (T.vi - T.last_vi).fillna(99)
T["recency"] = np.where(T.gap < 99, 0.5 ** (T.gap - 1), 0.0)
fp = T.groupby(["repo", "file", "vi"]).agg(f_ev=("ev", "sum")).reset_index()
fp["vi"] += 1
T = T.merge(fp.rename(columns={"f_ev": "file_prev"}), on=["repo", "file", "vi"], how="left").fillna({"file_prev": 0})
own = T[["repo", "key", "vi", "ev"]].copy(); own["vi"] += 1
T = T.merge(own.rename(columns={"ev": "own_prev"}), on=["repo", "key", "vi"], how="left").fillna({"own_prev": 0})
T["neighbours"] = T.file_prev - T.own_prev
T["A_prev"] = T.A_prev.fillna(1.0)
FE = ["persist", "shrunk", "clock", "recency", "neighbours", "A_prev", "age", "past_n", "nloc0", "ccn0", "principal_pm"]
# learned model: 5-fold by project
T["learned"] = np.nan
for tr, te in GroupKFold(5).split(T, groups=T.repo):
    clf = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0).fit(T.iloc[tr][FE], T.iloc[tr].ev)
    T.loc[T.index[te], "learned"] = clf.predict_proba(T.iloc[te][FE])[:, 1]
SC = {"persistence": "persist", "shrunk rate": "shrunk", "clock-normalised rate": "clock", "recency": "recency", "neighbours": "neighbours", "learned (GB)": "learned", "oracle (latent rate)": "latent"}
KS = [0.1, 0.2, 0.3]
rows = []
for (repo, vi), gg in T.groupby(["repo", "vi"]):
    if len(gg) < 6 or gg.y.sum() <= 0:
        continue
    y = gg.y.values
    rng = np.random.default_rng(0)
    for name, col in SC.items():
        s = gg[col].values + 1e-9 * gg.nloc0.values              # size breaks ties, same for every score
        caps = [np.mean([capture(s, y, k, np.random.default_rng(t)) for t in range(4)]) for k in KS]
        rows.append(dict(repo=repo, vi=vi, regime=gg.regime.iloc[0], tier=gg.tier.iloc[0], score=name, **{f"cap{int(k*100)}": c for k, c in zip(KS, caps)}))
    caps = [np.mean([capture(np.random.default_rng(t).random(len(y)), y, k, np.random.default_rng(t + 9)) for t in range(4)]) for k in KS]
    rows.append(dict(repo=repo, vi=vi, regime=gg.regime.iloc[0], tier=gg.tier.iloc[0], score="random", **{f"cap{int(k*100)}": c for k, c in zip(KS, caps)}))
G = pd.DataFrame(rows)
G.to_csv("../results/s2_ranking_per_group.csv", index=False)
out = []
P = lambda s="": (out.append(s), print(s))
order = list(SC) + ["random"]
for reg in ["ALL", "baseline", "sticky", "ar_clock", "decay", "contagion"]:
    gr = G if reg == "ALL" else G[G.regime == reg]
    pv = gr.pivot_table(index=["repo", "vi"], columns="score", values="cap20")
    P(f"\n### {reg}: {len(pv)} groups, capture in the top 20 % (difference to persistence, points, 95 % bootstrap interval)")
    for s in order:
        if s not in pv:
            continue
        d = (pv[s] - pv["persistence"]).values * 100
        lo, hi = boot_ci(d)
        P(f"  {s:24s} {pv[s].mean()*100:5.1f}   {d.mean():+5.1f} ({lo:+.1f}, {hi:+.1f})")
open("../results/s2_ranking.txt", "w").write("\n".join(out))
T.to_csv("../results/s2_rows_with_scores.csv", index=False)
