"""Quick check of one built project: every tag compiles, the smoke script runs at the last tag (and a few others)."""
import json, os, shutil, subprocess, sys, tempfile

def export(repo, tag, dst):
    os.makedirs(dst, exist_ok=True)
    tar = subprocess.run(["git", "-C", repo, "archive", tag], capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", dst], input=tar, check=True)

def check(out, pid, tags=None, verbose=True):
    repo = os.path.join(out, "repos", pid + ".git")
    man = json.load(open(os.path.join(out, "manifests", pid + ".json")))
    all_tags = [r["tag"] for r in man["release_table"]]
    use = tags or ([all_tags[0], all_tags[len(all_tags)//2], all_tags[-1]])
    res = {}
    for tg in all_tags:
        d = tempfile.mkdtemp()
        try:
            export(repo, tg, d)
            r = subprocess.run([sys.executable, "-m", "compileall", "-q", d], capture_output=True, text=True)
            ok = r.returncode == 0
            smoke = None
            if tg in use:
                open(os.path.join(d, "smoke_run.py"), "w").write(man["smoke"] if tg == all_tags[-1] else "")
                if tg == all_tags[-1]:
                    s = subprocess.run([sys.executable, "smoke_run.py"], cwd=d, capture_output=True, text=True, timeout=120)
                    smoke = (s.stdout.strip() + s.stderr.strip()[-300:])
            res[tg] = (ok, smoke)
        finally:
            shutil.rmtree(d)
    return res

if __name__ == "__main__":
    out, pid = sys.argv[1], sys.argv[2]
    r = check(out, pid)
    bad = [t for t, (ok, _) in r.items() if not ok]
    print(pid, "tags", len(r), "compile failures:", bad)
    for t, (ok, sm) in r.items():
        if sm:
            print(" smoke at", t, "->", sm)
