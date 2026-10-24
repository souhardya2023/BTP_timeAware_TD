#!/usr/bin/env python3
"""Put several bugs into every pair - the SAME bugs into the clean and into the TD project.  (No test suite is run.)

per pair  N bugs (default 3), each one small semantic change from mutate.py: flipped comparison, and/or swap, negated condition, +-1, off-by-one constant
          - the Python mutants are checked to still parse; the C mutants change an operator or a constant inside a condition / expression
          - a bug never overlaps the lines that td.patch changes, and its patch applies to BOTH the clean and the TD tree
          - one bug in a file the TD change touches when possible (so the debt and a bug can interact), the others elsewhere;
            different functions and different kinds of bug where possible
reads     PROJECT_DATASET/<lang>/P#/{P#_clean, P#_TD, P#_prop/td.patch}
writes    BUGS_DATASET/<lang>/P#/{P#_clean_bug, P#_TD_bug, P#_bugs/{bug1.patch.., bugs.json}}
          (the projects have no tests folder, as in the rest of the dataset)

usage: inject_bugs.py PROJECT_DATASET BUGS_DATASET [--bugs 3] [--only Python/P1,C_C++/P3]
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from common import read, src_files
from mutate import mutants, patch_of


def td_ranges(patch):
    """{file: [(start, end)]} lines of the clean project that td.patch changes, with a margin of 8 lines"""
    res, cur = {}, None
    for l in patch.split("\n"):
        m = re.match(r"diff --git a/(\S+) b/", l)
        if m:
            cur = m.group(1)
            res.setdefault(cur, [])
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", l)
        if m and cur:
            a, n = int(m.group(1)), int(m.group(2) or 1)
            res[cur].append((a - 8, a + n + 8))
    return res


def git_apply(tree, patch_text, check=False):
    r = subprocess.run(["git", "apply"] + (["--check"] if check else []) + ["-"], cwd=tree, input=patch_text, capture_output=True, text=True)
    return r.returncode == 0


def inject_pair(src, dst, p, seed, nb=3):
    """src = PROJECT_DATASET/<lang>/P#, dst = BUGS_DATASET/<lang>/P#. Returns the list of bugs."""
    clean, td = os.path.join(src, f"{p}_clean"), os.path.join(src, f"{p}_TD")
    patch = open(os.path.join(src, f"{p}_prop", "td.patch"), errors="ignore").read()
    rg = td_ranges(patch)
    rng = random.Random(seed)
    cands = []
    for rel, path, lang in src_files(clean):
        old = read(path)
        for m in mutants(rel, old, lang):
            if any(a <= m["line"] <= b for a, b in rg.get(rel, [])):
                continue
            m["old"], m["in_td_file"] = old, rel in rg
            cands.append(m)
    rng.shuffle(cands)
    chosen, funcs, ops, files = [], set(), set(), set()

    def pick(want_td):
        for m in sorted(cands, key=lambda m: (m["file"] in files, m["op"] in ops)):     # new files and new kinds of bug first
            if (m["file"], m["func"]) in funcs or (want_td and not m["in_td_file"]):
                continue
            pt = patch_of(m["file"], m["old"], m["new_text"])
            if git_apply(clean, pt, True) and git_apply(td, pt, True):
                m["patch"] = pt
                return m
        return None

    for want_td in [True] + [False] * (nb + 2):
        if len(chosen) >= nb:
            break
        m = pick(want_td)
        if m is None:
            continue
        tmp = dst + "_tmp_check"
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(clean, tmp, symlinks=True)
        good = all(git_apply(tmp, q["patch"]) for q in chosen + [m])      # the chosen patches must apply together
        shutil.rmtree(tmp, ignore_errors=True)
        if good:
            chosen.append(m); funcs.add((m["file"], m["func"])); ops.add(m["op"]); files.add(m["file"])
        else:
            cands.remove(m)
    shutil.rmtree(dst, ignore_errors=True)
    bdir = os.path.join(dst, f"{p}_bugs")
    os.makedirs(bdir)
    meta = []
    for i, m in enumerate(chosen, 1):
        open(os.path.join(bdir, f"bug{i}.patch"), "w").write(m["patch"])
        meta.append(dict(bug=f"bug{i}", file=m["file"], line=m["line"], function=m["func"], kind=m["op"], description=m["desc"], in_td_file=m["in_td_file"]))
    json.dump(meta, open(os.path.join(bdir, "bugs.json"), "w"), indent=1)
    for side, tree in (("clean", clean), ("TD", td)):
        out = os.path.join(dst, f"{p}_{side}_bug")
        shutil.copytree(tree, out, symlinks=True)
        for i in range(1, len(chosen) + 1):
            r = subprocess.run(["git", "apply", os.path.join(bdir, f"bug{i}.patch")], cwd=out, capture_output=True, text=True)
            assert r.returncode == 0, (p, side, i, r.stderr)
    return meta


def main():
    pd_, bd = (os.path.abspath(x) for x in sys.argv[1:3])
    nb = int(sys.argv[sys.argv.index("--bugs") + 1]) if "--bugs" in sys.argv else 3
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
    for lang_dir in ("Python", "C_C++"):
        for p in sorted((x for x in os.listdir(os.path.join(pd_, lang_dir)) if re.fullmatch(r"P\d+", x)), key=lambda x: int(x[1:])):
            if only and f"{lang_dir}/{p}" not in only:
                continue
            meta = inject_pair(os.path.join(pd_, lang_dir, p), os.path.join(bd, lang_dir, p), p, f"{lang_dir}/{p}", nb)
            print(f"{lang_dir}/{p}: {len(meta)} bugs, kinds {sorted(m['kind'] for m in meta)}", flush=True)


if __name__ == "__main__":
    main()
