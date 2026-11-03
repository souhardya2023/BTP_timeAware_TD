#!/usr/bin/env python3
"""Interest from real git history, following the 2025 method at function level.

For one repository (bare clone ok) walk the first-parent history, keep the table of functions of every source file,
and for every function that changes in a commit:
  smell (Long Method nloc>50, Complex Method CCN>10, Many Parameters >5) before / after the commit
  changed_lines = ADDED + MODIFIED lines of the commit that fall inside the function (new side of `git diff -U0`)
classification
  smell disappears                         -> principal repayment      (all changed lines)
  smell appears                            -> principal increase       (all changed lines)
  smell stays:  growth = max(0, nloc_new - nloc_old)
                principal increase = min(changed_lines, growth);  interest lines = the rest (re-work of existing lines)
effort = COCOMO II(interest lines) per event (cocomo.py).

Also writes snapshot rows (every STEP commits) for the prediction task: features use history strictly before the snapshot,
target = interest lines/PM of the same function in the next HORIZON commits.

usage: history.py REPO.git OUT_PREFIX [--window N]
"""
import csv
import os
import re
import subprocess
import sys

import lizard

sys.path.insert(0, os.path.dirname(__file__))
import cocomo

EXT = {".py": "py", ".c": "c", ".h": "c", ".cc": "c", ".cpp": "c", ".hpp": "c"}
SKIP = re.compile(r"(^|/)(tests?|docs?|examples?|doc|contrib|fuzz\w*|benchmarks?|scripts|\.github)(/|$)|(^|/)test_[^/]*$|_test\.\w+$|conftest\.py$")
STEP, HORIZON = 40, 100
LONG_NLOC, CCN, PARAMS = 50, 10, 5


def git(repo, *args, text=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if text else r.stdout


def is_src(path):
    return os.path.splitext(path)[1] in EXT and not SKIP.search(path)


def functions(path, code):
    out = {}
    try:
        info = lizard.analyze_file.analyze_source_code(path, code)
    except Exception:
        return out
    for f in info.function_list:
        k, n = f.name, 1
        while k in out:
            n += 1
            k = f"{f.name}#{n}"
        out[k] = dict(s=f.start_line, e=f.end_line, nloc=f.nloc, ccn=f.cyclomatic_complexity, par=len(f.parameters))
    return out


def smell(f):
    return (f["nloc"] > LONG_NLOC, f["ccn"] > CCN, f["par"] > PARAMS)


def is_smell(f):
    return any(smell(f))


def code_lines(code, lang, lines):
    """keep only changed lines that are source lines (not blank, not comment-only) - SLOC, as COCOMO needs."""
    src = code.split("\n")
    out = set()
    for ln in lines:
        if ln < 1 or ln > len(src):
            continue
        s = src[ln - 1].strip()
        if not s or (lang == "py" and s.startswith("#")) or (lang == "c" and s.startswith(("//", "/*", "*"))):
            continue
        out.add(ln)
    return out


def changed_ranges(diff):
    """{new_path: set(new-side line numbers added or modified)} and {new_path: old_path} for renames."""
    res, ren, cur = {}, {}, None
    old = None
    for l in diff.split("\n"):
        if l.startswith("--- "):
            old = l[4:].removeprefix("a/") if l[4:] != "/dev/null" else None
        elif l.startswith("+++ "):
            cur = l[4:].removeprefix("b/") if l[4:] != "/dev/null" else None
            if cur:
                res.setdefault(cur, set())
                if old and old != cur:
                    ren[cur] = old
        elif l.startswith("@@") and cur:
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", l)
            if m:
                a, c = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
                res[cur].update(range(a, a + c))
    return res, ren


def features(repo_name, idx, path, fn, f, fs, nsm, m):
    """Feature row of one smell function at commit index idx, from history strictly before it."""
    m = m or dict(first=None, last=0, il=[], ch=[], n=0)
    past = [(i, l) for i, l in m["il"] if i <= idx]
    chg = [(i, l) for i, l in m["ch"] if i <= idx]
    return dict(repo=repo_name, idx=idx, file=path, func=fn, lang=EXT[os.path.splitext(path)[1]],
                nloc=f["nloc"], ccn=f["ccn"], par=f["par"], is_long=int(f["nloc"] > LONG_NLOC), is_cx=int(f["ccn"] > CCN), is_par=int(f["par"] > PARAMS),
                file_smells=nsm, file_funcs=len(fs), age=idx - (m["first"] if m["first"] is not None else idx),
                since_change=idx - m["last"], n_changes=len(chg), churn50=sum(l for i, l in chg if i > idx - 50), churn_all=sum(l for i, l in chg),
                past_il=sum(l for i, l in past), past_pm=sum(cocomo.pm(l) for _, l in past), past_n_int=len(past))


def walk(repo, window, ref="HEAD", full=False):
    commits = git(repo, "rev-list", "--first-parent", "--reverse", f"-n{window}", ref).split()
    dates = {c: git(repo, "log", "-1", "--format=%cs", c).strip() for c in commits[:1]}
    # initial state: every source file at the first commit of the window
    state = {}
    for p in git(repo, "ls-tree", "-r", "--name-only", commits[0]).split("\n"):
        if p and is_src(p):
            state[p] = functions(p, git(repo, "show", f"{commits[0]}:{p}"))
    events, snaps = [], []
    meta = {}     # (file, func) -> dict(first_smell, last_change, ilines list[(idx, lines)], churn list[(idx, lines)])
    for p, fs in state.items():
        for fn, f in fs.items():
            meta[(p, fn)] = dict(first=0 if is_smell(f) else None, last=0, il=[], ch=[], n=0)
    for idx in range(1, len(commits)):
        c, par = commits[idx], commits[idx - 1]
        diff = git(repo, "diff", "-U0", "-M", "--no-color", par, c)
        rng, ren = changed_ranges(diff)
        for path, lines in rng.items():
            if not is_src(path):
                continue
            oldp = ren.get(path, path)
            old = state.pop(oldp, {}) if oldp != path else state.get(path, {})
            code = git(repo, "show", f"{c}:{path}")
            new = functions(path, code)
            lines = code_lines(code, EXT[os.path.splitext(path)[1]], lines)
            state[path] = new
            if oldp != path:
                for fn in list(new):
                    if (oldp, fn) in meta:
                        meta[(path, fn)] = meta.pop((oldp, fn))
            for fn, f in new.items():
                inside = sum(1 for ln in lines if f["s"] <= ln <= f["e"])
                key = (path, fn)
                m = meta.setdefault(key, dict(first=None, last=idx, il=[], ch=[], n=0))
                o = old.get(fn)
                if inside == 0 and o is not None and (o["nloc"], o["ccn"], o["par"]) == (f["nloc"], f["ccn"], f["par"]):
                    continue
                if o is None:      # new function
                    if is_smell(f):
                        m["first"] = idx
                    m["last"] = idx
                    m["ch"].append((idx, inside))
                    continue
                was, now = is_smell(o), is_smell(f)
                if inside == 0:
                    pass
                else:
                    if was and not now:
                        cls, il = "repayment", 0
                    elif now and not was:
                        cls, il = "increase", 0
                    elif was and now:
                        growth = max(0, f["nloc"] - o["nloc"])
                        inc = min(inside, growth)
                        cls, il = "interest", inside - inc
                    else:
                        cls, il = None, 0
                    if cls:
                        events.append(dict(repo=os.path.basename(repo), idx=idx, commit=c[:10], file=path, func=fn, cls=cls, changed=inside,
                                           interest_lines=il, pm=cocomo.pm(il), nloc_old=o["nloc"], nloc_new=f["nloc"], ccn_old=o["ccn"], ccn_new=f["ccn"]))
                        if cls == "interest" and il > 0:
                            m["il"].append((idx, il))
                    m["ch"].append((idx, inside))
                    m["last"] = idx
                    m["n"] += 1
                if now and m["first"] is None:
                    m["first"] = idx
                if not now:
                    m["first"] = None
            for fn in set(old) - set(new):
                meta.pop((path, fn), None)
        if idx % 25 == 0:      # drop files deleted since the last check
            alive = set(git(repo, "ls-tree", "-r", "--name-only", c).split("\n"))
            for dp in [p for p in state if p not in alive]:
                state.pop(dp, None)
        if idx % STEP == 0 and idx + HORIZON < len(commits):
            for path, fs in state.items():
                nsm = sum(1 for f in fs.values() if is_smell(f))
                for fn, f in fs.items():
                    if not is_smell(f):
                        continue
                    snaps.append(features(os.path.basename(repo), idx, path, fn, f, fs, nsm, meta.get((path, fn))))
    # targets: interest of the same (file, func) in (idx, idx+HORIZON]
    fut = {}
    for e in events:
        if e["cls"] == "interest" and e["interest_lines"] > 0:
            fut.setdefault((e["file"], e["func"]), []).append(e)
    for s in snaps:
        ev = [e for e in fut.get((s["file"], s["func"]), []) if s["idx"] < e["idx"] <= s["idx"] + HORIZON]
        s["fut_il"] = sum(e["interest_lines"] for e in ev)
        s["fut_pm"] = sum(e["pm"] for e in ev)
        s["fut_n"] = len(ev)
    if full:
        return events, snaps, len(commits), state, meta
    return events, snaps, len(commits)


def write(rows, path):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    repo, out = sys.argv[1], sys.argv[2]
    window = int(sys.argv[sys.argv.index("--window") + 1]) if "--window" in sys.argv else 600
    ev, sn, n = walk(repo, window)
    write(ev, out + "_events.csv")
    write(sn, out + "_snapshots.csv")
    from collections import Counter
    print(f"{os.path.basename(repo)}: {n} commits, events {dict(Counter(e['cls'] for e in ev))}, snapshots {len(sn)}, "
          f"with future interest {sum(1 for s in sn if s['fut_il'] > 0)}")
