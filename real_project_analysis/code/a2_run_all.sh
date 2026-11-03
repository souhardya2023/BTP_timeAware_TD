#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"; REPOS="${1:-$HERE/../../../repos}"; DATA="$HERE/../data"
PY=/home/souhardya/Desktop/BTP_26-27/project_vector/.venv/bin/python
ls -d "$REPOS"/*.git | xargs -P2 -I{} sh -c "timeout 3000 $PY $HERE/a2_commit_mining.py {} $DATA --n 700 >> $DATA/a2.log 2>&1 || echo FAILED {} >> $DATA/a2.log"
echo ALL_DONE >> $DATA/a2.log
