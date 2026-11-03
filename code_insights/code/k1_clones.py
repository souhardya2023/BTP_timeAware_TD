#!/usr/bin/env python3
"""Whole-repository near-clone detection (Type-1 and Type-2: identifiers, numbers and strings are normalised, so renamed copies match).

For every 4th release pair of each repository, all functions (>= 6 lines, >= 40 tokens) of all source files at the earlier release are turned into
token streams: comments and docstrings removed, identifiers -> I (keywords kept), numbers -> N, strings -> S. A function is the set of its
10-token shingles. Shingles that occur in more than 30 functions of the repository are dropped (generic boilerplate such as
'if ( I == N ) return I ;'). Two functions are clones when the Jaccard similarity of their shingle sets is >= 0.6 (exact copy: >= 0.95).
Output per function: the clone score of its best partner, number of partners, whether the partner is in the same file / a test path.
Output per clone pair: both functions and J.  Joined with the real-project edit table (funcs/*.csv: 'changed' lines per function per release pair).
-> ../results/k1_funcs.csv, ../results/k1_pairs.csv        usage: k1_clones.py [repo ...]"""
import os, re, sys
from collections import Counter, defaultdict
from multiprocessing import Pool
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); BTP = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "interest_exp", "code"))
import history as H
import interest_versions as IV

REPOS = os.path.join(BTP, "repos"); DATA = os.path.join(ROOT, "real_project_analysis", "data"); RES = os.path.join(HERE, "..", "results", "k1_parts")
K, MINLINES, MINTOK, MAXDF, THR, EVERY = 10, 6, 40, 30, 0.6, 4
CKW = set("auto break case char const continue default do double else enum extern float for goto if inline int long register return short signed sizeof static struct switch typedef union unsigned void volatile while NULL true false bool size_t uint8_t uint16_t uint32_t uint64_t int8_t int16_t int32_t int64_t".split())
PKW = set("False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield self cls".split())
TOK = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[A-Za-z_]\w*|\d[\w.]*|==|!=|<=|>=|->|\+\+|--|&&|\|\||<<|>>|::|\S")
TESTPATH = re.compile(r"(^|/)(tests?|testing|examples?|docs?|contrib|deps|vendor|third_party|fuzz\w*|bench\w*|programs)(/|$)", re.I)


def tokens(code, lang):
    if lang == "py":
        code = re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "", code); code = re.sub(r"#[^\n]*", "", code); kw = PKW
    else:
        code = re.sub(r"/\*[\s\S]*?\*/", "", code); code = re.sub(r"//[^\n]*", "", code); kw = CKW
    out = []
    for t in TOK.findall(code):
        c = t[0]
        if c in "\"'": out.append("S")
        elif c.isdigit(): out.append("N")
        elif c.isalpha() or c == "_": out.append(t if t in kw else "I")
        else: out.append(t)
    return out


def do_repo(name):
    out = os.path.join(RES, name + "_funcs.csv")
    if os.path.exists(out): return name
    os.makedirs(RES, exist_ok=True)
    try:
        R = pd.read_csv(os.path.join(DATA, "releases", name + ".csv"), usecols=["vi", "v0"], dtype={"v0": str}).dropna()
    except Exception:
        return name
    repo = os.path.join(REPOS, name + ".git"); rows, prow = [], []
    for vi, tag in zip(R.vi[::EVERY], R.v0[::EVERY]):
        paths = [p for p in __import__("subprocess").run(["git", "-C", repo, "ls-tree", "-r", "--name-only", tag], capture_output=True, text=True).stdout.split("\n") if p and H.is_src(p)]
        F, S = [], []
        for p in paths:
            code = IV.show(repo, tag, p)
            if code is None: continue
            lines = code.split("\n"); lang = H.EXT.get(os.path.splitext(p)[1], "c")
            for fn, d in IV.funcs(repo, tag, p).items():
                if d["e"] - d["s"] + 1 < MINLINES or d["e"] - d["s"] > 700: continue
                tk = tokens("\n".join(lines[d["s"] - 1:d["e"]]), lang)
                if len(tk) < MINTOK: continue
                sh = {hash(tuple(tk[i:i + K])) for i in range(len(tk) - K + 1)}
                F.append((p, fn)); S.append(sh)
        df = Counter(h for s in S for h in s); inv = defaultdict(list)
        for i, s in enumerate(S):
            for h in s:
                if df[h] <= MAXDF: inv[h].append(i)
        best = np.zeros(len(F)); npart = np.zeros(len(F), int); same = np.zeros(len(F), bool); testp = np.array([bool(TESTPATH.search(p)) for p, _ in F]); partner = [""] * len(F)
        seen = set()
        for i, s in enumerate(S):
            cnt = Counter(j for h in s if df[h] <= MAXDF for j in inv[h] if j != i)
            for j, c in cnt.items():
                if c < 0.3 * min(len(s), len(S[j])) or (i, j) in seen: continue
                seen.add((i, j)); seen.add((j, i))
                jac = len(s & S[j]) / len(s | S[j])
                if jac < THR: continue
                prow.append((name, int(vi), F[i][0], F[i][1], F[j][0], F[j][1], round(jac, 3)))
                for a, b in ((i, j), (j, i)):
                    npart[a] += 1
                    if jac > best[a]: best[a] = jac; same[a] = F[a][0] == F[b][0]; partner[a] = F[b][0] + "::" + F[b][1]
        for i, (p, fn) in enumerate(F):
            rows.append((name, int(vi), p, fn, round(best[i], 3), int(npart[i]), int(same[i]), int(testp[i]), partner[i]))
    pd.DataFrame(rows, columns=["repo", "vi", "file", "func", "jmax", "n_partners", "partner_same_file", "test_path", "partner"]).to_csv(out, index=False)
    pd.DataFrame(prow, columns=["repo", "vi", "file_a", "func_a", "file_b", "func_b", "jaccard"]).to_csv(os.path.join(RES, name + "_pairs.csv"), index=False)
    print(name, len(rows), "functions,", len(prow), "clone pairs", flush=True)
    return name


def main():
    names = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(os.path.join(DATA, "releases")) if f.endswith(".csv"))
    names = [n for n in names if os.path.exists(os.path.join(REPOS, n + ".git"))]
    with Pool(3) as p: p.map(do_repo, names, chunksize=1)
    A = [pd.read_csv(os.path.join(RES, n + "_funcs.csv")) for n in names if os.path.exists(os.path.join(RES, n + "_funcs.csv"))]
    B = [pd.read_csv(os.path.join(RES, n + "_pairs.csv")) for n in names if os.path.exists(os.path.join(RES, n + "_pairs.csv")) and os.path.getsize(os.path.join(RES, n + "_pairs.csv")) > 60]
    pd.concat(A).to_csv(os.path.join(RES, "..", "k1_funcs.csv"), index=False); pd.concat(B).to_csv(os.path.join(RES, "..", "k1_pairs.csv"), index=False); print("done")


if __name__ == "__main__":
    main()
