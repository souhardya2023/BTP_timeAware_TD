#!/bin/bash
# the whole of version 2: build, measure with the real pipeline, acceptance panel, ground truth, features, compile check
cd "$(dirname "$0")"
PY=/home/souhardya/Desktop/BTP_26-27/project_vector/.venv/bin/python
./build_and_measure.sh
rm -rf transitions releases features pairs.csv instances.csv projects.csv
$PY generator/ground_truth.py . > ground_truth.log 2>&1
$PY generator/summarize.py . >> ground_truth.log 2>&1
python3 compile_check.py > compile_check.log 2>&1
$PY generator/extract_features.py . pairs > features.log 2>&1
echo MAKE_ALL_DONE > make_all.done
