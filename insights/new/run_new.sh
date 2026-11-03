#!/bin/bash
# Re-run the experiments of INSIGHTS_NEW.md.  VENV: Python with scikit-learn, pandas, lizard.  TORCH: Python with torch and numpy, pandas (no scikit-learn needed).  FIG: Python with matplotlib.
# Needs ../../synthetic_dataset (with features/) and the real data of ../../interest_exp and ../../out_dataset.
cd "$(dirname "$0")/code"
VENV=${VENV:-python3}; TORCH=${TORCH:-python3}; FIG=${FIG:-python3}
$VENV n1_images.py              # code -> image (synthetic pairs from git, real pairs from td.patch)
$TORCH n2_cnn_code.py           # CNN on the code images: random / held-out project / held-out template, sim-to-real (about 45 minutes on two threads)
$VENV n3_sim2real_features.py   # the 133 features: synthetic -> real and real -> synthetic
$VENV n3b_scale_free.py         # scale-free versions of the delta
$VENV n4a_prep_ts.py            # git history as time-series features and sequence tensors
$VENV n4b_ts_models.py          # feature groups added one by one, held-out projects and temporal
$VENV n4c_regimes.py            # per regime
$TORCH n4d_seq_cnn.py           # CNN on the history image
$VENV n5_patterns.py            # patterns, real against synthetic
$VENV n6_size_prior.py          # size as a prior, history as the evidence
$VENV n7_combined.py            # panel, pooled training (real + synthetic)
$VENV n8_logistic_check.py      # model dependence of the real Level 1 result
$TORCH n9_codebert_embed.py      # CodeBERT embeddings of the diffs (needs transformers, downloads microsoft/codebert-base, about 9 minutes)
$VENV n9b_codebert_eval.py       # evaluation on the same splits, sim-to-real
$VENV n9c_fusion.py              # exploratory late fusion with the features
cd ../../../presentation/new_figures
$FIG diagrams.py; $FIG diagrams2.py; $FIG real_results.py; $FIG synthetic_figures.py; $FIG experiment_figures.py; $FIG combined_figures.py
