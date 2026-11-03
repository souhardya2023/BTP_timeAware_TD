#!/usr/bin/env python3
"""Re-evaluate the first interest-prediction model of the study (target = COCOMO II effort of the injected patch size).

That model (random forest, features = SonarQube issue counts + file-history numbers per pair) reported R2 0.8986 on a single 80/20 split. Here the same data is evaluated
with 5-fold cross-validation and with leave-one-project-out, and the data problems are counted.

usage: reeval_first_model.py DATA_DIR RESULTS_DIR      (DATA_DIR/earlier/all_projects_predictions.csv, model_comparison_predictions.csv)
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, LeaveOneGroupOut, cross_val_predict

warnings.filterwarnings("ignore")
d, res = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(res, "tables"), exist_ok=True)
ap = pd.read_csv(os.path.join(d, "earlier", "all_projects_predictions.csv"))
cm = pd.read_csv(os.path.join(d, "earlier", "model_comparison_predictions.csv"))
y = ap.Target_PM
drop = ["Pair", "Project", "Ground_Truth_TD_Type", "Ground_Truth_TD_Subtype", "Lines_Added", "Target_PM", "Predicted_PM", "project", "td_type", "files_analyzed"]
cols = [c for c in ap.columns if c not in drop]
X = pd.get_dummies(ap[["Ground_Truth_TD_Type", "Ground_Truth_TD_Subtype"]]).join(ap[cols].fillna(0))
rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
rows = [dict(evaluation="reported with the model (single 80/20 split, from the earlier summary)", R2=0.8986, MSE=0.002075)]
for name, cv, groups in (("5-fold cross-validation (rows of one project in several folds)", KFold(5, shuffle=True, random_state=42), None), ("leave one project out (4 projects)", LeaveOneGroupOut(), ap.Project)):
    p = cross_val_predict(rf, X, y, cv=cv, groups=groups)
    rows.append(dict(evaluation=name, R2=r2_score(y, p), MSE=mean_squared_error(y, p)))
for c in [c for c in cm.columns if c.startswith("Pred_PM")]:
    rows.append(dict(evaluation=f"column {c} of model_comparison_predictions.csv, as stored", R2=r2_score(cm.Actual_PM, cm[c]), MSE=mean_squared_error(cm.Actual_PM, cm[c])))
pd.DataFrame(rows).to_csv(os.path.join(res, "tables", "first_model_reevaluation.csv"), index=False)
exact = np.allclose(y, ap.Lines_Added.apply(lambda v: 2.64 * ((v / 1000) ** 0.91) if v > 0 else 0))
issues = [
    ("target Target_PM is an exact function of Lines_Added (2.64 x KSLOC^0.91)", "yes" if exact else "no"),
    ("rows whose project differs between the SonarQube side and the git-history side (pair-name join across Python/ and C_C++/)", f"{int((ap.Project != ap.project).sum())} of {len(ap)}"),
    ("rows whose TD type differs between the two sides", f"{int((ap.Ground_Truth_TD_Type != ap.td_type).sum())} of {len(ap)}"),
    ("distinct projects actually present in the model data", ", ".join(sorted(ap.Project.unique()))),
    ("distinct rows by (project, history-interest value): rows sharing identical history features", f"{len(ap) - ap[['Project', 'historical_td_interest_pm']].drop_duplicates().shape[0]} duplicated feature rows"),
]
pd.DataFrame(issues, columns=["check", "result"]).to_csv(os.path.join(res, "tables", "first_model_data_problems.csv"), index=False)
print(pd.DataFrame(rows).round(4).to_string(index=False)); print(pd.DataFrame(issues).to_string(index=False))
