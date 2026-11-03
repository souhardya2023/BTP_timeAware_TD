"""Architecture figure (whole work at a glance) and the Level 1 pipeline strip, drawn with matplotlib."""
import random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

random.seed(11)
plt.rcParams.update({"font.size": 7.5, "savefig.dpi": 300})
GREY, ORANGE, GREEN = "#cfcfcf", "C1", "#d8efd8"
j = lambda m=0.03: random.uniform(-m, m)


def box(ax, cx, cy, w, h, text, fc=GREY, fs=7, bold=False, ec="#555555", tc="k"):
    cx, cy = cx + j(), cy + j()
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="square,pad=0", fc=fc, ec=ec, lw=0.8))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=tc, linespacing=1.25)
    return cx, cy


def pill(ax, cx, cy, text, w=1.05):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - 0.09), w, 0.18, boxstyle="round,pad=0,rounding_size=0.08", fc="k", ec="k"))
    ax.text(cx, cy, text, color="white", ha="center", va="center", fontsize=6.2, fontweight="bold")


def arrow(ax, x0, y0, x1, y1, ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0 + j(0.02)), (x1, y1 + j(0.02)), arrowstyle="-|>", mutation_scale=7, lw=0.8, color="#555555", linestyle=ls))


# ---------------------------------------------------------------- whole work
fig = plt.figure(figsize=(9.2, 3.75))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 9.2); ax.set_ylim(0, 3.75); ax.axis("off")
X = [0.95, 2.85, 4.75, 6.55, 8.4]
W = 1.7
FS = 6.4
for x, t in zip(X, ["Data creation", "Characteristics", "Prediction", "Output", "Evaluation"]):
    ax.text(x, 3.6, t, ha="center", fontsize=9, fontweight="bold")

c1 = [box(ax, X[0], 3.0, W, 0.6, "10 open-source projects\n4 Python, 6 C/C++", fs=FS),
      box(ax, X[0], 2.0, W, 0.7, "clean copy + copy with one\ninjected debt: 5 types,\n61 pairs, 3 bugs each", fs=FS),
      box(ax, X[0], 1.0, W, 0.6, "git history of 9 projects\nlast 20 releases", fs=FS)]
pill(ax, X[0], 2.62, "test suites"); pill(ax, X[0], 1.58, "injection scripts"); pill(ax, X[0], 0.58, "git tags")

c2 = [box(ax, X[1], 3.0, W, 0.6, "133 features per project\nstructure 46, code 50, debt 37", fs=FS),
      box(ax, X[1], 2.0, W, 0.7, "fix-time label (minutes)\nfrom a time model,\ndebt copy - clean copy", fs=FS),
      box(ax, X[1], 1.0, W, 0.6, "interest per debt instance\nCOCOMO II, person-months", fs=FS)]
pill(ax, X[1], 2.62, "lizard, SonarQube", w=1.25); pill(ax, X[1], 1.58, "3 bugs per pair"); pill(ax, X[1], 0.58, "git diff -U0")

c3 = [box(ax, X[2], 2.45, W, 0.9, "Level 1\n10-best features +\nrandom forest:\ndebt type of a pair", fs=FS),
      box(ax, X[2], 1.15, W, 0.9, "Level 2\nrandom forest, two-part model:\nwill this instance absorb\nrework next release?", fs=FS)]
pill(ax, X[2], 1.88, "scikit-learn"); pill(ax, X[2], 0.58, "hurdle model")

c4 = [box(ax, X[3], 2.45, 1.35, 0.9, "debt type and its\ntime cost:\nrank the types", fc=ORANGE, fs=FS),
      box(ax, X[3], 1.15, 1.35, 0.9, "instances of a release\nranked by predicted\ninterest", fc=ORANGE, fs=FS)]

c5 = [box(ax, X[4], 2.45, 1.5, 0.9, "4 protocols:\nleave-one-project-out,\ntemporal split\naccuracy, F1, McNemar", fc=GREEN, fs=FS),
      box(ax, X[4], 1.15, 1.5, 0.9, "capture@k, lift, NDCG,\nbootstrap CI vs random,\npersistence, oracle", fc=GREEN, fs=FS)]

for a, b in zip(c1, c2):
    arrow(ax, a[0] + W / 2, a[1], b[0] - W / 2, b[1])
arrow(ax, c2[0][0] + W / 2, c2[0][1], c3[0][0] - W / 2, c3[0][1] + 0.15)
arrow(ax, c2[1][0] + W / 2, c2[1][1], c3[0][0] - W / 2, c3[0][1] - 0.2)
arrow(ax, c2[2][0] + W / 2, c2[2][1], c3[1][0] - W / 2, c3[1][1])
arrow(ax, c3[0][0] + W / 2, c3[0][1], c4[0][0] - 0.675, c4[0][1])
arrow(ax, c3[1][0] + W / 2, c3[1][1], c4[1][0] - 0.675, c4[1][1])
arrow(ax, c4[0][0] + 0.675, c4[0][1], c5[0][0] - 0.75, c5[0][1])
arrow(ax, c4[1][0] + 0.675, c4[1][1], c5[1][0] - 0.75, c5[1][1])
arrow(ax, c1[0][0] + 0.2, c1[0][1] - 0.3, c1[1][0] + 0.2, c1[1][1] + 0.35, ls="--")
sig = ["known type, place,\nclean twin", "what the debt changes,\nand what it costs", "what the vector\nsays about the debt", "a ranking a team\ncan act on", "better than chance and\nthan a simple rule?"]
for x, t in zip(X, sig):
    ax.text(x + j(0.02), 0.2, t, ha="center", va="center", fontsize=6.4, style="italic", color="#444444")
fig.savefig("figs/architecture.png", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- Level 1 pipeline
fig = plt.figure(figsize=(9.2, 0.8)); ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 9.2); ax.set_ylim(0, 0.8); ax.axis("off")
xs = [1.1, 3.35, 5.6, 7.9]
labels = ["133 delta features + time\ninput vector of a pair", "SelectKBest, k = 10\nANOVA F, inside each training fold",
          "Random forest\n300 trees, balanced class weights", "Debt type\n5 classes"]
pts = []
for x, t, fc in zip(xs, labels, [GREY, GREY, GREY, ORANGE]):
    pts.append(box(ax, x, 0.4, 1.95 if x < 7 else 1.3, 0.55, t, fc=fc, fs=7))
for a, b, wa, wb in zip(pts[:-1], pts[1:], [1.95, 1.95, 1.95], [1.95, 1.95, 1.3]):
    arrow(ax, a[0] + wa / 2, a[1], b[0] - wb / 2, b[1])
fig.savefig("figs/level1_flow.png", facecolor="white")
plt.close(fig)
