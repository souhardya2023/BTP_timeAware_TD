#!/bin/bash
# Build the whole dataset (about 10 minutes on 4 cores).  PY must have numpy, pandas, lizard (for ground_truth.py, insight_check.py); build.py needs only git and python3.
cd "$(dirname "$0")"
OUT=${1:-..}
PY=${PY:-python3}
python3 build.py --out "$OUT" --workers 4          # repos/ and manifests/
$PY ground_truth.py "$OUT"                          # transitions/, releases/, pairs.csv
$PY summarize.py "$OUT"                             # projects.csv, instances.csv
$PY validate.py "$OUT" --workers 4                  # VALIDATION.md
$PY insight_check.py "$OUT"                         # insight_check.md / .csv
