# Graphs of the previous talk, redrawn from freshly re-run models

What was done
- All models of the previous talk were run again from scratch into `results/` (nothing copied from the old result files):
  - Level 2: `model_pm.py`, `model_next_release.py`, `model_snapshots.py` (zero, persistence, RF regression, two-part model; next-release and function-level AUC).
  - Level 1: `run_experiments.py` (7 classifiers, 4 protocols, 20 repeats, with and without the time feature).
- `results/COMPARISON.txt`: the fresh outputs equal the stored ones (Level 1: 124 rows, max difference 0.0000; Level 2: 116,468 predictions identical; AUC tables identical).
- Graphs are drawn from the fresh outputs only (`code/r3_make_graphs.py`).

Excluded on purpose
- The fix-time chart (extra minutes per type) and the time-feature controls.
- Kept: the Level 1 accuracy bars with and without the time feature, because they are model results. Drop G2 if you want no time at all.

Figures (`figures/`)
- G1 dataset pairs (funnel, types, languages); G2 Level 1 accuracy by protocol and by classifier
- G3 ranking capture bars; G4 capture curves; G5 paired difference to persistence; G6 AUC predictability
- T1 ranking table (top 20 %); T2 paired-difference table

Run order: `code/r2_run_all_models.sh`, then `code/r3_make_graphs.py`, then `code/r4_compare_with_stored.py`.
