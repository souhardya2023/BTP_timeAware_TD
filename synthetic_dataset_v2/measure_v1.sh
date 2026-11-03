#!/bin/bash
# the same real-pipeline measurement and acceptance panel for the FIRST synthetic dataset (v1), for the before / after comparison
cd "$(dirname "$0")"
PY=/home/souhardya/Desktop/BTP_26-27/project_vector/.venv/bin/python
rm -rf real_pipeline_data_v1
ls -d ../synthetic_dataset/repos/*.git | xargs -P2 -I{} $PY ../real_project_analysis/code/a1_release_tables.py {} real_pipeline_data_v1 --k 20 > a1_v1.log 2>&1
$PY acceptance.py real_pipeline_data_v1 --min-releases 10 --out acceptance_v1.csv > acceptance_v1.txt 2>&1
echo done > measure_v1.done
