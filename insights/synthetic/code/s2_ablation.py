"""S2b: where does the gain of the shrunk rate come from, and does normalising by release activity help?  (baseline regime and all regimes)
variants: lines / (age+1)  |  events / (age+1)  |  shrunk events  |  shrunk lines  |  events normalised by the TRUE release activity (oracle clock)  |  by commits per release (observable)"""
import warnings
import numpy as np
import pandas as pd
from sload import boot_ci, capture, manifests, releases, transitions
warnings.filterwarnings("ignore")
T = pd.read_csv("../results/s2_rows_with_scores.csv")
R = releases(); M = manifests()
rows = []
for pid, m in M.items():
    cnt = pd.Series([c["release"] for c in m["commits"]]).value_counts()
    for i, r in enumerate(m["release_table"][:-1]):
        rows.append(dict(repo=pid, vi=i, true_act=m["activity"][i + 1], commits=cnt.get(i + 2, 0)))     # activity / commits of the release pair vi -> vi+1 (release number vi+2)
C = pd.DataFrame(rows)
C["commits_n"] = C.commits / C.groupby("repo").commits.transform("mean").replace(0, np.nan)
for c in ("true_act", "commits_n"):
    C[c] = C[c].fillna(1.0)
cum = {}
for repo, g in C.sort_values("vi").groupby("repo"):
    cum[repo] = {c: np.concatenate([[0.0], np.cumsum(g[c].values)]) for c in ("true_act", "commits_n")}
for c in ("true_act", "commits_n"):
    T["A_" + c] = [cum[r][c][v] - cum[r][c][max(i, 0)] for r, v, i in zip(T.repo, T.vi, T.vi - T.age)]
P0 = T.ev.mean()
T["v_lines"] = T.past_il / (T.age + 1)
T["v_count"] = T.past_n / (T.age + 1)
T["v_shr_count"] = (T.past_n + 2) / (T.age + 2 / P0)
T["v_shr_lines"] = (T.past_il + 2) / (T.age + 2 / P0)
T["v_oracle_clock"] = (T.past_n + 2) / (T.A_true_act + 2 / P0)
T["v_commits_clock"] = (T.past_n + 2) / (T.A_commits_n + 2 / P0)
V = {"lines/(age+1)  [persistence]": "v_lines", "events/(age+1)": "v_count", "shrunk events": "v_shr_count", "shrunk lines": "v_shr_lines",
     "events / TRUE release activity (oracle clock)": "v_oracle_clock", "events / commits per release (observable)": "v_commits_clock", "oracle (latent rate)": "latent"}
out = []
P = lambda s="": (out.append(s), print(s))
for reg in ("baseline", "ALL"):
    D = T if reg == "ALL" else T[T.regime == reg]
    res = {n: [] for n in V}
    for (repo, vi), gg in D.groupby(["repo", "vi"]):
        if len(gg) < 6 or gg.y.sum() <= 0:
            continue
        y = gg.y.values
        for n, c in V.items():
            s = gg[c].values + 1e-9 * gg.nloc0.values
            res[n].append(np.mean([capture(s, y, 0.2, np.random.default_rng(t)) for t in range(4)]))
    base = np.array(res["lines/(age+1)  [persistence]"])
    P(f"\n### {reg}: {len(base)} groups, capture in the top 20 %")
    for n in V:
        a = np.array(res[n]); d = (a - base) * 100; lo, hi = boot_ci(d)
        P(f"  {n:48s} {a.mean()*100:5.1f}   {d.mean():+5.1f} ({lo:+.1f}, {hi:+.1f})")
open("../results/s2_ablation.txt", "w").write("\n".join(out))
