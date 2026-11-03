#!/usr/bin/env python3
"""Run SonarQube on each release of a Python repo and store the unresolved code smells of every version.

The token is read from the environment (SONAR_TOKEN) and is never written to disk.
usage: SONAR_TOKEN=... sonar_versions.py REPO.git OUT_DIR [K]
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from versions import release_versions

HOST = "http://localhost:9000"
EXCL = "**/tests/**,**/test/**,**/docs/**,**/doc/**,**/examples/**,**/scripts/**,**/conftest.py,**/test_*.py,**/*_test.py,**/.github/**,**/artwork/**"


def api(path, token):
    req = urllib.request.Request(HOST + path, headers={"Authorization": "Basic " + base64.b64encode(f"{token}:".encode()).decode()})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def wait_ce(task_id, token, limit=900):
    t0 = time.time()
    while time.time() - t0 < limit:
        st = api(f"/api/ce/task?id={task_id}", token)["task"]["status"]
        if st in ("SUCCESS", "FAILED", "CANCELED"):
            return st
        time.sleep(3)
    return "TIMEOUT"


def issues(key, token):
    out, p = [], 1
    while True:
        d = api(f"/api/issues/search?componentKeys={key}&types=CODE_SMELL&resolved=false&ps=500&p={p}", token)
        out += d["issues"]
        if p * 500 >= d["paging"]["total"] or p >= 20:
            return out
        p += 1


def main():
    repo, out = sys.argv[1], sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    token = os.environ["SONAR_TOKEN"]
    name = os.path.basename(repo).replace(".git", "")
    key = f"{os.environ.get('SONAR_KEY_PREFIX', 'hist2')}-{name}"
    os.makedirs(out, exist_ok=True)
    for tag, commit, date in release_versions(repo, k):
        dst = os.path.join(out, f"{tag}.json")
        if os.path.exists(dst):
            continue
        tmp = tempfile.mkdtemp(prefix=f"sv_{name}_")
        try:
            tar = subprocess.run(["git", "-C", repo, "archive", commit], capture_output=True).stdout
            subprocess.run(["tar", "-x", "-C", tmp], input=tar, check=True)
            props = (f"sonar.projectKey={key}\nsonar.projectName={key}\nsonar.projectVersion={tag}\nsonar.sources=.\n"
                     f"sonar.exclusions={EXCL}\nsonar.inclusions=**/*.py\nsonar.host.url={HOST}\nsonar.sourceEncoding=UTF-8\n")
            open(os.path.join(tmp, "sonar-project.properties"), "w").write(props)
            t0 = time.time()
            env = dict(os.environ, SONAR_SCANNER_OPTS="-Xmx1g")
            r = subprocess.run(["sonar-scanner"], cwd=tmp, env=env, capture_output=True, text=True, timeout=1800)
            if r.returncode:
                print(tag, "scanner failed", r.stdout[-300:], flush=True)
                continue
            rt = dict(l.split("=", 1) for l in open(os.path.join(tmp, ".scannerwork", "report-task.txt")).read().split("\n") if "=" in l)
            st = wait_ce(rt["ceTaskId"], token)
            iss = issues(key, token)
            json.dump(dict(tag=tag, commit=commit, date=date, ce=st, issues=[dict(
                key=i["key"], rule=i["rule"], severity=i["severity"], file=i["component"].split(":", 1)[-1], line=i.get("line"),
                text_range=i.get("textRange"), effort=i.get("effort"), debt=i.get("debt"), message=i.get("message"),
                creation=i.get("creationDate"), tags=i.get("tags"), status=i.get("issueStatus") or i.get("status")) for i in iss]), open(dst, "w"))
            print(f"{tag} {date}: {len(iss)} code smells, {time.time() - t0:.0f}s, ce={st}", flush=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
