#!/usr/bin/env python3
"""Export everything a SonarQube server holds about its projects into plain files.

For every project on the server (http://localhost:9000/projects):
  projects.csv     key, name, quality gate, number of issues, date of the first and of the last issue change, and which dataset pair / project the key belongs to (see mapping below)
  measures.csv     one row per project: lines of code, bugs, vulnerabilities, code smells, technical debt (sqale_index, minutes), ratings, duplication, complexity ...
  issues/<key>.csv every issue of the project (rule, severity, type, status, file, line, message, effort, tags, dates, clean-code attribute, impacts)
  issues_all.csv   the same, all projects together (column project_key)
  hotspots.csv     security hotspots
  rules.csv        the rules that appear in the issues (name, language, type, default severity, tags, short description)
  metrics.csv      definition of the exported measures
  server_info.json server version, export date
The access token is read from the environment variable SONAR_TOKEN and is never written to disk.
(The token of the study has no permission for the analysis-history endpoints, so analysis dates are not exported; the release dates of the release scans are in project_details/<project>/sonarqube/.)

mapping of a project key to the dataset (mapping.method in projects.csv)
  Python-P<n>-TD, werkzeug-P<n>-TD   pair `Python/P<n>`   (key made by the scan script of the study)
  P<n>_TD                            Python P<n> or C/C++ P<n> (the folder name was used as the key): decided by which dataset TD folder contains the files that carry the issues
  hist-<project>, hist2-<project>    release-by-release scans of a project (hist2: last 20 releases scanned in chronological order)
  anything else                      not part of the dataset (BTP, search-o-SAURS)

usage: SONAR_TOKEN=... export_sonarqube_server.py OUT_DIR PROJECT_DATASET_DIR [--host http://localhost:9000]
"""
import base64
import csv
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

import pandas as pd

OUT, PD = (os.path.abspath(x) for x in sys.argv[1:3])
HOST = sys.argv[sys.argv.index("--host") + 1] if "--host" in sys.argv else "http://localhost:9000"
TOKEN = os.environ["SONAR_TOKEN"]
H = {"Authorization": "Basic " + base64.b64encode(f"{TOKEN}:".encode()).decode()}
METRICS = ("ncloc,lines,files,functions,classes,statements,comment_lines,comment_lines_density,complexity,cognitive_complexity,duplicated_lines,duplicated_lines_density,duplicated_blocks,"
           "duplicated_files,bugs,vulnerabilities,security_hotspots,code_smells,violations,sqale_index,sqale_debt_ratio,sqale_rating,reliability_rating,security_rating,"
           "reliability_remediation_effort,security_remediation_effort,alert_status,new_technical_debt,software_quality_maintainability_issues,software_quality_reliability_issues,"
           "software_quality_security_issues,software_quality_maintainability_remediation_effort,software_quality_maintainability_rating").split(",")


def api(path, **q):
    url = HOST + path + ("?" + urllib.parse.urlencode(q) if q else "")
    try:
        return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=120).read().decode())
    except Exception as e:
        return {"_error": str(e)[:150]}


def paged(path, key, **q):
    out, p = [], 1
    while True:
        d = api(path, ps=500, p=p, **q)
        if "_error" in d:
            return out
        out += d.get(key, [])
        total = d.get("paging", {}).get("total", d.get("total", len(out)))
        if p * 500 >= total or p >= 20:
            return out
        p += 1


def main():
    os.makedirs(os.path.join(OUT, "issues"), exist_ok=True)
    comps = paged("/api/components/search_projects", "components")
    keys = sorted(c["key"] for c in comps)
    # --- TD folders of the dataset, to decide P<n>_TD keys
    td_files = {}
    for ld in ("Python", "C_C++"):
        for p in os.listdir(os.path.join(PD, ld)):
            if re.fullmatch(r"P\d+", p):
                root = os.path.join(PD, ld, p, f"{p}_TD")
                td_files[f"{ld}/{p}"] = root
    props = pd.read_csv(os.path.join(PD, "properties_all_pairs.csv"), keep_default_na=False, dtype=str).set_index("id")
    prows, mrows, irows, hrows, rule_keys = [], [], [], [], set()
    byk = {c["key"]: c for c in comps}
    for key in keys:
        comp = byk[key]
        ms = api("/api/measures/component", component=key, metricKeys=",".join(METRICS)).get("component", {}).get("measures", [])
        mrow = {"project_key": key, **{m["metric"]: m.get("value", (m.get("period") or {}).get("value", "")) for m in ms}}
        mrows.append(mrow)
        gate = api("/api/qualitygates/project_status", projectKey=key).get("projectStatus", {}).get("status", "")
        iss = paged("/api/issues/search", "issues", componentKeys=key)
        rows = []
        for i in iss:
            rule_keys.add(i["rule"])
            rows.append(dict(project_key=key, issue_key=i["key"], rule=i["rule"], severity=i.get("severity", ""), type=i.get("type", ""), status=i.get("issueStatus") or i.get("status", ""),
                             file=i["component"].split(":", 1)[-1], line=i.get("line", ""), start_line=(i.get("textRange") or {}).get("startLine", ""), end_line=(i.get("textRange") or {}).get("endLine", ""),
                             message=i.get("message", ""), effort=i.get("effort", ""), debt=i.get("debt", ""), clean_code_attribute=i.get("cleanCodeAttribute", ""),
                             impacts="; ".join(f"{x['softwareQuality']}:{x['severity']}" for x in i.get("impacts", [])), tags=",".join(i.get("tags", [])),
                             creation_date=i.get("creationDate", ""), update_date=i.get("updateDate", ""), author=("" if not i.get("author") else "pseudonymised")))
        pd.DataFrame(rows).to_csv(os.path.join(OUT, "issues", f"{key}.csv"), index=False)
        irows += rows
        for h in paged("/api/hotspots/search", "hotspots", projectKey=key):
            hrows.append(dict(project_key=key, hotspot_key=h["key"], rule=h.get("ruleKey", ""), vulnerability_probability=h.get("vulnerabilityProbability", ""), status=h.get("status", ""),
                              file=h["component"].split(":", 1)[-1], line=h.get("line", ""), message=h.get("message", "")))
        # --- mapping to the dataset
        m = re.fullmatch(r"(Python)-P(\d+)-TD", key) or re.fullmatch(r"(werkzeug)-P(\d+)-TD", key)
        pair, method, project = "", "not part of the dataset", ""
        if m:
            pair, method = f"Python/P{m.group(2)}", "key pattern"
        elif re.fullmatch(r"P\d+_TD", key):
            n = key[1:].split("_")[0]
            best, score = "", -1
            files = {r["file"] for r in rows if not r["file"].endswith(("test.c",))}
            for cand in (f"Python/P{n}", f"C_C++/P{n}"):
                if cand in td_files and files:
                    s = sum(os.path.exists(os.path.join(td_files[cand], f)) for f in files) / len(files)
                    if s > score:
                        best, score = cand, s
            if best and score >= 0.5:
                pair, method = best, f"issue files found in the TD folder ({score:.0%})"
            else:
                pair, method = "", f"ambiguous: Python P{n} or C/C++ P{n} (no issue file matches)"
        m2 = re.fullmatch(r"hist2?-(.+)", key)
        if m2:
            project, method = m2.group(1), "release-by-release scan"
        if pair in props.index:
            project = props.loc[pair, "project"]
        prows.append(dict(project_key=key, name=comp.get("name", key), visibility=comp.get("visibility", ""), quality_gate=gate, issues_exported=len(rows),
                          first_issue_date=min((r["creation_date"] for r in rows), default="")[:10], last_issue_update=max((r["update_date"] for r in rows), default="")[:10], dataset_pair=pair, dataset_project=project, td_type=props.loc[pair, "td_type"] if pair in props.index else "", mapping=method))
    pd.DataFrame(prows).to_csv(os.path.join(OUT, "projects.csv"), index=False)
    pd.DataFrame(mrows).to_csv(os.path.join(OUT, "measures.csv"), index=False)
    pd.DataFrame(irows).to_csv(os.path.join(OUT, "issues_all.csv"), index=False)
    pd.DataFrame(hrows).to_csv(os.path.join(OUT, "hotspots.csv"), index=False)
    rr = []
    for rk in sorted(rule_keys):
        r = api("/api/rules/show", key=rk).get("rule", {})
        rr.append(dict(rule=rk, name=r.get("name", ""), language=r.get("langName", r.get("lang", "")), type=r.get("type", ""), severity=r.get("severity", ""), tags=",".join(r.get("sysTags", [])),
                       remediation=r.get("remFnBaseEffort", ""), description=re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.get("htmlDesc", "") or (r.get("descriptionSections") or [{}])[0].get("content", "")))[:400].strip()))
    pd.DataFrame(rr).to_csv(os.path.join(OUT, "rules.csv"), index=False)
    md = api("/api/metrics/search", ps=500).get("metrics", [])
    pd.DataFrame([dict(metric=x["key"], name=x.get("name", ""), type=x.get("type", ""), domain=x.get("domain", ""), description=x.get("description", "")) for x in md if x["key"] in METRICS]).to_csv(os.path.join(OUT, "metrics.csv"), index=False)
    json.dump(dict(server=api("/api/system/status"), exported=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), host=HOST, projects=len(keys), issues=len(irows)), open(os.path.join(OUT, "server_info.json"), "w"), indent=1)
    print(len(keys), "projects,", len(irows), "issues,", len(hrows), "hotspots,", len(rr), "rules")


if __name__ == "__main__":
    main()
