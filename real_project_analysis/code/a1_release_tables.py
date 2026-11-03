#!/usr/bin/env python3
"""Release-level tables of one repository (bare clone), from the last K release tags.

writes   DATA/transitions/<repo>.csv     per debt instance and release pair: interest (same method as interest_exp; structural smell detector)
         DATA/releases/<repo>.csv        per release pair: dates, version step, code size, debt size, changed lines (all / inside debt)
         DATA/files/<repo>.csv           per release pair and file: changed lines, code lines, debt lines (for the path-of-work features)
         DATA/funcs/<repo>.csv           per release pair: every function of V0 (nloc, ccn, params, smell flags, changed lines in it at V1) - the size law

usage: a1_release_tables.py REPO.git DATA [--k 20] [--no-transitions]
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "interest_exp", "code"))
import history as H
import interest_versions as IV
from versions import release_versions, sh


def vparts(tag):
    return [int(x) for x in re.findall(r"\d+", tag)][:3]


def step(t0, t1):
    a, b = vparts(t0), vparts(t1)
    a += [0] * (3 - len(a)); b += [0] * (3 - len(b))
    if b[0] != a[0]:
        return "major"
    if b[1] != a[1]:
        return "minor"
    return "patch"


def main():
    repo, data = sys.argv[1], sys.argv[2]
    k = int(sys.argv[sys.argv.index("--k") + 1]) if "--k" in sys.argv else 20
    name = os.path.basename(repo).replace(".git", "")
    for d in ("transitions", "releases", "files", "funcs"):
        os.makedirs(os.path.join(data, d), exist_ok=True)
    vers = release_versions(repo, k)
    if len(vers) < 4:
        sys.exit(f"{name}: only {len(vers)} release tags")

    if "--no-transitions" not in sys.argv:
        iss = IV.load_issues(repo, vers, None)
        rows = IV.run(repo, vers, iss)
        with open(os.path.join(data, "transitions", name + ".csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    rel, files, fn_rows = [], [], []
    for vi in range(len(vers) - 1):
        (t0, c0, d0), (t1, c1, d1) = vers[vi], vers[vi + 1]
        rng, ren = IV.diff_changes(repo, c0, c1)
        old_of = {n: o for o, n in ren.items()}                      # new path -> old path
        paths0 = [p for p in sh(repo, "ls-tree", "-r", "--name-only", c0).split("\n") if p and H.is_src(p)]
        paths1 = [p for p in sh(repo, "ls-tree", "-r", "--name-only", c1).split("\n") if p and H.is_src(p)]
        code0 = debt0 = 0
        smell0 = {}                                                    # (path, func) -> flags at V0
        for p in paths0:
            for fn, f in IV.funcs(repo, c0, p).items():
                code0 += f["nloc"]
                fl = H.smell(f)
                if any(fl):
                    debt0 += f["nloc"]
                smell0[(p, fn)] = (f, fl)
        code1 = debt1 = 0
        chg_all = chg_debt1 = chg_debt_pre = 0
        n_funcs_changed = 0
        for p in paths1:
            fnc = IV.funcs(repo, c1, p)
            cl = H.code_lines(IV.show(repo, c1, p) or "", H.EXT.get(os.path.splitext(p)[1], "py"), rng.get(p, set())) if p in rng else set()
            f_code = f_debt = f_chg_debt = 0
            p0 = old_of.get(p, p)
            for fn, f in fnc.items():
                f_code += f["nloc"]
                fl = H.smell(f)
                inside = sum(1 for ln in cl if f["s"] <= ln <= f["e"])
                prev = smell0.get((p0, fn))
                if any(fl):
                    f_debt += f["nloc"]
                    f_chg_debt += inside
                if prev is not None and any(prev[1]):
                    chg_debt_pre += inside
                if inside:
                    n_funcs_changed += 1
                if prev is not None:
                    f0, fl0 = prev
                    fn_rows.append(dict(repo=name, vi=vi, file=p0, func=fn, nloc0=f0["nloc"], ccn0=f0["ccn"], par0=f0["par"],
                                        long0=int(fl0[0]), cx0=int(fl0[1]), par_smell0=int(fl0[2]), nloc1=f["nloc"], changed=inside))
            code1 += f_code; debt1 += f_debt; chg_all += len(cl); chg_debt1 += f_chg_debt
            if cl:
                files.append(dict(repo=name, vi=vi, file=p, changed=len(cl), file_code=f_code, file_debt=f_debt, changed_in_debt=f_chg_debt))
        rel.append(dict(repo=name, vi=vi, v0=t0, v1=t1, d0=d0, d1=d1, step=step(t0, t1),
                        n_commits=int(sh(repo, "rev-list", "--count", f"{c0}..{c1}").strip() or 0),
                        code0=code0, debt0=debt0, code1=code1, debt1=debt1, n_src_files1=len(paths1),
                        chg_all=chg_all, chg_in_debt1=chg_debt1, chg_in_debt_pre=chg_debt_pre, n_funcs_changed=n_funcs_changed))
    for dname, rows in (("releases", rel), ("files", files), ("funcs", fn_rows)):
        if rows:
            with open(os.path.join(data, dname, name + ".csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"{name}: {len(vers)} releases, {len(rel)} pairs, {sum(r['chg_all'] for r in rel)} changed lines, funcs rows {len(fn_rows)}", flush=True)


if __name__ == "__main__":
    main()
