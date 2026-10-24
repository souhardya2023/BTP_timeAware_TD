#!/usr/bin/env python3
"""From project pairs to the machine-learning input.

  build   read the pairs of ../project_dataset and the bugged projects of ../project_with_bugs_dataset, vectorise every project (extract.py),
          assign the fix times (time model in bug_injection/sample_times.py), and write ../out_dataset/{full,delta_only}/dataset_with_time.csv and dataset_without_time.csv
  inject  put 3 bugs into every pair that has none yet (bug_injection/inject_bugs.py)
  add     add a NEW pair (clean project folder + TD project folder + its TD type): copies it into ../project_dataset, injects bugs, rebuilds the dataset
  times   merge MEASURED fix times (replaces the model values)

the model input   target = td_type (one of 5 classes);   features = every column after `label`
  out_dataset/full/        dataset_with_time.csv  features = time_diff_min + clean__* + td__* + delta__*      dataset_without_time.csv = the same without time_diff_min
  out_dataset/delta_only/  dataset_with_time.csv  features = time_diff_min + delta__*                       dataset_without_time.csv = the same without time_diff_min
usage: make_dataset.py build [--workers 3]
       make_dataset.py inject
       make_dataset.py add --lang Python|C_C++ --clean DIR --td DIR --td-type TYPE [--td-subtype S] [--project NAME] [--repository URL] [--base-commit SHA] [--no-build]
       make_dataset.py times FILLED.csv           (columns: id, bug, clean_min, td_min)
"""
import argparse
import concurrent.futures as cf
import difflib
import json
import os
import random
import re
import shutil
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)
PROJECTS, BUGGED, OUT = (os.path.join(FINAL, d) for d in ("project_dataset", "project_with_bugs_dataset", "out_dataset"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "bug_injection"))
TD_TYPES = ["complexity", "concurrency", "coupling_cohesion", "dependency_structure", "security"]
LABEL = {t: i for i, t in enumerate(TD_TYPES)}
RULES = [
    (r"^s_files$|^s_dirs$|^s_files_per_dir|^s_depth|^s_file_|^s_share_", "directory layout and file sizes"),
    (r"^s_graph_|^s_cyc_|^s_fan_|^s_instability|^s_isolated|^s_dep_depth|^s_weak|^s_clustering|^s_modularity|^s_communities|^s_assort|^s_pagerank|^s_spec_", "dependency graph (imports / #includes)"),
    (r"^c_loc|^c_sloc|^c_comment|^c_blank|^c_file_sloc|^c_big_files|^c_indent", "lines of code, comments, file sizes, indentation"),
    (r"^c_functions|^c_funcs_per|^c_fn_", "functions: count, size, cyclomatic complexity, parameters, tokens"),
    (r"^c_py_", "Python idioms"), (r"^c_c_", "C idioms"),
    (r"^t_long|^t_complex|^t_many|^t_params|^t_smell|^t_very|^t_huge|^t_large|^t_principal", "code smells and their principal (COCOMO II)"),
    (r"^t_god|^t_lcom", "class cohesion"), (r"^t_satd", "self-admitted debt in comments"), (r"^t_dup", "duplicated code"),
    (r"^t_sec|^t_guards", "security findings and validation guards"), (r"^t_conc", "concurrency idioms"),
]


def prop_rows():
    return pd.read_csv(os.path.join(PROJECTS, "properties_all_pairs.csv"), keep_default_na=False, dtype=str)


def pair_dirs(pid):
    ld, p = pid.split("/")
    return os.path.join(PROJECTS, ld, p), os.path.join(BUGGED, ld, p), p


def _extract(folder):
    from extract import extract
    return extract(folder)


def assign_folds(df):
    """fold: stratified by td_type (5 folds);  fold_by_project: whole projects per fold (no project is in two folds)"""
    rng = random.Random(42)
    fold = pd.Series(0, index=df.index)
    for t, g in df.groupby("td_type"):
        idx = list(g.index)
        rng.shuffle(idx)
        for k, i in enumerate(idx):
            fold[i] = k % 5
    load, pf = [0] * 5, {}
    for proj, n in df.project.value_counts().items():
        f = load.index(min(load))
        pf[proj] = f
        load[f] += n
    return fold, df.project.map(pf)


def cmd_build(a):
    from sample_times import sample_bug_times
    P = prop_rows()
    jobs = []
    for pid in P.id:
        src, bsrc, p = pair_dirs(pid)
        if not os.path.isdir(os.path.join(bsrc, f"{p}_clean_bug")):
            sys.exit(f"{pid} has no bugged project - run `make_dataset.py inject` first")
        jobs += [os.path.join(bsrc, f"{p}_clean_bug"), os.path.join(bsrc, f"{p}_TD_bug")]
    print(len(P), "pairs ->", len(jobs), "projects to vectorise", flush=True)
    with cf.ProcessPoolExecutor(a.workers) as ex:
        feats = list(ex.map(_extract, jobs))
    old = pd.read_csv(os.path.join(OUT, "bugs.csv"), keep_default_na=False, dtype=str).set_index(["id", "bug"]) if os.path.exists(os.path.join(OUT, "bugs.csv")) else None
    brows = []
    for _, r in P.iterrows():
        bj = json.load(open(os.path.join(pair_dirs(r.id)[1], f"{pair_dirs(r.id)[2]}_bugs", "bugs.json")))
        for b in bj:
            c, t = sample_bug_times(r.id, b["bug"], r.td_type, b["in_td_file"])
            src = "sample"
            if old is not None and (r.id, b["bug"]) in old.index and old.loc[(r.id, b["bug"]), "time_source"] == "measured":
                c, t, src = float(old.loc[(r.id, b["bug"]), "clean_min"]), float(old.loc[(r.id, b["bug"]), "td_min"]), "measured"
            brows.append(dict(id=r.id, bug=b["bug"], td_type=r.td_type, kind=b["kind"], file=b["file"], function=b["function"], line=b["line"], description=b["description"],
                              in_td_file=b["in_td_file"], clean_min=c, td_min=t, diff_min=round(t - c, 1), time_source=src))
    B = pd.DataFrame(brows)
    rows = []
    for k, (_, r) in enumerate(P.iterrows()):
        fc, ft = feats[2 * k], feats[2 * k + 1]
        g = B[B.id == r.id]
        row = dict(id=r.id, project=r.project, language=r.language, td_type=r.td_type, label=LABEL[r.td_type], time_diff_min=round(float(g.diff_min.sum()), 1))
        row.update({f"clean__{n}": fc[n] for n in fc})
        row.update({f"td__{n}": ft.get(n, 0.0) for n in fc})
        row.update({f"delta__{n}": ft.get(n, 0.0) - fc[n] for n in fc})
        rows.append(row)
    D = pd.DataFrame(rows)
    D.insert(3, "fold", assign_folds(D)[0])
    D.insert(4, "fold_by_project", assign_folds(D)[1])
    meta = ["id", "project", "language", "fold", "fold_by_project", "td_type", "label"]
    feat = [c for c in D.columns if c not in meta]
    for variant, keep in (("full", lambda c: True), ("delta_only", lambda c: c == "time_diff_min" or c.startswith("delta__"))):
        vd = os.path.join(OUT, variant)
        os.makedirs(vd, exist_ok=True)
        cols = [c for c in feat if keep(c)]
        D[meta + cols].to_csv(os.path.join(vd, "dataset_with_time.csv"), index=False, float_format="%.6g")
        D[meta + [c for c in cols if c != "time_diff_min"]].to_csv(os.path.join(vd, "dataset_without_time.csv"), index=False, float_format="%.6g")
    B.to_csv(os.path.join(OUT, "bugs.csv"), index=False)
    names = list(feats[0])
    desc = lambda n: next((d for rx, d in RULES if re.search(rx, n)), "")
    pd.DataFrame([dict(feature=n, block={"s": "structure", "c": "code", "t": "technical_debt"}[n[0]], what=desc(n)) for n in names]).to_csv(os.path.join(OUT, "feature_dictionary.csv"), index=False)
    json.dump({"meta_columns_not_features": ["id", "project", "language", "fold", "fold_by_project", "td_type", "label"], "target": "td_type (or the integer `label`)",
               "time_feature": ["time_diff_min"], "clean_project_features": [f"clean__{n}" for n in names], "td_project_features": [f"td__{n}" for n in names],
               "difference_features": [f"delta__{n}" for n in names]}, open(os.path.join(OUT, "feature_groups.json"), "w"), indent=1)
    json.dump(LABEL, open(os.path.join(OUT, "label_map.json"), "w"), indent=1)
    print(f"{len(D)} datapoints; full: {1 + 3 * len(names)} features with time / {3 * len(names)} without; delta_only: {1 + len(names)} / {len(names)}; target td_type {({k: int(v) for k, v in D.td_type.value_counts().items()})}")


def cmd_inject(a):
    from inject_bugs import inject_pair
    P = prop_rows()
    for pid in P.id:
        src, bsrc, p = pair_dirs(pid)
        if not os.path.isdir(os.path.join(bsrc, f"{p}_clean_bug")):
            meta = inject_pair(src, bsrc, p, pid)
            print(pid, len(meta), "bugs")


def cmd_add(a):
    P = prop_rows()
    ld = a.lang
    n = 1 + max([int(x[1:]) for x in os.listdir(os.path.join(PROJECTS, ld)) if re.fullmatch(r"P\d+", x)] + [0])
    p = f"P{n}"
    dst = os.path.join(PROJECTS, ld, p)
    ig = shutil.ignore_patterns(".git")
    shutil.copytree(a.clean, os.path.join(dst, f"{p}_clean"), ignore=ig, symlinks=True)
    shutil.copytree(a.td, os.path.join(dst, f"{p}_TD"), ignore=ig, symlinks=True)
    os.makedirs(os.path.join(dst, f"{p}_prop"))
    from mutate import patch_of
    patch, files = "", []
    for dp, _, fn in os.walk(os.path.join(dst, f"{p}_TD")):
        for f in fn:
            t = os.path.join(dp, f)
            rel = os.path.relpath(t, os.path.join(dst, f"{p}_TD"))
            c = os.path.join(dst, f"{p}_clean", rel)
            if os.path.exists(c) and open(c, "rb").read() != open(t, "rb").read():
                patch += f"diff --git a/{rel} b/{rel}\n" + patch_of(rel, open(c, encoding="utf-8", errors="ignore").read(), open(t, encoding="utf-8", errors="ignore").read())
                files.append(rel)
    open(os.path.join(dst, f"{p}_prop", "td.patch"), "w").write(patch)
    project = a.project or os.path.basename(os.path.abspath(a.clean))
    row = dict(id=f"{ld}/{p}", language="Python" if ld == "Python" else "C/C++", project=project, repository=a.repository or "", base_commit=a.base_commit or "", td_type=a.td_type,
               td_subtype=a.td_subtype or "", cwe="", description="added with make_dataset.py add", source="user supplied", tier="main", files_changed=str(len(files)),
               lines_added="", lines_deleted="", changed_files=";".join(files), tests_on_clean="", tests_on_TD="", test_command="", validation_quality="not validated", static_metric_delta="")
    pd.concat([P, pd.DataFrame([row])], ignore_index=True).to_csv(os.path.join(PROJECTS, "properties_all_pairs.csv"), index=False)
    cmd_inject(a)
    print("added", row["id"], f"({len(files)} files differ between the clean and the TD project)")
    if not a.no_build:
        a.workers = 3
        cmd_build(a)


def cmd_times(a):
    B = pd.read_csv(os.path.join(OUT, "bugs.csv"), keep_default_na=False, dtype=str)
    T = pd.read_csv(a.file, keep_default_na=False, dtype=str)
    n = 0
    for _, r in T.iterrows():
        c, t = pd.to_numeric(r.get("clean_min", ""), errors="coerce"), pd.to_numeric(r.get("td_min", ""), errors="coerce")
        m = (B.id == r["id"]) & (B.bug == r["bug"])
        if pd.isna(c) or pd.isna(t) or not m.any():
            continue
        B.loc[m, ["clean_min", "td_min", "diff_min", "time_source"]] = [str(c), str(t), str(round(t - c, 1)), "measured"]
        n += 1
    B.to_csv(os.path.join(OUT, "bugs.csv"), index=False)
    for f in (os.path.join("full", "dataset_with_time.csv"), os.path.join("delta_only", "dataset_with_time.csv")):
        D = pd.read_csv(os.path.join(OUT, f), keep_default_na=False, dtype=str)
        for i, g in B.groupby("id"):
            D.loc[D.id == i, "time_diff_min"] = str(round(pd.to_numeric(g.diff_min).sum(), 1))
        D.to_csv(os.path.join(OUT, f), index=False)
    print(f"merged measured times for {n} bugs into out_dataset/bugs.csv and both dataset_with_time.csv files")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = ap.add_subparsers(dest="cmd", required=True)
    b = s.add_parser("build"); b.add_argument("--workers", type=int, default=3)
    s.add_parser("inject")
    d = s.add_parser("add")
    for x in ("--lang", "--clean", "--td", "--td-type"):
        d.add_argument(x, required=True)
    for x in ("--td-subtype", "--project", "--repository", "--base-commit"):
        d.add_argument(x)
    d.add_argument("--no-build", action="store_true")
    t = s.add_parser("times"); t.add_argument("file")
    a = ap.parse_args()
    {"build": cmd_build, "inject": cmd_inject, "add": cmd_add, "times": cmd_times}[a.cmd](a)


if __name__ == "__main__":
    main()
