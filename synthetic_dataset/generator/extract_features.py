"""133 features (pipeline/extract.py of this repository) of the synthetic code bases.
  python extract_features.py <dataset dir> pairs      parent and child commit of every debt introduction   -> features/pairs_delta.csv  (delta = child - parent, + parent and child vectors)
  python extract_features.py <dataset dir> releases   every release tag of every project                   -> features/releases/<id>.csv   (the project as a time series)
Needs a Python with numpy, pandas, networkx, lizard, bandit, flawfinder (see pipeline/requirements.txt)."""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import warnings
from multiprocessing import Pool

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))


def vec(job):
    repo, ref = job
    from extract import extract
    d = tempfile.mkdtemp()
    try:
        tar = subprocess.run(["git", "-C", repo, "archive", ref], capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", d], input=tar, check=True)
        return ref, extract(d)
    except Exception as e:
        return ref, {"error": str(e)[:80]}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    out, mode = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(out, "features", "releases"), exist_ok=True)
    if mode == "pairs":
        rows = list(csv.DictReader(open(os.path.join(out, "pairs.csv"))))
        jobs = sorted({(os.path.join(out, "repos", r["project"] + ".git"), h) for r in rows for h in (r["parent"], r["child"])})
        with Pool(4) as p:
            V = {ref: v for ref, v in p.imap_unordered(vec, jobs, chunksize=4)}
        names = None
        res = []
        for r in rows:
            a, b = V.get(r["parent"]), V.get(r["child"])
            if not a or not b or "error" in a or "error" in b:
                continue
            names = names or list(a)
            res.append({**{k: r[k] for k in ("project", "instance", "ptype", "template", "granularity", "regime", "tier", "mixed", "files_changed", "lines_added", "lines_deleted")},
                        **{"delta__" + k: b[k] - a[k] for k in names}, **{"parent__" + k: a[k] for k in names}})
        with open(os.path.join(out, "features", "pairs_delta.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, list(res[0]))
            w.writeheader()
            w.writerows(res)
        print("pairs", len(res), "of", len(rows))
    else:
        ids = sorted(f[:-5] for f in os.listdir(os.path.join(out, "manifests")))
        with Pool(4) as p:
            for pid in ids:
                man = json.load(open(os.path.join(out, "manifests", pid + ".json")))
                repo = os.path.join(out, "repos", pid + ".git")
                tags = [r["tag"] for r in man["release_table"]]
                res = dict(p.map(vec, [(repo, t) for t in tags]))
                rows = [{"project": pid, "tag": t, "release": i + 1, **res[t]} for i, t in enumerate(tags) if "error" not in res[t]]
                with open(os.path.join(out, "features", "releases", pid + ".csv"), "w", newline="") as fh:
                    w = csv.DictWriter(fh, list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
                print(pid, len(rows), flush=True)


if __name__ == "__main__":
    main()
