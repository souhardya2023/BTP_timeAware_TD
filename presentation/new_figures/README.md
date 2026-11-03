# new_figures - every graph, plot and dataset-creation picture of the project, drawn with matplotlib

All pictures are PNG files made by the Python scripts of this folder (matplotlib defaults, boxes slightly uneven on purpose). Nothing here is a screenshot. Re-run with `insights/new/run_new.sh` (last block) or each script on its own; they read the data of `../../insights`, `../../synthetic_dataset`, `../data` and `../../out_dataset`.

## 01_dataset_creation  (how the data were made)
| file | shows |
|---|---|
| `real_dataset_creation.png` | the 8 steps of the real data set: projects, injected debt, tests, metric audit (102 -> 52), added pairs (61), bugs (183), fix-time label, 133 features |
| `synthetic_dataset_creation.png` | the 8 steps of the synthetic benchmark: domain, tier, clean code, debt plan, simulation, git, ground truth, validation |
| `interest_calculation.png` | how the interest of one debt instance between two releases is computed (git diff, classification, COCOMO II), with a worked example |
| `history_as_time_series.png` | one real debt instance (zlib) as a time series: its events, the project's activity, and the features built from the past only |
| `code_to_image_examples.png` | a debt change drawn as an image (one example per type), with the changed lines underneath |

## 02_real_results  (the real 61 pairs and 9 histories)
| file | shows |
|---|---|
| `R1_dataset_composition.png` | funnel 102 -> 52 -> 61, pairs per type and language, the time model |
| `R2_level1_accuracy.png` | accuracy by protocol with and without the time feature; seven classifiers |
| `R3_time_feature_controls.png` | shuffled and noisy time, four calibrations of the time model |
| `R4_ranking_capture.png` | share of next-release interest captured (top 10 / 20 / 30 %), the capture curve |
| `R5_size_vs_persistence.png` | "largest region first" against persistence, and the shrunk rate |
| `R6_interest_and_predictability.png` | interest per project (10.52 person-months), AUC of the interest models |

## 03_synthetic_dataset  (the 150 generated projects)
| file | shows |
|---|---|
| `S1_tiers.png` | files, lines, releases and commits by size tier |
| `S2_types_templates.png` | 1,321 instances by type; the 23 templates |
| `S3_balance.png` | major type by tier and by regime; projects per regime |
| `S4_pairs.png` | size of a debt introduction, mixed commits, granularity |
| `S5_patterns_vs_real_by_regime.png` | eight patterns per regime against the real value (dashed) |
| `S6_interest_by_type.png` | event rate and person-months by type |

## 04_insights  (earlier analyses, copied)
`real_i1 ... real_i10`: concentration, memory, avoided debt, the ceiling, where/when, hotness scores, generalisation by project and origin, drift, context shift, graph visibility (`insights/INSIGHTS.md`).
`synthetic_sf1 ... sf6`: ranking by regime, decomposition of the gain, size real against synthetic, repayment policy, the type of a change under splits, the two protocols (`insights/synthetic/INSIGHTS_SYNTHETIC.md`).

## 05_new_experiments  (`insights/new/INSIGHTS_NEW.md`)
| file | shows |
|---|---|
| `E1_code_image_cnn.png` | CNN on code images against the features and the patch words, by split; the real-pair confusion matrix |
| `E2_sim_to_real_features.png` | train synthetic -> test real and the reverse; the length of the delta vectors (44 times) |
| `E3_time_series_features.png` | AUC with the git-history time series, project clock and neighbours added, real and synthetic, both protocols |
| `E4_patterns_real_vs_synthetic.png` | lifecycle shapes, frozen debt is small debt, early against late |
| `E5_sequence_cnn.png` | CNN on the history as a time-series image |
| `E6_size_and_history.png` | size x history under both protocols (real) |
| `E7_codebert_embeddings.png` | frozen CodeBERT embeddings of the diff: per held-out template against the features, accuracy by split, trained on synthetic and tested on real |

## 06_combined  (real and synthetic together)
| file | shows |
|---|---|
| `C1_panel_real_vs_synthetic.png` | 20 metrics on the real histories, the synthetic baseline, all synthetic and the pooled rows, with a same / similar / different verdict |
| `C2_pooled_training_level2.png` | does adding the synthetic histories to the training data help on the real data (AUC, both protocols) |
| `C3_graph_visibility_both.png` | share of pairs whose dependency graph changes, by type, real and synthetic |
| `C4_level1_model_dependence_and_pooling.png` | per project accuracy of the random forest and of the direction-only logistic regression on the real pairs; the effect of pooling |

**`INSIGHTS_ALL.txt`** (a copy of `final_folder/INSIGHTS_ALL.txt`): every insight, tagged real / synthetic / both / disagree / combined, with evidence, strength, the figures that support it and the source file; plus an index figure -> insight.

Scripts: `diagrams.py`, `diagrams2.py`, `real_results.py`, `synthetic_figures.py`, `experiment_figures.py`, `combined_figures.py`.
