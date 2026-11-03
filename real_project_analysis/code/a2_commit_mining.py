#!/usr/bin/env python3
"""Commit-level mining of one repository: what real changes look like, and which of them create or remove debt.

For the last N non-merge commits that touch source files:
  data/commits/<repo>.csv        one row per commit: size, files, functions touched, bug-fix flag, subject keywords per debt type,
                                 self-admitted-debt comments added / removed, smell functions created / removed / grown / shrunk
  data/commit_funcs/<repo>.csv   one row per function whose smell status or size changed in a commit (the natural-pair candidates):
                                 before / after nloc, ccn, parameters, smell flags, changed lines

usage: a2_commit_mining.py REPO.git DATA [--n 700] [--max-files 40]
"""
import csv
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "interest_exp", "code"))
import history as H
import interest_versions as IV

FIX = re.compile(r"\b(fix|fixes|fixed|bug|crash|leak|overflow|regression|cve|segfault|npe|race|deadlock|hang|corrupt)", re.I)
NOTFIX = re.compile(r"\b(typo|docs?|documentation|style|lint|format|changelog|readme|spelling)\b", re.I)
KW = {
    "security": re.compile(r"cve|vuln|overflow|injection|sanitiz|xss|csrf|secur|bounds|out[- ]of[- ]bounds|use[- ]after|double[- ]free|traversal|escape|untrusted|malicious|exploit|dos\b|denial", re.I),
    "concurrency": re.compile(r"race|deadlock|thread|\block|mutex|atomic|concurren|synchroni|semaphore|reentran|async", re.I),
    "dependency": re.compile(r"import|circular|cycle|dependenc|layer|include|header|module", re.I),
    "coupling": re.compile(r"decoupl|coupl|extract|move |split|encapsul|interface|abstract|inherit|visibility|private", re.I),
    "complexity": re.compile(r"simplif|complex|refactor|clean ?up|reduce|long function|too many|deduplicat|duplicate", re.I),
}
SAD = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True).stdout.decode("utf-8", "replace")


def main():
    repo, data = sys.argv[1], sys.argv[2]
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 700
    maxf = int(sys.argv[sys.argv.index("--max-files") + 1]) if "--max-files" in sys.argv else 40
    name = os.path.basename(repo).replace(".git", "")
    for d in ("commits", "commit_funcs"):
        os.makedirs(os.path.join(data, d), exist_ok=True)
    log = git(repo, "log", "--no-merges", "-n", str(n * 3), "--format=%x01%H|%P|%cs|%ae|%s", "--numstat")
    commits = []
    for blk in log.split("\x01")[1:]:
        head, *stat = blk.strip("\n").split("\n")
        sha, parents, date, mail, subj = head.split("|", 4)
        files = []
        for ln in stat:
            p = ln.split("\t")
            if len(p) == 3:
                a, d, path = p
                files.append((path, int(a) if a.isdigit() else 0, int(d) if d.isdigit() else 0))
        src = [f for f in files if H.is_src(f[0])]
        if src and parents:
            commits.append((sha, parents.split()[0], date, hashlib.sha1(mail.encode()).hexdigest()[:8], subj, files, src))
        if len(commits) >= n:
            break
    rows, frows = [], []
    for sha, par, date, au, subj, files, src in commits:
        add = sum(f[1] for f in files); dele = sum(f[2] for f in files)
        sadd = sum(f[1] for f in src); sdel = sum(f[2] for f in src)
        r = dict(repo=name, sha=sha[:10], date=date, author=au, subject=subj[:100], files=len(files), src_files=len(src), added=add, deleted=dele,
                 src_added=sadd, src_deleted=sdel, bugfix=int(bool(FIX.search(subj)) and not NOTFIX.search(subj)),
                 sad_added=0, sad_removed=0, funcs_changed=0, smell_created=0, smell_removed=0, smell_grew=0, smell_shrank=0, new_funcs=0, deleted_funcs=0,
                 bulk=int(len(src) > maxf), max_changed_func_nloc=0, smell_touched=0, smell_touched_lines=0, code_lines_changed=0)
        for k, rx in KW.items():
            r["kw_" + k] = int(bool(rx.search(subj)))
        if not r["bulk"]:
            diff = git(repo, "diff", "-U0", "-M", "--no-color", par, sha, "--", *[f[0] for f in src])
            r["sad_added"] = sum(1 for l in diff.split("\n") if l.startswith("+") and not l.startswith("+++") and SAD.search(l))
            r["sad_removed"] = sum(1 for l in diff.split("\n") if l.startswith("-") and not l.startswith("---") and SAD.search(l))
            rng, ren = H.changed_ranges(diff)
            old_of = {nw: old for old, nw in ren.items()}
            for path, _, _ in src:
                p0 = old_of.get(path, path)
                before = IV.funcs(repo, par, p0)
                after = IV.funcs(repo, sha, path)
                cl = H.code_lines(IV.show(repo, sha, path) or "", H.EXT.get(os.path.splitext(path)[1], "py"), rng.get(path, set()))
                r["code_lines_changed"] += len(cl)
                for fn, f in after.items():
                    inside = sum(1 for ln in cl if f["s"] <= ln <= f["e"])
                    b = before.get(fn)
                    fa = H.smell(f)
                    if b is None:
                        r["new_funcs"] += 1
                        if any(fa):
                            r["smell_created"] += 1
                            frows.append(dict(repo=name, sha=sha[:10], date=date, file=path, func=fn, event="created_smell", nloc0=0, ccn0=0, par0=0, nloc1=f["nloc"], ccn1=f["ccn"], par1=f["par"],
                                              long1=int(fa[0]), cx1=int(fa[1]), par_smell1=int(fa[2]), changed=inside, bugfix=r["bugfix"]))
                        continue
                    fb = H.smell(b)
                    if inside == 0 and (b["nloc"], b["ccn"], b["par"]) == (f["nloc"], f["ccn"], f["par"]):
                        continue
                    r["funcs_changed"] += 1
                    r["max_changed_func_nloc"] = max(r["max_changed_func_nloc"], f["nloc"])
                    if any(fa) or any(fb):
                        r["smell_touched"] += 1
                        r["smell_touched_lines"] += inside
                    ev = None
                    if any(fa) and not any(fb):
                        ev = "introduced_smell"; r["smell_created"] += 1
                    elif any(fb) and not any(fa):
                        ev = "removed_smell"; r["smell_removed"] += 1
                    elif any(fa) and any(fb):
                        if f["nloc"] > b["nloc"] or f["ccn"] > b["ccn"]:
                            ev = "grew_smell"; r["smell_grew"] += 1
                        elif f["nloc"] < b["nloc"] or f["ccn"] < b["ccn"]:
                            ev = "shrank_smell"; r["smell_shrank"] += 1
                    if ev:
                        frows.append(dict(repo=name, sha=sha[:10], date=date, file=path, func=fn, event=ev, nloc0=b["nloc"], ccn0=b["ccn"], par0=b["par"], nloc1=f["nloc"], ccn1=f["ccn"],
                                          par1=f["par"], long1=int(fa[0]), cx1=int(fa[1]), par_smell1=int(fa[2]), changed=inside, bugfix=r["bugfix"]))
                for fn, b in before.items():
                    if fn not in after:
                        r["deleted_funcs"] += 1
                        if any(H.smell(b)):
                            r["smell_removed"] += 1
                            frows.append(dict(repo=name, sha=sha[:10], date=date, file=path, func=fn, event="deleted_smell", nloc0=b["nloc"], ccn0=b["ccn"], par0=b["par"], nloc1=0, ccn1=0,
                                              par1=0, long1=0, cx1=0, par_smell1=0, changed=0, bugfix=r["bugfix"]))
        rows.append(r)
    for dname, rr in (("commits", rows), ("commit_funcs", frows)):
        if rr:
            with open(os.path.join(data, dname, name + ".csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rr[0])); w.writeheader(); w.writerows(rr)
    print(f"{name}: {len(rows)} commits, {len(frows)} function events, smell created {sum(r['smell_created'] for r in rows)} removed {sum(r['smell_removed'] for r in rows)}", flush=True)


if __name__ == "__main__":
    main()
