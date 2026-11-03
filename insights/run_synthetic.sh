#!/bin/bash
# Re-run the analysis of the synthetic benchmark. VENV: Python with scikit-learn, pandas, lizard; FIG: Python with matplotlib. Needs final_folder/synthetic_dataset (incl. features/).
cd "$(dirname "$0")/synthetic/code"
VENV=${VENV:-python3}
FIG=${FIG:-python3}
$VENV s2_ranking.py            # ranking inside a release, per regime
$VENV s2_ablation.py           # counts / lines / shrinkage / release clock
$VENV s2_alpha_real.py         # alpha chosen on the synthetic baseline, tested on the real histories
$VENV s2_tiebreak_real.py      # real histories: the size tie-break
$VENV s2_size.py               # size against history, real and synthetic
$VENV s3_timeseries.py         # time to identify a hot spot, repayment policy, predictability of release totals
$VENV s1_pairs.py              # type of a debt change: splits, twin, mixed commits, drift scaling, learning curve (about 20 min)
$VENV s1_words_invariance.py   # patch words, host invariance, graph visibility
$VENV s1_protocols.py          # Level 1 under random, leave-one-project-out and temporal protocols
$VENV s2_protocols.py          # ranking under leave-one-project-out and temporal, synthetic and real
$FIG s_figures.py
$FIG s_fig_protocols.py
