"""Loaders for the synthetic dataset (final_folder/synthetic_dataset) and shared evaluation helpers."""
import glob
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SD = os.path.join(ROOT, "synthetic_dataset")


def manifests():
    return {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(SD, "manifests", "*.json"))}


def transitions():
    T = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(SD, "transitions", "*.csv")))], ignore_index=True)
    M = manifests()
    T["regime"] = T.repo.map(lambda r: M[r]["regime"])
    T["tier"] = T.repo.map(lambda r: M[r]["tier"])
    T["ev"] = (T.interest_lines > 0).astype(int)
    T["y"] = T.pm_interest * 1000.0
    return T.sort_values(["repo", "key", "vi"]).reset_index(drop=True)


def releases():
    R = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(SD, "releases", "*.csv")))], ignore_index=True)
    return R


def latent():
    I = pd.read_csv(os.path.join(SD, "instances.csv"))
    return I.set_index("instance")


def capture(score, y, k, rng):
    n = len(y)
    m = max(1, int(np.ceil(k * n)))
    o = np.lexsort((rng.random(n), -np.asarray(score, float)))
    return y[o[:m]].sum() / y.sum()


def boot_ci(x, B=3000, seed=0):
    x = np.asarray(x, float)
    r = np.random.default_rng(seed)
    return np.percentile(x[r.integers(0, len(x), (B, len(x)))].mean(1), [2.5, 97.5])
