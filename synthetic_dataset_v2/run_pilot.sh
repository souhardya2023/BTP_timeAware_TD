#!/bin/bash
# build N projects (spread over tiers) and measure them with the real pipeline: ./run_pilot.sh N OUTDIR
N=${1:-40}; OUT=${2:-pilot}; cd "$(dirname "$0")"
PY=/home/souhardya/Desktop/BTP_26-27/project_vector/.venv/bin/python
rm -rf $OUT ${OUT}_data; python3 generator/build.py --out $OUT --n $N --workers 4 > $OUT.build.log 2>&1
ls -d $OUT/repos/*.git | xargs -P4 -I{} $PY ../real_project_analysis/code/a1_release_tables.py {} ${OUT}_data --k 20 > /dev/null 2>&1
$PY acceptance.py ${OUT}_data --manifests $OUT/manifests --min-releases 10
