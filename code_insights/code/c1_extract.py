#!/usr/bin/env python3
"""Read the CODE of the debt functions and turn what is visible in the text into features.

For a sample of release pairs of every repository (every 3rd pair: 0, 3, 6, ...) the source of each debt function is taken from the earlier
release (git show TAG:file, function lines from lizard). From the text:
  repetition   dup_line_ratio    share of meaningful lines that occur at least twice in the function
               shape_run_ratio   share of lines inside runs of >= 3 consecutive lines with the same shape (identifiers -> x, numbers -> 0, strings -> S)
               clone_ratio       share of 4-line shingles of the function that also occur in ANOTHER function of the same file set
  structure    max_nest, n_calls, n_distinct_calls, calls_per_line, n_return, n_locals, magic_numbers, comment_ratio, n_branch_words
  pointers (C) n_arrow, n_deref, n_alloc (malloc/calloc/realloc/free), n_null_check, n_cast_ptr, n_unsafe (strcpy, sprintf, ...), n_goto
  python       n_try, n_bare_except, n_isinstance, n_self_attr, n_kwargs, n_nested_def, n_global
outcome: event = the instance had interest lines in that release pair (from the transitions of the real-project analysis).
-> ../results/c1_features.csv, ../results/c1_texts.jsonl (function text, first 150 lines)
usage: c1_extract.py [repo ...]   (default: all 33 repositories, 3 processes)"""
import json, os, re, subprocess, sys
from collections import Counter, defaultdict
from multiprocessing import Pool
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); BTP = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "interest_exp", "code"))
import history as H
import interest_versions as IV

REPOS = os.path.join(BTP, "repos"); TR = os.path.join(ROOT, "real_project_analysis", "data", "transitions"); RES = os.path.join(HERE, "..", "results")
STEP = 3
KEYW = {"if", "for", "while", "switch", "return", "sizeof", "catch", "else", "elif", "def", "lambda", "and", "or", "not", "in", "is", "print", "assert", "with", "yield", "await", "typeof"}
CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
STR = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'")
NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
IDENT = re.compile(r"\b[A-Za-z_]\w*\b")
MAGIC = re.compile(r"(?<![\w.])(?:0x[0-9a-fA-F]+|\d{2,}|\d\.\d+)(?![\w.])")
ALLOC = re.compile(r"\b(?:malloc|calloc|realloc|free|xmalloc|xfree|alloc\w*|\w*_free|\w*_alloc)\s*\(")
UNSAFE = re.compile(r"\b(?:strcpy|strcat|sprintf|vsprintf|gets|memcpy|memmove|strncpy|strncat|snprintf)\s*\(")
NULLCHK = re.compile(r"(?:[=!]=\s*NULL|NULL\s*[=!]=|\bif\s*\(\s*!\s*\w|\bif\s*\(\s*\w+\s*\)|\bis None\b|\bis not None\b)")
CASTP = re.compile(r"\(\s*(?:const\s+|unsigned\s+|struct\s+)?\w+\s*\*+\s*\)")
BRANCH = re.compile(r"\b(?:if|elif|else|for|while|case|switch|except|catch)\b|&&|\|\||\?")


def lang_of(path): return H.EXT.get(os.path.splitext(path)[1], "c")


def clean_lines(code, lang):
    """lines without comments/blank; returns (list of stripped code lines, number of comment lines)"""
    out, com, inblock = [], 0, False
    for ln in code.split("\n"):
        s = ln.strip()
        if not s: continue
        if lang == "py":
            if s.startswith("#"): com += 1; continue
        else:
            if inblock:
                com += 1
                if "*/" in s: inblock = False
                continue
            if s.startswith("/*"):
                com += 1
                if "*/" not in s: inblock = True
                continue
            if s.startswith("//"): com += 1; continue
        out.append(s)
    return out, com


def shape(s):
    s = STR.sub("S", s); s = NUM.sub("0", s); return IDENT.sub("x", s)


def feats(code, lang):
    lines, ncom = clean_lines(code, lang); n = max(len(lines), 1)
    norm = [re.sub(r"\s+", " ", l) for l in lines]; meaningful = [l for l in norm if len(l) >= 8 and l not in ("else:", "} else {", "return;", "break;", "continue;")]
    cnt = Counter(meaningful); dup = sum(c for c in cnt.values() if c >= 2) / max(len(meaningful), 1)
    sh = [shape(l) for l in norm]; inrun = 0; i = 0
    while i < len(sh):
        j = i
        while j + 1 < len(sh) and sh[j + 1] == sh[i] and len(sh[i]) >= 6: j += 1
        if j - i + 1 >= 3: inrun += j - i + 1
        i = j + 1
    text = "\n".join(lines)
    calls = [c for c in CALL.findall(text) if c not in KEYW]
    if lang == "py":
        ind = [len(l) - len(l.lstrip(" \t")) for l in code.split("\n") if l.strip()]
        nest = (max(ind) - min(ind)) // 4 if ind else 0
    else:
        d = m = 0
        for ch in text:
            if ch == "{": d += 1; m = max(m, d)
            elif ch == "}": d -= 1
        nest = max(m - 1, 0)
    f = dict(lines=n, dup_line_ratio=dup, shape_run_ratio=inrun / n, max_nest=nest, n_calls=len(calls), n_distinct_calls=len(set(calls)), calls_per_line=len(calls) / n,
             n_return=len(re.findall(r"\breturn\b", text)), n_locals=len(set(re.findall(r"\b([A-Za-z_]\w*)\s*=(?!=)", text))), magic_numbers=len(MAGIC.findall(STR.sub("", text))),
             comment_ratio=ncom / (ncom + n), n_branch_words=len(BRANCH.findall(text)))
    if lang == "c":
        f.update(n_arrow=text.count("->"), n_deref=len(re.findall(r"(?<![\w)\]])\*\s*\w", text)), n_alloc=len(ALLOC.findall(text)), n_null_check=len(NULLCHK.findall(text)),
                 n_cast_ptr=len(CASTP.findall(text)), n_unsafe=len(UNSAFE.findall(text)), n_goto=len(re.findall(r"\bgoto\b", text)))
    else:
        f.update(n_try=len(re.findall(r"^\s*try:", text, re.M)), n_bare_except=len(re.findall(r"except\s*(?:Exception\s*)?(?:as \w+\s*)?:", text)), n_isinstance=text.count("isinstance("),
                 n_self_attr=len(set(re.findall(r"\bself\.(\w+)", text))), n_kwargs=len(re.findall(r"\*\*?\w+", text.split(":")[0] if ":" in text else text)),
                 n_nested_def=len(re.findall(r"^\s+def ", text, re.M)), n_global=len(re.findall(r"\bglobal\b", text)))
    return f, norm


def shingles(norm, k=4):
    ls = [l for l in norm if len(l) >= 6]
    return {hash(" | ".join(ls[i:i + k])) for i in range(max(len(ls) - k + 1, 0))}


def do_repo(name):
    out = os.path.join(RES, "c1_parts", name + ".csv")
    if os.path.exists(out): return name
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        T = pd.read_csv(os.path.join(TR, name + ".csv"))
    except Exception:
        return name
    T = T[T.cls != "introduced"].copy(); T["event"] = (T.interest_lines > 0).astype(int)
    repo = os.path.join(REPOS, name + ".git"); rows, texts = [], []
    vis = sorted(T.vi.unique())[::STEP]
    for vi in vis:
        P = T[T.vi == vi]
        if P.empty: continue
        tag = P.v0.iloc[0]
        per_file = {}
        for f in P.file.unique():
            code = IV.show(repo, tag, f)
            if code is None: continue
            fn = IV.funcs(repo, tag, f); lines = code.split("\n"); per_file[f] = (fn, lines)
        # clone index over all functions of these files
        sh, owner = {}, defaultdict(set)
        for f, (fn, lines) in per_file.items():
            lang = lang_of(f)
            for k, d in fn.items():
                body = "\n".join(lines[d["s"] - 1:d["e"]]); _, norm = feats(body, lang) if d["e"] - d["s"] < 400 else (None, [])
                s = shingles(norm); sh[(f, k)] = s
                for h in s: owner[h].add((f, k))
        for _, r in P.iterrows():
            if r.file not in per_file or r.func not in per_file[r.file][0]: continue
            fn, lines = per_file[r.file]; d = fn[r.func]
            body = "\n".join(lines[d["s"] - 1:d["e"]])
            if d["e"] - d["s"] > 600: continue
            f, _ = feats(body, lang_of(r.file)); s = sh.get((r.file, r.func), set())
            f["clone_ratio"] = sum(1 for h in s if len(owner[h]) > 1) / max(len(s), 1)
            f.update(repo=name, vi=int(vi), v0=tag, v1=r.v1, key=r.key, file=r.file, func=r.func, rule=r.rule, nloc0=r.nloc0, ccn0=r.ccn0, event=int(r.event), interest_lines=int(r.interest_lines),
                     age=r.age, lang=lang_of(r.file), start=d["s"], end=d["e"])
            rows.append(f)
            if len(texts) < 3000 and r.nloc0 <= 120: texts.append(dict(repo=name, vi=int(vi), key=r.key, text="\n".join(lines[d["s"] - 1:d["s"] + 150])))
    pd.DataFrame(rows).to_csv(out, index=False)
    with open(os.path.join(RES, "c1_parts", name + ".jsonl"), "w") as fh:
        for t in texts: fh.write(json.dumps(t) + "\n")
    print(name, len(rows), flush=True)
    return name


def main():
    names = sys.argv[1:] or sorted(os.path.basename(f)[:-4] for f in os.listdir(TR) if f.endswith(".csv"))
    names = [n for n in names if os.path.exists(os.path.join(REPOS, n + ".git"))]
    with Pool(3) as p: p.map(do_repo, names, chunksize=1)
    parts = [pd.read_csv(os.path.join(RES, "c1_parts", n + ".csv")) for n in names if os.path.exists(os.path.join(RES, "c1_parts", n + ".csv")) and os.path.getsize(os.path.join(RES, "c1_parts", n + ".csv")) > 5]
    pd.concat(parts, ignore_index=True).to_csv(os.path.join(RES, "c1_features.csv"), index=False)
    with open(os.path.join(RES, "c1_texts.jsonl"), "w") as out:
        for n in names:
            f = os.path.join(RES, "c1_parts", n + ".jsonl")
            if os.path.exists(f): out.write(open(f).read())
    print("done")


if __name__ == "__main__":
    main()
