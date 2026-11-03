"""Dataset-creation diagrams, drawn with matplotlib (default colours; boxes slightly uneven on purpose).
 01_dataset_creation/real_dataset_creation.png, synthetic_dataset_creation.png, interest_calculation.png, history_as_time_series.png, code_to_image_examples.png"""
import json, os, random
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
random.seed(5)
plt.rcParams.update({"font.size": 7.5, "savefig.dpi": 220})
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(os.path.dirname(__file__), "01_dataset_creation")
GREY, ORANGE, GREEN, BLUE = "#d6d6d6", "C1", "#d8efd8", "#dbe7f5"
j = lambda m=0.03: random.uniform(-m, m)

def box(ax, cx, cy, w, h, title, body="", fc=GREY, tfs=8, bfs=6.8):
    cx, cy = cx + j(), cy + j()
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle="square,pad=0", fc=fc, ec="#555", lw=0.8))
    ax.text(cx, cy + h / 2 - 0.12, title, ha="center", va="top", fontsize=tfs, fontweight="bold")
    if body:
        ax.text(cx, cy - 0.06, body, ha="center", va="center", fontsize=bfs, linespacing=1.3)
    return cx, cy

def arrow(ax, a, b, w1, w2):
    ax.add_patch(FancyArrowPatch((a[0] + w1 / 2, a[1] + j(0.02)), (b[0] - w2 / 2, b[1] + j(0.02)), arrowstyle="-|>", mutation_scale=7, lw=0.8, color="#555"))

def flow(name, title, steps, notes, figsize=(11.5, 4.3)):
    n = len(steps); fig = plt.figure(figsize=figsize); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, n * 1.45 + 0.3); ax.set_ylim(0, 4.3); ax.axis("off")
    ax.text(0.15, 4.12, title, fontsize=10, fontweight="bold", va="top")
    pts = []
    for i, (t, b, fc) in enumerate(steps):
        yy = 2.55 + (0.35 if i % 2 else -0.05) + j(0.04)
        pts.append(box(ax, 0.9 + i * 1.45, yy, 1.28, 2.0, t, b, fc))
    for a, b in zip(pts[:-1], pts[1:]):
        arrow(ax, a, b, 1.28, 1.28)
    for i, t in enumerate(notes):
        ax.text(0.9 + i * 1.45 + j(0.03), 0.62, t, ha="center", va="center", fontsize=6.4, style="italic", color="#444", linespacing=1.3)
    fig.savefig(os.path.join(OUT, name), facecolor="white"); plt.close(fig)

flow("real_dataset_creation.png", "Real dataset: how the 61 clean / debt pairs were made",
     [("1 Projects", "10 open-source\nprojects with tests\n4 Python\n6 C / C++", GREY),
      ("2 Inject debt", "one small change per\npair, 5 types:\n45 scripted\n15 SmellBench-style\n+ 1 natural (libpng)", GREY),
      ("3 Keep working", "the debt copy must\npass the project's\nown tests", GREY),
      ("4 Metric audit", "keep a pair only if a\nmetric of its own\ntype moved\n102 -> 52", ORANGE),
      ("5 Add pairs", "+ 9 pairs from\nC-Thread-Pool and\nlibyaml\n= 61", GREY),
      ("6 Bugs", "3 mutations per pair,\nthe same patch on\nboth copies\n183 bugs", GREY),
      ("7 Fix-time label", "time model: factor\nper debt type\n(3.4 ... 1.05)\ntime_diff_min", GREY),
      ("8 Features", "133 per project\nstructure 46\ncode 50, debt 37\ndelta = debt - clean", GREEN)],
     ["whole projects, not\nsnippets", "known type, place\nand a clean twin", "real debt does not\nbreak behaviour", "50 of 102 dropped:\n'not visible to\nthese metrics'", "more concurrency\nand security in C", "same bugs, so the\nonly difference is\nthe debt", "a model, not a\nmeasurement", "the model sees the\ndifference of the\ntwo vectors"], (12.6, 4.3))

flow("synthetic_dataset_creation.png", "Synthetic benchmark: how the 150 projects with histories were generated",
     [("1 Domain", "150 domains\n88 public app-ideas\n62 classic tasks\nentities and fields", GREY),
      ("2 Tier", "small  5 files, 5-6 rel.\nmedium 8 files, 10-15\nlarge 15 files, 20-30\nxlarge ~31 files, 25-30", GREY),
      ("3 Clean code", "layered package\n11 function archetypes\nper entity + workflows\nstyle per project", GREY),
      ("4 Debt plan", "major type: 5-10\ninstances; two other\ntypes: 1 each\n23 templates", ORANGE),
      ("5 Simulate", "release clock\nlatent rate per instance\nedits: modify (interest)\nor grow (principal)\n5 regimes", ORANGE),
      ("6 Git", "real commits, dates,\n4 authors, tag per\nrelease\nbare repositories", GREY),
      ("7 Ground truth", "interest per instance\nand release from\ngit diff + COCOMO II\n1,321 commit pairs", GREEN),
      ("8 Validate", "specification: 0 violations\n2,038 releases compile\nand run; rebuild gives\nthe same hash", GREEN)],
     ["different names and\nentities, same\nalgorithms", "tiers of the public\nlist map to sizes", "valid, runs (smoke\ntest)", "balanced: 30 projects\nper major type", "baseline 90 projects;\nsticky, ar_clock,\ndecay, contagion 15 each", "same format as the\nreal histories", "same columns as\ninterest_exp", "PASS"], (12.6, 4.3))

# ---- interest calculation
fig = plt.figure(figsize=(11, 4.1)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 11); ax.set_ylim(0, 4.1); ax.axis("off")
ax.text(0.15, 4.0, "Interest of one debt instance between two releases (method of Wiriyakul and Senivongse, COCOMO II)", fontsize=10, fontweight="bold", va="top")
a = box(ax, 1.3, 2.4, 2.0, 2.0, "Release V0", "instance = a smell in\nfunction f\nregion = f, 56 lines", GREY)
b = box(ax, 3.9, 2.4, 2.0, 2.0, "Release V1", "same instance found\n(issue key, or rule +\nfile + function)\nregion = 60 lines", GREY)
arrow(ax, a, b, 2.0, 2.0)
c = box(ax, 6.8, 3.1, 2.9, 1.0, "git diff -U0 V0 V1", "added or modified lines of V1\ninside the region: 12", BLUE)
d = box(ax, 6.8, 1.6, 2.9, 2.0, "Classify", "gone -> repayment of principal\nnew -> principal increase\nstill there:\n  growth = 60 - 56 = 4 (principal)\n  interest lines = 12 - 4 = 8", ORANGE)
e = box(ax, 9.9, 2.4, 1.9, 2.0, "COCOMO II", "PM = 2.94 x (8/1000)^1.0997\n= 0.0145 person-months\n(14.5 milli-PM)\nprincipal of f:\n0.1235 PM", GREEN)
arrow(ax, b, c, 2.0, 2.9); ax.add_patch(FancyArrowPatch((8.25, 3.1), (9.0, 2.7), arrowstyle="-|>", mutation_scale=7, lw=0.8, color="#555")); ax.add_patch(FancyArrowPatch((8.25, 1.6), (9.0, 2.1), arrowstyle="-|>", mutation_scale=7, lw=0.8, color="#555"))
ax.text(0.15, 0.75, "worked example: click 8.1.3 -> 8.1.4, __init__ in src/click/_termui_impl.py (rule python:S107, too many parameters)\nSeveral instances in one function share the changed lines equally. Effort is computed per event, because the formula is not linear.\nPython: SonarQube issues; C/C++: structural smells (function > 50 lines, complexity > 10, > 5 parameters, found with lizard).", fontsize=7, va="top", style="italic", color="#444")
fig.savefig(os.path.join(OUT, "interest_calculation.png"), facecolor="white"); plt.close(fig)
print("flows ok")
