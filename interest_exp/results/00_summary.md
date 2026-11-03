# Interest experiment - summary

Question: can the technical-debt **interest**, in **person-months**, be calculated and predicted? Method of the 2025 paper, on 9 real projects, 20 releases each.

## What was calculated

| number | meaning |
|---|---|
| 20853 | instance-releases analysed (an instance counts once per release) |
| 1557 | distinct technical-debt instances (SonarQube issues / structural smells) |
| 1607 | interest events (an instance re-worked while it persists) |
| 5572 | lines re-worked inside persisting debt |
| 10.52 person-months | interest paid in total (COCOMO II nominal constants) |
| 1.17 person-months | per project on average (range 0.09 - 2.44) |

## What can be predicted

| task | result | verdict |
|---|---|---|
| any interest in the next release (AUC) | 0.59 for unseen projects, 0.71 for later releases | weak but real signal (chance 0.5) |
| amount of interest of an instance (mPM) | R2 <= 0 for every model (best -0.0002); no model beats 'predict zero' in MAE | not predictable from these features |
| total interest of a project over all its instances | predicted / actual = 1.14 (two-part model, leave one repo out) | right order of magnitude overall; not per project or release |
| total interest of a project in the next release | best R2 -0.14 | no skill |
| function-level interest in the next 100 commits (AUC) | 0.57 / 0.62 | weak signal |

## Conclusions

1. The interest **calculation** works and is reproducible: all 9 transition files were regenerated from the git histories and equal the earlier results exactly.
2. Predicting **whether** an instance will absorb work inside the debt is possible only weakly (AUC up to 0.71); predicting **how many person-months** is not possible with the available features: the zero model has the smallest absolute error because 92% of the instance-releases pay nothing, and R2 is zero or negative.
3. The overall **total** is predicted within the order of magnitude by the two-part model, which is usable for budgeting a whole portfolio, not for ranking single instances.
4. The amount of interest depends on the detector (SonarQube vs structural smells) and on the COCOMO II constants; the constants of the paper could not be checked.
5. The interest is not defined for the injected pairs of the dataset (the debt is new, there is no history after it); it is available for the real repositories only. Section 3.1 shows the model applied to the pairs: it only reacts to complexity and structure changes.

Documents: `01_interest_calculation.md`, `02_predicting_interest.md`, `03_pairs_and_first_model.md`; all tables in `tables/` and the model outputs as CSV in `results/`.
