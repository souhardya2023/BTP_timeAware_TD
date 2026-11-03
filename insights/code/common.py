"""Shared helpers for the insight experiments (Level 2: real git history)."""
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "interest_exp", "code"))
PY = ["click", "jinja", "werkzeug", "boltons"]


def load_transitions():
    """All instance-release rows (Python and C), 'introduced' rows removed as in the main experiment."""
    df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(ROOT, "interest_exp/data/transitions/*.csv")))], ignore_index=True)
    df = df[df.cls != "introduced"].copy()
    df["any"] = (df.interest_lines > 0).astype(int)
    df["y"] = df.pm_interest * 1000.0                 # milli person-months
    return df.sort_values(["repo", "vi"]).reset_index(drop=True)


def groups(df, min_n=10):
    """(repo, release) groups that can be ranked: >= min_n instances and some real interest."""
    out = []
    for (r, vi), g in df.groupby(["repo", "vi"]):
        if len(g) >= min_n and g.y.sum() > 0:
            out.append((r, vi))
    return out


def capture(score, y, k, rng):
    """share of the total y inside the top k fraction of the ranking by score (ties broken at random)."""
    n = len(y)
    m = max(1, int(np.ceil(k * n)))
    o = np.lexsort((rng.random(n), -np.asarray(score, float)))
    return y[o[:m]].sum() / y.sum()


def boot_ci(x, B=3000, seed=0):
    x = np.asarray(x, float)
    r = np.random.default_rng(seed)
    m = x[r.integers(0, len(x), (B, len(x)))].mean(1)
    return np.percentile(m, [2.5, 97.5])
