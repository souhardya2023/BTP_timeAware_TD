"""Do the fresh runs reproduce the stored results?  Compares ../results with ml_model/results and interest_exp/results (same code, same seeds: differences should be 0 or tiny)."""
import os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results"); FF = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
out = []
P = lambda s="": (out.append(s), print(s))
a = pd.read_csv(os.path.join(RES, "level1", "summary.csv")); b = pd.read_csv(os.path.join(FF, "ml_model", "results", "summary.csv"))
m = a.merge(b, on=["layout", "protocol", "model", "with_time"], suffixes=("_new", "_old"))
d = (m.accuracy_mean_new - m.accuracy_mean_old).abs()
P("Level 1 (summary.csv): %d rows compared; max |difference| of the accuracy %.4f; rows that differ by more than 0.001: %d" % (len(m), d.max(), (d > 0.001).sum()))
if (d > 0.001).any(): P(m[d > 0.001][["layout", "protocol", "model", "with_time", "accuracy_mean_new", "accuracy_mean_old"]].round(3).to_string(index=False))
a = pd.read_csv(os.path.join(RES, "level2", "pm_predictions.csv")); b = pd.read_csv(os.path.join(FF, "interest_exp", "results", "pm_predictions.csv"))
m = a.merge(b, on=["protocol", "model", "repo", "vi", "key"], suffixes=("_new", "_old"))
P("Level 2 (pm_predictions.csv): %d rows fresh, %d stored, %d matched" % (len(a), len(b), len(m)))
for model, g in m.groupby("model"): P("  %-12s max |difference| of the prediction %.6f" % (model, (g.predicted_mPM_new - g.predicted_mPM_old).abs().max()))
for f, keys in (("next_release_model_results.csv", ["protocol", "fold", "model"]), ("snapshot_model_results.csv", ["protocol", "fold", "model"])):
    x = pd.read_csv(os.path.join(RES, "level2", f)); y = pd.read_csv(os.path.join(FF, "interest_exp", "results", f)); z = x.merge(y, on=keys, suffixes=("_new", "_old"))
    P("Level 2 (%s): %d rows matched; max |difference| of the AUC %.6f" % (f, len(z), (z.AUC_new - z.AUC_old).abs().max()))
open(os.path.join(RES, "COMPARISON.txt"), "w").write("\n".join(out))
