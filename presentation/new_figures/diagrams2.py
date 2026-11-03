"""01_dataset_creation/history_as_time_series.png and code_to_image_examples.png"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 7.5, "savefig.dpi": 220})
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(os.path.dirname(__file__), "01_dataset_creation")
R = pd.read_csv(os.path.join(ROOT, "insights", "new", "results", "n4_rows_real.csv"))
# one real instance with several events, in a repository with enough releases
cand = R.groupby(["repo", "key"]).agg(n=("ev", "size"), k=("ev", "sum")).query("n >= 16 and k >= 5 and k <= 8").sort_values("k", ascending=False)
repo, key = cand.index[1]
g = R[(R.repo == repo) & (R.key == key)].sort_values("vi")
proj = R[R.repo == repo].groupby("vi").agg(share=("ev", "mean"), act=("clk_a1", "mean"))
fig, ax = plt.subplots(4, 1, figsize=(10.5, 6.2), sharex=True, gridspec_kw={"height_ratios": [1, 1, 1, 1.6]})
v = g.vi.values
ax[0].bar(v, g.ev.values, color="C1"); ax[0].set_ylabel("interest\nevent"); ax[0].set_yticks([0, 1])
ax[0].set_title("One real debt instance (%s, %s) and its history as a time series; the model sees only the releases to the left of the one it predicts" % (repo, g.file.iloc[0].split("/")[-1]), fontsize=8.5)
ax[1].bar(v, g.interest_lines.values, color="C0"); ax[1].set_ylabel("interest\nlines")
ax[2].bar(proj.index, proj.share.values, color="C7"); ax[2].set_ylabel("share of the\nproject's instances\nwith an event")
for a in ax[:3]:
    a.grid(alpha=0.25)
ax[3].plot(v, g.ts_shr, "o-", label="shrunk event rate"); ax[3].plot(v, g.ts_ew, "s-", label="recency-weighted events"); ax[3].plot(v, g.ts_chg_share, "^-", label="share of releases with a change")
ax[3].step(v, g.ts_run, where="post", label="current run of events"); ax[3].set_ylabel("features built from\nthe past only"); ax[3].legend(fontsize=6.5, ncol=4, loc="upper center"); ax[3].set_xlabel("release pair index (time)"); ax[3].grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "history_as_time_series.png"), facecolor="white"); plt.close(fig)
# code images
Z = np.load(os.path.join(ROOT, "insights", "new", "results", "n1_images.npz")); X = Z["X"]
M = pd.read_csv(os.path.join(ROOT, "insights", "new", "results", "n1_meta.csv"))
import subprocess, sys
sys.path.insert(0, os.path.join(ROOT, "insights", "new", "code"))
from n1_images import parse_diff
SD = os.path.join(ROOT, "synthetic_dataset")
PA = pd.read_csv(os.path.join(SD, "pairs.csv")).set_index("instance")
fig, ax = plt.subplots(2, 5, figsize=(12.5, 5.6), gridspec_kw={"height_ratios": [1.3, 1]})
for j, t in enumerate(sorted(M.ptype.unique())):
    i = M[(M.ptype == t) & (~M.mixed)].index[3]
    rows = int((np.abs(X[i, 1]).sum(1) > 0).sum())
    ax[0, j].imshow(X[i, 0][: max(rows, 8) + 2], cmap="nipy_spectral", aspect="auto", vmin=0, vmax=1)
    ax[0, j].set_title("%s\n(%s)" % (t, M.template[i]), fontsize=8); ax[0, j].set_xlabel("character position")
    r = PA.loc[M.instance[i]]
    txt = subprocess.run(["git", "-C", os.path.join(SD, "repos", r.project + ".git"), "diff", "-U0", r.parent, r.child], capture_output=True, text=True).stdout
    lines = [("+" if s_ > 0 else "-") + l[:44] for s_, l in parse_diff(txt)[:11]]
    ax[1, j].axis("off"); ax[1, j].text(0, 1, "\n".join(lines), family="monospace", fontsize=5.4, va="top")
ax[0, 0].set_ylabel("changed line (row)")
fig.suptitle("Code as an image: the changed lines of a debt introduction (rows = lines, columns = characters)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "code_to_image_examples.png"), facecolor="white"); plt.close(fig)
print("ok", repo, key[:8])
