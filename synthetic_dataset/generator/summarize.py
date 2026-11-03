"""projects.csv (one row per project) and instances.csv (one row per debt instance) from the manifests and the transitions."""
import csv, glob, json, os, sys
out = sys.argv[1]
P, I = [], []
for f in sorted(glob.glob(os.path.join(out, "manifests", "*.json"))):
    m = json.load(open(f))
    tr = os.path.join(out, "transitions", m["id"] + ".csv")
    rows = list(csv.DictReader(open(tr))) if os.path.exists(tr) else []
    ev = sum(1 for r in rows if float(r["interest_lines"]) > 0)
    pm = sum(float(r["pm_interest"]) for r in rows)
    P.append(dict(project=m["id"], title=m["title"], domain=m["domain"], domain_source=m["source"], tier=m["tier"], regime=m["regime"], seed=m["seed"],
                  python_files=len(m["modules"]) + 1, loc=m["loc"], releases=m["releases"], commits=len(m["commits"]), major_type=m["major_type"], n_major=m["n_major"],
                  minor_types="+".join(m["minor_types"]), instances=len(m["instances"]), repaid=sum(1 for i in m["instances"] if i["repaid_release"]),
                  frozen_instances=sum(1 for i in m["instances"] if i["frozen"]), interest_events=ev, interest_pm=round(pm, 4)))
    for i in m["instances"]:
        I.append(dict(project=m["id"], instance=i["id"], ptype=i["ptype"], major=int(i["ptype"] == m["major_type"]), template=i["template"], granularity=i["granularity"],
                      region_kind=i["region_kind"], file=i["file"], entity=i["entity"], intro_release=i["intro_release"], intro_commit=i["intro_hash"], parent_commit=i["parent_hash"],
                      mixed=i["mixed"], repaid_release=i["repaid_release"], latent_rate=i["latent_rate"], frozen=i["frozen"], regime=m["regime"], tier=m["tier"]))
for name, rows in (("projects.csv", P), ("instances.csv", I)):
    with open(os.path.join(out, name), "w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(P), "projects", len(I), "instances")
