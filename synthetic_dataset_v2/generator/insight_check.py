"""Do the patterns that were found in the real histories (insights/INSIGHTS.md) show up in the synthetic histories, and where are they absent on purpose?
Measured per regime on the ground-truth transitions (from git), never on the simulator's latent parameters.
usage: python insight_check.py <dataset dir> [out.md]"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

out = sys.argv[1]
man = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(out, "manifests", "*.json"))}
T = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(out, "transitions", "*.csv"))], ignore_index=True)
T["regime"] = T.repo.map(lambda r: man[r]["regime"])
T["tier"] = T.repo.map(lambda r: man[r]["tier"])
T["ev"] = (T.interest_lines > 0).astype(int)
T["y"] = T.pm_interest * 1000
T = T[T.cls != "introduced"].sort_values(["repo", "key", "vi"]).reset_index(drop=True)
R = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(out, "releases", "*.csv"))], ignore_index=True)
R["regime"] = R.repo.map(lambda r: man[r]["regime"])
lines = []
P = lambda s="": (lines.append(s), print(s))


def gini(x):
    x = np.sort(np.asarray(x, float))
    return 1 - 2 * np.sum(np.cumsum(x) - x / 2) / (len(x) * x.sum()) if x.sum() > 0 else float("nan")


def capture(score, y, k, rng):
    n = len(y)
    m = max(1, int(np.ceil(k * n)))
    o = np.lexsort((rng.random(n), -np.asarray(score, float)))
    return y[o[:m]].sum() / y.sum()


P("# Do the real-data patterns appear in the synthetic histories?")
P(f"{len(man)} projects, {T.key.nunique()} instances, {len(T)} instance-releases, {int(T.ev.sum())} interest events ({T.ev.mean():.1%} of instance-releases)\n")
rows = []
for reg, g in list(T.groupby("regime")) + [("ALL", T)]:
    r = {"regime": reg, "projects": g.repo.nunique(), "inst-releases": len(g), "events": int(g.ev.sum()), "event rate": g.ev.mean()}
    inst = g.groupby(["repo", "key"]).y.sum().sort_values(ascending=False)
    r["gini"] = gini(inst.values)
    r["top10% share"] = inst.iloc[: max(1, int(0.1 * len(inst)))].sum() / inst.sum()
    cnt = g.groupby(["repo", "key"]).size()
    d = g.set_index(["repo", "key"]).loc[cnt[cnt >= 5].index].reset_index()
    r["never pay"] = (d.groupby(["repo", "key"]).ev.sum() == 0).mean()
    # memory by lag
    dd = g[["repo", "key", "vi", "ev"]]
    for lag in (1, 3, 5):
        s = dd.copy(); s["vi"] += lag
        m = dd.merge(s.rename(columns={"ev": "prev"}), on=["repo", "key", "vi"])
        r[f"P(ev|ev,lag{lag})"] = m[m.prev == 1].ev.mean() if (m.prev == 1).any() else np.nan
    # hazard by time since the LAST event (decay shows here, not in the lag table)
    gg0 = g.sort_values(["repo", "key", "vi"]).copy()
    gg0["last"] = gg0.vi.where(gg0.ev == 1)
    gg0["last"] = gg0.groupby(["repo", "key"])["last"].transform(lambda x: x.shift(1).ffill())
    gg0["gap"] = gg0.vi - gg0["last"]
    for lo, hi, nm in ((1, 1, "1"), (2, 2, "2"), (3, 4, "3-4"), (5, 99, "5+")):
        q = gg0[(gg0.gap >= lo) & (gg0.gap <= hi)]
        r[f"P(ev | last event {nm} releases ago)"] = q.ev.mean() if len(q) else np.nan
    r["P(ev|none,lag1)"] = None
    s = dd.copy(); s["vi"] += 1
    m = dd.merge(s.rename(columns={"ev": "prev"}), on=["repo", "key", "vi"])
    r["P(ev|none,lag1)"] = m[m.prev == 0].ev.mean()
    # same-file neighbours
    fp = g.groupby(["repo", "file", "vi"]).agg(fi=("interest_lines", "sum"), fn=("key", "size")).reset_index()
    s = fp.copy(); s["vi"] += 1
    own = g[["repo", "key", "vi", "interest_lines"]].copy(); own["vi"] += 1
    m = g[["repo", "file", "key", "vi", "ev"]].merge(s.rename(columns={"fi": "f_prev", "fn": "f_n"}), on=["repo", "file", "vi"], how="inner").merge(own.rename(columns={"interest_lines": "own_prev"}), on=["repo", "key", "vi"], how="left").fillna({"own_prev": 0})
    m["nb"] = m.f_prev - m.own_prev
    sub = m[(m.own_prev == 0) & (m.f_n > 1)]
    a_, b_ = sub[sub.nb > 0].ev.mean(), sub[sub.nb == 0].ev.mean()
    r["neighbour ratio"] = a_ / b_ if b_ else np.nan
    # enrichment
    rr = R[R.regime == reg] if reg != "ALL" else R
    r["enrichment"] = (rr.region_changed.sum() / rr.total_added.sum()) / (rr.region_nloc.sum() / rr.total_nloc.sum())
    r["debt share of code"] = rr.region_nloc.sum() / rr.total_nloc.sum()
    r["debt share of edits"] = rr.region_changed.sum() / rr.total_added.sum()
    # ceiling: persistence vs oracle long-run rate at top 20 %
    g = g.copy()
    g["persist"] = g.past_il / (g.age + 1)
    tot = g.groupby(["repo", "key"]).y.transform("sum"); n = g.groupby(["repo", "key"]).y.transform("size")
    g["oracle_rate"] = (tot - g.y) / (n - 1).clip(lower=1)
    caps = {"persistence": [], "oracle long-run": [], "random": []}
    rng = np.random.default_rng(0)
    for (repo, vi), gg in g.groupby(["repo", "vi"]):
        if len(gg) < 8 or gg.y.sum() <= 0:
            continue
        y = gg.y.values
        caps["persistence"].append(capture(gg.persist.values, y, 0.2, rng))
        caps["oracle long-run"].append(capture(gg.oracle_rate.values, y, 0.2, rng))
        caps["random"].append(capture(rng.random(len(y)), y, 0.2, rng))
    r["groups"] = len(caps["persistence"])
    for k, v in caps.items():
        r["cap20 " + k] = np.mean(v) if v else np.nan
    # release clock autocorrelation and ICC
    rel = g.groupby(["repo", "vi"]).agg(rate=("ev", "mean"), tot=("y", "sum")).reset_index()
    rel["lag"] = rel.groupby("repo").rate.shift(1)
    rr2 = rel.dropna().copy()
    for c in ("rate", "lag"):
        rr2[c] = rr2[c] - rr2.groupby("repo")["rate"].transform("mean") if c == "rate" else rr2[c] - rr2.groupby("repo")["lag"].transform("mean")
    r["clock autocorr"] = np.corrcoef(rr2.rate, rr2.lag)[0, 1]
    def icc(D, by):
        gb = D.groupby(by)["ev"]
        nn, mm = gb.size(), gb.mean()
        N, k, gm = len(D), len(nn), D.ev.mean()
        msb = (nn * (mm - gm) ** 2).sum() / (k - 1)
        msw = ((D.ev - gb.transform("mean")) ** 2).sum() / (N - k)
        n0 = (N - (nn ** 2).sum() / N) / (k - 1)
        return (msb - msw) / (msb + (n0 - 1) * msw)
    ra = R[R.regime == reg] if reg != "ALL" else R
    ac = []
    for rp_, gg in ra.groupby("repo"):
        v = np.log(gg.sort_values("vi").activity.values)
        if len(v) > 3 and v.std() > 0:
            ac.append(np.corrcoef(v[:-1], v[1:])[0, 1])
    r["activity autocorr (generator clock)"] = np.nanmean(ac)
    rr3 = g.groupby(["repo", "vi"]).y.sum().reset_index()
    r["top20% releases share of interest"] = np.mean([np.sort(x.y.values)[::-1][: max(1, len(x) // 5)].sum() / x.y.sum() for _, x in rr3.groupby("repo") if x.y.sum() > 0 and len(x) >= 5])
    r["ICC instance"] = icc(d, ["repo", "key"]) if len(d) else np.nan
    r["ICC release"] = icc(g, ["repo", "vi"])
    rows.append(r)
S = pd.DataFrame(rows).set_index("regime")
pd.set_option("display.width", 250)
show = S.T
P(show.round(3).to_string())
P()
P("Reading guide (real data of the 9 projects: event rate 7.8 %, Gini 0.83, never-pay 46 %, P(ev|ev) 0.2-0.25 at every lag against 0.07, neighbour ratio 1.1,")
P("enrichment 0.39, persistence 39 % = oracle long-run 38 % at the top 20 %, clock autocorrelation -0.01, ICC release 0.28 against instance 0.13).")
open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(out, "insight_check.md"), "w").write("\n".join(lines))
S.to_csv(os.path.join(out, "insight_check.csv"))
