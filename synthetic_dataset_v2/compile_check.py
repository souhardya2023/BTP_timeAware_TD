"""Every release of every v2 project compiles; the smoke script runs at the last release. Writes compile_check.txt"""
import json, os, sys
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "generator"))
import check_project as C
def job(pid):
    try:
        res = C.check(HERE, pid, verbose=False)
        return pid, res
    except Exception as e:
        return pid, "ERROR %s" % e
if __name__ == "__main__":
    ids = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, "manifests")))
    with Pool(3) as p:
        out = dict(p.map(job, ids))
    nrel = sum(len(v) for v in out.values() if isinstance(v, dict))
    fail = sum(1 for v in out.values() if isinstance(v, dict) for ok, _ in v.values() if not ok)
    smoke = {k: [sm for ok, sm in v.values() if sm] for k, v in out.items() if isinstance(v, dict)}
    smoke_bad = {k: x for k, x in smoke.items() if any("SMOKE 0" not in t for t in x)}
    msg = "projects %d, releases %d, compile failures %d, projects whose smoke script reports failures %d\n%s" % (len(out), nrel, fail, len(smoke_bad), json.dumps(smoke_bad, default=str)[:3000])
    open(os.path.join(HERE, "compile_check.txt"), "w").write(msg); print(msg[:600])
