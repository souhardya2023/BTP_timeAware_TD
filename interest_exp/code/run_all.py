#!/usr/bin/env python3
"""Run the whole interest experiment, step by step.

steps (in this order; choose with --steps a,b,c; default = all):
  transitions   version-wise interest of every instance: SonarQube issues (Python projects) / structural smells (C/C++)   -> data/transitions/<project>.csv
  structural    the same for the Python projects with the structural detector (detector comparison)                      -> data/transitions_structural/
  snapshots     function-level snapshots from the commit history (next 100 commits)                                      -> data/snapshots/
  models        next-release classification, person-month regression, function-level model                              -> results/*.csv
  pairs         the interest model applied to the 61 dataset pairs                                                       -> results/pair_scores.csv
  analysis      descriptive tables (per project / release / rule, principal vs interest, sensitivity)                    -> results/tables/
  reeval        re-evaluation of the first prediction model                                                              -> results/tables/
  report        write the result documents                                                                               -> results/*.md

usage: run_all.py [--repos DIR] [--steps transitions,models,...] [--workers 3]
The repositories (bare clones with full history) come from `clone_repos.sh`; the SonarQube issues of every release of the Python projects are read from
../../project_dataset/project_details/<project>/sonarqube/issues_by_release (to re-scan with a SonarQube server use sonar_versions.py).
"""
import argparse
import concurrent.futures as cf
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
FINAL = os.path.dirname(EXP)
PD = os.path.join(FINAL, "project_dataset")
DATA, RES = os.path.join(EXP, "data"), os.path.join(EXP, "results")
PY = sys.executable
PYTHON_PROJECTS = ["boltons", "click", "jinja", "werkzeug"]
C_PROJECTS = ["cJSON", "jansson", "libpng", "libyaml", "zlib"]
ALL = {"transitions", "structural", "snapshots", "models", "pairs", "analysis", "reeval", "report"}


def run(cmd, **kw):
    r = subprocess.run([PY] + cmd, cwd=HERE, capture_output=True, text=True, **kw)
    tail = (r.stdout or r.stderr).strip().splitlines()[-1:] if (r.stdout or r.stderr) else [""]
    print(("ok   " if r.returncode == 0 else "FAIL ") + " ".join(map(os.path.basename, cmd[:2])), tail[0][:150], flush=True)
    if r.returncode:
        print(r.stderr[-800:])
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", default=os.environ.get("INTEREST_REPOS", os.path.join(os.path.dirname(FINAL), "repos")))
    ap.add_argument("--steps", default=",".join(sorted(ALL)))
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--k", type=int, default=20, help="number of release tags per project")
    ap.add_argument("--window", type=int, default=700, help="commits per project for the function-level snapshots")
    a = ap.parse_args()
    steps = set(a.steps.split(","))
    repos = os.path.abspath(a.repos)
    jobs = []
    if "transitions" in steps:
        os.makedirs(os.path.join(DATA, "transitions"), exist_ok=True)
        for p in PYTHON_PROJECTS + C_PROJECTS:
            c = ["interest_versions.py", os.path.join(repos, p + ".git"), os.path.join(DATA, "transitions", p + ".csv"), "--k", str(a.k)]
            if p in PYTHON_PROJECTS:
                c += ["--sonar", os.path.join(PD, "project_details", p, "sonarqube", "issues_by_release")]
            jobs.append(c)
    if "structural" in steps:
        os.makedirs(os.path.join(DATA, "transitions_structural"), exist_ok=True)
        for p in PYTHON_PROJECTS:
            jobs.append(["interest_versions.py", os.path.join(repos, p + ".git"), os.path.join(DATA, "transitions_structural", p + ".csv"), "--k", str(a.k)])
    if "snapshots" in steps:
        os.makedirs(os.path.join(DATA, "snapshots"), exist_ok=True)
        for p in PYTHON_PROJECTS + C_PROJECTS + ["C-Thread-Pool"]:
            jobs.append(["history.py", os.path.join(repos, p + ".git"), os.path.join(DATA, "snapshots", p), "--window", str(a.window)])
    if jobs:
        with cf.ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(run, jobs))
    seq = []
    if "models" in steps:
        seq += [["model_next_release.py", DATA, RES], ["model_pm.py", DATA, RES], ["model_snapshots.py", DATA, RES]]
    if "pairs" in steps:
        seq += [["score_pairs.py", PD, repos, DATA, RES]]
    if "analysis" in steps:
        seq += [["analysis_tables.py", DATA, RES]]
    if "reeval" in steps:
        seq += [["reeval_first_model.py", DATA, RES]]
    if "report" in steps:
        seq += [["build_report.py"]]
    for c in seq:
        run(c)


if __name__ == "__main__":
    main()
