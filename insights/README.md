# insights - what the data says beyond the numbers

Start with **`INSIGHTS.md`**: nine findings (and the hypotheses that failed), what each means, what to change in the talk, and what to do next.

```
insights/
  INSIGHTS.md   the report
  code/         one script per experiment (common.py = shared helpers); run_all.sh at this level lists them in order
  results/      the numbers of every experiment (CSV and text); l1_context_*.csv are the pair features in older host versions
  figs/         i1 ... i10: the figures of the report (matplotlib defaults)
  run_all.sh    runs everything (set VENV to a Python with scikit-learn, networkx, lizard, bandit, flawfinder; TORCH to one with torch)
```
**`new/`**: code turned into images and a CNN, the git history as a time series (features and a CNN), sim-to-real, patterns (`new/INSIGHTS_NEW.md`, run with `new/run_new.sh`); the picture folder is `../presentation/new_figures/`.

**`synthetic/`**: the same questions asked of the synthetic benchmark (`../synthetic_dataset`), what held, what did not, and a correction of insight I (`synthetic/INSIGHTS_SYNTHETIC.md`, run with `run_synthetic.sh`).

Level 1 (the 61 pairs): `l1_local_signal.py`, `l1_graph_image.py`, `l1_cnn.py`, `l1_context_shift.py`, `l1_drift.py`, `l1_context_aug.py`.
Level 2 (the git histories): `l2_temporal_structure.py`, `l2_rank_models.py`, `l2_ceiling_horizon.py`, `l2_icc.py`, `l2_release_clock.py`, `l2_enrichment.py`.
Needs the bare clones in `../../repos` (`../interest_exp/code/clone_repos.sh`). Nothing here changes the dataset or the models of the other folders.
