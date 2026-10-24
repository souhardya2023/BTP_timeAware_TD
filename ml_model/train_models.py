#!/usr/bin/env python3
"""Train the final classifiers on ALL 61 pairs: for each layout one model WITH time_diff_min and one WITHOUT it.

usage: train_models.py [--model kbest10_random_forest|random_forest|gradient_boosting|logistic_regression|svm_rbf|knn|kbest10_logistic_regression]   (default kbest10_random_forest:
       the same classifier for the with-time and the without-time model, so the two are directly comparable)
output models/<layout>_with_time.joblib, models/<layout>_without_time.joblib  (the fitted model, the ordered feature columns, the class names)
These models are fitted on all the data: use run_experiments.py (cross-validation) for honest performance numbers, not their accuracy on the training pairs.
"""
import os
import sys

import joblib
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_experiments import MODELS, META, load


def main():
    name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "kbest10_random_forest"
    for layout in ("delta_only", "full"):
        for wt in (True, False):
            D = load(layout, wt)
            cols = [c for c in D.columns if c not in META]
            m = MODELS[name]().fit(D[cols], D.td_type)
            path = os.path.join(HERE, "models", f"{layout}_{'with' if wt else 'without'}_time.joblib")
            joblib.dump(dict(model=m, columns=cols, classes=list(m.classes_), classifier=name, layout=layout, with_time=wt, trained_on=len(D)), path)
            print(f"{layout:11s} {'with' if wt else 'without':7s} time: {name} on {len(D)} pairs, {len(cols)} features -> {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()
