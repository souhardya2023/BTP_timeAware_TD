#!/usr/bin/env python3
"""Natural pairs for a Level-1 (type of debt change) dataset: small focused commits of the 34 repositories, with a weak type label from the
commit SUBJECT (strict patterns) and the code diff (parent -> commit) as the input.  The classifier never sees the subject.

writes results/b1_pairs.csv (one row per pair), results/b1_diffs.jsonl (diff text), results/b1_label_check.csv (a random sample for checking by hand)
usage: b1_natural_pairs.py [REPOS_DIR]
"""
import glob, json, os, re, subprocess, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(ROOT)), "repos")
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "interest_exp", "code"))
import history as H

LABEL = {   # strict subject patterns (an approximation; see results/b1_label_check.csv)
    "security": re.compile(r"cve-\d|use[- ]after[- ]free|heap[- ]?(buffer|overflow)|buffer overflow|stack overflow|integer overflow|out[- ]of[- ]bounds|injection|sanitiz|path traversal|vulnerab|\bxss\b|\bcsrf\b|untrusted|memory leak|double[- ]free|null pointer|denial of service|\bdos\b", re.I),
    "concurrency": re.compile(r"\brace\b|race condition|deadlock|mutex|\batomic|thread[- ]?safe|thread safety|\blocking\b|\block\b|synchroni[sz]|concurren", re.I),
    "dependency": re.compile(r"circular|cyclic|import cycle|\bimport(s|ed)?\b|dependenc(y|ies)|\binclude(s|d)?\b", re.I),
    "coupling": re.compile(r"decoupl|\bcoupl|\bextract(ed)?\b|encapsulat|abstraction|\binherit|\bprivate\b|split out|move[sd]? (the )?\w+ (to|into|out)", re.I),
    "complexity": re.compile(r"simplif|complex|refactor|clean ?up|deduplicat|duplicate|reduce", re.I),
}
NOISE = re.compile(r"\bdocs?\b|documentation|typo|changelog|readme|\bci\b|\bversion\b|bump|release notes|test(s|ing)? only|merge|^revert", re.I)
KEYS = ["lock", "mutex", "thread", "atomic", "volatile", "sync", "async", "await", "memcpy", "strcpy", "sprintf", "snprintf", "malloc", "free", "sizeof", "len", "size", "bounds", "check", "assert", "eval",
        "exec", "subprocess", "pickle", "escape", "quote", "sanitize", "path", "import", "include", "from", "require", "class", "def", "self", "static", "return", "raise", "error", "null", "None", "if", "else", "for", "while"]


def diff_text(repo, par, sha, paths):
    t = subprocess.run(["git", "-C", repo, "diff", "-U0", "-M", "--no-color", par, sha, "--", *paths], capture_output=True).stdout.decode("utf-8", "replace")
    add, rem = [], []
    for l in t.split("\n"):
        if l.startswith("+") and not l.startswith("+++"):
            add.append(l[1:])
        elif l.startswith("-") and not l.startswith("---"):
            rem.append(l[1:])
    return add, rem


def main():
    C = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(ROOT, "data", "commits", "*.csv")))], ignore_index=True)
    C["lines"] = C.src_added + C.src_deleted
    C = C[(C.bulk == 0) & (C.lines >= 2) & (C.lines <= 80) & (C.src_files <= 3)]
    C = C[~C.subject.str.contains(NOISE)]
    for k, rx in LABEL.items():
        C["l_" + k] = C.subject.map(lambda s: bool(rx.search(s)))
    C["nl"] = C[["l_" + k for k in LABEL]].sum(axis=1)
    C = C[C.nl == 1].copy()
    C["label"] = C[["l_" + k for k in LABEL]].idxmax(axis=1).str[2:]
    # full subjects and file lists from git
    rows, out = [], open(os.path.join(ROOT, "results", "b1_diffs.jsonl"), "w")
    for repo, g in C.groupby("repo"):
        rp = os.path.join(REPOS, repo + ".git")
        full = subprocess.run(["git", "-C", rp, "log", "--no-merges", "--format=%H|%P|%s", "-n", "3000"], capture_output=True, text=True).stdout.split("\n")
        idx = {l.split("|")[0][:10]: l for l in full if l}
        for _, r in g.iterrows():
            ln = idx.get(r.sha)
            if not ln:
                continue
            sha, par, _ = ln.split("|", 2)
            par = par.split()[0] if par.split() else None
            if not par:
                continue
            files = subprocess.run(["git", "-C", rp, "diff", "--name-only", par, sha], capture_output=True, text=True).stdout.split()
            src = [f for f in files if H.is_src(f)]
            if not src:
                continue
            add, rem = diff_text(rp, par, sha, src)
            txt = "\n".join(["+" + a for a in add] + ["-" + a for a in rem])
            if len(txt.strip()) < 10:
                continue
            words = re.findall(r"[A-Za-z_]+", txt)
            cnt = {("k_" + k): sum(1 for w in words if w.lower() == k.lower()) for k in KEYS}
            impl = [l for l in add + rem if re.match(r"\s*(import\s|from\s+\S+\s+import|#\s*include|require\b|use\s)", l)]
            rows.append(dict(imp_frac=round(len(impl) / max(1, len(add) + len(rem)), 3), repo=repo, sha=r.sha, date=r.date, label=r.label, subject=r.subject, lines=int(r.lines), files=len(src), added=len(add), removed=len(rem),
                             funcs_changed=int(r.funcs_changed), smell_touched=int(r.smell_touched), bugfix=int(r.bugfix), lang="python" if src[0].endswith(".py") else "c", **cnt))
            out.write(json.dumps(dict(repo=repo, sha=r.sha, text=txt[:6000])) + "\n")
    out.close()
    D = pd.DataFrame(rows)
    CF = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(ROOT, "data", "commit_funcs", "*.csv")))], ignore_index=True)
    D["debt_event"] = D.set_index(["repo", "sha"]).index.isin(CF.set_index(["repo", "sha"]).index)
    sec_tok = ["check", "bounds", "free", "sizeof", "size", "len", "escape", "quote", "sanitize", "null", "None", "assert", "memcpy", "strcpy", "snprintf"]
    D["dual_ok"] = (((D.label == "concurrency") & (D[["k_lock", "k_mutex", "k_thread", "k_atomic", "k_volatile", "k_sync", "k_async", "k_await"]].sum(axis=1) > 0)) |
                    ((D.label == "security") & (D[["k_" + t for t in sec_tok if "k_" + t in D.columns]].sum(axis=1) > 0)) |
                    ((D.label == "dependency") & (D.imp_frac >= 0.5)) |
                    ((D.label == "complexity") & D.debt_event & (D.funcs_changed >= 1)))
    D.loc[D.label == "coupling", "dual_ok"] = False                  # keyword labels of coupling were too imprecise (4 of 12 right in a manual look): not used
    D.to_csv(os.path.join(ROOT, "results", "b1_pairs.csv"), index=False)
    print(len(D), D.label.value_counts().to_dict(), "repos", D.repo.nunique(), "| dual-evidence:", D[D.dual_ok].label.value_counts().to_dict(), "repos", D[D.dual_ok].repo.nunique())
    chk = D.groupby("label").sample(n=12, random_state=11)[["label", "repo", "sha", "subject", "lines"]]
    chk.to_csv(os.path.join(ROOT, "results", "b1_label_check.csv"), index=False)
    for k, g in chk.groupby("label"):
        print("==", k)
        for s in g.subject:
            print("   ", s[:100])


if __name__ == "__main__":
    main()
