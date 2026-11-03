"""Validate a built dataset against the specification.   python validate.py <dataset dir> [--full] [--workers 4]
 1  structure: 150 projects, tiers, file counts, history length, instance counts (major 5-10, two minor types with one each)
 2  every release of every project compiles; the smoke script (calls every function) runs without failures at the last release (all releases with --full)
 3  determinism: one project is rebuilt from its seed and must have the same HEAD hash
 4  git against the simulator: the interest events measured from git agree with the events the simulator made
 5  balance: major type, regime, domain source, tier"""
import csv
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_project import export  # noqa: E402

SPEC = {"S": dict(rel=(5, 6), files=(4, 6), major=(5, 6)), "M": dict(rel=(10, 15), files=(7, 9), major=(5, 8)), "L": dict(rel=(20, 30), files=(14, 18), major=(7, 10)), "X": dict(rel=(25, 30), files=(25, 40), major=(8, 10))}


def one(a):
    out, pid, full = a
    repo = os.path.join(out, "repos", pid + ".git")
    man = json.load(open(os.path.join(out, "manifests", pid + ".json")))
    tags = [r["tag"] for r in man["release_table"]]
    problems = []
    n_files = None
    for tg in (tags if full else [tags[0], tags[len(tags) // 2], tags[-1]]):
        d = tempfile.mkdtemp()
        try:
            export(repo, tg, d)
            r = subprocess.run([sys.executable, "-m", "compileall", "-q", d], capture_output=True, text=True)
            if r.returncode:
                problems.append("compile " + tg)
            if tg == tags[-1]:
                n_files = sum(1 for _ in glob.glob(os.path.join(d, "**", "*.py"), recursive=True))
            if tg == tags[-1] or full:
                open(os.path.join(d, "smoke_run.py"), "w").write(man["smoke"])
                s = subprocess.run([sys.executable, "smoke_run.py"], cwd=d, capture_output=True, text=True, timeout=180)
                last = [l for l in s.stdout.splitlines() if l.startswith("SMOKE")]
                if not last or not last[0].startswith("SMOKE 0 "):
                    problems.append("smoke %s: %s" % (tg, (last or [s.stderr[-120:]])[0]))
        finally:
            shutil.rmtree(d)
    tags_git = subprocess.run(["git", "-C", repo, "tag"], capture_output=True, text=True).stdout.split()
    if len(tags_git) != man["releases"]:
        problems.append("tag count")
    return pid, problems, n_files


def main():
    out = sys.argv[1]
    full = "--full" in sys.argv
    mans = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(out, "manifests", "*.json"))}
    rep = []
    P = lambda s="": (rep.append(s), print(s))
    P("# Validation of the synthetic dataset\n")
    ok = True
    P("## 1. Structure against the specification")
    bad = []
    by = defaultdict(list)
    for pid, m in mans.items():
        s = SPEC[m["tier"]]
        types = Counter(i["ptype"] for i in m["instances"])
        minors = [t for t in types if t != m["major_type"]]
        if not (s["rel"][0] <= m["releases"] <= s["rel"][1]):
            bad.append((pid, "releases", m["releases"]))
        if types[m["major_type"]] != m["n_major"] or not (s["major"][0] <= m["n_major"] <= s["major"][1]):
            bad.append((pid, "major count", dict(types)))
        if len(minors) != 2 or any(types[t] != 1 for t in minors):
            bad.append((pid, "minor types", dict(types)))
        by[m["tier"]].append(m)
    P("projects: %d (domains %d unique)" % (len(mans), len({m["domain"] for m in mans.values()})))
    for t in "SMLX":
        g = by[t]
        P("  %s: %d projects, releases %d-%d, commits %d-%d (median %d), LOC %d-%d (median %d), instances %d-%d" % (
            t, len(g), min(m["releases"] for m in g), max(m["releases"] for m in g), min(len(m["commits"]) for m in g), max(len(m["commits"]) for m in g),
            int(np.median([len(m["commits"]) for m in g])), min(m["loc"] for m in g), max(m["loc"] for m in g), int(np.median([m["loc"] for m in g])),
            min(len(m["instances"]) for m in g), max(len(m["instances"]) for m in g)))
    P("specification violations: %d %s" % (len(bad), bad[:5]))
    ok &= not bad
    P("\n## 2. Every release compiles; smoke test (calls every function) at %s" % ("every release" if full else "the first, middle and last release"))
    with Pool(int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4) as pool:
        res = pool.map(one, [(out, pid, full) for pid in sorted(mans)])
    fails = [(p, pr) for p, pr, _ in res if pr]
    nfiles = defaultdict(list)
    for pid, _, nf in res:
        nfiles[mans[pid]["tier"]].append(nf)
    P("projects with problems: %d %s" % (len(fails), fails[:5]))
    for t in "SMLX":
        v = nfiles[t]
        P("  python files at the last release, tier %s: %d-%d (median %d)" % (t, min(v), max(v), int(np.median(v))))
    ok &= not fails
    P("\n## 3. Determinism (rebuild of one project from its seed)")
    sys.path.insert(0, HERE)
    import domains
    import simulate
    pid = sorted(mans)[7]
    m = mans[pid]
    dom = [d for d in domains.load() if d["slug"].replace("-", "_") == pid][0]
    tmp = tempfile.mkdtemp()
    m2 = simulate.simulate(dom, m["seed"], m["regime"], os.path.join(tmp, "x.git"), m["major_type"])
    same = m2["commits"][-1]["hash"] == m["commits"][-1]["hash"]
    shutil.rmtree(tmp)
    P("project %s: HEAD %s -> %s" % (pid, m["commits"][-1]["hash"][:10], "identical after rebuild" if same else "DIFFERENT"))
    ok &= same
    P("\n## 4. Interest from git against the simulator's own edit log")
    tot = agree = 0
    for pid, m in mans.items():
        p = os.path.join(out, "transitions", pid + ".csv")
        if not os.path.exists(p):
            continue
        gt = defaultdict(float)
        for r in csv.DictReader(open(p)):
            gt[(r["key"], int(r["vi"]) + 2)] += float(r["interest_lines"])
        for inst in m["instances"]:
            sim = defaultdict(int)
            for rel, kind, n in inst["sim_edits"]:
                if kind == "modify":
                    sim[rel] += n
            for r in set(sim) | {r for (k, r) in gt if k == inst["id"]}:
                alive = inst["intro_release"] < r and (inst["repaid_release"] is None or inst["repaid_release"] >= r)
                if alive:
                    tot += 1
                    agree += (sim.get(r, 0) > 0) == (gt.get((inst["id"], r), 0) > 0)
    P("instance-releases compared: %d, event / no event agreement: %.2f %%" % (tot, 100 * agree / max(tot, 1)))
    ok &= agree / max(tot, 1) > 0.99
    P("\n## 5. Balance")
    P("major type: %s" % dict(Counter(m["major_type"] for m in mans.values())))
    P("regime: %s" % dict(Counter(m["regime"] for m in mans.values())))
    P("source of the domain (A = public app-ideas list, C = classic task): %s" % dict(Counter(m["source"] for m in mans.values())))
    P("major type by tier:")
    for t in "SMLX":
        P("  %s: %s" % (t, dict(Counter(m["major_type"] for m in mans.values() if m["tier"] == t))))
    P("major type by regime:")
    for r in ("baseline", "sticky", "ar_clock", "decay", "contagion"):
        P("  %s: %s" % (r, dict(Counter(m["major_type"] for m in mans.values() if m["regime"] == r))))
    P("templates (all instances): %s" % dict(Counter(i["template"] for m in mans.values() for i in m["instances"]).most_common()))
    P("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
    open(os.path.join(out, "VALIDATION.md"), "w").write("\n".join(rep))


if __name__ == "__main__":
    main()
