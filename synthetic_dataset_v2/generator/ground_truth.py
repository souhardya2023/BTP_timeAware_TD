"""Interest ground truth from the git history of a synthetic project (not from the simulator's own log).

For every release pair (v0.t -> v0.t+1) and every debt instance that is alive at v0.t, the region of the instance (function(s), class or import line)
is located in both versions, and the lines of v1 that git diff -U0 reports as added or modified inside the region are counted (source lines only:
blank and comment-only lines are not).  The rule is the one of interest_exp (2025 method):
    instance repaid between the versions    -> cls repayment
    region grew                             -> principal increase of the growth
    changed lines beyond the growth         -> interest lines   (COCOMO II effort in person-months)
Output rows have the columns of interest_exp/data/transitions/*.csv, so that the existing experiments run on them unchanged.
"""
import ast
import csv
import io
import json
import os
import re
import subprocess
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "interest_exp", "code"))
import cocomo  # noqa: E402

try:
    import lizard
except ImportError:
    lizard = None

COLS = ["repo", "v0", "v1", "vi", "key", "file", "func", "rule", "severity", "sonar_effort_min", "nloc0", "ccn0", "age", "past_il", "past_n", "principal_pm",
        "cls", "persisted", "nloc1", "changed", "interest_lines", "pm_interest"]
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def tree(repo, tag):
    tar = subprocess.run(["git", "-C", repo, "archive", tag], capture_output=True).stdout
    out = {}
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        for m in tf.getmembers():
            if m.isfile() and m.name.endswith(".py"):
                out[m.name] = tf.extractfile(m).read().decode("utf-8", "replace")
    return out


def code_lines(text):
    """set of 1-based line numbers that hold source code (not blank, not comment only, not inside a docstring-only line is kept as code)"""
    s = set()
    for i, l in enumerate(text.splitlines(), 1):
        t = l.strip()
        if t and not t.startswith("#"):
            s.add(i)
    return s


def regions(text, inst):
    """list of (start, end) line ranges (1-based, inclusive) of the instance in this file text; [] if absent"""
    if inst["region_kind"] == "import":
        stmt = inst["stmt"]
        return [(i, i) for i, l in enumerate(text.splitlines(), 1) if l.strip().startswith(stmt)]
    try:
        mod = ast.parse(text)
    except SyntaxError:
        return []
    out = []
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in inst["quals"]:
            out.append((node.lineno, node.end_lineno))
    return out


def diff_new_lines(repo, a, b):
    """{file: set of new-side line numbers added or modified between the two tags}"""
    out = subprocess.run(["git", "-C", repo, "diff", "-U0", a, b], capture_output=True, text=True).stdout
    res, cur = {}, None
    for l in out.splitlines():
        if l.startswith("+++ "):
            cur = l[6:] if l.startswith("+++ b/") else None
            if cur:
                res.setdefault(cur, set())
        elif l.startswith("@@") and cur:
            m = HUNK.match(l)
            if m:
                s, n = int(m.group(1)), int(m.group(2) or 1)
                res[cur].update(range(s, s + n))
    return res


def ccn(text, ranges):
    if lizard is None or not ranges:
        return 1
    try:
        info = lizard.analyze_file.analyze_source_code("x.py", text)
    except Exception:
        return 1
    best = 1
    for f in info.function_list:
        if any(s <= f.start_line <= e for s, e in ranges):
            best = max(best, f.cyclomatic_complexity)
    return best


def ground_truth(repo, man):
    tags = [r["tag"] for r in man["release_table"]]
    trees = {t: tree(repo, t) for t in tags}
    clines = {t: {p: code_lines(x) for p, x in tr.items()} for t, tr in trees.items()}
    rows, rel_rows = [], []
    past = {}
    for ti in range(len(tags) - 1):
        t0, t1 = tags[ti], tags[ti + 1]
        rel0 = ti + 1
        nd = diff_new_lines(repo, t0, t1)
        total_added = sum(len(v & clines[t1].get(f, set())) for f, v in nd.items() if f.endswith(".py"))
        total_nloc = sum(len(v) for v in clines[t0].values())
        reg_nloc = reg_changed = 0
        seen_reg = set()
        for inst in man["instances"]:
            if inst["intro_release"] > rel0 or (inst["repaid_release"] is not None and inst["repaid_release"] <= rel0):
                continue
            f = inst["file"]
            if f not in trees[t0]:
                continue
            r0 = regions(trees[t0][f], inst)
            r1 = regions(trees[t1].get(f, ""), inst)
            cl0, cl1 = clines[t0].get(f, set()), clines[t1].get(f, set())
            nloc0 = sum(len([x for x in range(s, e + 1) if x in cl0]) for s, e in r0)
            nloc1 = sum(len([x for x in range(s, e + 1) if x in cl1]) for s, e in r1)
            ch = sum(len([x for x in range(s, e + 1) if x in nd.get(f, set()) and x in cl1]) for s, e in r1)
            repaid = inst["repaid_release"] == rel0 + 1
            growth = max(0, nloc1 - nloc0)
            il = 0 if repaid else ch - min(ch, growth)
            cls = "repayment" if repaid else ("interest" if il > 0 else ("increase" if growth > 0 else "none"))
            key = inst["id"]
            pi, pn = past.get(key, (0, 0))
            rows.append(dict(repo=man["id"], v0=t0, v1=t1, vi=ti, key=key, file=f, func=(inst["quals"][0] if inst["quals"] else "<imports>:" + str(inst["stmt"])[:30]),
                             rule="synth:" + inst["template"], severity="MAJOR", sonar_effort_min=15, nloc0=nloc0, ccn0=ccn(trees[t0][f], r0), age=rel0 - inst["intro_release"],
                             past_il=pi, past_n=pn, principal_pm=cocomo.pm(nloc0), cls=cls, persisted=0 if repaid else 1, nloc1=nloc1, changed=ch,
                             interest_lines=float(il), pm_interest=cocomo.pm(il) if il > 0 else 0.0))
            past[key] = (pi + il, pn + (1 if il > 0 else 0))
            if (f, tuple(r0)) not in seen_reg:
                seen_reg.add((f, tuple(r0)))
                reg_nloc += nloc0
                reg_changed += ch
        rel_rows.append(dict(repo=man["id"], v0=t0, v1=t1, vi=ti, activity=man["activity"][ti + 1], total_added=total_added, total_nloc=total_nloc,
                             region_nloc=reg_nloc, region_changed=reg_changed, instances=len(seen_reg)))
    return rows, rel_rows


def pair_rows(repo, man):
    out = []
    for inst in man["instances"]:
        if not inst["parent_hash"]:
            continue
        s = subprocess.run(["git", "-C", repo, "diff", "--numstat", inst["parent_hash"], inst["intro_hash"]], capture_output=True, text=True).stdout
        add = dele = files = 0
        for l in s.splitlines():
            a, d, _ = l.split("\t", 2)
            if a.isdigit():
                files += 1
                add += int(a)
                dele += int(d)
        out.append(dict(project=man["id"], instance=inst["id"], ptype=inst["ptype"], template=inst["template"], granularity=inst["granularity"], regime=man["regime"],
                        tier=man["tier"], intro_release=inst["intro_release"], parent=inst["parent_hash"], child=inst["intro_hash"], mixed=inst["mixed"],
                        files_changed=files, lines_added=add, lines_deleted=dele))
    return out


def run_one(args):
    out, pid = args
    repo = os.path.join(out, "repos", pid + ".git")
    man = json.load(open(os.path.join(out, "manifests", pid + ".json")))
    rows, rel = ground_truth(repo, man)
    pairs = pair_rows(repo, man)
    os.makedirs(os.path.join(out, "transitions"), exist_ok=True)
    os.makedirs(os.path.join(out, "releases"), exist_ok=True)
    with open(os.path.join(out, "transitions", pid + ".csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, COLS)
        w.writeheader()
        w.writerows(rows)
    if rel:
        with open(os.path.join(out, "releases", pid + ".csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, list(rel[0]))
            w.writeheader()
            w.writerows(rel)
    return pid, len(rows), sum(1 for r in rows if r["interest_lines"] > 0), pairs


if __name__ == "__main__":
    from multiprocessing import Pool
    out = sys.argv[1]
    ids = sorted(f[:-5] for f in os.listdir(os.path.join(out, "manifests")) if f.endswith(".json"))
    allpairs = []
    with Pool(4) as pool:
        for pid, n, ev, pairs in pool.imap_unordered(run_one, [(out, i) for i in ids]):
            allpairs += pairs
            print(pid, n, ev, flush=True)
    if allpairs:
        with open(os.path.join(out, "pairs.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, list(allpairs[0]))
            w.writeheader()
            w.writerows(allpairs)
    print("pairs", len(allpairs))
