"""Build the synthetic projects.   python build.py --n 8 --out ../ [--only slug,slug] [--workers 4]
Writes  <out>/repos/<id>.git (bare, tagged history)  and  <out>/manifests/<id>.json  (ground truth of the generator)."""
import argparse
import json
import os
import random
import sys
import traceback
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import domains
import simulate

# regime of each project: 60 % baseline, 10 % each for the four counter-regimes (assigned by a fixed shuffle of the domain list)
REG = ["baseline"] * 6 + ["sticky", "ar_clock", "decay", "contagion"] * 1


def plan(seed=2026):
    doms = domains.load()
    rng = random.Random(seed)
    order = list(range(len(doms)))
    rng.shuffle(order)
    types = ["complexity", "concurrency", "coupling_cohesion", "dependency_structure", "security"]
    count = {t: 0 for t in types}
    out = []
    for k, i in enumerate(order):
        d = doms[i]
        low = min(count.values())
        pick = rng.choice([t for t in types if count[t] == low])    # the type that has been the major type the fewest times so far: balanced over the 150
        count[pick] += 1
        out.append((d, REG[k % len(REG)], 1000 + i * 7 + seed % 13, pick))
    return sorted(out, key=lambda x: x[0]["slug"])


def job(a):
    dom, regime, seed, major, out = a
    pid = dom["slug"].replace("-", "_")
    try:
        man = simulate.simulate(dom, seed, regime, os.path.join(out, "repos", pid + ".git"), major)
        with open(os.path.join(out, "manifests", pid + ".json"), "w") as fh:
            json.dump(man, fh)
        return pid, "ok", man["tier"], man["loc"], len(man["commits"]), man["releases"]
    except Exception:
        return pid, "ERROR " + traceback.format_exc()[-800:], None, 0, 0, 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "repos"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "manifests"), exist_ok=True)
    P = plan(a.seed)
    if a.only:
        keep = set(a.only.split(","))
        P = [p for p in P if p[0]["slug"] in keep]
    elif a.n:
        by = {}
        for p in P:                                  # a spread over tiers for a pilot
            by.setdefault(p[0]["tier"], []).append(p)
        P = [p for t in "SMLX" for p in by[t][: max(1, a.n // 4)]]
    jobs = [(d, r, s, m, a.out) for d, r, s, m in P]
    with Pool(a.workers) as pool:
        for res in pool.imap_unordered(job, jobs):
            print(*res, flush=True)
