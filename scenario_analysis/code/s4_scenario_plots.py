"""Per-repository view of three chosen scenarios: two that repeat and one that is noise. -> ../figures/s4_*.png, ../results/s4_numbers.json
Each dot is one repository (rate ratio of the scenario group against the rest of the repository at the same size); 1 = no effect."""
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import s1_scenarios as S

FIG = os.path.join(S.HERE, "..", "figures"); RES = S.OUT
INK, GREY, ACC = "#111111", "#8a8a8a", "#1f5fa8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 220, "savefig.transparent": True})
T, R = S.build(S.REAL, "real"); SY, _ = S.build(S.SYN, "syn")
py = set(T[T.lang == "python"].repo); cc = set(T[T.lang == "c"].repo); sy = set(SY.repo)
F = S.load(S.REAL, "funcs"); F["event"] = (F.changed > 0).astype(int); F["debt"] = (F.long0 + F.cx0 + F.par_smell0) > 0
F["size_bin"] = pd.cut(F.nloc0, [0, 5, 10, 20, 30, 40, 60, 80, 120, 200, 1e9], labels=False)
FS = S.load(S.SYN, "funcs"); FS["event"] = (FS.changed > 0).astype(int); FS["debt"] = (FS.long0 + FS.cx0 + FS.par_smell0) > 0
FS["size_bin"] = pd.cut(FS.nloc0, [0, 5, 10, 20, 30, 40, 60, 80, 120, 200, 1e9], labels=False)
cm = lambda d: d.n_commits > d.groupby("repo").n_commits.transform("median")
SC = {"size": ("large function (top third of its repository)", T, SY, lambda d: d.rel_size > .67, ["vi"], "repeats"),
      "release": ("release with many commits", T, SY, cm, ["repo"], "repeats"),
      "avoid": ("debt function edited more than a clean one", F, FS, lambda d: d.debt, ["size_bin"], "noise")}
nums = {}
for key, (title, D, DS, fn, strata, kind) in SC.items():
    res = S.rr_group(D, fn(D), strata); sres = S.pooled(S.rr_group(DS, fn(DS), strata), sy)
    pts = [(r, o / e, r in py) for r, (o, e, n) in res.items() if e >= 3 and n >= 30]
    pts.sort(key=lambda t: t[1])
    rr = np.array([p[1] for p in pts]); isp = np.array([p[2] for p in pts])
    pl, pc = S.pooled(res, py), S.pooled(res, cc)
    nums[key] = dict(title=title, kind=kind, repos=len(pts), above1=int((rr > 1).sum()), python=pl, c=pc, synthetic=sres, python_repos=int(isp.sum()), c_repos=int((~isp).sum()))
    fig, ax = plt.subplots(figsize=(5.2, 3.7))
    y = np.arange(len(pts))
    ax.scatter(rr[isp], y[isp], color=GREY, s=34, marker="o", label="Python repositories"); ax.scatter(rr[~isp], y[~isp], color=ACC, s=34, marker="s", label="C/C++ repositories")
    ax.axvline(1, color=INK, ls="--", lw=1); ax.set_xscale("log"); ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    lo, hi = max(rr.min() / 1.3, 1e-2), rr.max() * 1.3; lo, hi = min(lo, 0.5), max(hi, 2)
    ax.set_xlim(lo, hi); ticks = [t for t in (0.1, 0.25, 0.5, 1, 2, 4, 8, 16) if lo <= t <= hi]; ax.set_xticks(ticks); ax.set_xticklabels([str(t) for t in ticks])
    ax.set_yticks([]); ax.set_ylabel("repositories (sorted)"); ax.set_xlabel("rate ratio (1 = no effect)")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, f"s4_{key}.png")); plt.close(fig)
    print(key, "repos", len(pts), "RR>1 in", int((rr > 1).sum()), "py", None if pl is None else (round(pl["rr"], 2), round(pl["lo"], 2), round(pl["hi"], 2)),
          "c", None if pc is None else (round(pc["rr"], 2), round(pc["lo"], 2), round(pc["hi"], 2)), "syn", None if sres is None else round(sres["rr"], 2))
json.dump(nums, open(os.path.join(RES, "s4_numbers.json"), "w"), indent=1, default=float)
