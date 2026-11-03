# Insights: what the data says beyond the numbers

Written for: you (the project author), to decide what to claim, what to change in the talk, and what to do next.

Everything below was computed from the data in this repository. Code: `code/`, numbers: `results/`, figures: `figs/`. Each claim names the file that holds its numbers. Hypotheses that **failed** are listed too, because they are as informative as the ones that worked.

## 0. The short version

| # | Insight | Evidence | Status |
|---|---|---|---|
| A | **The clean twin cancels the host.** The change that a debt injection makes in the 133 features is the same whatever version of the host project it is applied to (cosine 1.00, 3 % relative variation). Hence adding older versions of the host as extra data points adds copies, not information | 188 older-host copies; augmentation does not improve accuracy | confirmed, and it is a *negative* result for augmentation |
| B | **Seen alone, the debt is invisible.** The debt change is about 100 times smaller than the natural change of the same feature between two versions of the project; a typical pair has 1 of 133 features above the natural drift | median ratio 0.01 | confirmed |
| C | **"Does not generalise to unseen projects" was one project.** The pooled leave-one-project-out accuracy (0.43 to 0.51) is dominated by boltons (24 of 61 pairs, accuracy 0.00, because without it only 2 concurrency pairs remain in training). On the other 37 pairs the accuracy is 0.70 to 0.76 against a majority of 0.43 | per-project table | confirmed. **This changes a statement in the talk** |
| D | **But the generator leaves a fingerprint.** Scripted injections are recognised on unseen projects with 0.95 accuracy; LLM-written ones (SmellBench) with 0.47 (about chance). A classifier tells the two origins apart with AUC 0.98 | by-origin table | confirmed. The dataset difficulty axis is *origin*, not project |
| E | **A dependency graph / image sees only 14 of 61 debt changes.** Concurrency (26) and security (16) live inside functions and do not change the file graph at all. A CNN on the graph image: 0.57 on shared hosts, 0.14 on unseen projects (it learns the host) | graph and CNN runs | confirmed. The idea is right for structural debt only |
| F | **Debt is avoided, not attractive.** Debt regions are 32 % of the code and receive 12 % of the edits (enrichment 0.39; below 1 in all 9 projects) | git numstat against regions | confirmed |
| G | **Interest is a persistent hot-spot trait, extremely concentrated.** 46 % of the debt instances observed for at least 10 releases never pay interest; the top 10 % of instances hold 70 % of it (Gini 0.83); the chance to pay again does not fade with lag (22 to 25 % at lags 1 to 6, against 7 % for instances that did not pay) and rises with the number of past events (5 % to 44 %) | lag and dose-response tables | confirmed |
| H | **The ranking is at its ceiling for "where"; the rest is "when".** Ranking by persistence captures 39 % of the next-release interest in the top 20 %; ranking by the *true long-run hotness of every instance* (which uses the future) captures 38 %. The remaining gap to 96 % is timing. The release clock explains twice the variance of the instance (ICC 0.28 against 0.13) and is not autocorrelated (-0.01) | ceiling and ICC | confirmed |
| I | **(CORRECTED, see `synthetic/INSIGHTS_SYNTHETIC.md` section 3.)** ~~Cheap time-series "hotness" scores beat persistence at larger budgets.~~ With the same size tie-break on both sides the gain is not significant. Original text: **Cheap time-series "hotness" scores beat persistence at larger budgets.** Change-proneness (share of past releases in which the region changed at all, shrunk) gains +8.1 points at the top 30 % and +8.3 at the top 50 % (95 % intervals +1.8 to +14.2 and +3.5 to +13.4, 123 groups), but nothing at the top 10 and 20 % and nothing in the temporal protocol | paired bootstrap | not confirmed: part of it was the size tie-break (+5.4 (-0.6, +11.7) at the top 30 %, +2.9 (-0.8, +6.9) at the top 50 % after the correction) |
| - | Refuted: patch-local features, patch words, drift-scaled deltas, file-level contagion, Hawkes-style decay, size-times-rate scores | sections 1.4, 1.5, 2.4 | refuted |

Your four ideas, with a verdict:

| idea | verdict |
|---|---|
| Code structure as an image, then a CNN | Works for **structural** debt only (E). On this data the CNN learns the host project (0.14 on unseen projects). Needs a different image: of the *edit*, at function level |
| The project as a graph, then a GNN | Same limit as the image: the file dependency graph is blind to 43 of 61 changes. A GNN would need a multi-granularity graph (calls, control flow, lock regions). With 61 pairs it cannot be trained; the experiments show *what* it must see |
| More data points by cutting the history into time windows | For **level 1** the time windows add no information (A), but they are the right tool to *test host-invariance*. For **level 2** the windows already exist (20,853 rows) and they are strongly dependent (G, H), so they do not add independent evidence. The scalable route is a different one: every commit and its parent form a natural pair (section 3) |
| The project and its history as a time series, with new features | The temporal analysis found what a time-series feature must capture: persistence without decay, change-proneness, a frozen flag, and a release clock that is **not** predictable from the past. The best new feature (change-proneness) is a +8-point gain at larger budgets (I) |

---

## 1. Level 1: the pair dataset (61 pairs)

### 1.1 Insight A: the clean twin cancels the host, so history windows add copies, not information

**What was done.** For every pair, the debt patch was applied to up to 5 earlier versions of its host project (release tags, or evenly spaced commits for C-Thread-Pool), and the 133 features were recomputed for the clean and the debt version of that older host. (`code/l1_context_shift.py`, `results/l1_context_td.csv`, `l1_context_clean.csv`.)

**What was found.**
- The patch applied in 188 of 305 attempts (62 %); 56 of 61 pairs have at least one older copy. boltons provides 95 of the 188 copies, werkzeug and libpng none (their patches do not apply to older code).
- The signature of the debt (the delta vector) in an older host is the same as in the original: cosine similarity median 1.00, sign agreement median 1.00, median relative change 3 % (`results/l1_context_stability.csv`, `figs/i9_context_augmentation.png`).
- Training on the 61 originals plus the 188 copies (all copies of a held-out pair or project removed from training) does not help: leave-one-project-out accuracy on the 37 non-boltons pairs 0.730 against 0.757 with RF, and 0.541 against 0.703 with the 10-best + RF (`results/l1_context_aug.csv`).

**Why (the latent mechanism).** The pair is a *difference of two copies that share the same host*. Everything that the host contributes (its size, its style, how far it has drifted) is the same in both copies and cancels in the difference. What remains is the edit, and the edit is the same text. Moving it to another version of the host cannot create a new example of the edit; it can only re-measure it.

**What it means.**
- Diversity must come from different **edits** (new templates, LLM-written variants, natural fixes), not from different hosts or dates. The effective sample size of the dataset is closer to the number of distinct edit templates (16 `td_subtype` values over 61 pairs; concurrency is 24 `lock_removed` and 2 `lock_pair_removed`) than to 61.
- The same property is a **strength**: the difference between a copy and its twin is host-invariant. That is why the twin design is worth keeping, and why it can be moved to history (section 3).

### 1.2 Insight B: seen alone, the debt is invisible

**What was done.** The clean copies at the 5 earlier versions plus the base commit are a time series of the 133 features of each project. The natural change of a feature between two such versions is compared with the change that the injection makes in the same feature (`code/l1_drift.py`).

**What was found.** The injection changes a feature in 31 % of the pair-feature cells (median 35 of 133 per pair). In those cells the injected change is a median of 0.01 times the natural change between versions; it is larger than the natural drift in 4.9 % of them. A typical pair has **1 of 133 features** above the natural drift (`results/l1_drift.txt`, `figs/i8_drift.png`). (The versions are a few releases apart, so the drift is larger than from one release to the next; the ratio is an upper bound on the gap, and still very far from 1.)

**What it means.** A model that looks at a single snapshot of a project cannot find a debt change of this size in global features. It works in this dataset only because the clean twin removes the drift (A). In practice there is no twin; the twin of a commit is its parent (section 3). The *dilution* is the same story in space: the median patch changes 9 lines in 1 file, which is 0.086 % of the lines and 5 % of the files of the project (`results/l1_dilution.csv`).

**A hypothesis that failed.** Scaling each delta by the drift of its own project (so that the features count in units of "natural change") did not help: leave-one-project-out accuracy on the 37 non-boltons pairs 0.68 against 0.76 (`results/l1_drift.txt`). With only 5 to 6 versions per project the drift scale is too noisy to normalise by.

### 1.3 Insight C: "does not generalise to unseen projects" was one project

**What was done.** The leave-one-project-out predictions were split by held-out project and by how the change was made (`code/l1_local_signal.py`, `results/l1_lopo_per_project.csv`, `l1_lopo_by_origin.csv`).

**What was found.**
| held-out project | pairs | accuracy (whole-project delta, RF) |
|---|---|---|
| boltons | 24 | **0.00** |
| click | 10 | 0.50 |
| jansson | 6 | 1.00 |
| jinja | 5 | 0.40 |
| libyaml | 5 | 1.00 |
| C-Thread-Pool | 4 | 1.00 |
| zlib | 3 | 0.67 |
| werkzeug, cJSON, libpng | 2, 1, 1 | 1.00 |

When boltons is held out, only 2 concurrency pairs are left in the training data, and the model predicts the other 24 as security. On the 37 pairs of the other 9 projects, the leave-one-project-out accuracy is 0.757 (RF) and 0.703 (the talk's 10-best + RF), against a majority baseline of 0.432.

**What it means.** The pooled number of the talk (0.43 without time, 0.51 with time) mixes two different failures. One is a *missing class* (concurrency exists in practice in one project) and has nothing to do with the representation. The other, the remaining error, is section 1.4.

**Change this in the talk.** Slide 15 says that the accuracy on new projects is very low "due to no knowledge of the project versions". Better: "the leave-one-project-out figure is dominated by boltons: without it, concurrency has only 2 training pairs. On the other nine projects accuracy is 0.70 to 0.76 against 0.43 for the majority". That is a stronger and more accurate result. Re-run the with-time model the same way before quoting a with-time number.

### 1.4 Insight D: the generator leaves a fingerprint (and three local-view ideas that failed)

**What was found.**
- Leave-one-project-out accuracy on unseen projects, boltons excluded: scripted injections (21 pairs) **0.95**; LLM-written SmellBench pairs (15 pairs) **0.47**, about the level of the majority within that group (`figs/i7_level1_generalisation.png`).
- A random forest separates LLM-written from scripted pairs with AUC **0.98** on held-out projects (`results/l1_origin.txt`). The two kinds of change differ in the feature space in a way that has nothing to do with the debt type.

**Why.** A script that inserts a lock removal, a null-check removal or an include cycle does it the same way in every project, so the delta looks alike across projects. A model that has learned "this is what inject_c.py does" will transfer across projects. LLM-written refactorings are different in each project and carry no such template.

**What it means.** The dataset has a hidden axis of difficulty, the *origin* of the change. Evaluating "by project" does not remove the generator template, and the number "unseen projects 0.70 to 0.76" mostly measures recognition of templates. To make a claim about natural debt, the dataset needs more LLM-written and natural pairs and must be evaluated by origin.

**Three hypotheses that failed** (all measured without the time feature, `results/l1_local_signal.txt`):
1. *"Use only the files the patch touches."* Features from the touched files (clean vs debt): leave-one-project-out on the non-boltons pairs 0.70 to 0.73, no better than the whole project (0.76). On LLM-written pairs 0.53.
2. *"Use the words of the patch."* TF-IDF of added and removed identifiers with a logistic regression: **0.885 on the stratified folds** (the same as the best model) but 0.59 on the non-boltons unseen pairs and 0.20 on LLM-written ones; trained on scripted pairs only and tested on the 16 LLM-written or natural pairs, 0.06. The words (`lock`, `mutex`, `null`, `bounds`) identify the template, which is why the stratified score is high.
3. *"Normalise by drift"* (section 1.2): no gain.

### 1.5 Insight E: the graph and the image see only the structural debts

**What was done.** The file dependency graph (imports for Python, `#include` for C) of the clean and the debt copy; the adjacency matrix as a 32 x 32 image; edit-graph features; a CNN (`code/l1_graph_image.py`, `l1_cnn.py`).

**What was found.**
- The dependency graph changes in **14 of 61** pairs: all 6 coupling pairs, all 7 dependency pairs, 1 of 6 complexity pairs, and **none of the 26 concurrency or the 16 security pairs** (`figs/i10_graph_visibility.png`). The median difference image has 0 pixels (of 32 x 32).
- Six edit-graph numbers (edges added or removed, nodes touched, nodes in cycles, ...) separate dependency-structure from the rest with AUC **0.95** (leave-one-project-out, 7 positive pairs).
- A small CNN on two channels (the debt copy and the difference) gives 0.574 with the shared folds and **0.144** with leave-one-project-out (5 seeds), below the majority of 0.426: it recognises the host project from the image of its graph.

**Why.** A lock that is removed, or a bounds check that is missing, is a property of the *inside of a function*. A file-level graph has no place to put it. Debt types live at different granularities: file graph (dependency, coupling), call and control-flow graph (complexity), lock and data-flow regions (concurrency, security).

**What it means.** Image, CNN and GNN ideas are right for the structural debts and structurally blind for 69 % of this dataset. A model for all five types needs a graph with several levels and nodes such as functions, lock regions and data flows, and, since 61 pairs cannot train it, it needs the data of section 3 or a pretrained code model on the *edit* (a diff), not on the project.

---

## 2. Level 2: the real histories (9 projects, 20 releases)

### 2.1 Insight G: interest is a persistent, very concentrated hot-spot trait

**What was found** (`code/l2_temporal_structure.py`, `l2_icc.py`, `figs/i1_concentration.png`, `i2_memory.png`):
- Of 1,540 instances, 768 ever pay interest. The top 1 % of instances hold 16 % of all interest, the top 10 % hold 70 %, the top 20 % hold 89 % (Gini 0.83). Among 1,080 instances observed for at least 10 releases, **501 (46 %) never pay interest**; the others mostly pay in 5 to 30 % of the releases (5 instances above 60 %).
- *Memory does not fade.* P(interest in release t) given interest at lag 1 to 6: 23, 21, 20, 24, 25, 22 %; given none: 7 %. The ratio is 3 to 4 at every lag.
- *Dose-response.* P(interest next release) by number of past events: 0 events 5 %, 1 event 9.5 %, 2 events 12.6 %, 3 to 4 events 20.7 %, 5 or more 43.7 %.
- *No age effect:* 9 %, 7 %, 5 %, 8 %, 9 %, 8 % for age 0 to 9+.

**What it means.** An instance is either in the path of the work (it is edited again and again) or frozen. A process in which a recent event makes the next one more likely (self-exciting, Hawkes-like) would show a decay with the lag; it does not. The right model is a **persistent rate per instance** estimated from all its history, which is what persistence does. Prioritising debt is therefore not about finding the worst code, it is about finding the code that is still being worked on.

**A hypothesis that failed.** *Contagion within a file*: if another instance in the same file paid interest last release, P(interest) is 7.1 % against 6.5 % otherwise (ratio 1.1), against 22.7 % when the instance paid itself. Interest is local to the function, not to the file.

### 2.2 Insight F: developers avoid debt

**What was done.** For each repository and release pair: the added or modified source lines inside the regions of debt instances (as in the interest calculation) divided by all added or modified source lines (`git diff --numstat`), compared with the share of the code that the debt regions occupy. If edits fell uniformly on code, the two shares would be equal (`code/l2_enrichment.py`, `figs/i3_enrichment.png`).

**What was found.** Debt regions are **31.8 %** of the source lines and receive **12.3 %** of the edits: enrichment **0.39**, below 1 in all nine projects (0.26 for libyaml, 0.28 for libpng, 0.85 for click).

**What it means.** Debt is not a magnet for work. Most of it sits in stable code that nobody changes, so it costs nothing *now* (and was kept as "debt" by a detector that looks only at size and complexity). It is the same fact as the frozen half in 2.1, seen from the code side. The cost of debt is paid only where the work goes, which is why history (persistence) beats static properties as a predictor.

**Caveat.** The total lines are counted with a line-based approximation (non-blank, non-comment lines), and the C regions are large functions that are often core algorithms. The direction is clear, the exact ratio is not.

### 2.3 Insight H: "where" is saturated, "when" is random

**What was done.** The ranking by persistence was compared with a ranking by the *true long-run hotness of each instance* (the mean interest over all other releases, which uses the future and is therefore not available to any real method), both evaluated on the next release (`code/l2_ceiling_horizon.py`, `figs/i4_ceiling.png`).

**What was found.** In the top 20 %: random 19 %, persistence 39.1 %, true long-run hotness **37.8 %**, perfect (realised value) 95.8 %. The same holds for horizons of 2, 3 and 5 releases (persistence 35.5, 31.9, 30.1; true hotness 36.5, 32.8, 30.3, with the target window excluded from the oracle).

The share of the variance of "this instance pays interest in this release" that belongs to the instance is small (ICC 0.134), to the file 0.125, to the repository 0.091, and to the **(repository, release) pair 0.280** (`results/l2_release_clock.txt`, `figs/i5_where_when.png`). The release totals are not related to the previous release's (within-project correlation of the event rate -0.01, of log total interest -0.06; 155 releases).

**What it means.** Interest is (instance hotness) x (release activity). The first factor is stable and already captured by persistence, with nothing left to gain from a better static or historical model *for ranking inside a release*. The second is a clock that nobody can predict from the debt data, which explains why the amount and the project total could not be predicted (R² below 0). Any further gain has to come from information about **when** work happens (planned release size, open issues and pull requests, maintainer activity, roadmap), which is not in the repository of the debt itself.

### 2.4 Insight I: cheap hotness scores beat persistence at larger budgets  **[corrected: see 2.5]**

**What was done.** Rules (no training) built from the history of an instance and one small learned model, evaluated on the same groups as the talk (123 groups leave-one-repo-out, 57 temporal), against persistence with a paired bootstrap (`code/l2_rank_models.py`, `results/l2_rank_models_paired.csv`, `figs/i6_hotness_vs_persistence.png`).
- *Event rate, shrunk*: (events + 2) / (releases + 2 / base rate). Stops an instance seen for 1 release with 1 event from outranking one with 6 events in 20.
- *Change-proneness*: the same shrinkage applied to "the region changed at all" (not only the interest lines).
- *Persistence with a size tie-break*: the many ties of persistence (instances with no history) are broken by region size (exposure).
- *Learned*: gradient boosting on these and the earlier features.

**What was found** (leave-one-repo-out, difference to persistence in points of capture; 95 % interval):
| score | top 10 % | top 20 % | top 30 % | top 50 % |
|---|---|---|---|---|
| change-proneness | +3.7 (-1.4, 8.4) | +3.2 (-2.9, 9.1) | **+8.1 (1.8, 14.2)** | **+8.3 (3.5, 13.4)** |
| event rate, shrunk | +4.2 (-1.0, 9.1) | +2.1 (-3.0, 7.4) | +5.8 (0.8, 10.7) | +5.3 (0.7, 9.8) |
| learned (GB) | +2.7 (-2.6, 8.1) | +2.5 (-3.3, 8.5) | +8.1 (2.1, 14.2) | +6.7 (1.5, 11.7) |
| persistence + size tie-break | +1.2 (0.0, 2.7) | +2.1 (-0.1, 4.9) | +2.7 (-0.2, 6.0) | +5.4 (1.8, 9.1) |

In the temporal protocol (57 groups) none of them differs from persistence (all intervals include 0).

**What it means.** The talk's statement "the model does not beat persistence" holds at the top 10 and 20 %, and it does not hold at the larger budgets, where simple hotness scores gain 5 to 8 points. The reason is that persistence knows nothing about instances that never paid interest and ranks them all equal, while change-proneness orders them by whether the *region* was changed. At the same time the ceiling (2.3) shows that at the top 20 % nothing can be gained from history.

**How far to trust it.** This is 4 budgets x 4 scores x 2 protocols = many looks; the temporal protocol does not confirm it; intervals are wide. Present it as a pattern and a hypothesis for the next run, not a result.

**Rules that failed:** a score of rate x expected magnitude (-3.6 points at the top 20 %): the size of an event is unpredictable, so multiplying by an estimate only adds noise.

---

### 2.5 Insight J (new): region size predicts interest as well as the history does, and corrects insight I
In 2.4 the hotness scores had a size tie-break and the persistence baseline of the talk had random ties; that alone explains a large part of the "+8 points". On the 123 real groups (`synthetic/results/s2_size.txt`, `s2_tiebreak_real.txt`): persistence with random ties 38.3 / 47.6 / 67.0 in the top 20 / 30 / 50 %; persistence with size ties 40.1 / 49.6 / 72.3; **size alone (largest region first) 40.1 / 51.4 / 73.4**; shrunk events with size ties 40.1 / 52.7 / 72.0; size x shrunk rate 40.9 / 54.5 / 76.1. No difference to persistence with size ties is significant (size x shrunk rate: +4.9 (+0.1, +10.0) in the top 30 %). The AUC of region size alone for "interest in this release pair" is 0.66 and the Spearman correlation of size with the event rate per instance is 0.31. Larger regions are edited more often (exposure), and a rule without history ties persistence. So: *persistence is not a strong baseline, it is a size proxy plus a little history*, and the earlier statement that no feature beats it should read that nothing tested beats **size**. See `synthetic/INSIGHTS_SYNTHETIC.md`.

## 3. What to do with this (ranked)

1. **Fix the unseen-project statement** (1.3) and recompute the with-time, leave-one-project-out numbers per project. Cheap, and it turns a weak result into a stronger one.
2. **Make pairs from history: a commit and its parent are a clean twin.** Insight A says that the twin cancels everything the host contributes; insight B says that without a twin the debt is invisible. Every refactoring, SATD-removal or fix commit in the 10 repositories (and in thousands of others) is a natural pair, with a label from the commit message or from a smell detector. The difficulty is that a real commit also contains other changes (drift), so the signal must be computed on the **touched functions** (1.4, 1.5), not on the project. This is the scalable and natural dataset the work lacks, and it removes the injection fingerprint (D).
3. **Evaluate by origin and by template**, not only by project: report scripted, LLM-written and natural separately (D); count the effective sample size as the number of distinct templates.
4. **Level 2 features, in order of expected value:**
   - change-proneness and shrunk event rate (done; I),
   - a *frozen flag* (no change of the region in the last N releases),
   - *path-of-work* features: distance, in the call graph or in co-change, to code that changed in the last releases,
   - *release-clock* inputs (planned release size, open pull requests and issues, commits since the last tag): the only way to predict "when" (H),
   - the evolution of the project's own feature series (volatility, trend), as a normaliser of the Level 1 delta (1.2, failed with 5 versions; it may work with a long series, e.g. one version per month).
5. **If you build a GNN or a CNN:** put the **edit** in the graph, at several granularities (file graph, call graph, lock and data-flow regions), and train on the data from step 2. Do not feed it the whole project (E, B, A).
6. **Re-state the claim of Level 2** for the talk: "debt is a persistent hot-spot trait; ranking inside a release is at its ceiling; the open problem is timing". That is a clearer message than "ties persistence".

## 4. Suggested changes to the presentation

- Slide 15 (Result 1): replace "accuracy is very low for new projects due to no knowledge of the project versions" by the boltons finding (1.3), with the per-project chart `figs/i7_level1_generalisation.png`.
- Slide 18 (Result 4): add one line "92 % zeros" -> "46 % of the instances never pay interest; the top 10 % hold 70 %" (`figs/i1_concentration.png`).
- New slide after Result 3: "Why persistence is hard to beat": memory without decay (`i2_memory.png`) and the ceiling (`i4_ceiling.png`).
- New slide: "Debt is avoided: 32 % of the code, 12 % of the edits" (`i3_enrichment.png`), as the motivation for ranking by activity.
- Limits slide: add "the graph/image view is blind to function-internal debt" and "injection leaves a fingerprint".

## 5. Caveats (read before quoting any number)

- **Sample sizes.** 61 pairs (10 projects, one with 24 pairs); 9 repositories for Level 2. The intervals of Level 1 are about +-0.10. Per-project accuracies rest on 1 to 10 pairs.
- **Many looks.** Section 2.4 compares 4 scores at 4 budgets in 2 protocols without correction. Treat it as exploratory.
- **Host copies.** 62 % of the patch applications succeed and 51 % of the copies come from one project (boltons). The stability result (A) is clear (cosine 1.00 over 188 copies), but it covers the hosts where the patch applies.
- **Drift.** Measured between versions that are several releases apart, on 5 to 6 versions per project. It is an upper bound for the release-to-release drift.
- **Enrichment.** Uses approximate line counts for the whole code base; the debt-instance definition differs by language.
- **Level 1 origin effect (D).** Based on 15 LLM-written pairs, all in click and jinja.
- **Time feature.** None of the above uses the time feature; the time model is an assumption (see the main README). The per-project and by-origin tables should be repeated with it.

## 6. Reproduce

`run_all.sh` lists every script in order and the Python it needs: a Python with scikit-learn, networkx, lizard, bandit and flawfinder (the `project_vector` venv of this machine was used), one with torch for the CNN, and matplotlib for the figures. The bare git clones of the 10 projects must be in `../repos` (`interest_exp/code/clone_repos.sh`). The context run (`l1_context_shift.py`) takes about 10 minutes on 4 cores.

| script | produces |
|---|---|
| `l2_temporal_structure.py` | concentration, memory, hazard, contagion, burstiness (`results/l2_temporal_structure.txt`) |
| `l2_rank_models.py` | hotness rules and a learned model vs persistence (`l2_rank_models*.csv`) |
| `l2_ceiling_horizon.py` | the ceiling and the horizons (`l2_ceiling_horizon.csv`) |
| `l2_icc.py`, `l2_release_clock.py` | instance, file, repository and release shares of variance (`l2_icc.txt`, `l2_release_clock.txt`) |
| `l2_enrichment.py` | debt-region share of code and of edits (`l2_enrichment.csv`) |
| `l1_local_signal.py` | dilution, touched-file features, patch words, per-project and by-origin accuracy (`l1_local_signal.txt`) |
| `l1_graph_image.py`, `l1_cnn.py` | graph visibility, edit-graph features, CNN (`l1_graph_image.txt`, `l1_cnn.txt`) |
| `l1_context_shift.py` | the patch in older hosts (`l1_context_td.csv`, `l1_context_clean.csv`) |
| `l1_drift.py`, `l1_context_aug.py` | drift against injected change; stability and augmentation (`l1_drift.txt`, `l1_context_aug.txt`) |
| `make_insight_figures.py` | `figs/i1` to `i10` |
