# Your work explained in depth: what you did, why, and what it means

This is a study guide for you, not a speech. Read it before presenting. Every number comes from files in `final_folder` (the file is named next to the numbers). Where something is an interpretation and not a measured fact, I say so.

Contents
1. The whole story in one minute
2. The key ideas (technical debt, principal, interest, prioritisation)
3. How the dataset was built from scratch, and why each step
4. The features: what a vector is and why it looks like this
5. The time feature: what it is, why it exists, how it was made, what it can and cannot show
6. Level 1: the debt-type classifier, step by step
7. Level 2: interest from git history, step by step
8. How a prioritisation is evaluated (the core of your work)
9. Results, and why each one came out that way
10. Slide by slide: what to understand behind each slide
11. Mistakes found along the way (this shows rigour)
12. What you can claim, what you cannot
13. Questions you may get, with answers
14. Glossary

---

## 1. The whole story in one minute

1. Teams always have more technical debt than they can repay, so they must choose what to fix first. That choice is **prioritisation**.
2. Papers on prioritisation say: no agreed factors, no validated tools, no benchmark with a known right answer. So nobody can say whether a ranking is good.
3. To test a ranking you need data where you know the truth. You built two kinds:
   - **Pairs of projects** (clean version vs version with one injected debt of a known type). Here the truth is the debt type, and a fix-time label says how costly it is.
   - **Real project histories** (git). Here the truth is the interest that debt really absorbed in later releases.
4. On the pairs, a classifier tells which debt type a change introduces. On the histories, a model predicts which debt instances will absorb future rework (interest), measured in person-months with COCOMO II.
5. You then **evaluated the ranking**: how much of the real future interest falls in the top 20% of your ranking, against random, against a simple history rule, and against a perfect ranking.
6. Findings: the ranking is about 1.9 times better than random in the top 20% (38.5% of the interest vs 20%), but a simple rule ("rank by interest already paid") does as well (38.8%). The amount of interest per item cannot be predicted. The gain from the time feature depends on an assumed time model.

So the honest message is: **a working, reproducible way to build and evaluate a prioritisation, with results that beat chance but not yet the simple baseline.**

---

## 2. The key ideas

**Technical debt (TD).** A shortcut in the code that saves time now and costs more later. Examples in your work: a very complex function, code with missing locks, tight coupling between modules, import cycles, missing input checks.

**Principal.** The effort to remove the debt once (rewrite or refactor the function). In your interest experiment: COCOMO II effort of the size of the smelly function.

**Interest.** The extra effort paid *because* the debt is still there. In the 2025 method you follow: when a function with a smell is changed while the smell persists, the lines changed inside it are interest. You then turn those lines into person-months.

**Prioritisation.** Putting debt items in an order so that repaying the top ones gives the most benefit. The benefit you use is "interest avoided" (type level: fix time).

**Evaluating a prioritisation.** Asking: if I had followed this order, how much of the real cost would I have caught in the first k percent, compared with a random order and the best possible order? This is the main goal of your talk.

Why two levels?
- Level 1 (type, with a fix time) works on the injected pairs, where the truth is controlled. It says *what kind* of debt is costly.
- Level 2 (interest) works on real histories, where debt actually cost something. It says *which instance* will cost.
They use different data because the injected debt has no later history (so no real interest), and the real projects have no labelled debt type.

---

## 3. How the dataset was built from scratch, and why

### 3.1 Why pairs of whole projects

A paper's dataset often gives single code snippets. Your plan (from your own `dataset.pdf` notes) was different: each data point is a pair of **whole projects**, D = (P_clean, P_TD). Reasons:
- The debt types you care about (coupling, dependency structure, concurrency) are *project-level* properties. A snippet cannot show an import cycle or fan-in/fan-out.
- A pair isolates the effect: everything is identical except one debt change, so the difference between the two vectors is the signature of the debt.
- Whole projects have real tests, so you can check that the TD version still works (the change is behaviour-preserving, like real debt).

### 3.2 Why these five debt types

complexity, concurrency, coupling/cohesion, dependency structure, security. They are the types for which you could (a) inject a small change and (b) measure with a metric of that type (cyclomatic complexity, lock counts, import-graph edges and cycles, security findings and validation guards). Together they differ a lot in how costly they are to fix, which is what the prioritisation needs.

### 3.3 Why Python and C/C++

Both are common in the debt literature, and they give two different tool settings: Python can use SonarQube; C/C++ needs structural detectors (see section 7). You first tried to finalise only Python, then added C/C++ for concurrency and security, because those were thin in Python.

### 3.4 The funnel, stage by stage (from `results/01_dataset.md`)

| stage | pairs | what happened and why |
|---|---|---|
| A. Candidates | 178 recorded for Python, 40 rejected | The patch did not apply, or tests failed. Rejecting these keeps only valid, working pairs. |
| B. Folder structure | 102 (Python 71, C/C++ 31) | You removed very large projects (numpy, pandas, scikit-learn, seaborn, xarray: too big to run), flagged pairs whose TD side failed tests, and pairs without a test run. C/C++ had 20 injected + 11 natural pairs from a security-debt dataset (libpng 6, libxml2 4, zlib 1). |
| C. Metric audit | 52 | A pair stays only if a metric of its **own type** moved in the debt direction. You did this because you asked yourself: "a one or two line change can introduce the TD, is it really TD?" The audit is the answer: if the type's own metric does not move, you cannot claim the change is that debt. 50 pairs removed. |
| D. Added projects | 61 | You added C-Thread-Pool (4 pairs) and libyaml (5 pairs). expat passed but each pair was 260 MB, so it was left out. |

Why the audit removed what it removed: all C/C++ coupling pairs (functions moved between modules) and 10 of 11 natural pairs, because the import-graph and flawfinder metrics cannot *see* those changes. Your own wording in the results: "not moved" means "not visible to these metrics", not "not debt". That is a limit to state honestly.

After that the projects were trimmed (docs, CI, examples removed; dataset 208 MB to 100 MB). The tests were run before trimming and the result is stored in each `properties.txt`.

### 3.5 What the final 61 pairs look like

By type: concurrency 26, security 16, dependency structure 7, coupling/cohesion 6, complexity 6.
By language: Python 41, C/C++ 20. By project: boltons 24, click 10, jansson 6, jinja 5, libyaml 5, C-Thread-Pool 4, zlib 3, werkzeug 2, cJSON 1, libpng 1.
Sources: 45 scripted or hand-written injections, 15 SmellBench-style (LLM-written refactorings), 1 natural (libpng, a real vulnerability fix).

Important consequence: **boltons gives 24 pairs, all concurrency.** So project identity and debt type are tangled. That is why, when you hold out a whole project, accuracy collapses (section 9.2).

### 3.6 Why injected, not collected from real history

Real debt has no label for its type and its introduction cannot be cleanly separated from other changes. Injection gives a **known type, a known location and a known clean twin**. The cost: 60 of 61 are artificial, so results may not transfer to natural debt. The one natural pair is a start.

### 3.7 Why bugs, 3 per pair, same on both sides

You wanted a **time to fix** that reflects how debt makes work harder. The idea: take the same bug and fix it in the clean project and in the TD project; the extra time in the TD project is the "cost" of the debt. So:
- 3 bugs per pair (183 total), made by small mutations (flip a comparison, change a boundary, negate a condition, off-by-one, swap an operator).
- The **same patch** goes into both versions, so the only difference is the surrounding debt.
- 70 of 183 bugs are in a file that the TD change also touched.
- Checks: bugged Python files all parse (246/246), bugged C files pass a syntax compile (59/59), and re-running the injection reproduces identical patches. **Not done:** proving each bug makes a test fail. A partial attempt caught only some (e.g. boltons 12 of 24) and was stopped; nothing from it is used. Say this if asked.

### 3.8 Background data you also collected

- Git history per project (commits, authors, bug-fix commits found from messages like "fix", "crash", "CVE").
- **SZZ** bug mining: take the lines a bug-fix changed, trace them back to the commit that last touched them, and call that the bug-introducing commit. Gives bug lifetimes (median from 40 days in jinja to 830 in libyaml).
- SonarQube export: 52 projects, 10,727 issues on the server; 36 of 61 pairs have a scan (all Python, since the Community edition has no C/C++ analyser). These are **not used as model features** because coverage is partial.

---

## 4. The features: what a vector is

Each project (clean or TD) is turned into one row of **133 numbers** in three blocks:
- **Structure (46):** import/#include graph (33 numbers: edges, fan-in, fan-out, cycles, PageRank entropy...) and directory layout (13).
- **Code (50):** idioms (8 C, 11 Python), function statistics (20: size, cyclomatic complexity, parameters, tokens), line counts and comments (11).
- **TD (37):** class cohesion (4), code smells and their COCOMO principal (15), concurrency idioms (6), duplicated code (2), security findings and validation guards (3), self-admitted debt in comments (7).

Two layouts:
- `full`: clean values, TD values and the difference, 399 columns (+ time).
- `delta_only`: only the difference (TD minus clean), 133 columns (+ time).

Why the difference matters: the delta says *what the debt changed*, independent of which project it is. The full layout lets the model see project identity, which is the main source of leakage (the debt change is small compared with differences between projects: mean |delta| / std = 0.008). That is why the final model uses `delta_only`.

Sanity checks you ran: 0 missing values, 0 infinite values, 1 of 133 features constant, and 0 pairs where the TD vector equals the clean vector.

---

## 5. The time feature

### 5.1 What it is
`time_diff_min` = minutes to fix the 3 bugs in the TD project minus in the clean project (sum over the three).

### 5.2 Why you included it
The point of debt is that it makes later work slower. A fix-time difference is a direct cost signal, so it is the natural input for a cost ranking, and you wanted to test whether knowing the cost helps decide the debt type.

### 5.3 How the values were made (important to understand)
You had no developers fixing 183 bugs on 122 project versions. So the values come from a **ground-truth time model** (`pipeline/bug_injection/sample_times.py`; `time_source = sample` in `bugs.csv`):
- clean time per bug = 25 min × a random factor (log-normal);
- TD time = clean time × (type factor) × small noise;
- type factors: concurrency 3.4, security 2.4, complexity 1.8, coupling 1.4, dependency 1.05;
- bugs outside the TD-touched file get a weaker factor (0.85 of the effect).
- The model does **not** use the code, the project or the bug kind. Only the type and whether the file was touched.

You asked twice to describe this as a survey result. I did not, because it is not one. The agreed wording is "ground-truth time model". If an examiner asks "how did you get times?", say exactly this: "from a time model with assumed per-type factors, to be replaced by measured times."

### 5.4 What it can and cannot show
- The factors were chosen **after** seeing how the classifiers behaved. The weakest of four settings gave no gain and was replaced (`results/04_time_feature.md`, section 4.3).
- Time alone predicts the type with 0.93 accuracy. That is because the model builds the time *from* the type. So the time is almost a label.
- Therefore: the gain from adding time (for example 0.79 to 0.92) tells you the pipeline can use a cost signal. It does **not** tell you real developers behave like that.
- Controls that support the pipeline (not the time model): **shuffled time** gives zero gain (0.840 to 0.839), so the gain is not a leak from other features. **Noisy time** loses the gain as noise grows (log-noise 0.5 keeps 44% of the gain, 1.0 keeps 0%).

### 5.5 Why it matters for prioritisation
The type-level ranking says concurrency and security are the costliest. That ranking comes straight from the factors you set. It is a consistent *illustration* of cost-based ranking, not a discovery. When you get measured times, this result must be redone.

---

## 6. Level 1: the debt-type classifier

### 6.1 Task
Input: the feature vector of a pair. Output: one of 5 debt types. With time: one extra input.

### 6.2 Why seven classifiers
To check whether the effect of time depends on the algorithm: random forest, gradient boosting, logistic regression, SVM, kNN, and two with feature selection (the ten best features, then random forest or logistic regression). Settings fixed, nothing tuned on a test fold.

### 6.3 Why the ten-best-features selector
With 61 rows and 133 features, a model can drown in noise. The selector (`SelectKBest`, ANOVA F, k=10) keeps the ten most class-separating features **inside each training fold**, so the test fold never influences which features are chosen. That is leakage-safe. In your data `time_diff_min` is the **top-ranked feature** (F = 120). So the selector always keeps it, and the model with time gains clearly. A plain random forest uses all 133 features and mixes in many weak ones, so adding one more feature changes little. This is my explanation of why the selector shows the gain and the plain forest does not. It fits the numbers, but you did not test it separately, so say "likely".

Caution: the final model was picked because it showed the time effect clearly, not on a separate held-out set. This is listed as a multiple-comparison threat. Say so if asked "did you choose the model to get the result?"

### 6.4 Why four evaluation protocols
Each answers a different question and has a different leakage risk.

| protocol | what it does | what it tells you |
|---|---|---|
| given stratified (5 folds) | folds keep the type proportions | optimistic; pairs of the same project appear in train and test |
| 20 random stratified splits | repeats the above 20 times | stable average, gives a spread |
| given by project (5 folds) | a project is in one fold only | tests unseen projects |
| leave-one-project-out (10 folds) | each project held out once | strictest test of generalisation |

### 6.5 Results (kbest10 + random forest, delta_only, accuracy)

| protocol | without time | with time | change |
|---|---|---|---|
| given stratified | 0.787 | 0.918 | +0.131 |
| 20 random splits | 0.840 | 0.938 | +0.098 |
| given by project | 0.311 | 0.508 | +0.197 |
| leave-one-project-out | 0.426 | 0.508 | +0.082 |

Baselines: majority class 0.426 (concurrency = 26 of 61), time alone 0.934.
Significance (given stratified): 95% CI of the gain +0.05 to +0.23, McNemar p = 0.008. Leave-one-project-out is borderline (p = 0.062). Across 8 comparisons, 7 were clear and 1 borderline.

### 6.6 Why unseen projects drop to about 0.43 to 0.51
Pairs of one project share a type (boltons = 24 concurrency pairs). Inside one project, the model can learn "this project's fingerprint means concurrency". Hold the project out and that shortcut disappears, leaving a model with little real signal. Without time, leave-one-project-out accuracy is 0.426, which equals the majority baseline. So **without time the model does not generalise yet.** This is a real weakness, and the honest reading.

---

## 7. Level 2: interest from git history

### 7.1 Why a second level
The pairs have no later history, so no real interest. To rank real debt instances by cost you need real projects with releases. That is the interest experiment (`interest_exp/`), based on the 2025 method of Wiriyakul and Senivongse (full citation still to be added).

### 7.2 Step by step
1. **Versions.** Last 20 release tags per project. C-Thread-Pool has no tags (0), so it is not in the interest set; libyaml has 13. That is why the interest set is **9 projects**, not 10.
2. **Debt instances.**
   - Python: SonarQube issues (a stable key per issue).
   - C/C++: structural smells found by a detector: long method (more than 50 lines of code), complex method (cyclomatic complexity above 10), many parameters (more than 5). Needed because Community SonarQube has no C/C++ analyser.
3. **Region.** The function that contains the instance.
4. **Changed lines.** `git diff -U0` between consecutive releases: count added and modified source lines in that function (comments, blank lines and deletions not counted).
5. **Classification between two releases:**
   - instance gone = **repayment**;
   - instance new = **principal increase**;
   - instance persists: growth of the function = principal increase; remaining changed lines = **interest lines**.
6. **Convert to effort.** COCOMO II: `PM = A × (KSLOC)^E` with A = 2.94 and E = 1.0997 (all effort multipliers 1, nominal scale factors).

### 7.3 A worked example
A smelly function receives 100 changed lines that are not growth.
`PM = 2.94 × (100/1000)^1.0997 = 2.94 × 0.0795 = 0.234 person-months`.
Because E is above 1, the same 100 lines split into 10 events of 10 lines cost less: `10 × 2.94 × (0.01)^1.0997 = 0.186`. That is why effort is computed **per event**, and why the number is a relative estimate.

### 7.4 What the calculation gave
20,853 instance-releases, 1,557 distinct instances, 1,607 interest events, 5,572 reworked lines, **10.52 person-months of interest** in total (0.09 to 2.44 per project), around 6% of the effort to rewrite all debt once. Reproducibility check: all 9 transition files regenerated from the git histories were identical.

### 7.5 Why this is "COCOMO II enhanced with git history"
COCOMO II normally takes the size of a whole project. You keep the formula and use git history to decide **which lines** are the size: the lines re-worked inside persisting debt. The history also gives features for prediction (age, interest paid so far, number of events).

### 7.6 Predicting interest: three targets
- **Any interest in the next release** (yes/no). Works weakly: AUC 0.59 on unseen projects, 0.71 on later releases (chance 0.5).
- **Amount in person-months.** Does not work: no model beats predicting zero. Why: about 92% of instance-releases have no interest at all (8.1% have any), and the few positives are heavy-tailed (some very large). A regression gets nothing from a spike of zeros plus rare outliers.
- **Two-part (hurdle) model.** First predict if interest occurs, then how much. Project total = 1.14 times the actual (right order of magnitude), usable for budgeting a portfolio, not for single items.

### 7.7 The earlier model that was dropped
Your first model predicted a COCOMO effort of the *injected patch*, with R² 0.90. Re-checking showed the target was an exact function of the patch size (`Lines_Added`), so it predicted size, not debt effort; with a project-held-out test the same model had R² below 0 (-0.43). It was replaced by the current design. Keep this in mind as an example of why you evaluate carefully.

---

## 8. How a prioritisation is evaluated (the core)

### 8.1 Setup
- **Unit of ranking:** one group = one repository at one release. Inside it you rank all debt instances.
- **Ground truth:** the interest each instance really absorbed in the **next** release (`actual_mPM`; mPM = milli person-months).
- **Ranking:** by predicted interest (higher first). Ties broken at random (this matters for the "zero" model, which predicts zero for everything: it becomes a random ranking).
- **Groups used:** only groups with at least 10 instances and some real interest. 123 groups (leave-one-repo-out) and 57 (temporal: train on earlier releases, test on later).

### 8.2 Metrics (and what each one tells you)
- **Capture@k:** share of all real interest in the group that falls in your top k%. A random ranking gets k%. Easy to explain: "if I only fix the top 20%, how much of the cost do I catch?"
- **Precision@k and lift:** fraction of the top k% that really paid interest, and that fraction divided by the base rate (lift 1.9 = 1.9 times more likely than a random pick).
- **NDCG@20:** like capture but rewards getting the biggest ones first. Yours is about 0.21, so order inside the top is weak.
- **Spearman rho:** rank agreement over all instances (about 0.14).
- **Bootstrap 95% CI:** resample the groups 2,000 times to see the uncertainty.

### 8.3 Baselines (what each one is for)
- **Random / zero:** lower bound. If you do not beat it, the ranking is useless.
- **Persistence:** rank by interest already paid. This is the "simple rule a manager could apply with no model". Beating it is what shows the model adds value.
- **Oracle:** sort by the real future interest. Upper bound (about 96% in the top 20%).

### 8.4 Why these choices
- Capture is used because the practical question is budget-limited: "I can fix k% of items".
- Groups are per release because a team prioritises at a given moment, not over the whole history.
- Leave-one-repo-out because the ranking must work on a project it has not seen.
- Temporal because the real use is "train on the past, rank the future".

---

## 9. Results, and why they came out that way

### 9.1 Result 1: instance ranking (leave-one-repo-out, 123 groups)

| model | top 10% | top 20% | top 30% |
|---|---|---|---|
| random (by definition) | 10% | 20% | 30% |
| zero model (ties = random) | 9.6% | 18.6% | 30.6% |
| persistence | 21.7% | 38.8% | 46.9% |
| RF regression | 17.2% | 35.0% | 48.9% |
| hurdle RF | 20.0% | 38.5% | 51.5% |
| oracle | 89.9% | 95.8% | 98.1% |

Hurdle top 20%: 95% CI 32.4% to 44.4%. NDCG@20: hurdle 0.21, persistence 0.23. Lift at 20%: about 1.9.
Temporal (57 groups): hurdle 28.2% at top 10% and 41.9% at top 20%; persistence 23.4% and 39.1%; intervals overlap.

**Why it came out like this.**
- The learned models beat random because debt that already absorbed rework keeps absorbing it (rework concentrates in a few "hot" functions).
- Persistence is as good because it uses exactly that signal directly. The features of the learned model (age, past interest, size, complexity) are mostly proxies of the same signal, so they add little.
- The gap to the oracle is large because many positives are one-off events that no history predicts.
- Spearman of 0.14 and NDCG of 0.21 are low for the same reason.

What you can say: "the ranking captures about 1.9 times more of the future interest than random." What you cannot say: "it beats a simple history rule."

### 9.2 Result 2: type level
See 6.5 and 6.6. What you can say: the pipeline can use a cost signal, and with it the classifier is more accurate (shuffled control shows it is not a leak). What you cannot say: that real developers' times behave like this, or that the classifier generalises to unseen projects.

### 9.3 Result 3: interest predictability
See 7.6. Message: **ranking is possible, amount estimation is not.**

---

## 10. Slide by slide: what must be clear behind each slide

| slide | message | behind it you must know |
|---|---|---|
| 1 | Debt grows faster with AI code, teams must choose | the four statistics and their sources (section 12 warns which to verify) |
| 2 | Real incidents show cost, no validated ranking | Amazon is "reported, disputed" |
| 3 | Prioritisation literature: no consensus, no validated tools | 4 papers, one finding each |
| 4 | Interest/cost literature: interest is central but hard to measure; violation count is a weak rank | why you chose interest in person-months |
| 5 | AI-era work and benchmarks: need ground-truth benchmark | SmellBench injects smells; you follow the idea at project level |
| 6 | Two levels and one evaluation | why two data sources |
| 7 | Dataset funnel | section 3.4 (102 to 52, +9 = 61) |
| 8 | 133 features, time label | section 4 and 5, say "assumed model" |
| 9 | Classifier and interest model | why selector inside folds, why three targets |
| 10 | Interest calculation | section 7, the worked example |
| 11 | Evaluation design | section 8 |
| 12 | Main result: 38.5% vs 20% | persistence 38.8% |
| 13 | Type level and time | time alone 0.93, unseen projects 0.43 to 0.51 |
| 14 | What interest prediction can do | any-interest weak, amount no, total yes |
| 15 | Next steps | real times, richer features, cost-aware metric |
| 16-17 | References | item [12] needs a full citation |

---

## 11. Mistakes found along the way (say these to show rigour)

- **First prediction model (R² 0.90)** predicted the size of the patch, not debt effort; under project-held-out test R² was -0.43. Replaced.
- **Join key bug:** pair names repeat in `Python/` and `C/C++/`, so a join on name alone mixed rows. Fixed.
- **Relative-change blow-up** when a feature is near zero: fixed by normalising with the feature's standard deviation.
- **Principal = 0** for instances that appear mid-run: fixed by using principal at first appearance.
- **Time model calibrated after seeing the classifiers:** documented as a threat, with shuffled and noisy controls.
- **Bugs not validated by tests:** documented, not hidden.

---

## 12. What you can claim, and what you cannot

**You can claim**
- A reproducible dataset of 61 clean/TD pairs with 183 bugs and 133 features, and a reproducible interest calculation (10.52 person-months, 9 projects).
- An evaluation framework for prioritisation (capture@k, lift, NDCG, baselines, bootstrap CIs).
- The learned ranking captures about 1.9 times more of the real future interest than random in the top 20% (38.5% vs 20%).
- Any-interest prediction is weak but above chance; amount per instance is not predictable.

**You cannot claim**
- That your model beats the simple persistence rule.
- That the time feature comes from developers, or that real time gain equals the reported gain.
- That the type classifier works on unseen projects (about 0.43 to 0.51).
- That injected debt behaves like natural debt (60 of 61 are injected).
- That COCOMO person-months are real developer hours (multipliers not calibrated).

**Check before presenting (not verified in this work):** 233 AI incidents (Stanford AI Index 2025), Veracode 45%, IBM 97%, GitClear and CISQ figures, and the Amazon details. The 22.7% figure and the three arXiv papers (Liu 2603.28592, Ehsani 2606.14796, SmellBench 2606.05574) were checked against their pages. The Wiriyakul and Senivongse citation is incomplete.

---

## 13. Questions you may get

**Why inject debt instead of using real debt?** Known type, known place and a clean twin give a controlled truth. Cost: artificial. One natural pair (libpng) is included as a start; more natural pairs are future work.

**How do you know a small change is really debt?** The metric audit: a pair stays only if a metric of its own type moved in the debt direction. 50 of 102 failed and were removed. It also means some real debt is not captured by these metrics.

**Why is time so important in your results?** It is not independent evidence. It comes from an assumed model, alone gives 0.93 accuracy, and was calibrated after seeing the classifiers. The controls only show it is not leaking other features.

**Why is the classifier bad on unseen projects?** Pairs of a project share a type (24 boltons pairs are concurrency), and the change is small relative to between-project differences (0.008 of one standard deviation on average). The model learns the project more than the debt.

**Why does persistence do as well as the model?** Past interest is the strongest predictor of future interest, and my features are proxies for it. Richer features (change-proneness, ownership, test coverage) are the next step.

**Why is the amount not predictable?** About 92% of instance-releases have zero interest, the rest are rare and heavy-tailed; no model beats predicting zero in MAE.

**Why COCOMO II and not SonarQube's remediation time?** The method I follow uses COCOMO II, which turns changed lines into person-months. SonarQube's remediation time is a rule-based estimate and papers report it as inaccurate (Baldassarre et al. 2020).

**Why 9 projects for interest, not 10?** C-Thread-Pool has no release tags, so there is no version history to follow.

**Could the results be luck, with so few pairs?** Possibly in part: 61 pairs, class sizes 26/16/7/6/6, one pair equals 1.6 accuracy points, CIs about ±0.10. For the ranking, the CI over 123 groups is clearly above the random 20%.

**What is the novelty?** Putting together (1) a whole-project pair dataset with five debt types, bugs and a cost label, (2) an interest calculation in person-months from git history, and (3) a ranking evaluation with baselines and confidence intervals. The literature lacks a ground-truth benchmark for prioritisation.

---

## 14. Glossary

- **TD:** technical debt.
- **Principal:** effort to remove the debt once.
- **Interest:** extra effort caused by debt that stays; here lines reworked inside persisting smelly code, in person-months.
- **COCOMO II:** effort model `PM = A × KSLOC^E × (effort multipliers)`.
- **SZZ:** method that links a bug-fix to the commit that introduced the bug.
- **SATD:** self-admitted technical debt (comments like "TODO", "hack").
- **CCN:** cyclomatic complexity number.
- **Delta:** TD vector minus clean vector.
- **LORO / LOPO:** leave-one-repo-out / leave-one-project-out.
- **Capture@k:** share of real interest found in the top k% of the ranking.
- **Lift:** precision in the top k% divided by the base rate.
- **NDCG:** ranking quality that rewards putting the largest items first.
- **Hurdle model:** two-part model: will interest occur, and how much.
- **Oracle:** the best possible ranking using the true future values.
- **Persistence:** baseline that ranks by interest already paid.
- **mPM:** milli person-month (0.001 person-month).
