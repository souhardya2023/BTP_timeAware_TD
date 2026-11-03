# Proposed order for presenting the new insights (about 12 slides, 12-15 minutes)

One message and one figure per slide. Figure paths are inside `figures/`. The numbers and the strength of each claim are in `INSIGHTS_NEW_ONLY.txt` (IDs in brackets).

| # | message | figure | IDs |
|---|---|---|---|
| 1 | We now have two data sets: the real histories (9 repositories, 61 pairs) and a 150-project benchmark with known truth. Real = evidence, synthetic = testbed. | `01_new_dataset/synthetic_dataset_creation.png` | S1, C5 |
| 2 | What the benchmark contains, and that it passes its own checks. | `01_new_dataset/S1_tiers.png`, `S2_types_templates.png` | S1 |
| 3 | Interest is concentrated and persistent: half of the debt is never touched; a past event predicts a new one at any lag. | `02_real_data_insights/real_i1_concentration.png`, `real_i2_memory.png` | A1, A2 |
| 4 | Developers avoid debt: a third of the code, an eighth of the edits. | `02_real_data_insights/real_i3_enrichment.png` | A3 |
| 5 | The new baseline: size alone ties "interest already paid"; frozen debt is small debt. | `02_real_data_insights/R5_size_vs_persistence.png`, `04_new_experiments/E4_patterns_real_vs_synthetic.png` | R1, R2 |
| 6 | Where the ranking stops: persistence is close to the ceiling of "where"; the release clock is calibration, not timing. | `02_real_data_insights/real_i4_ceiling.png`, `real_i5_where_when.png`, `04_new_experiments/E3_time_series_features.png` | A5, A6, R6 |
| 7 | The one candidate positive under both protocols: size x history. | `04_new_experiments/E6_size_and_history.png` | R4 |
| 8 | History as a time series, or as an image to a CNN, adds nothing on real data. | `04_new_experiments/E5_sequence_cnn.png` | A11, R10 |
| 9 | A clean twin makes a debt change visible; a snapshot cannot. | `02_real_data_insights/real_i8_drift.png`, `03_synthetic_analysis/synthetic_sf5_pairs_level1.png` | A7 |
| 10 | Models learn the template, not the debt: code images, patch words, CodeBERT all fall on a new template. | `04_new_experiments/E1_code_image_cnn.png`, `E7_codebert_embeddings.png` | A8, C6 |
| 11 | "Does not generalise to new projects" was one project, and depends on the model. | `05_combined/C4_level1_model_dependence_and_pooling.png` | R7 |
| 12 | The benchmark is not yet a proxy: 44 times too visible, no size effect; pooling does not help. | `05_combined/C1_panel_real_vs_synthetic.png`, `04_new_experiments/E2_sim_to_real_features.png` | D1-D8, C1-C4 |
| 13 | The out-of-the-box insights and the next step for each. | (table from Part J of `INSIGHTS_NEW_ONLY.txt`) | J1-J10 |
