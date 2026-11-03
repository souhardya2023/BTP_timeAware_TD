"""Is the injected debt visible to objective detectors?  complexity: lizard (CCN > 10, NLOC > 50 or > 5 parameters, the thresholds of interest_exp);
security: bandit (any finding inside the function).  concurrency / coupling / dependency have no detector in this audit (reported as such).
usage: python audit_detection.py <dataset dir>   (needs lizard and bandit on the PATH of the Python used)"""
import csv, glob, json, os, subprocess, sys, tempfile
from collections import defaultdict
import lizard

out = sys.argv[1]
man = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(out, "manifests", "*.json"))}
res = defaultdict(lambda: [0, 0])
detail = defaultdict(lambda: [0, 0])
bandit = os.path.join(os.path.dirname(sys.executable), "bandit")
for pid, m in man.items():
    repo = os.path.join(out, "repos", pid + ".git")
    for inst in m["instances"]:
        if inst["ptype"] not in ("complexity", "security") or not inst["intro_hash"]:
            continue
        text = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (inst["intro_hash"], inst["file"])], capture_output=True, text=True).stdout
        funcs = {f.name: f for f in lizard.analyze_file.analyze_source_code("x.py", text).function_list}
        f = funcs.get(inst["quals"][0]) if inst["quals"] else None
        hit = False
        if inst["ptype"] == "complexity":
            hit = bool(f) and (f.cyclomatic_complexity > 10 or f.nloc > 50 or f.parameter_count > 5)
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
                fh.write(text)
            r = subprocess.run([bandit, "-q", "-f", "json", fh.name], capture_output=True, text=True)
            os.unlink(fh.name)
            try:
                issues = json.loads(r.stdout).get("results", [])
            except Exception:
                issues = []
            hit = bool(f) and any(f.start_line <= i["line_number"] <= f.end_line for i in issues)
        res[inst["ptype"]][0] += 1
        res[inst["ptype"]][1] += hit
        detail[inst["template"]][0] += 1
        detail[inst["template"]][1] += hit
lines = ["# Detection audit (the debt is visible to an objective detector?)"]
for t, (n, h) in res.items():
    lines.append("%s: %d of %d instances flagged (%.0f %%)" % (t, h, n, 100 * h / n))
for t, (n, h) in sorted(detail.items()):
    lines.append("  %-22s %3d of %3d flagged" % (t, h, n))
lines.append("concurrency, coupling_cohesion, dependency_structure: not audited (no detector run)")
open(os.path.join(out, "detection_audit.txt"), "w").write("\n".join(lines))
print("\n".join(lines))
