#!/usr/bin/env bash
# run a1_release_tables.py on every bare clone in REPOS (default ../../../repos), 3 at a time
HERE="$(cd "$(dirname "$0")" && pwd)"; REPOS="${1:-$HERE/../../../repos}"; DATA="$HERE/../data"
PY=/home/souhardya/Desktop/BTP_26-27/project_vector/.venv/bin/python
ls -d "$REPOS"/*.git | grep -v C-Thread-Pool | xargs -P3 -I{} sh -c "timeout 3000 $PY $HERE/a1_release_tables.py {} $DATA --k 20 >> $DATA/a1.log 2>&1 || echo FAILED {} >> $DATA/a1.log"
echo ALL_DONE >> $DATA/a1.log
