"""TECHNICAL-DEBT block. Every TD type of the study is represented:
  code complexity / size smells (long method, complex method, many parameters, large file, god class) and their principal (COCOMO II refactoring effort)
  self-admitted debt in comments (design / defect / requirement / test / documentation keywords)
  duplication (normalised 6-line window hashes shared by several places)
  security (bandit for Python, flawfinder for C, plus validation-guard density)
  concurrency (lock / thread / wait-loop idioms)
  cohesion (LCOM4 of Python classes) - coupling comes from the dependency graph in the structure block
"""
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict

import numpy as np

from common import log1p, read

LONG_NLOC, CCN, PARAMS = 50, 10, 5
COCOMO_A, COCOMO_E = 2.94, 0.91 + 0.01 * 18.97      # COCOMO II.2000 nominal (same as td_interest/cocomo.py "nominal")
BIN = os.path.join(os.path.dirname(sys.executable))


def pm(sloc):
    return COCOMO_A * (sloc / 1000.0) ** COCOMO_E if sloc > 0 else 0.0


SATD = {
    "design": r"\b(hack|kludge|workaround|ugly|temporary|temp fix|for now|quick fix|dirty|refactor|clean ?up|hacky|monkey.?patch)\b",
    "defect": r"\b(fixme|bug|broken|wrong|incorrect|crash|leak|race condition|not thread.?safe|unsafe|vulnerab\w*|overflow)\b",
    "requirement": r"\b(todo|not implemented|unimplemented|not supported|missing|support for|should support|implement)\b",
    "test": r"\b(needs? test|add tests?|no tests?|untested|test me)\b",
    "doc": r"\b(document(ation)?|undocumented|needs? docs?|xxx)\b",
}
SATD_RE = {k: re.compile(v, re.I) for k, v in SATD.items()}
PY_LOCK = re.compile(r"\b(threading\.)?(R?Lock|Semaphore|BoundedSemaphore|Condition|Event|Barrier)\s*\(")
PY_WITH_LOCK = re.compile(r"\bwith\s+[\w\.\[\]\(\)]*(lock|Lock|mutex|_cond|cond)\b[^:]*:")
C_LOCK = re.compile(r"\b(pthread_mutex_lock|pthread_rwlock_(?:rd|wr)lock|pthread_spin_lock|mtx_lock|EnterCriticalSection)\s*\(")
C_UNLOCK = re.compile(r"\b(pthread_mutex_unlock|pthread_rwlock_unlock|pthread_spin_unlock|mtx_unlock|LeaveCriticalSection)\s*\(")
GUARD_PY = re.compile(r"^\s*if\s+(?:not\s+\w[\w\.]*|\w[\w\.]*\s+is\s+None|len\([^)]*\)\s*[<>=]+\s*\w+|[\w\.]+\s*[<>]=?\s*\w+)\s*:\s*(?:raise|return)\b", re.M)
GUARD_C = re.compile(r"^\s*if\s*\((?:!\s*\w[\w\->\.]*|\w[\w\->\.]*\s*==\s*(?:NULL|0)|[^;{}()]*[<>]=?[^;{}()]*(?:len|size|count|max|limit|cap|idx|index|num)\w*[^;{}()]*)\)\s*(?:\{\s*)?(?:return|goto)\b", re.M)


def smells(ctx):
    f = {}
    fn = ctx["funcs"]
    n = max(len(fn), 1)
    kl = max(sum(m["sloc"] for m in ctx["fmeta"]) / 1000, 1e-3)
    lm = [x for x in fn if x["nloc"] > LONG_NLOC]
    cm = [x for x in fn if x["ccn"] > CCN]
    mp = [x for x in fn if x["par"] > PARAMS]
    anyf = [x for x in fn if x["nloc"] > LONG_NLOC or x["ccn"] > CCN or x["par"] > PARAMS]
    f["t_long_method"], f["t_complex_method"], f["t_many_params"] = len(lm) / kl, len(cm) / kl, len(mp) / kl
    f["t_long_share"], f["t_complex_share"], f["t_params_share"], f["t_smell_share"] = len(lm) / n, len(cm) / n, len(mp) / n, len(anyf) / n
    f["t_smell_count"] = log1p(len(anyf))
    f["t_principal_pm"] = log1p(1000 * sum(pm(x["nloc"]) for x in anyf))          # milli-person-months, log
    f["t_principal_pm_per_kloc"] = sum(pm(x["nloc"]) for x in anyf) / kl
    f["t_very_complex"] = sum(1 for x in fn if x["ccn"] > 20) / kl
    f["t_huge_functions"] = sum(1 for x in fn if x["nloc"] > 150) / kl
    f["t_large_files"] = sum(1 for m in ctx["fmeta"] if m["sloc"] > 1000) / max(len(ctx["fmeta"]), 1)
    # smells concentrated in few files?
    per = Counter(x["file"] for x in anyf)
    f["t_smell_file_share"] = len(per) / max(len(ctx["fmeta"]), 1)
    f["t_smell_top1_share"] = (max(per.values()) / len(anyf)) if anyf else 0.0
    return f


def god_class_and_lcom(ctx):
    classes, lcom, big = 0, [], 0
    for rel, p, lang in ctx["files"]:
        if lang != "py":
            continue
        try:
            tree = ast.parse(read(p))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            classes += 1
            methods = [b for b in node.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if len(methods) > 20 or (getattr(node, "end_lineno", node.lineno) - node.lineno) > 500:
                big += 1
            if len(methods) < 2:
                continue
            attrs = []
            for m in methods:
                a = {n.attr for n in ast.walk(m) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self"}
                attrs.append(a)
            parent = list(range(len(methods)))

            def find(i):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i
            for i in range(len(methods)):
                for j in range(i + 1, len(methods)):
                    if attrs[i] & attrs[j]:
                        parent[find(i)] = find(j)
            lcom.append(len({find(i) for i in range(len(methods))}))
    return {"t_god_classes": big / max(classes, 1), "t_lcom4_mean": float(np.mean(lcom)) if lcom else 1.0,
            "t_lcom4_gt1_share": (sum(1 for x in lcom if x > 1) / len(lcom)) if lcom else 0.0, "t_lcom4_max": float(max(lcom)) if lcom else 1.0}


def satd(ctx):
    kl = max(sum(m["sloc"] for m in ctx["fmeta"]) / 1000, 1e-3)
    cnt = Counter()
    for _, c in ctx["comments"]:
        hit = False
        for k, rx in SATD_RE.items():
            if rx.search(c):
                cnt[k] += 1
                hit = True
        cnt["any"] += hit
    f = {"t_satd_" + k: cnt[k] / kl for k in list(SATD) + ["any"]}
    f["t_satd_ratio"] = cnt["any"] / max(len(ctx["comments"]), 1)
    return f


def duplication(ctx, win=6):
    seen = defaultdict(list)
    total = 0
    for rel, p, lang in ctx["files"]:
        norm = []
        for i, l in enumerate(read(p).split("\n")):
            s = re.sub(r"\s+", " ", l.strip())
            if len(s) < 4 or s.startswith(("#", "//", "/*", "*", '"""', "import ", "from ", "#include", "}", "{")):
                continue
            norm.append((i, s))
        total += len(norm)
        for k in range(len(norm) - win + 1):
            key = hash(tuple(s for _, s in norm[k:k + win]))
            seen[key].append((rel, norm[k][0]))
    dup = set()
    for locs in seen.values():
        if len(locs) > 1:
            for rel, i in locs:
                dup.update((rel, i + d) for d in range(win))
    return {"t_dup_ratio": len(dup) / max(total, 1), "t_dup_blocks": log1p(sum(1 for l in seen.values() if len(l) > 1))}


def security(root, ctx, lang):
    kl = max(sum(m["sloc"] for m in ctx["fmeta"]) / 1000, 1e-3)
    f = {}
    env = dict(os.environ, PATH=BIN + os.pathsep + os.environ.get("PATH", ""))
    tot = hi = 0
    try:
        if lang == "py":
            out = subprocess.run(["bandit", "-r", root, "-f", "json", "-q", "-x", "tests,test,docs,examples"], capture_output=True, text=True, timeout=400, env=env)
            res = json.loads(out.stdout or "{}").get("results", [])
            tot = len(res)
            hi = sum(1 for r in res if r["issue_severity"] in ("HIGH", "MEDIUM"))
        else:
            out = subprocess.run(["flawfinder", "--csv", "--minlevel=1", "--quiet", root], capture_output=True, text=True, timeout=600, env=env)
            rows = [l for l in out.stdout.splitlines()[1:] if l.strip()]
            tot = len(rows)
            hi = sum(1 for l in rows if re.match(r"^[^,]*,[^,]*,\d+,[4-5]", l))
    except Exception:
        pass
    f["t_sec_findings"], f["t_sec_high"] = tot / kl, hi / kl
    g = 0
    for rel, p, l in ctx["files"]:
        g += len((GUARD_PY if l == "py" else GUARD_C).findall(read(p)))
    f["t_guards_per_kloc"] = g / kl
    return f


def concurrency(ctx, lang):
    kl = max(sum(m["sloc"] for m in ctx["fmeta"]) / 1000, 1e-3)
    c = Counter()
    for rel, p, l in ctx["files"]:
        t = read(p)
        if l == "py":
            c["lock"] += len(PY_LOCK.findall(t)) + len(PY_WITH_LOCK.findall(t))
            c["thread"] += len(re.findall(r"\bThread\s*\(|ThreadPoolExecutor|threading\.|asyncio\.|multiprocessing", t))
            c["wait"] += len(re.findall(r"\.wait\s*\(|\.acquire\s*\(|\.notify(?:_all)?\s*\(", t))
        else:
            c["lock"] += len(C_LOCK.findall(t)) + len(C_UNLOCK.findall(t))
            c["thread"] += len(re.findall(r"\bpthread_create\b|\bthrd_create\b|\bstd::thread\b", t))
            c["wait"] += len(re.findall(r"\bpthread_cond_(?:timed)?wait\b|\bcnd_(?:timed)?wait\b", t))
            c["atomic"] += len(re.findall(r"\b_Atomic\b|\batomic_\w+|__atomic_\w+|__sync_\w+", t))
        c["global_mut"] += len(re.findall(r"^\s*global\s+\w+", t, re.M)) if l == "py" else len(re.findall(r"^static\s+(?!const)[\w\s\*]+\s+\w+\s*(?:=|;)", t, re.M))
    f = {f"t_conc_{k}_per_kloc": c[k] / kl for k in ("lock", "thread", "wait", "atomic", "global_mut")}
    f["t_conc_uses_threads"] = float(c["thread"] > 0)
    return f


def td_features(root, ctx, lang):
    f = {}
    f.update(smells(ctx))
    f.update(god_class_and_lcom(ctx))
    f.update(satd(ctx))
    f.update(duplication(ctx))
    f.update(security(root, ctx, lang))
    f.update(concurrency(ctx, lang))
    return f
