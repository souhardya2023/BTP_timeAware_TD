#!/usr/bin/env python3
"""Predict the technical-debt type of pairs with a trained model.

usage: predict.py --layout delta_only|full --with-time|--without-time (--id Python/P1 | --csv FILE) [--dataset PATH]
  --id      a pair of the dataset (looked up in ../out_dataset/<layout>/dataset_with_time.csv, or --dataset PATH)
  --csv     a CSV with the same feature columns as the dataset (for example a new pair added with ../pipeline/make_dataset.py add and then built)
prints the predicted type and the probability of every class (if the model gives probabilities).
Pairs of the training data are predicted with a model that has seen them: this is a demonstration, not an evaluation.
"""
import argparse
import os
import sys

import joblib
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True, choices=["delta_only", "full"])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--with-time", action="store_true")
    g.add_argument("--without-time", action="store_true")
    ap.add_argument("--id")
    ap.add_argument("--csv")
    ap.add_argument("--dataset")
    a = ap.parse_args()
    bundle = joblib.load(os.path.join(HERE, "models", f"{a.layout}_{'with' if a.with_time else 'without'}_time.joblib"))
    if a.csv:
        D = pd.read_csv(a.csv)
    else:
        D = pd.read_csv(a.dataset or os.path.join(HERE, "..", "out_dataset", a.layout, "dataset_with_time.csv"))
        D = D[D.id == a.id] if a.id else D
    missing = [c for c in bundle["columns"] if c not in D.columns]
    if missing:
        sys.exit(f"{len(missing)} feature columns missing, e.g. {missing[:3]}")
    X = D[bundle["columns"]]
    pred = bundle["model"].predict(X)
    out = pd.DataFrame(dict(id=D.get("id", range(len(D))), predicted_td_type=pred))
    if hasattr(bundle["model"], "predict_proba"):
        pr = pd.DataFrame(bundle["model"].predict_proba(X), columns=[f"p_{c}" for c in bundle["classes"]]).round(3)
        out = pd.concat([out.reset_index(drop=True), pr], axis=1)
    if "td_type" in D.columns:
        out.insert(2, "true_td_type", D.td_type.values)
    print(f"model: {bundle['classifier']}, {a.layout}, {'with' if a.with_time else 'without'} time_diff_min, trained on {bundle['trained_on']} pairs")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
