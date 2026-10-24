"""Shared helpers: source-file discovery, reading, language detection, tree export from git."""
import functools
import os
import re
import subprocess

EXT = {".py": "py", ".c": "c", ".h": "c", ".cc": "c", ".cpp": "c", ".hpp": "c", ".cxx": "c"}
SKIP_DIRS = {".git", "tests", "test", "testing", "docs", "doc", "examples", "example", "build", "dist", "contrib", "fuzz", "fuzzing",
             "benchmarks", "benchmark", "scripts", ".github", "node_modules", "venv", ".venv", "__pycache__", "artwork", "android", "msdos",
             "os400", "qnx", "watcom", "win32", "amiga", "projects", "ci", "regression-inputs", "docker", "pkg", "misc"}
SKIP_FILE = re.compile(r"(^test_|_test\.|conftest\.py$|^setup\.py$)")


def log1p(x):
    import math
    return math.log1p(max(x, 0))


def src_files(root):
    """[(relpath, abspath, lang)] of production source files (tests/docs/examples/vendor dirs skipped)."""
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(fn):
            ext = os.path.splitext(f)[1]
            if ext in EXT and not SKIP_FILE.search(f):
                p = os.path.join(dp, f)
                out.append((os.path.relpath(p, root), p, EXT[ext]))
    return out


@functools.lru_cache(maxsize=20000)
def read(path):
    try:
        return open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""


def dominant_lang(files):
    n = {"py": 0, "c": 0}
    for _, p, lang in files:
        n[lang] += read(p).count("\n")
    return "py" if n["py"] >= n["c"] else "c"


def git(repo, *a, text=True):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if text else r.stdout


def export_tree(repo, commit, dst):
    os.makedirs(dst, exist_ok=True)
    tar = subprocess.run(["git", "-C", repo, "archive", commit], capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", dst], input=tar, check=True)


def gini(xs):
    xs = sorted(x for x in xs if x >= 0)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * sum(xs)) - (n + 1) / n


def quant(xs, prefix, qs=(0.5, 0.9, 1.0), mean=True):
    """quantile features of a list under a name prefix"""
    import numpy as np
    out = {}
    if len(xs) == 0:
        xs = [0.0]
    a = np.asarray(xs, dtype=float)
    if mean:
        out[prefix + "_mean"] = float(a.mean())
    for q in qs:
        out[f"{prefix}_p{int(q * 100)}"] = float(np.quantile(a, q))
    return out


def is_src_path(path):
    parts = path.split("/")
    if os.path.splitext(path)[1] not in EXT or SKIP_FILE.search(parts[-1]):
        return False
    return not any(p in SKIP_DIRS or p.startswith(".") for p in parts[:-1])
