# 8. Is the current setup better than the previous one?

Each row compares what exists now with what existed before, on the same data and splits. **Clear** = on the deterministic splits the 95% bootstrap interval of the accuracy difference is above 0 AND the exact McNemar test gives p < 0.05; on the random splits, the current setup wins in every one of the 20 splits. **Borderline** = better, but one of the two criteria fails. With 61 pairs a gain of a few pairs is hard to prove, so 'borderline' is not 'no gain'.

## 8.1 Model with the time feature (current) vs model without it (previous) - final classifier `kbest10_random_forest`

| layout | protocol | without_time | with_time | difference | evidence | verdict |
|---|---|---|---|---|---|---|
| delta_only | given_stratified | 0.787 | 0.918 | 0.131 | 95% CI +0.05 to +0.23; fixed 8, broken 0; McNemar p=0.008 | better, clear |
| delta_only | repeated_stratified | 0.840 | 0.938 | 0.098 | with time better in 20 of 20 splits (range +0.049 to +0.148) | better, clear |
| delta_only | given_by_project | 0.311 | 0.508 | 0.197 | 95% CI +0.10 to +0.30; fixed 12, broken 0; McNemar p=0.000 | better, clear |
| delta_only | leave_one_project_out | 0.426 | 0.508 | 0.082 | 95% CI +0.02 to +0.16; fixed 5, broken 0; McNemar p=0.062 | better, borderline |
| full | given_stratified | 0.705 | 0.820 | 0.115 | 95% CI +0.03 to +0.20; fixed 7, broken 0; McNemar p=0.016 | better, clear |
| full | repeated_stratified | 0.781 | 0.927 | 0.146 | with time better in 20 of 20 splits (range +0.082 to +0.197) | better, clear |
| full | given_by_project | 0.115 | 0.279 | 0.164 | 95% CI +0.08 to +0.26; fixed 10, broken 0; McNemar p=0.002 | better, clear |
| full | leave_one_project_out | 0.246 | 0.377 | 0.131 | 95% CI +0.05 to +0.21; fixed 8, broken 0; McNemar p=0.008 | better, clear |

Of the 8 comparisons: 7 clear, 1 borderline, 0 mixed or without gain (borderline: delta_only / leave_one_project_out).
For the plain classifiers (random forest, gradient boosting, logistic regression, SVM, kNN) the change from adding the time ranges from -0.016 to +0.085 accuracy; the only negative cell is random_forest / full / leave_one_project_out (-0.016, one pair).

**Verdict:** yes - with the ten-best selector the model with time is more accurate than the one without it in all 8 comparisons (7 of them clear by the criteria above). The gain is conditional on the time values, which come from the ground-truth time model (section 4); the controls in section 4.4 show how it depends on them.

## 8.2 Dataset versions

| protocol | v1_bug_free | v2_bugs | v3_bugs_and_time |
|---|---|---|---|
| given_by_project | 0.336 | 0.336 | 0.393 |
| given_stratified | 0.787 | 0.787 | 0.840 |
| leave_one_project_out | 0.377 | 0.377 | 0.416 |
| repeated_stratified | 0.838 | 0.839 | 0.898 |

Averaged over classifiers and layouts: adding the bugs to the vectors changes accuracy by +0.000; adding the time changes it by +0.052.

**Verdict:** the dataset with bugs is neither better nor worse than the bug-free one for TD-type classification (the vectors barely move, section 6.1); it exists for the time feature. The time feature is the only change that improves accuracy.

## 8.3 Selector vs plain classifier (with time)

| layout | protocol | random_forest_with_time | kbest10_random_forest_with_time | difference |
|---|---|---|---|---|
| delta_only | given_stratified | 0.885 | 0.918 | 0.033 |
| delta_only | repeated_stratified | 0.919 | 0.938 | 0.019 |
| delta_only | given_by_project | 0.459 | 0.508 | 0.049 |
| delta_only | leave_one_project_out | 0.459 | 0.508 | 0.049 |
| full | given_stratified | 0.803 | 0.820 | 0.017 |
| full | repeated_stratified | 0.876 | 0.927 | 0.051 |
| full | given_by_project | 0.393 | 0.279 | -0.114 |
| full | leave_one_project_out | 0.393 | 0.377 | -0.016 |

**Verdict:** on the delta layout the selector is better in all 4 protocols (+0.019 to +0.049); on the full layout it is better on the random-split protocols (+0.017, +0.051) and worse on the project-held-out protocols (-0.114, -0.016). The final models therefore use the delta layout.

## 8.4 Current classification vs the earlier experiments

| experiment | metric | result | validity | status |
|---|---|---|---|---|
| first prediction model (patch-size effort) | regression, R2 | 0.8986 reported; 0.53 (5-fold) / -0.43 (leave one project out) recomputed | invalid target and join; no held-out skill | superseded; not comparable |
| interest from git history (function level) | AUC | 0.568 held-out projects, 0.625 later commits | weak but real signal; chance 0.5 | different task; not applicable to security / concurrency |
| interest, release-by-release | AUC | 0.594 held-out repositories, 0.713 later versions | weak but real signal | different task |
| project vector -> bug lifetime | R2 | negative for every feature set | no skill (119 points) | dropped |
| TD-type classification (current), without time | accuracy | 0.31 (project folds), 0.43 (leave one project out) to 0.84 (random splits) | above the 0.43 majority-class rate on random splits; at or below it when whole projects are held out | current |
| TD-type classification (current), with time | accuracy | 0.51 (project folds), 0.51 (leave one project out) to 0.94 (random splits) | above the majority-class rate on random splits and, narrowly, on project folds; improvement over the model without time | current, best |

The numbers of different tasks cannot be ranked against each other; what the table shows is that the current experiment is the first with an evaluation that holds out projects, has baselines, and shows a skill above them (with the time feature).
