"""Insight L2-E: do developers work more, or less, inside debt-carrying code than its size would predict?
null model: edits land uniformly on source lines, so a region with a share s of the code receives a share s of all added/modified lines.
observed:   changed lines inside the regions of debt instances (git diff -U0, as in the interest calculation) / all added+modified source lines of the release pair.
enrichment = observed share / region share.  >1: debt attracts work (sticky/hot), <1: debt is avoided or dead code."""
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

from common import ROOT, load_transitions

import importlib.util
_sp = importlib.util.spec_from_file_location("pipeline_common", os.path.join(ROOT, "pipeline", "common.py"))
_pc = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(_pc)
is_src_path = _pc.is_src_path

REPOS = os.path.abspath(os.path.join(ROOT, "..", "repos"))
T = load_transitions()
PYR = {"boltons", "click", "jinja", "werkzeug"}


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True).stdout.decode("utf-8", "replace")


def total_added(repo, v0, v1, py):
    pats = ["*.py"] if py else ["*.c", "*.h", "*.cc", "*.cpp"]
    out = git(repo, "diff", "--numstat", v0, v1, "--", *pats)
    s = 0
    for line in out.splitlines():
        a, d, p = line.split("\t", 2)
        if a.isdigit() and is_src_path(p):
            s += int(a)
    return s


def total_nloc(repo, v, py):
    pats = ["*.py"] if py else ["*.c", "*.h", "*.cc", "*.cpp"]
    rx = r"^[[:space:]]*[^[:space:]#]" if py else r"^[[:space:]]*[^[:space:]/*]"
    out = git(repo, "grep", "-c", "-E", rx, v, "--", *pats)
    s = 0
    for line in out.splitlines():
        p, n = line.rsplit(":", 1)
        p = p.split(":", 1)[1] if ":" in p else p
        if is_src_path(p) and n.isdigit():
            s += int(n)
    return s


rows = []
for repo, g in T.groupby("repo"):
    py = repo in PYR
    rp = f"{REPOS}/{repo}.git"
    for (v0, v1, vi), gg in g.groupby(["v0", "v1", "vi"]):
        reg = gg.drop_duplicates(["file", "func"])
        rows.append(dict(repo=repo, vi=vi, v0=v0, v1=v1, regions=len(reg), region_nloc=reg.nloc0.sum(), region_changed=reg.changed.sum(),
                         region_interest_lines=reg.groupby(["file", "func"]).interest_lines.max().sum(),
                         total_added=total_added(rp, v0, v1, py), total_nloc=total_nloc(rp, v0, py)))
E = pd.DataFrame(rows)
E["share_code"] = E.region_nloc / E.total_nloc
E["share_changed"] = E.region_changed / E.total_added.replace(0, np.nan)
E["enrich"] = E.share_changed / E.share_code
E.to_csv("../results/l2_enrichment_by_release.csv", index=False)
S = E.groupby("repo").agg(releases=("vi", "size"), region_nloc=("region_nloc", "sum"), total_nloc=("total_nloc", "sum"), region_changed=("region_changed", "sum"), total_added=("total_added", "sum"))
S["share_of_code_in_debt_regions"] = S.region_nloc / S.total_nloc
S["share_of_changes_in_debt_regions"] = S.region_changed / S.total_added
S["enrichment"] = S.share_of_changes_in_debt_regions / S.share_of_code_in_debt_regions
S.to_csv("../results/l2_enrichment.csv")
tot = S[["region_nloc", "total_nloc", "region_changed", "total_added"]].sum()
txt = S[["share_of_code_in_debt_regions", "share_of_changes_in_debt_regions", "enrichment"]].round(3).to_string()
txt += f"\n\nall projects: debt regions are {tot.region_nloc/tot.total_nloc:.1%} of the code and receive {tot.region_changed/tot.total_added:.1%} of the added/modified lines -> enrichment {(tot.region_changed/tot.total_added)/(tot.region_nloc/tot.total_nloc):.2f}"
open("../results/l2_enrichment.txt", "w").write(txt)
print(txt)
