# Script for TD-presentation.pptx (final deck, 21 slides)

Written for: you, the presenter, in front of an examiner.

Contents
- Part A: spoken script, slide by slide (about 14 minutes, about 2,300 words). Slides 20 and 21 are references and are not spoken.
- Part B: the results explained in depth: what each result means, what it does not mean, and how to say it.
- Part C: the architecture and what was done, stage by stage (use it to answer "what exactly did you do?").
- Part D: questions the examiner can ask, with answers.
- Part E: numbers to keep in your head, and rules for answering.

Slide numbers are the positions in the file and match the numbers printed on the slides.

How to speak this: the script is written to be said, not read. Look at the slide while you say the numbers. When a sentence has a number in it, pause after it.

---

# PART A: SPOKEN SCRIPT

## Slide 1: title (15 s)

Good morning. I am Souhardya Dandapat. My project is called Characterising AI-Induced Technical Debt and Its Impact on Software Maintenance. In the next fourteen minutes I will show how I built a dataset to study technical debt, how I rank debt items, and, mainly, how I test whether the ranking is any good.

## Slide 2: why this matters (45 s)

The question behind the project is simple. When a team has more technical debt than it can repay, what should it fix first?

It matters more now because of AI-generated code. The Stanford AI Index counted 233 reported AI incidents in 2024, which is 56 percent more than the year before. Veracode found a security flaw in 45 percent of the AI-generated code samples in its benchmark. And a study of more than six thousand repositories found that 22.7 percent of the issues introduced by AI-written commits are still in the code at the latest revision. These numbers come from different studies, so I read them as signals, not as one population.

So code is written faster, debt builds up faster, nobody can repay all of it, and the team has to rank. The two things I work on are the ranking, and the evaluation of the ranking. For the second one, no standard benchmark exists.

## Slide 3: incidents and the gap (30 s)

Some concrete cases, with causes as reported by their sources. The Financial Times reported a long AWS outage in December 2025 after a change by an AI coding agent; Amazon disputes the AI cause and blames an access misconfiguration, so I present it as reported, not proven. A Replit agent deleted a production database during a code freeze in 2025. GitClear measured more duplicated code and less refactoring in the AI period.

What I take from these: changes land faster than people can review them, and what to repay first has no validated answer. So my question is: does a ranking by predicted cost beat chance, and does it beat a simple rule?

## Slides 4, 5, 6: literature (about 1 minute 40 s in total)

I read twelve papers, in three groups.

Slide 4, prioritisation. Lenarduzzi and colleagues reviewed 44 primary studies and found no consensus and no validated tools. Alfayez and colleagues found that how teams value debt is subjective. Baldassarre and colleagues showed that SonarQube's remediation time is often inaccurate. Biazotto and colleagues found that debt-management automation is not integrated. So I need ranking criteria I can measure, and a way to test them.

Slide 5, interest. Ampatzoglou and colleagues call interest the central idea, and hard to measure. Digkas and colleagues propose a risk-of-interest metric. Lenarduzzi and colleagues found that SonarQube issues have only a small effect on faults, so counting violations is a weak ranking. The interest method I implemented is from Wiriyakul and Senivongse: the rework inside a code smell that persists, converted to effort with COCOMO II.

Slide 6, the AI era and data. Liu and colleagues studied 302 thousand AI-written commits, and 22.7 percent of the issues are still present. Ehsani and colleagues reviewed 104 sources and found no standard benchmark. SmellBench injects smells into clean real code so every case has a known answer. What is missing is a benchmark where the type, the cost and the future interest are known. I follow the injection idea, but with whole projects, five debt types and a time label.

## Slide 7: the architecture (50 s)

This is the whole work, left to right, on one slide.

Data creation: ten open-source projects, a clean copy and a debt copy of each, three bugs injected, plus the git history of nine real projects. Characteristics: 133 numbers per project, a fix-time label per pair, and an interest value in person-months for every debt instance in the history. Prediction has two levels. Level one says which type of debt a change introduces. Level two says which debt instance will absorb future work. Output: a ranking of debt types by cost, and a ranking of instances within a release. Evaluation, which is the main goal: protocols that avoid leakage, and comparison with random, a simple rule, and a perfect order.

Look at the black labels. They name the tool behind each step, and the italic line under each column says what that stage means. Level one runs on the injected pairs, level two runs on real history, and they are two separate experiments joined by the idea of ranking by cost.

## Slide 8: dataset creation (55 s)

How I built the dataset. A snippet cannot show an import cycle or a fan-in, so each data point is a pair of whole projects, one clean and one with a single injected debt.

I took ten open-source projects with test suites, four Python and six C or C++. For each pair I made one small change that introduces a debt of one of five types, so the type, the place and the clean twin are known. Sixty are injected, 45 by scripts and 15 in the SmellBench style, and one is a real libpng fix. The debt copy must pass the project's own tests, because real debt does not break behaviour.

Then the audit. Can a change of one or two lines really be debt? I keep a pair only if a metric of its own type moved. Of 102 candidates, 52 stayed. The 50 dropped are not "not debt", they are "not visible to these metrics", and with richer features they could come back. I then added nine pairs from two more projects, C-Thread-Pool and libyaml, giving 61.

## Slide 9: the dataset as it stands (40 s)

This is the dataset. Each row is one pair, and the model sees the difference between the debt copy and the clean copy: 133 numbers in three blocks. Structure, 46: layout, and the dependency graph with fan-in, fan-out, cycles and modularity. Code, 50: size, function length, complexity, parameters and language idioms. Debt, 37: smells and their COCOMO principal, class cohesion, locks and threads, security findings, self-admitted debt and duplication. Plus one time number and the target, the type.

Remember one number from the chart: 24 of the 26 concurrency pairs come from one project, boltons. It comes back in the results.

## Slide 10: bugs and the fix-time label (60 s)

Why a time number? Debt makes later work slower. So the same bug goes into the clean copy and into the debt copy, and the extra time to fix it in the debt copy is the cost of the debt. There are three bugs per pair, 183 in total, small mutations such as a negated condition or an off-by-one, with the same patch in both copies. I checked that all 246 bugged Python files parse and all 59 C files pass a syntax compile; I did not run the tests on them.

The time comes from a ground-truth time model with a slowdown factor per type: concurrency 3.4, security 2.4, complexity 1.8, coupling 1.4, dependency 1.05. That gives about 162 extra minutes per concurrency pair and 3 minutes per dependency pair. I set the factors after seeing the classifiers, and time alone predicts the type with 0.93 accuracy. So, any gain from time depends on this model.

## Slide 11: Level 1, the classifier (50 s)

Level one: which of five types does a pair introduce. The final model takes the 133 delta features plus time, a selector keeps the ten best by ANOVA F, and a random forest with 300 trees and balanced class weights gives the type. With 61 rows and 134 columns a model drowns in noise, so the selector helps, and it is fitted inside each training fold, so the test fold never decides which features are kept.

I compared seven classifiers, to see whether the time effect depends on the algorithm. The classes are unequal, 26, 16, 7, 6 and 6, so I report accuracy, macro F1 and balanced accuracy against a majority baseline of 0.426. To check a gain is real I use a McNemar test and a bootstrap interval. In total there are 656 runs, with nothing tuned on a test fold.

## Slide 12: the four protocols (45 s)

Why four protocols? Because pairs of one project look alike. In boltons, 24 pairs are all concurrency, so if one is in training and another in testing, the model can recognise the project instead of the debt.

The first two, stratified folds and 20 repeated random splits, keep the type proportions. They are optimistic, because the same project sits on both sides. The last two hold out whole projects: by-project folds, and leave-one-project-out, where each project is tested once after training on the other nine. These are the honest numbers for a new project. And the debt change is tiny, 0.008 standard deviations on average, so projects differ much more than debt does, which is why this leak matters.

## Slide 13: Level 2, interest from git history (60 s)

Level two works on real projects, because the injected pairs have no later history. I follow the 2025 method. Take the last 20 releases of nine projects. A debt instance is a SonarQube issue for Python, and for C and C++ a structural smell: a function over 50 lines, complexity over 10, or more than five parameters. Between two releases, git diff gives the lines changed inside that function.

If the instance disappears, that is repayment. If it is new, or the function grew, the principal increased. If it persists, the other changed lines are interest. COCOMO II turns lines into person-months: 2.94 times thousands of lines to the power 1.0997. I compute the effort per event, because the formula is not linear: 100 lines in one event is 0.234 person-months, but ten events of ten lines is 0.186.

The result: 10.52 person-months over nine projects, about 6 percent of the effort to rewrite all the debt once. The multipliers are one, so this is a relative estimate, not measured developer time.

## Slide 14: Level 2, models and evaluation design (55 s)

Now the interest models and how I evaluate them. A row is one debt instance in one release. I have three targets: whether any interest happens in the next release, how many person-months, and a two-part model that combines both.

The evaluation is the core of my work. For every repository and release I rank the instances by predicted interest, then look at what happened in the next release. Capture at k is the share of all real next-release interest that falls inside my top k percent; random gets k. Lift says how much more likely the top items are to pay interest. NDCG rewards putting the big ones first. The baselines are random, persistence, which ranks by the interest already paid, and the oracle, which sorts by the truth.

There are two protocols. Leave-one-repo-out trains without one repository and tests on all its releases, which gives 123 groups. Temporal trains on earlier releases and tests on later ones, which gives 57 groups. The hard part is that 92 percent of instance-releases have zero interest.

## Slide 15: Result 1, debt type (65 s)

The first result. On the left, the final model with and without the time feature, for the four protocols. With stratified folds, accuracy goes from 0.79 to 0.92, and with 20 random splits from 0.84 to 0.94. For the stratified case, the interval of the gain is 0.05 to 0.23 and McNemar gives p equal to 0.008. So with the time feature the model separates the debt types better.

On the right, the seven classifiers. Only the selector models gain a lot. The plain random forest is already at 0.885 and does not move. My reading, which I have not tested separately, is that time is the top-ranked feature, so the selector always keeps it, while the forest mixes it with 133 weaker features.

Now the unseen-project bars. Without time the accuracy is 0.31 and 0.43, which is the level of always guessing concurrency, 0.426. With time it is 0.51. So the model does not generalise to new projects yet. The reason is that the change a debt makes in the features is tiny compared with the difference between projects, and concurrency comes almost only from one project.

## Slide 16: Result 2, ranking instances (65 s)

The main result. For every repository and release I ranked the instances and checked how much of the next release's interest falls into the top 10, 20 and 30 percent.

Random gets 10, 20 and 30. The two-part model gets 38.5 percent in the top 20, with an interval from 32 to 44, so about 1.9 times random. A perfect order would get 95.8. The zero model, which predicts nothing, lands on random, as it should.

But the simple rule, rank by interest already paid, gets 38.8 percent. So my learned models are clearly better than chance, and I cannot show that they beat that rule at this budget. NDCG is 0.21 against 0.23, and the rank correlation is 0.14, so the order inside the top group is weak. What this means for a team: if they repay the top fifth of the list, they touch about two fifths of the effort that debt will absorb next, instead of one fifth.

## Slide 17: Result 3, the capture curve (60 s)

This is the whole curve, in the plot and in the table: if the team repays the top k percent, how much of the future interest do they catch. The diagonal is random, the dotted top line is the oracle.

All methods are well above random. Persistence is as good or slightly ahead at small budgets, but the two-part model pulls ahead for larger ones: at 50 percent it captures 73.5 percent against 67.0. A paired bootstrap over the 123 groups gives plus 5.6 points, with an interval from 0.4 to 10.7. That is positive but marginal, and I looked at several budgets, so I would not oversell it. At 20 percent the difference is minus 2.2 points, and the interval includes zero.

The honest reading: the model adds something for larger budgets, and nothing demonstrated for small ones.

## Slide 18: Result 4, what can be predicted (45 s)

The last result. Whether an instance absorbs any work in the next release is weakly predictable: AUC 0.59 on unseen repositories and 0.71 on later releases, where chance is 0.5. A function-level model on the next 100 commits gives 0.57 and 0.62.

How many person-months is not predictable per instance. No model beats predicting zero, because 92 percent of instance-releases have no interest and the rest is heavy-tailed. The two-part model predicts the project total at 1.14 times the actual, so it can help budget a portfolio, but not size a single item. In one line: ranking is possible, estimating the amount is not.

## Slide 19: limits and next steps (55 s)

To close. What I cannot claim yet: that my learned ranking beats the simple history rule; that the type classifier works on unseen projects; or that injected debt behaves like natural debt. Sixty of 61 pairs are injected, the data is small, with intervals of about plus or minus 0.10, the COCOMO multipliers are one, and the bugs were checked by parsing, not by tests.

Next: more natural pairs and projects, richer features such as change-proneness, ownership and test coverage to try to beat persistence, running the project tests on the bugged copies, measured fix times, a cost-aware metric, and applying the ranking to AI-written changes, where I started.

The status: a working, reproducible way to build and evaluate a prioritisation, with a ranking that beats chance and is not yet better than a simple rule. Thank you. I am happy to take questions.

## Slides 20, 21: references (not spoken)

---

# PART B: THE RESULTS, EXPLAINED IN DEPTH

Use this to understand what each result means. If the examiner asks "so what does this tell us?", this is the answer.

## B0. How to read the evaluation in one minute

- A **group** is one repository at one release. The model ranks the debt instances of that group by predicted interest.
- **Interest** here is the person-months of rework done inside a debt-carrying function in the next release (from git diff and COCOMO II).
- **Capture@k** is the share of the group's total next-release interest that sits inside the top k percent of the ranking. A toy case: a release has 10 instances, and in the next release the total interest is 100 milli-person-months. The top 2 instances (k = 20 percent) hold 40 of those. Capture@20 = 40 percent. A random ranking gives 20 percent on average. A perfect ranking (the oracle) gives the biggest share possible.
- **Lift** is the hit rate in the top k divided by the base rate. Lift 1.9 means the top group pays interest 1.9 times more often than a random group.
- **NDCG@20** rewards putting large amounts at the top. 1 is perfect.
- **Persistence** is a rule with no learning: rank by the interest the instance has already paid. It is the baseline a model has to beat to be worth building.

## B1. Result 1: debt type, with and without fix time (slide 15)

**What was done.** 61 pairs, delta features (debt copy minus clean copy). Final model: ten best features by ANOVA F, then a random forest. Four ways of testing, with and without the time column.

**What was found.**
- Stratified folds: 0.787 without time, 0.918 with time (+0.131; bootstrap interval +0.05 to +0.23; McNemar p = 0.008).
- 20 random splits: 0.840, 0.938.
- Project folds: 0.311, 0.508. Leave-one-project-out: 0.426, 0.508. The majority baseline is 0.426.
- The plain random forest is 0.885 with and without time.
- Time alone gives 0.93.

**What it means.**
1. *When the cost of fixing a bug differs by debt type, and that cost is known, a classifier can use it.* This is the mechanism the experiment demonstrates. It is the expected direction, because the time model gives each type its own slowdown factor.
2. *It is not evidence about real developers.* The time comes from the ground-truth time model; I set its factors after seeing the classifiers; and time alone gives 0.93. If you shuffle the time between pairs, the gain disappears (0.840 against 0.839), so the gain is not a leak from the other features. If you add noise, the gain shrinks, and it is gone at log-noise 1.0. So the gain is conditional on the time model.
3. *The model does not generalise to new projects.* With whole projects held out, accuracy is at the majority baseline without time, and 0.51 with time. Two reasons: the debt change moves the features by only 0.008 standard deviations on average while projects differ far more; and 24 of 26 concurrency pairs come from boltons, so with boltons held out the model has seen only two concurrency pairs and misses the rest (it predicts them as security).
4. *Why the plain forest does not gain.* My reading (not tested separately): time is the top-ranked feature by F (about 120), so the selector always keeps it. A forest on all 134 columns spreads attention over many weak features, so one more column does not change it.

**How to say it in one sentence.** "With the time feature the type classifier improves where the same projects are seen in training, but that depends on my time model and does not carry over to unseen projects."

## B2. Result 2: ranking instances by predicted interest (slide 16)

**What was done.** For each of 123 repo-release groups (leave-one-repo-out), rank instances by predicted interest, measure the capture of next-release interest in the top 10, 20, 30 percent.

**What was found (top 20 percent).**
| model | capture | lift | NDCG@20 |
|---|---|---|---|
| zero model (= random) | 18.6% | 0.91 | 0.12 |
| persistence | 38.8% (32-45) | 1.93 | 0.23 |
| RF regression | 35.0% (29-41) | 1.66 | 0.21 |
| two-part model | 38.5% (32-44) | 1.86 | 0.21 |
| oracle | 95.8% | | |
Top 10 and top 30: two-part 20.0% and 51.5%; persistence 21.7% and 46.9%; random 10% and 30%.

**What it means.**
1. *The learned ranking is real.* It captures about 1.9 times what chance would, and the interval (32 to 44) is far from 20.
2. *It does not beat the simplest sensible rule at this budget.* 38.5 against 38.8 is a tie. Past interest is a strong predictor of future interest, and my features add little on top of it.
3. *The order inside the top is weak.* NDCG 0.21 and rank correlation 0.14 say that the model finds the group of risky instances but not their exact order.
4. *The gap to the oracle (95.8) is large.* The oracle sorts by the truth, so it is an upper bound, not a target. It shows that interest is concentrated: a few instances take almost all of it. That is why ranking is worth doing even though prediction is weak.
5. *Practical meaning.* If a team repays only the top fifth of the list, it touches about two fifths of next release's interest instead of one fifth.

## B3. Result 3: the capture curve and the simple rule (slide 17)

**What was found.** The two-part model against persistence, as differences in percentage points with 95 percent bootstrap intervals over 123 groups: top 10: -2.0 (-7.0 to +2.8); top 20: -2.2 (-7.4 to +3.0); top 30: +3.3 (-2.2 to +8.9); top 50: +5.6 (+0.4 to +10.7). Values at 50 percent: 73.5 against 67.0.

**What it means.**
1. *At small budgets there is no evidence the model beats persistence.* The persistence line is the same or a little above.
2. *At larger budgets the model might be better.* Persistence only knows instances that have already paid interest, and has no information on the others, so for a budget that reaches beyond those, a model that scores every instance can help. That is my interpretation, which I did not test separately.
3. *The 50 percent result is marginal.* The lower end of the interval is +0.4, and I examined several budgets (10, 20, 30, 50), so it is a hint, not a finding. Do not claim it.
4. *All methods are far above random, and below the oracle.* This frames the work: the information is there, my features capture a part of it.

## B4. Result 4: what can and cannot be predicted (slide 18)

**What was found.**
| task | result | verdict |
|---|---|---|
| any interest in the next release (AUC) | 0.59 unseen repos / 0.71 later releases | weak, real |
| amount per instance (person-months) | R2 at or below 0; no model beats predicting zero | no |
| total interest of a project | predicted / actual = 1.14 | portfolio level only |
| total of a project, next release | best R2 = -0.14 | no |
| function-level, next 100 commits (AUC) | 0.57 / 0.62 | weak |

**What it means.**
1. *Whether* an instance absorbs work is a bit predictable. AUC above 0.5 is the reason the ranking beats chance in Result 2.
2. *How much* is not. 92 percent of instance-releases have zero interest and the rest is heavy-tailed, so predicting the average gives a worse error than predicting zero.
3. *Temporal is better than unseen-repo* (0.71 against 0.59). Knowing the earlier releases of the same repository helps, and this is the realistic use: a team has its own history.
4. *Portfolio totals are close (1.14)* but single items are not, so this can support budgeting, not task estimates.

## B5. Which result to lead with if you have only one minute
"I built a pair dataset with known debt type and a time label. A type classifier with that time feature improves, but only conditional on my time model and not for unseen projects. On real history I ranked debt instances by predicted interest. It beats random by 1.9 times and ties a simple persistence rule, and the amount of interest cannot be predicted. So the contribution is a way to build and to test a prioritisation, with honest limits."

---

# PART C: THE ARCHITECTURE AND WHAT I DID

Use this to answer "what exactly did you do?". It follows slide 7, column by column.

## C1. Data creation (slides 8, 10)
1. **Projects.** 10 open-source projects with test suites: boltons, click, jinja, werkzeug (Python); C-Thread-Pool, cJSON, jansson, libpng, libyaml, zlib (C/C++). Test folders were removed from the copies in the dataset, and the test results measured before are stored with each pair.
2. **Pairs.** For each pair: the clean project, and the same project with one small debt change of one of five types (concurrency, security, dependency structure, coupling and cohesion, complexity). 60 injected (45 scripted or hand-written, 15 SmellBench-style LLM refactorings in click and jinja) and 1 natural (libpng, a real fix commit).
3. **Keep working.** The debt copy must pass the project's own tests, since real debt does not break behaviour.
4. **Audit.** A pair is kept only if a metric of its own type changed (102 candidates, 52 kept), so that a one or two line change is visible as debt. 50 were dropped as "not visible to these metrics".
5. **Add.** 9 pairs from C-Thread-Pool (4) and libyaml (5), to get 61: concurrency 26, security 16, dependency 7, coupling 6, complexity 6.
6. **Bugs.** 3 small mutations per pair (negated condition, off-by-one, arithmetic, boolean operator, equality, boundary), the same patch on both copies: 183 bugs. Never on the lines the debt change touched; 70 are in a file the debt change touched. Checked: 246 of 246 Python files parse, 59 of 59 C files pass a syntax compile.
7. **Git history** of 9 projects (last 20 release tags) for level two. C-Thread-Pool has no tags.

## C2. Characteristics (slide 9, 10, 13)
- **133 features** per project: structure 46 (layout 13, dependency graph 33), code 50, technical debt 37. Computed with lizard, bandit, flawfinder, networkx and own code. The model sees `delta = debt copy minus clean copy`.
- **Time label** `time_diff_min`: minutes to fix the 3 bugs in the debt copy minus in the clean copy, from the ground-truth time model (type factor, with 0.85 weight when the bug is in a file the debt change did not touch).
- **Interest per debt instance** for level two, from git diff and COCOMO II (2.94 x KLOC^1.0997), per event, in person-months.

## C3. Prediction (slides 11, 14)
- **Level 1.** Input: delta features plus time. SelectKBest (ANOVA F, k = 10, inside each training fold) then a random forest (300 trees, balanced class weights). Output: the debt type among five. Seven classifiers compared (RF, gradient boosting, logistic regression, SVM, kNN, 10-best + LR, 10-best + RF), two layouts (delta only 133 columns, full 399 columns), four protocols, with and without time: 656 runs.
- **Level 2.** Input: per instance and release: age, interest paid so far, number of events, function size and complexity. Models: random forest classifier (any interest next release), random forest regressor (person-months), two-part hurdle model (probability times amount). Predictions are made per instance.

## C4. Output
- Level 1: the debt type of a change and, through the time model, its cost, so types can be ranked by cost.
- Level 2: a ranked list of the debt instances of a release by predicted interest.

## C5. Evaluation (slides 11, 12, 14 to 18)
- Level 1: accuracy, macro F1, balanced accuracy; majority baseline 0.426; McNemar test and bootstrap interval; four protocols (stratified, 20 random splits, by project, leave-one-project-out); controls on the time feature (shuffled, noisy, four calibrations).
- Level 2: capture@k, lift, NDCG@20, rank correlation, bootstrap intervals; baselines random, persistence, oracle; two protocols (leave-one-repo-out 123 groups, temporal 57 groups); a paired bootstrap of two-part minus persistence.

## C6. Why this design (the reasons, in one line each)
- Whole projects, not snippets: structural debt (cycles, fan-in, layout) cannot be seen in a snippet.
- Clean twin: it gives a known answer, which real projects lack.
- Audit: avoids assuming a one-line change is debt.
- Same bugs in both copies: the only difference in fix time is the debt.
- Selector inside folds: no test-fold leakage with 61 rows and 134 columns.
- Project-held-out protocols: pairs of one project share their type.
- Level 2 on real history: injected pairs have no later releases.
- Capture@k against persistence: it tests the ranking in terms a team can act on and compares with a free rule.

---

# PART D: QUESTIONS THE EXAMINER CAN ASK

Format: question, answer to say, and "If pushed" where a follow-up is likely. Group order: your work and architecture, the dataset, the time label, the models and metrics, the interest part, the results, limits and future, general and difficult.

## D1. Your work and the architecture

**Q1. In one minute, what did you do?**
A: I built a dataset of 61 pairs of clean and debt projects with known debt type and a fix-time label, and I built a pipeline to turn each pair into 133 features. I trained a type classifier with and without the time feature. On real git history of nine projects I computed technical-debt interest in person-months, and ranked debt instances by predicted interest. The main goal was the evaluation: how to test whether a ranking is any good, with baselines and confidence intervals.

**Q2. What is your research question?**
A: When a team has more debt than it can repay, can a model rank the items so that the costliest are repaid first, and how do we test that ranking? Does it beat chance and a simple rule?

**Q3. What is the contribution?**
A: Three things together: a pair dataset with a known type, place and clean twin; a reproducible interest pipeline from git history in person-months; and an evaluation of the ranking with baselines and intervals. Each part uses known methods; the value is that a ranking can now be tested.

**Q4. Why two levels, are they connected?**
A: Level one predicts the type on injected pairs, which have no later history. Level two ranks instances on real histories. They share the idea of ranking by cost, but they are two separate experiments, not one pipeline. A single model needs natural debt with both history and fix times.

**Q5. Why is the evaluation the main goal?**
A: Reviews (Lenarduzzi, Ehsani) say no validated tools and no standard benchmark exist. A ranking whose quality cannot be measured cannot be trusted, so I spent most effort on how to measure it.

**Q6. What does the architecture figure show?**
A: Five stages: data creation, characteristics, prediction, output, evaluation. The black labels are the tools used at each step and the italic line says what each stage signifies. Level one and level two are the two rows of the prediction column.

**Q7. How is this different from SmellBench?**
A: SmellBench evaluates code agents on refactoring tasks with injected smells (294 cases, 7 smell types). I took the injection idea (and 15 pairs in that style), but I work at whole-project level, with five debt types, features and a time label, and use them to train and evaluate rankings.

**Q8. How is this different from Wiriyakul and Senivongse?**
A: I implement their interest idea (rework inside a persisting smell, COCOMO II) on nine projects with my own definition of instances for C and C++. Then I add prediction and a ranking evaluation on top. Their full citation is still to be added to the references.

**Q9. Is capture@k new?**
A: No, effort-aware measures such as capture, lift and NDCG are standard in defect prediction and retrieval. I use them for debt instances and add a persistence baseline and bootstrap intervals.

**Q10. What is the practical use today?**
A: A ranked list per release that finds about two fifths of next release's interest in its top fifth. It ties a simple rule today, so I do not claim a deployable tool yet.

## D2. The dataset

**Q11. Why whole projects instead of snippets or commits?**
A: Debt such as import cycles, fan-in and layout only exists at project level.

**Q12. Is injected debt real debt?**
A: It is a controlled debt, with a known type and place. I audit it: a pair stays only if a metric of its own type moved. But it is not natural, and the main limit is that 60 of 61 pairs are injected. I have one natural pair (libpng). More natural pairs are the first next step.

**Q13. Can a 1 or 2 line change be technical debt?**
A: Only if it is visible in the metrics, which is what the audit checks: 52 of 102 candidates stayed. The dropped ones are "not visible to these metrics", not "not debt". With richer features some could return.

**Q14. The audit uses metrics similar to the features. Is that circular?**
A: Partly. Keeping pairs where a type-related metric moved makes the type easier to see, and may make level one look better than it is. That is one more reason to read the unseen-project numbers as the honest ones, and those are weak.

**Q15. Why only 61 pairs and 10 projects?**
A: Each pair needs a working clean and debt copy that pass tests, plus the audit. Large or untested projects were removed. With 61 pairs, intervals are about plus or minus 0.10, so I do not claim fine differences.

**Q16. Class imbalance, boltons?**
A: Classes are 26, 16, 7, 6, 6. 24 of the 26 concurrency pairs are boltons. So project and type are tangled, and a model can learn the project. This is why I hold out projects and report the majority baseline of 0.426.

**Q17. How were the injections made?**
A: 45 by scripted or hand-written small changes per type (for example, removing a lock or a bounds check, adding an import cycle, deepening nesting), 15 by LLM refactorings in the SmellBench style, and one real libpng fix. Each is a small, controlled diff.

**Q18. Are the bugs valid?**
A: They are valid code: Python files parse (246 of 246), C files pass a syntax compile (59 of 59). I did not run the test suites on the bugged copies, so I do not know that each bug makes a test fail. It is in the next steps.

**Q19. How do you avoid train-test leakage between clean and debt copies?**
A: The two copies are one row (one delta), so they cannot be split. The leak I worry about is across pairs of the same project, so I use project-held-out protocols.

**Q20. Can others reproduce the dataset?**
A: Yes. The pipeline is scripted (`pipeline/`), the bug injection is seeded by pair id, so re-running gives identical patches, and the README and GUIDE document each step.

## D3. The time label (expect the hardest questions here)

**Q21. Is the fix time measured from developers?**
A: No. It comes from the ground-truth time model in `pipeline/bug_injection/sample_times.py`: a slowdown factor per type (concurrency 3.4, security 2.4, complexity 1.8, coupling 1.4, dependency 1.05) applied to the bug patches, with a smaller weight if the bug is in a file the debt change did not touch. Measured values can replace it at any time (`make_dataset.py times`).
If pushed: so the time is an assumption that I treat as ground truth for the experiment. It is not evidence about developers.

**Q22. Then the time gain is circular, is it not?**
A: Partly. Because time depends on the type, adding it gives the classifier the answer in another form; time alone gives 0.93. I call the gain conditional on the time model. What the experiment shows is the mechanism: if cost differences between types are known, the classifier uses them. The real question, whether real fix times separate the types, needs measured times.

**Q23. Why those factors, who decided them?**
A: I set them from the idea that concurrency and security bugs take longer to debug, with complexity somewhat longer. I calibrated after seeing the classifiers (four settings) and replaced one weak setting that gave almost no gain. That is a selection I disclose, and it is why measured times matter.

**Q24. Did you check the gain is not a leak?**
A: Yes. Shuffling the time between pairs removes the gain (0.840 against 0.839). Adding noise shrinks it, and it is gone at log-noise 1.0. These controls are in `results/04_time_feature.md`.

**Q25. Why not measure real fix times?**
A: 183 bugs on 122 project versions was not feasible by hand in the project time. A small study (20 to 30 pairs) or real proxies, such as SZZ bug lifetimes or issue resolution times, are my first next steps.

**Q26. Why call it ground truth?**
A: For the experiment, it is the reference the model is trained and evaluated against. I do not mean it was measured.

## D4. Models and metrics

**Q27. Why random forest?**
A: A strong default for small tabular data, handles mixed scales, needs little tuning, and has class weights for the imbalance.

**Q28. Why a selector, and why k = 10?**
A: With 61 rows and 134 columns, noise features hurt. The selector runs inside each training fold, so the test fold never influences which features are kept. k = 10 was fixed in advance, not tuned on a test fold. I did not scan k, so I cannot say 10 is optimal.

**Q29. Why did the plain random forest not gain from time?**
A: My reading is that the selector always keeps time because it has the top F score, while the forest spreads attention over 133 weaker features. I did not test it separately.

**Q30. Why those seven classifiers?**
A: To see if the time effect depends on the algorithm: tree ensemble, boosting, linear, margin-based, distance-based, and two with the selector. Settings are fixed, not tuned. Note that gradient boosting reaches 0.92 with time too, and the plain RF is already 0.885 without it.

**Q31. Why accuracy, macro-F1 and balanced accuracy?**
A: Classes are unequal (26, 16, 7, 6, 6), so accuracy alone favours concurrency. Macro F1 and balanced accuracy weight classes equally. The majority baseline of 0.426 is the floor.

**Q32. What does the McNemar test do here?**
A: It compares two models on the same test items, counting the items one gets right and the other wrong. For time against no time with stratified folds, p = 0.008.
If pushed: I ran 656 experiments and did not correct p-values for multiple comparisons, so I treat a single p-value as an indication.

**Q33. Why four protocols?**
A: Each answers a different question. Stratified: same splits for all models. 20 random splits: a stable average. By project and leave-one-project-out: unseen projects. Only the last two are honest for a new project.

**Q34. Which number should I believe for Level 1?**
A: For unseen projects: 0.43 without time and 0.51 with time, at the majority baseline. The 0.92 is optimistic because pairs of the same project are in train and test.

**Q35. Why not deep learning or a pretrained code model?**
A: With 61 rows it would overfit. Embeddings from a pretrained model as features are a possible direction with more data. I have not run that.

**Q36. What is SelectKBest with ANOVA F?**
A: It scores each feature by the ratio of between-class to within-class variance and keeps the 10 highest, fitted on the training fold only.

## D5. The interest part

**Q37. What is interest?**
A: The effort spent working inside code that carries debt while the debt remains: changed lines inside the smelly function, beyond its growth, converted with COCOMO II into person-months.

**Q38. Why COCOMO II and is it valid?**
A: It is the conversion used by the method I follow [12], and a standard size-to-effort model [13]. I use nominal constants (A = 2.94, E = 1.0997) with multipliers one, so values are relative. I did not calibrate them for these projects. With the constants of the paper (A = 2.64, E = 0.91) values are 2.1 to 2.8 times larger, which is in `interest_exp/results/tables/cocomo_sensitivity.csv`.

**Q39. Why compute effort per event?**
A: The formula is not linear (exponent 1.0997). 100 lines in one event gives 0.234 person-months, but ten events of ten lines gives 0.186.

**Q40. How do you define a debt instance?**
A: Python: a SonarQube code smell, tracked by issue key. C and C++: a structural smell found with lizard, a function over 50 lines, with complexity over 10, or with more than 5 parameters. These are common defaults and not tuned; other thresholds would change the counts.

**Q41. Is any change inside a smelly function interest?**
A: In the method, yes: changed lines beyond the growth of the function are counted as interest, whether or not the smell made them harder. That can inflate interest, and it is a limit.

**Q42. Why are the injected pairs not used for interest?**
A: They have no later history, so interest is undefined for them.

**Q43. Why is C-Thread-Pool not in level two?**
A: It has no release tags, so nine of the ten projects are used.

**Q44. What does 6 percent mean?**
A: Over 20 releases the observed rework is about 6 percent of what rewriting all the debt once would cost, on the relative COCOMO scale.

## D6. The results

**Q45. Is 38.5 percent good?**
A: It is about 1.9 times random (20 percent) and equal to persistence (38.8 percent). Against the oracle (95.8) it is far.

**Q46. What does your model add over persistence?**
A: At small budgets, nothing demonstrated. At 50 percent, plus 5.6 points with an interval of 0.4 to 10.7, which is marginal, and I examined several budgets. My interpretation is that a model scores instances that have no interest history yet, where persistence cannot, but I did not test that.

**Q47. Why is NDCG only 0.21?**
A: The order inside the top group is weak: rank correlation is 0.14. Most instances have zero interest and the amounts are heavy-tailed.

**Q48. Why can the amount not be predicted?**
A: 92 percent of instance-releases have no interest and the rest is heavy-tailed, so no regressor beats predicting zero. The total of a project is predicted at 1.14 times the actual, so only a portfolio view is usable.

**Q49. Is AUC 0.59 useful?**
A: It is weak but real; chance is 0.5. 0.71 on the temporal protocol is better. It is enough for the 1.9 times capture, not for single-item decisions.

**Q50. Why is temporal better than leave-one-repo-out?**
A: Knowing the earlier releases of the same repository helps. It is also the realistic use, since a team has its own history.

**Q51. Do the two protocols agree?**
A: In direction, yes: temporal gives two-part 28.2 and 41.9 percent at top 10 and 20, persistence 23.4 and 39.1, with overlapping intervals. Again no clear win over persistence.

**Q52. Are results stable across projects?**
A: I report averages over groups with bootstrap intervals, not per project. A per-project breakdown is worth adding, because large projects with many releases may dominate.

**Q53. What was wrong with the earlier model with R2 = 0.90?**
A: It predicted the COCOMO effort of the patch, which is an exact function of the lines added, so it was leakage. Under leave-one-project-out the R2 was negative. I replaced it by the instance-ranking task.

**Q54. What does the 123 and 57 mean?**
A: The number of repo-release groups with at least 10 instances and some real interest: 123 for leave-one-repo-out and 57 for the temporal protocol.

## D7. Limits and future work

**Q55. What are the biggest threats to validity?**
A: Internal: the time model was set after seeing the classifiers, the audit uses metrics like the features, bugs were not run through tests. External: 10 projects, 60 of 61 injected, one project gives 24 pairs. Construct: nominal COCOMO, and every change in a smelly function counted as interest.

**Q56. Is the dataset big enough to conclude anything?**
A: Not for strong claims. Intervals are about plus or minus 0.10. It is enough to show the method works and to find where it fails.

**Q57. Did you choose settings after seeing the test results?**
A: The time setting, yes, and I disclose it. The classifier settings were fixed, feature selection is inside folds, and the paired comparison looked at several budgets, which I flag.

**Q58. Does it work on other languages?**
A: Tested on Python and C/C++ only. Features include language idioms, so other languages need new extractors.

**Q59. Does it work on AI-generated code?**
A: Untested. It is the motivation and the last next step.

**Q60. What would you do first with more time?**
A: Measured or real-proxy fix times, even for 20 to 30 pairs; then more natural pairs; then richer features (change-proneness, ownership, tests) to try to beat persistence; then run the tests on the bugged copies.

**Q61. Is it publishable?**
A: As a benchmark and evaluation-method paper with honest negative results, at a workshop or data-track level. A full empirical paper needs measured costs, more natural debt, and a model that beats persistence.

**Q62. What would change your conclusions?**
A: If measured fix times did not separate the types, the time gain would vanish. If richer features beat persistence in a paired test, the ranking claim would change.

## D8. General and difficult

**Q63. Why should one trust a model trained on injected data?**
A: Not yet for deployment. I use injection to have a known answer for evaluation, and the transfer to natural debt is untested.

**Q64. If time alone gives 0.93, is the classifier pointless?**
A: As a predictor of the type with time given, it adds little. The time is not known before the fix, so it is a probe of the cost-type link, not a deployed input. For prioritisation, the useful target is the cost itself, which is where I would go next.

**Q65. Why present negative results?**
A: The goal was to test the ranking, and an honest comparison with persistence is the point of the evaluation.

**Q66. Explain the formula 2.94 x KLOC^1.0997.**
A: The COCOMO II.2000 nominal equation: A = 2.94, exponent E = 0.91 + 0.01 times the sum of the scale factors (18.97 here), effort multipliers one. Size is in thousands of source lines.

**Q67. What is a hurdle (two-part) model?**
A: One part predicts whether the outcome is above zero, a second part predicts the amount given it is positive; the product is the prediction. It suits data with many zeros [27].

**Q68. What are capture@k, lift and NDCG in one line each?**
A: Capture@k: share of the real next-release interest inside my top k percent. Lift: hit rate in the top k divided by the base rate. NDCG: ranking quality that rewards big amounts first.

**Q69. What is persistence and why is it the baseline?**
A: Rank instances by the interest they have already paid. It is free and uses the same history, so a model must beat it to be worth building.

**Q70. How much of the code did you write, and with which tools?**
A: Answer from your own facts. Be ready to explain every number on the slides and every step of the pipeline, since the examiner may ask you to walk through it.

---

# PART E: NUMBERS AND RULES

## E1. Numbers
- Dataset: 61 pairs, 10 projects (4 Python, 6 C/C++); 60 injected (45 scripted, 15 SmellBench-style), 1 natural; classes 26/16/7/6/6; funnel 102, 52, then +9 = 61; 183 bugs (70 in a touched file); 246 of 246 parse, 59 of 59 compile.
- Features: 133 = structure 46, code 50, debt 37; layouts delta only 133, full 399; mean absolute delta 0.008 standard deviations.
- Time model factors: 3.4, 2.4, 1.8, 1.4, 1.05; minutes per pair 161.6, 92.0, 53.5, 22.7, 3.2; time alone 0.93; shuffled control 0.839 against 0.840.
- Level 1 (10-best + RF): stratified 0.787 to 0.918; 20 splits 0.840 to 0.938; by project 0.311 to 0.508; leave-one-project-out 0.426 to 0.508; majority 0.426; gain interval +0.05 to +0.23; McNemar p = 0.008; plain RF 0.885 both; 656 runs.
- Seven classifiers (without, with time): RF 0.885/0.885; GB 0.836/0.918; LR 0.721/0.787; SVM 0.705/0.705; kNN 0.639/0.639; 10-best + LR 0.525/0.803; 10-best + RF 0.787/0.918.
- Interest: 10.52 PM; about 6 percent of principal; 20,853 instance-releases; 1,557 instances; 1,607 events; 9 projects (0.09 to 2.44 PM); 92 percent zeros.
- Ranking (leave-one-repo-out, 123 groups), top 10/20/30: two-part 20.0/38.5/51.5; persistence 21.7/38.8/46.9; RF regression 17.2/35.0/48.9; zero 9.6/18.6/30.6; oracle 89.9/95.8/98.1. At 50 percent: 73.5 against 67.0 (+5.6, 0.4 to 10.7). Differences at 10, 20, 30: -2.0, -2.2, +3.3.
- Temporal (57 groups): two-part 28.2 and 41.9 at top 10 and 20; persistence 23.4 and 39.1.
- Predictability: any-interest AUC 0.59 / 0.71; function level 0.57 / 0.62; amount no gain over zero; project total ratio 1.14.

## E2. Rules for answering
1. Answer the question in the first sentence, then add one number.
2. When the criticism is right, say so and point to the limit slide (19). Do not defend what the data does not show.
3. Describe the fix times as coming from the ground-truth time model. Never say they were measured from developers or surveyed.
4. Say the 50 dropped pairs are "not visible to these metrics", not "not debt".
5. Do not claim that the model beats persistence; call the 50 percent result marginal.
6. If you do not know, say "I did not test that" and say how you would.
7. Keep to the numbers of Part E1; if a number is not there, say you will check it in the results files.
