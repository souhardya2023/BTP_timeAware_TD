#!/bin/bash
# full build of the 150 projects of version 2 and measurement with the real pipeline (a1) -> acceptance panel
cd "$(dirname "$0")"
PY=/home/souhardya/Desktop/BTP_26-27/project_vector/.venv/bin/python
OUT=${1:-.}; DATA=${2:-real_pipeline_data}
rm -rf $OUT/repos $OUT/manifests $DATA
python3 generator/build.py --out $OUT --workers 4 > build.log 2>&1
ls -d $OUT/repos/*.git | xargs -P4 -I{} $PY ../real_project_analysis/code/a1_release_tables.py {} $DATA --k 20 > a1.log 2>&1
$PY acceptance.py $DATA --manifests $OUT/manifests --min-releases 10 --out acceptance_v2.csv > acceptance_v2.txt 2>&1
echo DONE >> a1.log
