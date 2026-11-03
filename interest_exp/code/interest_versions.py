#!/usr/bin/env python3
"""Version-wise TD interest, following the 2025 method.

For every pair of consecutive releases (V0 -> V1) of a repo:
  1. TD instances of V0 and of V1 come from a smell detector: SonarQube code smells (Python repos, out/sonar/<repo>/<tag>.json) or
     the structural smell detector of history.py (C repos: Long Method / Complex Method / Many Parameters per function).
  2. An instance of V0 is followed into V1 (same SonarQube issue key, else same rule + file + function).
  3. git diff V0..V1 gives the ADDED + MODIFIED source lines; those inside the instance's region (the function containing the issue) are its changed lines.
  4. classification
       instance disappears                -> principal repayment (changed lines = refactoring size)
       instance appears                   -> principal increase  (changed lines)
       instance stays, region changed     -> region growth (nloc1 - nloc0, capped by changed lines) = principal increase,
                                              the remaining changed lines = INTEREST (work done inside the debt while it remains)
  5. effort = COCOMO II(lines) (cocomo.py); principal of an instance = COCOMO II(region size) = effort to rewrite its region.
Paid interest of an instance = sum over transitions; of a repo = sum over instances.

usage: interest_versions.py REPO.git OUT_CSV [--sonar DIR] [--k 20]
"""
import csv
import functools
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import cocomo
import history as H
from versions import release_versions


@functools.lru_cache(maxsize=4096)
def show(repo, commit, path):
    r = subprocess.run(["git", "-C", repo, "show", f"{commit}:{path}"], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


@functools.lru_cache(maxsize=4096)
def funcs(repo, commit, path):
    code = show(repo, commit, path)
    return H.functions(path, code) if code is not None else {}


def region(repo, commit, path, line):
    """(func_name, start, end, nloc, ccn) of the function containing `line`, else a one-line region."""
    best = None
    for n, f in funcs(repo, commit, path).items():
        if f["s"] <= line <= f["e"] and (best is None or f["e"] - f["s"] < best[2] - best[1]):
            best = (n, f["s"], f["e"], f["nloc"], f["ccn"])
    return best or (f"<module>:{line}", line, line, 1, 1)


def diff_changes(repo, c0, c1):
    d = subprocess.run(["git", "-C", repo, "diff", "-U0", "-M", "--no-color", c0, c1], capture_output=True).stdout.decode("utf-8", "replace")
    return H.changed_ranges(d)


def lizard_issues(repo, commit):
    out = []
    for p in subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only", commit], capture_output=True, text=True).stdout.split("\n"):
        if not p or not H.is_src(p):
            continue
        for fn, f in funcs(repo, commit, p).items():
            for kind, flag in zip(("long_method", "complex_method", "many_params"), H.smell(f)):
                if flag:
                    out.append(dict(key=f"{p}::{fn}::{kind}", rule=kind, severity="MAJOR", file=p, line=f["s"], effort=None))
    return out


def load_issues(repo, versions, sonar_dir):
    res = {}
    for tag, commit, date in versions:
        if sonar_dir:
            fp = os.path.join(sonar_dir, f"{tag}.json")
            if not os.path.exists(fp):
                return None
            res[tag] = [i for i in json.load(open(fp))["issues"] if i.get("line") and H.is_src(i["file"])]
        else:
            res[tag] = lizard_issues(repo, commit)
    return res


def effort_min(e):
    if not e:
        return 0
    m = re.match(r"(?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)min)?", e)
    return int(m.group(1) or 0) * 480 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0) if m else 0


def run(repo, versions, issues):
    rows = []
    name = os.path.basename(repo).replace(".git", "")
    first_seen, past_il, past_n = {}, {}, {}
    for vi in range(len(versions) - 1):
        (t0, c0, d0), (t1, c1, d1) = versions[vi], versions[vi + 1]
        rng, ren = diff_changes(repo, c0, c1)
        new_name = {o: n for n, o in ren.items()}                     # old path -> new path
        code_lines = {}

        def changed_in(path, s, e):
            if path not in code_lines:
                code_lines[path] = H.code_lines(show(repo, c1, path) or "", H.EXT.get(os.path.splitext(path)[1], "py"), rng.get(path, set()))
            return sum(1 for ln in code_lines[path] if s <= ln <= e)

        I0, I1 = issues[t0], issues[t1]
        by_key1 = {i["key"]: i for i in I1}
        by_sig1 = {}
        for i in I1:
            r = region(repo, c1, i["file"], i["line"])
            by_sig1.setdefault((i["rule"], i["file"], r[0]), []).append((i, r))
        matched1 = set()
        for i in I0:
            path0 = i["file"]
            path1 = new_name.get(path0, path0)
            r0 = region(repo, c0, path0, i["line"])
            iid = f"{path0}::{r0[0]}::{i['rule']}"
            first_seen.setdefault(i["key"], vi)
            cand = by_key1.get(i["key"])
            r1 = None
            if cand is not None:
                r1 = region(repo, c1, cand["file"], cand["line"])
                matched1.add(cand["key"])
            else:
                c = [x for x in by_sig1.get((i["rule"], path1, r0[0]), []) if x[0]["key"] not in matched1]
                if len(c) >= 1:
                    cand, r1 = c[0]
                    matched1.add(cand["key"])
            base = dict(repo=name, v0=t0, v1=t1, vi=vi, key=i["key"], file=path0, func=r0[0], rule=i["rule"], severity=i["severity"],
                        sonar_effort_min=effort_min(i.get("effort")), nloc0=r0[3], ccn0=r0[4], age=vi - first_seen[i["key"]],
                        past_il=past_il.get(i["key"], 0), past_n=past_n.get(i["key"], 0),
                        principal_pm=cocomo.pm(r0[3]))
            if cand is None:      # instance gone
                ch = changed_in(path1, r0[1], r0[2]) if show(repo, c1, path1) is not None else 0
                rows.append(dict(base, cls="repayment", persisted=0, nloc1=0, changed=ch, interest_lines=0, pm_interest=0.0))
                continue
            ch = changed_in(cand["file"], r1[1], r1[2])
            growth = max(0, r1[3] - r0[3])
            inc = min(ch, growth)
            il = ch - inc
            cls = "interest" if il > 0 else ("increase" if inc > 0 else "none")
            rows.append(dict(base, cls=cls, persisted=1, nloc1=r1[3], changed=ch, interest_lines=il, pm_interest=cocomo.pm(il)))
            past_il[cand["key"]] = past_il.get(i["key"], 0) + il
            past_n[cand["key"]] = past_n.get(i["key"], 0) + (1 if il > 0 else 0)
            first_seen.setdefault(cand["key"], first_seen[i["key"]])
        for i in I1:           # instances that appear in V1
            if i["key"] in matched1 or any(r["key"] == i["key"] and r["vi"] == vi for r in rows):
                continue
            r1 = region(repo, c1, i["file"], i["line"])
            rows.append(dict(repo=name, v0=t0, v1=t1, vi=vi, key=i["key"], file=i["file"], func=r1[0], rule=i["rule"], severity=i["severity"],
                             sonar_effort_min=effort_min(i.get("effort")), nloc0=0, ccn0=0, age=0, past_il=0, past_n=0, principal_pm=0.0,
                             cls="introduced", persisted=1, nloc1=r1[3], changed=changed_in(i["file"], r1[1], r1[2]), interest_lines=0, pm_interest=0.0))
            first_seen.setdefault(i["key"], vi + 1)
    # a function can carry several issues: its re-worked lines are one piece of work, so share them among its persisting instances
    from collections import Counter
    grp = Counter((r["vi"], r["file"], r["func"]) for r in rows if r["cls"] == "interest")
    for r in rows:
        if r["cls"] == "interest":
            n = grp[(r["vi"], r["file"], r["func"])]
            r["pm_interest"] = cocomo.pm(r["interest_lines"]) / n
            r["interest_lines"] = r["interest_lines"] / n
    return rows


def main():
    repo, out = sys.argv[1], sys.argv[2]
    sonar = sys.argv[sys.argv.index("--sonar") + 1] if "--sonar" in sys.argv else None
    k = int(sys.argv[sys.argv.index("--k") + 1]) if "--k" in sys.argv else 20
    vers = release_versions(repo, k)
    iss = load_issues(repo, vers, sonar)
    if iss is None:
        sys.exit("missing Sonar results for some version")
    rows = run(repo, vers, iss)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    pm = sum(r["pm_interest"] for r in rows)
    print(f"{os.path.basename(repo)}: {len(vers)} versions, {len(rows)} instance-transitions {dict(Counter(r['cls'] for r in rows))}, paid interest {pm:.3f} PM")


if __name__ == "__main__":
    main()
