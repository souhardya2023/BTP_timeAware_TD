#!/usr/bin/env python3
"""After regenerate.sh: copy the freshly made PNGs from the repository folders back into figures/ (names as used in report.tex), using MANIFEST.csv."""
import csv, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); FR = os.path.dirname(HERE); PR = os.path.dirname(FR); n = 0
for r in csv.DictReader(open(os.path.join(FR, "MANIFEST.csv"))):
    f = os.path.join(FR, r["figure"])
    if r["group"] == "report" and r["source_image"]:
        src = os.path.join(PR, r["source_image"].split(" | ")[0])
    elif r["group"] == "talk_final":
        src = next((os.path.join(PR, d, os.path.basename(f)) for d in ("presentation/insight_slides/figs", "scenario_analysis/figures") if os.path.exists(os.path.join(PR, d, os.path.basename(f)))), "")
    elif r["group"] == "talk_earlier":
        src = next((os.path.join(PR, d, os.path.basename(f)) for d in ("presentation/figs", "presentation/tables") if os.path.exists(os.path.join(PR, d, os.path.basename(f)))), "")
    else: continue
    if src and os.path.exists(src): shutil.copy2(src, f); n += 1
print("refreshed", n, "figures")
