#!/bin/bash
# Re-run every insight experiment. VENV: a Python with scikit-learn, networkx, lizard, bandit, flawfinder (the project_vector venv was used);
# TORCH: a Python with torch (only for l1_cnn.py). Needs the bare clones in ../../repos (interest_exp/code/clone_repos.sh).
cd "$(dirname "$0")/code"
VENV=${VENV:-python3}
TORCH=${TORCH:-python3}
$VENV l2_temporal_structure.py      # concentration, memory by lag, hazard, same-file contagion, burstiness
$VENV l2_rank_models.py             # hotness rules and a learned model against persistence (paired bootstrap)
$VENV l2_ceiling_horizon.py         # the ceiling of any history-based ranking, and longer horizons
$VENV l2_icc.py                     # instance / file / repository share of variance, frozen vs live
$VENV l2_release_clock.py           # release clock (when) against instance (where)
$VENV l2_enrichment.py              # do developers work in debt regions more or less than their size predicts
$VENV l1_local_signal.py            # dilution, touched-file features, patch words, leave-one-project-out per project and origin
$VENV l1_graph_image.py             # dependency graph / image of the debt change
$TORCH l1_cnn.py                    # CNN on the graph images
$VENV l1_context_shift.py           # the debt patch applied to older versions of the host (about 10 minutes)
$VENV l1_drift.py                   # natural drift against the injected change; drift-scaled classification
$VENV l1_context_aug.py             # stability of the signature across hosts; augmentation
$TORCH make_insight_figures.py      # figures (needs matplotlib)
