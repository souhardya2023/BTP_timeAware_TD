"""N4a: git history as a time series.  For every instance-release row, features computed ONLY from the releases before it:
 instance signals: events so far, shrunk rate, events in the last 1 / 3 / 5 releases, gap since the last event, mean and regularity (CV) of the gaps, current and longest run of
                   consecutive events, trend (late half minus early half), exponentially weighted events, delay to the first event, lag-1 autocorrelation, share of releases with any change
 project clock:    activity (lines added) of the previous release, mean of the last 3, trend, share of the project's instances active in the previous release and in the last 3
 neighbours:       events of the other instances of the same file in the previous release and in the last 3
 sequence tensor:  the last 12 releases x 7 channels (event, log lines, log changed, activity, project active share, neighbour events, exists) for a CNN.
Output: results/n4_rows_{real,synthetic}.csv, results/n4_seq_{real,synthetic}.npy"""
import os, sys
import numpy as np, pandas as pd
from sload import SD, ROOT, transitions, releases
sys.path.insert(0, os.path.join(ROOT, "insights", "code"))
from common import load_transitions
T_LEN = 12

def build(D, act, name):
    D = D.sort_values(["repo", "key", "vi"]).reset_index(drop=True)
    P0 = D.ev.mean()
    # project level series
    pe = D.groupby(["repo", "vi"]).ev.mean().rename("pshare")
    D = D.merge(pe.reset_index(), on=["repo", "vi"], how="left")
    pser = {r: g.set_index("vi").pshare.to_dict() for r, g in pe.reset_index().groupby("repo")}
    fe = D.groupby(["repo", "file", "vi"]).ev.sum().rename("fev").reset_index()
    fser = {k: g.set_index("vi").fev.to_dict() for k, g in fe.groupby(["repo", "file"])}
    feats, seqs = [], np.zeros((len(D), T_LEN, 7), np.float32)
    row = 0
    for (repo, key), g in D.groupby(["repo", "key"], sort=False):
        ev, il, ch, vi = g.ev.values, g.interest_lines.values, g.changed.values, g.vi.values
        f = g.file.iloc[0]
        a = act.get(repo, {}); ps = pser[repo]; fs = fser[(repo, f)]
        for j in range(len(g)):
            h = ev[:j]; n = len(h)
            last = np.where(h == 1)[0]
            gaps = np.diff(last) if len(last) > 1 else np.array([])
            run = 0
            for e in h[::-1]:
                if e: run += 1
                else: break
            mx = 0; c = 0
            for e in h:
                c = c + 1 if e else 0; mx = max(mx, c)
            half = n // 2
            tr = (h[half:].sum() - h[:half].sum()) / max(n, 1) if n >= 2 else 0.0
            ac = np.corrcoef(h[:-1], h[1:])[0, 1] if n >= 4 and h.std() > 0 else 0.0
            v = vi[j]
            a1 = a.get(v - 1, 1.0); a3 = np.mean([a.get(v - k, 1.0) for k in (1, 2, 3)]); a4 = np.mean([a.get(v - k, 1.0) for k in (2, 3, 4)])
            p1 = ps.get(v - 1, np.nan); p3 = np.nanmean([ps.get(v - k, np.nan) for k in (1, 2, 3)]) if any(v - k in ps for k in (1, 2, 3)) else np.nan
            own1 = ev[j - 1] if j >= 1 else 0
            n1 = fs.get(v - 1, 0) - own1
            n3 = sum(fs.get(v - k, 0) for k in (1, 2, 3)) - h[-3:].sum() if n else 0
            feats.append([n, h.sum(), (h.sum() + 2) / (n + 2 / P0), h[-1:].sum(), h[-3:].sum(), h[-5:].sum(), (n - last[-1]) if len(last) else 99,
                          gaps.mean() if len(gaps) else -1, (gaps.std() / gaps.mean()) if len(gaps) > 1 and gaps.mean() > 0 else -1, run, mx, tr,
                          sum(0.7 ** (n - 1 - s) for s in range(n) if h[s]), last[0] if len(last) else -1, (il[:j][h == 1].mean() if h.sum() else 0.0), ac,
                          (ch[:j] > 0).mean() if n else 0.0, a1, a3, a1 - a4, p1, p3, max(n1, 0), max(n3, 0)])
            for s in range(T_LEN):                      # position j - T_LEN + s
                k = j - T_LEN + s
                if k >= 0:
                    vv = vi[k]
                    seqs[row, s] = [ev[k], np.log1p(il[k]), np.log1p(ch[k]), a.get(vv, 1.0), ps.get(vv, 0.0), max(fs.get(vv, 0) - ev[k], 0), 1.0]
            row += 1
    cols = ["ts_n", "ts_ev", "ts_shr", "ts_l1", "ts_l3", "ts_l5", "ts_gap", "ts_gap_mean", "ts_gap_cv", "ts_run", "ts_maxrun", "ts_trend", "ts_ew", "ts_first", "ts_il_per_ev", "ts_ac1",
            "ts_chg_share", "clk_a1", "clk_a3", "clk_trend", "clk_pshare1", "clk_pshare3", "nbr_1", "nbr_3"]
    F = pd.DataFrame(feats, columns=cols)
    out = pd.concat([D.reset_index(drop=True), F], axis=1)
    out[["clk_pshare1", "clk_pshare3"]] = out[["clk_pshare1", "clk_pshare3"]].fillna(0)
    out.to_csv("../results/n4_rows_%s.csv" % name, index=False); np.save("../results/n4_seq_%s.npy" % name, seqs)
    print(name, out.shape, seqs.shape)

# real
R = load_transitions(); R["ev"] = R["any"]; R["y"] = R.pm_interest * 1000
E = pd.read_csv(os.path.join(ROOT, "insights", "results", "l2_enrichment_by_release.csv"))
E["act"] = E.total_added / E.groupby("repo").total_added.transform("mean").replace(0, np.nan)
actR = {r: g.set_index("vi").act.fillna(1.0).to_dict() for r, g in E.groupby("repo")}
build(R, actR, "real")
# synthetic
S = transitions(); RR = releases(); RR["act"] = RR.total_added / RR.groupby("repo").total_added.transform("mean").replace(0, np.nan)
actS = {r: g.set_index("vi").act.fillna(1.0).to_dict() for r, g in RR.groupby("repo")}
lat = pd.read_csv(os.path.join(SD, "instances.csv")).set_index("instance").latent_rate
S["latent"] = S.key.map(lat)
build(S, actS, "synthetic")
