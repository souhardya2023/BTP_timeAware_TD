"""L1-C: put the SAME debt change into OLDER versions of its host project ("time windows" of the history) and re-vectorise.
For every pair: take up to N earlier commits of the host project (release tags if the project has them, else evenly spaced commits),
check out each one, try to apply the pair's td.patch, and compute the 133 features of the clean and the debt version.
Output  results/l1_context_clean.csv   features of the clean project at each (project, commit)
        results/l1_context_td.csv      per (pair, context): patch status and the features of the debt version
Why: (1) the clean series is the NATURAL DRIFT of every feature over time; (2) the patched series are extra, differently hosted copies of the same debt."""
import concurrent.futures as cf
import os
import shutil
import subprocess
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
REPOS = os.path.abspath(os.path.join(ROOT, "..", "repos"))
N_CTX = int(os.environ.get("N_CTX", 5))
PR = pd.read_csv(f"{ROOT}/project_dataset/properties_all_pairs.csv")
NAME = {"C-Thread-Pool": "C-Thread-Pool", "boltons": "boltons", "cJSON": "cJSON", "click": "click", "jansson": "jansson", "jinja": "jinja", "libpng": "libpng", "libyaml": "libyaml", "werkzeug": "werkzeug", "zlib": "zlib"}


def git(repo, *a):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True)
    return r.stdout.decode("utf-8", "replace").strip()


def contexts(project, base):
    repo = f"{REPOS}/{NAME[project]}.git"
    tags = [t for t in git(repo, "tag", "--sort=creatordate").splitlines() if t]
    commits = []
    for t in tags:
        c = git(repo, "rev-list", "-n1", t)
        if c and c != base and subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", c, base], capture_output=True).returncode == 0:
            commits.append(c)
    if len(commits) < N_CTX:                       # no (usable) tags: evenly spaced first-parent commits
        fp = git(repo, "rev-list", "--first-parent", base).splitlines()[1:]
        step = max(1, len(fp) // (N_CTX + 1))
        commits = fp[step::step][:N_CTX] if fp else []
    commits = list(dict.fromkeys(commits))
    if len(commits) > N_CTX:                       # spread over the last releases before the base commit
        tail = commits[-3 * N_CTX:]
        idx = np.linspace(0, len(tail) - 1, N_CTX).round().astype(int)
        commits = [tail[i] for i in idx]
    return commits[::-1]                           # nearest first


def export(project, commit, dst):
    repo = f"{REPOS}/{NAME[project]}.git"
    tar = subprocess.run(["git", "-C", repo, "archive", commit], capture_output=True).stdout
    os.makedirs(dst, exist_ok=True)
    subprocess.run(["tar", "-x", "-C", dst], input=tar, check=True)


def clean_job(a):
    project, commit = a
    from extract import extract
    tmp = tempfile.mkdtemp()
    try:
        export(project, commit, tmp)
        return dict(project=project, commit=commit, **extract(tmp))
    except Exception as e:
        return dict(project=project, commit=commit, error=str(e)[:80])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def td_job(a):
    pid, project, commit, patch, k = a
    from extract import extract
    tmp = tempfile.mkdtemp()
    try:
        export(project, commit, tmp)
        r = subprocess.run(["patch", "-p1", "--fuzz=2", "--no-backup-if-mismatch", "-s", "-f", "-d", tmp, "-i", patch], capture_output=True)
        if r.returncode != 0:
            return dict(id=pid, ctx=k, commit=commit, status="patch_failed")
        return dict(id=pid, ctx=k, commit=commit, status="ok", **extract(tmp))
    except Exception as e:
        return dict(id=pid, ctx=k, commit=commit, status="error:" + str(e)[:60])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ctxs = {}
    for _, r in PR.iterrows():
        n = r.id.split("/")[1]
        ctxs[r.id] = contexts(r.project, r.base_commit)
    print("contexts per pair:", pd.Series({k: len(v) for k, v in ctxs.items()}).describe()[["min", "mean", "max"]].to_dict(), flush=True)
    uniq = sorted({(PR.set_index("id").loc[k].project, c) for k, v in ctxs.items() for c in v})
    print("unique (project, commit) contexts:", len(uniq), flush=True)
    with cf.ProcessPoolExecutor(4) as ex:
        clean = list(ex.map(clean_job, uniq))
    pd.DataFrame(clean).to_csv("../results/l1_context_clean.csv", index=False)
    print("clean features done", flush=True)
    jobs = []
    for _, r in PR.iterrows():
        lang, n = r.id.split("/")
        patch = f"{ROOT}/project_dataset/{'Python' if lang == 'Python' else 'C_C++'}/{n}/{n}_prop/td.patch"
        for k, c in enumerate(ctxs[r.id]):
            jobs.append((r.id, r.project, c, patch, k))
    print("td jobs:", len(jobs), flush=True)
    rows = []
    with cf.ProcessPoolExecutor(4) as ex:
        for i, res in enumerate(ex.map(td_job, jobs)):
            rows.append(res)
            if i % 25 == 0:
                print(i, "/", len(jobs), flush=True)
    pd.DataFrame(rows).to_csv("../results/l1_context_td.csv", index=False)
    print("done", flush=True)
