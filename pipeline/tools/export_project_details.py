#!/usr/bin/env python3
"""ONE-TIME export tool that built final_folder/project_dataset and project_with_bugs_dataset from the working folders of the study.
(You do not need it to use the dataset or the pipeline; it documents where everything came from.)

reads   ../dataset                 the 61 pairs (P#_clean, P#_TD, P#_prop) and their injected bugs
        ../repos/<project>.git     bare clones with the full git history
        ../project_vector/out      commit tables and SZZ bug tables
        ../td_interest/out         SonarQube issues of every release (Python projects), version-wise interest transitions
        ../05_Results_and_Datasets the SonarQube scan of the TD folders and the history analysis of the pairs
writes  project_dataset/{Python,C_C++}/P#/{P#_clean,P#_TD,P#_prop}     project_dataset/properties_all_pairs.csv + INDEX.md
        project_dataset/project_details/<project>/...                  git history, SonarQube, properties of every project
        project_with_bugs_dataset/{Python,C_C++}/P#/{P#_clean_bug,P#_TD_bug,P#_bugs}

usage: export_project_details.py WORK_ROOT FINAL_FOLDER        (WORK_ROOT = the BTP_26-27 folder)
"""
import glob
import hashlib
import json
import os
import pickle
import re
import shutil
import subprocess
import sys

import pandas as pd

ROOT, FINAL = (os.path.abspath(x) for x in sys.argv[1:3])
PD, PB = os.path.join(FINAL, "project_dataset"), os.path.join(FINAL, "project_with_bugs_dataset")
LANG = {"Python": "Python", "C_C++": "C/C++"}


def sh(*a, cwd=None):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True).stdout


def prop(t, k):
    m = re.search(rf"(?m)^{k}: (.*)$", t)
    return m.group(1).strip() if m else ""


def pairs():
    for ld in ("Python", "C_C++"):
        d = os.path.join(ROOT, "dataset", ld)
        for p in sorted((x for x in os.listdir(d) if re.fullmatch(r"P\d+", x)), key=lambda x: int(x[1:])):
            yield ld, p, os.path.join(d, p)


# ---------------------------------------------------------------------------------------------------- 1. the two project folders
def copy_projects():
    rows = []
    for ld, p, src in pairs():
        t = open(os.path.join(src, f"{p}_prop", "properties.txt")).read()
        patch = open(os.path.join(src, f"{p}_prop", "td.patch"), errors="ignore").read()
        files = re.findall(r"(?m)^diff --git a/(\S+)", patch)
        # --- project_dataset: clean, TD, prop (without the bugs/ subfolder)
        dst = os.path.join(PD, ld, p)
        if not os.path.exists(dst):
            os.makedirs(dst)
            for s in ("clean", "TD"):
                shutil.copytree(os.path.join(src, f"{p}_{s}"), os.path.join(dst, f"{p}_{s}"), symlinks=True)
            shutil.copytree(os.path.join(src, f"{p}_prop"), os.path.join(dst, f"{p}_prop"), ignore=shutil.ignore_patterns("bugs"))
        # --- project_with_bugs_dataset: the same projects with 3 injected bugs, the same bugs on both sides
        dstb = os.path.join(PB, ld, p)
        if not os.path.exists(dstb):
            os.makedirs(dstb)
            for s in ("clean", "TD"):
                shutil.copytree(os.path.join(src, f"{p}_{s}_bug"), os.path.join(dstb, f"{p}_{s}_bug"), symlinks=True)
            shutil.copytree(os.path.join(src, f"{p}_prop", "bugs"), os.path.join(dstb, f"{p}_bugs"))
        rows.append(dict(
            id=f"{ld}/{p}", language=LANG[ld], project=prop(t, "project"), repository=prop(t, "repository"), base_commit=prop(t, "base_commit"),
            td_type=prop(t, "td_type"), td_subtype=prop(t, "td_subtype"), cwe=prop(t, "cwe"), description=prop(t, "description"), source=prop(t, "source"),
            tier=prop(t, "tier"), files_changed=prop(t, "files_changed"), lines_added=prop(t, "lines_added"), lines_deleted=prop(t, "lines_deleted"),
            changed_files=";".join(files), tests_on_clean=prop(t, "tests_on_clean"), tests_on_TD=prop(t, "tests_on_TD"), test_command=prop(t, "test_command"),
            validation_quality=prop(t, "validation_quality"), static_metric_delta=prop(t, "static_metric_delta \\(TD - clean, non-zero only\\)")))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(PD, "properties_all_pairs.csv"), index=False)
    shutil.copy(os.path.join(ROOT, "dataset", "INDEX.md"), os.path.join(PD, "INDEX.md"))
    return df


# ---------------------------------------------------------------------------------------------------- 2. per-project details
def project_details(df):
    srcs = {k: os.path.join(ROOT, k) for k in ("repos", "project_vector/out", "td_interest/out", "05_Results_and_Datasets")}
    sonar_pairs = pd.read_csv(os.path.join(srcs["05_Results_and_Datasets"], "elaborate_sonarqube_dataset.csv"), keep_default_na=False)
    hist_pairs = pd.read_csv(os.path.join(srcs["05_Results_and_Datasets"], "historical_analysis_all_pairs.csv"), keep_default_na=False)
    for proj, g in df.groupby("project"):
        d = os.path.join(PD, "project_details", proj)
        gh, sq = os.path.join(d, "git_history"), os.path.join(d, "sonarqube")
        os.makedirs(gh, exist_ok=True)
        os.makedirs(sq, exist_ok=True)
        repo = os.path.join(srcs["repos"], os.path.basename(g.repository.iloc[0]) + ".git")
        g.to_csv(os.path.join(d, "pairs.csv"), index=False)
        # ---- git history
        hp = os.path.join(srcs["project_vector/out"], "hist", proj + ".pkl")
        summ = {}
        if os.path.exists(hp):
            h = pickle.load(open(hp, "rb"))
            h = h.assign(author=h.author.map(lambda a: hashlib.sha1(a.encode()).hexdigest()[:10]), files=h.files.map(";".join), date=pd.to_datetime(h.ts, unit="s").dt.strftime("%Y-%m-%d"))
            h[["sha", "date", "ts", "author", "subject", "added", "deleted", "files", "bugfix"]].to_csv(os.path.join(gh, "commits.csv"), index=False)
            summ = dict(commits_non_merge=int(len(h)), first_commit=h.date.min(), last_commit=h.date.max(), authors=int(h.author.nunique()), bug_fix_commits=int(h.bugfix.sum()),
                        lines_added=int(h.added.sum()), lines_deleted=int(h.deleted.sum()))
        tags = [l.split(" ", 1) for l in sh("git", "-C", repo, "for-each-ref", "--sort=creatordate", "--format=%(creatordate:short) %(refname:short) %(objectname)", "refs/tags").strip().split("\n") if l]
        rel = [dict(tag=t.split()[0], date=dte, tag_object=t.split()[1] if len(t.split()) > 1 else "") for dte, t in tags]
        pd.DataFrame(rel).to_csv(os.path.join(gh, "releases.csv"), index=False)
        szz = os.path.join(srcs["project_vector/out"], "bugs", proj + ".csv")
        if os.path.exists(szz):
            shutil.copy(szz, os.path.join(gh, "szz_bugs.csv"))
            b = pd.read_csv(szz)
            summ.update(szz_bugs=int(len(b)), szz_median_bug_lifetime_days=round(float(b.lifetime_days.median()), 1) if len(b) else None)
        summ["release_tags"] = len(rel)
        json.dump(summ, open(os.path.join(gh, "summary.json"), "w"), indent=1)
        # ---- SonarQube
        rdir = os.path.join(srcs["td_interest/out"], "sonar20", proj)
        rows = []
        if os.path.isdir(rdir):
            os.makedirs(os.path.join(sq, "issues_by_release"), exist_ok=True)
            for f in sorted(glob.glob(os.path.join(rdir, "*.json")), key=lambda f: json.load(open(f))["date"]):
                j = json.load(open(f))
                shutil.copy(f, os.path.join(sq, "issues_by_release", os.path.basename(f)))
                sev = pd.Series([i["severity"] for i in j["issues"]]).value_counts().to_dict()
                rows.append(dict(release=j["tag"], date=j["date"], commit=j["commit"], code_smells=len(j["issues"]), **{f"sev_{k.lower()}": v for k, v in sev.items()}))
        if rows:
            pd.DataFrame(rows).fillna(0).astype({c: int for c in pd.DataFrame(rows).columns if c.startswith("sev_") or c == "code_smells"}).to_csv(os.path.join(sq, "releases_summary.csv"), index=False)
        sp = sonar_pairs[sonar_pairs.Project == proj]
        if len(sp):
            sp.to_csv(os.path.join(sq, "scan_of_TD_projects.csv"), index=False)
        iv = os.path.join(srcs["td_interest/out"], "versions", proj + ".csv")
        if os.path.exists(iv):
            shutil.copy(iv, os.path.join(sq, "version_wise_interest.csv"))
        hp2 = hist_pairs[hist_pairs.project == proj]
        if len(hp2):
            hp2.to_csv(os.path.join(gh, "history_interest_of_pairs.csv"), index=False)
        py = g.language.iloc[0] == "Python"
        open(os.path.join(sq, "README.md"), "w").write(
            f"# SonarQube details of {proj}\n\n" + (
                "* `issues_by_release/<tag>.json` - every unresolved code smell SonarQube reported for each release (last 20 release tags, scanned in chronological order, so issue keys are stable from release to release).\n"
                "* `releases_summary.csv` - code smells per release by severity.\n" if py else
                "SonarQube Community has no C/C++ analyzer, so no SonarQube issues exist for this project. The code smells per release come from the structural detector of the study (Long Method nloc>50, Complex Method CCN>10, Many Parameters >5) - see `version_wise_interest.csv`.\n") +
            ("* `scan_of_TD_projects.csv` - SonarQube issues found when the TD projects of this project's pairs were scanned (one row per issue, with the pair, TD type and subtype)." + ("" if py else " Rows with `Sonar_Rule = NONE` mean that nothing could be analysed (no C/C++ analyzer).") + "\n" if len(sp) else "") +
            ("* `version_wise_interest.csv` - the technical-debt instances followed from release to release: classification (interest / increase / repayment), changed lines, COCOMO II effort in person-months.\n" if os.path.exists(iv) else "")
            + "\nSee `../git_history/` for the commit history.\n")
        open(os.path.join(d, "README.md"), "w").write(
            f"# {proj}\n\n* repository: {g.repository.iloc[0]}\n* language: {g.language.iloc[0]}\n* pairs in the dataset: {len(g)} ({', '.join(g.id)})\n"
            f"* base commit(s) of the pairs: {', '.join(sorted(set(c[:10] for c in g.base_commit)))}\n* induced TD types: {({k: int(v) for k, v in g.td_type.value_counts().items()})}\n\n"
            "## Contents\n* `pairs.csv` - one row per pair: TD type and subtype, CWE, description, files and lines changed, validation results (all properties of the pairs)\n"
            "* `git_history/commits.csv` - every non-merge commit (author pseudonymised): date, size, source files touched, bug-fix flag\n"
            "* `git_history/releases.csv` - all release tags; `szz_bugs.csv` - bugs mined with SZZ (fix commit, introducing commit, lifetime in days); `summary.json`\n"
            "* `git_history/history_interest_of_pairs.csv` - earlier historical analysis of the files each pair touches\n"
            "* `sonarqube/` - see its README\n\n"
            f"History summary: {json.dumps(summ)}\n")
    return None


if __name__ == "__main__":
    df = copy_projects()
    project_details(df)
    print(len(df), "pairs exported;", df.project.nunique(), "projects")
