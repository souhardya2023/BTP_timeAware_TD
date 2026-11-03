#!/bin/bash
# Re-runs every model behind the graphs of the previous talk, writing to ../results (the stored results of ml_model/ and interest_exp/ are not touched).
# PY: a Python with scikit-learn, pandas, scipy.
cd "$(dirname "$0")"
PY=${PY:-python3}
FF=$(cd ../../.. && pwd)
mkdir -p ../results/level1 ../results/level2
# Level 2: interest and ranking models (leave-one-repository-out and temporal)
$PY $FF/interest_exp/code/model_pm.py            $FF/interest_exp/data ../results/level2 > ../results/level2/model_pm.log 2>&1
$PY $FF/interest_exp/code/model_next_release.py  $FF/interest_exp/data ../results/level2 > ../results/level2/model_next_release.log 2>&1
$PY $FF/interest_exp/code/model_snapshots.py     $FF/interest_exp/data ../results/level2 > ../results/level2/model_snapshots.log 2>&1
# Level 1: the type of a debt change, 7 classifiers x 2 layouts x with/without time x 4 protocols
TALK_DATA=$FF/out_dataset TALK_RES=$(pwd)/../results/level1 $PY r1_run_level1.py --repeats 20 --workers 3 > ../results/level1/run.log 2>&1
echo finished > ../results/ALL_MODELS_DONE
