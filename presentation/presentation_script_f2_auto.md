# Presentation script (spoken, about 14 minutes)

Generated from the speaker notes of the deck. About 1939 words at 140 words per minute. Slides 20 and 21 (references) are not spoken.

## Slide 2: Why this matters: debt arrives faster than it is repaid (54 s)

Good morning. My project is about technical debt, and the question behind it is simple: when a team has more debt than it can repay, what should it fix first?

This matters more now because of AI-generated code. The Stanford AI Index counted 233 reported AI incidents in 2024, 56 percent more than the year before. Veracode found a security flaw in 45 percent of AI-generated code samples. And a study of more than 6,000 repositories found that 22.7 percent of the issues introduced by AI-written commits are still in the code.

So debt builds up faster, nobody can repay all of it, and the team has to rank. My work is about building such a ranking, and mostly about measuring whether the ranking is any good.

## Slide 3: Incidents show what rushed change costs (35 s)

A few concrete cases. In December 2025 the Financial Times reported a long AWS outage after a change by an AI coding agent. Amazon disputes the AI framing and blames a misconfigured access role, so I present it as reported, not proven. A Replit agent deleted a production database during a code freeze in 2025.

What I take from these: failures are cheap to create and expensive to repay, and what to repay first has no validated answer. That is the gap.

## Slide 4: Literature 1 of 3: how debt is prioritised and managed (31 s)

I read twelve papers in three groups. First, prioritisation. Lenarduzzi and colleagues reviewed 44 primary studies and found no consensus on the factors and no validated tools. Alfayez and colleagues found that the value of debt is subjective. Baldassarre and colleagues showed that SonarQube's remediation time is often inaccurate. Biazotto and colleagues found that automation pieces are not integrated.

So I need ranking criteria I can measure, and a way to test them.

## Slide 5: Literature 2 of 3: interest, cost and impact (34 s)

Second group: interest, the extra cost debt causes while it stays. Ampatzoglou and colleagues call interest central but hard to measure. Digkas and colleagues propose an interest-risk metric that helps prioritise. Lenarduzzi and colleagues found that rule violations have only a small effect on faults, so counting violations is a weak ranking.

The method I implemented is from Wiriyakul and Senivongse: interest is rework inside a code smell that persists, converted to effort with COCOMO II, which gives person-months.

## Slide 6: Literature 3 of 3: AI-era debt, benchmarks and detection (37 s)

Third group: the AI era and data. Liu and colleagues studied 302 thousand AI-written commits: 484 thousand issues, 22.7 percent still present. Ehsani and colleagues reviewed 104 sources and found no standard benchmark. SmellBench injects smells into clean real code so each case has a known answer. Li and colleagues detect self-admitted debt.

What is missing is a benchmark where the type, the cost and the future interest are known. I follow the injection idea, but with whole projects, five debt types and a time label.

## Slide 7: What I built, at one glance (42 s)

This is the whole work, left to right. One: data creation, ten open-source projects with a clean and a debt copy of each, plus the git history of nine real projects. Two: the characteristics, 133 numbers per project, a fix-time number, and an interest per debt instance. Three: two models. Level one says what kind of debt a change introduces. Level two says which instance will absorb future work. Four: the outputs, a type and cost ranking and an instance ranking. Five: the evaluation, which is the main goal, with protocols that avoid leakage and baselines to compare with.

## Slide 8: Dataset creation: 61 pairs of clean and debt projects (59 s)

How I built the dataset. A snippet cannot show an import cycle, so each data point is a pair of whole projects, one clean and one with a single injected debt.

I took ten open-source projects with working tests. For each pair I made one small change that introduces a debt of one of five types, so type, place and clean twin are known. Sixty are injected, 45 by scripts and 15 in the SmellBench style, and one is a real libpng fix. Both copies must pass the project's tests, because real debt does not break the program.

Then the audit. Can a one or two line change really be debt? A pair stays only if a metric of its own type moved. Of 102 candidates, 52 stayed. I added nine pairs from two more projects, giving 61.

## Slide 9: Dataset curated so far: 61 datapoints, 133 features (42 s)

This is the dataset as it stands. Each row is one pair and the model sees the difference between the debt copy and the clean copy: 133 numbers in three blocks. Structure, 46: layout and the import graph with fan-in, fan-out, cycles and modularity. Code, 50: size, function length, complexity, language idioms. Debt, 37: smells and their COCOMO principal, cohesion, locks and threads, duplication, security findings and self-admitted debt. Plus one time number.

The chart shows the types by language. Remember this: 24 of the 26 concurrency pairs come from one project, boltons. It comes back in the results.

## Slide 10: Bugs and the fix-time label (54 s)

Why a time number? Debt makes later work slower. So I fix the same bug in the clean copy and in the debt copy, and the extra time is the cost of the debt. Three bugs per pair, 183 in total, small mutations like a flipped comparison, with the same patch on both copies.

Now the honest part. I could not have developers fix 183 bugs on 122 project versions, so the times come from a time model with assumed factors per type: concurrency 3.4 times slower, security 2.4, down to dependency at 1.05. I set the factors after seeing the classifiers, and time alone predicts the type with 0.93 accuracy. So any gain from time depends on this model. It is not evidence about real developers.

## Slide 11: Level 1: debt-type classifier, architecture, metrics (57 s)

Level one: which of five types does a pair introduce. The final model takes the 133 delta features plus time, a selector keeps the ten best by ANOVA F, and a random forest with 300 trees gives the type. With 61 rows and 134 columns a model drowns in noise, so the selector helps, and it is fitted inside each training fold, so the test fold never decides which features are kept.

I compared seven classifiers to see if the time effect depends on the algorithm. Classes are unequal, 26, 16, 7, 6, 6, so I report accuracy, macro F1 and balanced accuracy, against a majority baseline of 0.426. To check a gain is real I use a McNemar test and a bootstrap interval. 656 runs, nothing tuned on a test fold.

## Slide 12: Why four protocols, and how each is used (49 s)

Why four protocols? Because pairs of one project look alike. In boltons, 24 pairs are all concurrency, so if one is in training and another in testing, the model can just recognise the project.

The first two, stratified folds and 20 repeated random splits, keep type proportions. They are optimistic, and the repeated one gives a stable average. The last two hold out whole projects: project folds, and leave-one-project-out where each project is tested once after training on the other nine. These show the truth for new projects, and I read them as the honest result. Also, the debt change is tiny, 0.008 standard deviations on average, so projects differ far more than debt does.

## Slide 13: Level 2: interest in person-months from git history (68 s)

Level two works on real projects, because the injected pairs have no later history. I follow the 2025 method. Take the last 20 releases. A debt instance is a SonarQube issue for Python, and for C and C++ a structural smell: a method over 50 lines, complexity over 10, or more than five parameters. Between two releases, git diff gives the lines changed inside that function.

If the instance disappears, that is repayment. If it is new or the function grew, the principal increased. If it persists, the other changed lines are interest. COCOMO II converts them: 2.94 times thousands of lines to the power 1.0997. For example, 100 lines in one event is 0.234 person-months, ten events of ten lines is 0.186, so I compute effort per event.

Result: 10.52 person-months over nine projects, about 6 percent of the effort to rewrite all debt once. Multipliers are one, so it is a relative estimate, not measured developer time.

## Slide 14: Level 2: interest models and ranking evaluation (51 s)

Now the interest models and the evaluation. A row is one debt instance in one release. Targets: whether any interest happens next, how many person-months, and a two-part model that combines both.

The evaluation is the core. In each repository and release I rank the instances by predicted interest and look at what happened next. Capture at k is the share of all real interest inside my top k percent; random gets k. Lift says how much more likely the top items are to pay interest. NDCG rewards putting big ones first. Baselines: random, persistence, which ranks by interest already paid, and the oracle. Uncertainty from a bootstrap. Two protocols: leave-one-repo-out with 123 groups, and temporal with 57.

## Slide 15: Result 1: debt type, with and without fix time (45 s)

Results. Left: the final model with and without time. With stratified folds accuracy goes from 0.79 to 0.92; the interval of the gain is 0.05 to 0.23 and McNemar gives p of 0.008. Right: seven classifiers. Only the selector models gain a lot; the plain forest is already at 0.885 and does not move. My reading, not tested separately, is that time is the top feature so the selector keeps it, while the forest mixes it with 133 weaker ones.

Look at the unseen-project bars: without time 0.43, the same as always guessing concurrency, and 0.51 with time. The model does not generalise across projects yet.

## Slide 16: Result 3: ranking instances by predicted interest (47 s)

The main result. For every repository and release I ranked the instances and checked how much of next release's interest falls into the top 10, 20 and 30 percent.

Random gets 10, 20 and 30. The two-part model captures 38.5 percent in the top 20, interval 32 to 44, about 1.9 times random. A perfect order gets 95.8. The zero model lands on random, as it should.

But the simple rule, rank by interest already paid, gets 38.8 percent. So my models are clearly better than chance, and I cannot show they beat that rule at this budget. NDCG is only 0.21, so the order inside the top is weak.

## Slide 17: Result 4: capture curve and the simple rule (44 s)

This is the whole curve: if the team repays the top k percent, how much of the future interest do they catch. Diagonal is random, top line is the oracle.

All methods sit well above random. Persistence is slightly ahead at small budgets, but the two-part model pulls ahead for larger ones: at 50 percent it captures 73.5 against 67.0. A paired bootstrap over 123 groups gives plus 5.6 points, interval 0.4 to 10.7. Positive but marginal, and I looked at several budgets, so I would not oversell it. At 20 percent the difference is minus 2 points with an interval including zero.

## Slide 18: Result 5: what can and cannot be predicted (34 s)

Last result. Whether an instance absorbs any work next release is weakly predictable: AUC 0.59 on unseen repositories, 0.71 on later releases. How many person-months is not predictable per instance: no model beats predicting zero, because about 92 percent of instance-releases have no interest and the rest is heavy-tailed. The two-part model predicts a project total at 1.14 times the actual, good for budgeting a portfolio, not for single items.

In one line: ranking is possible, amount estimation is not.

## Slide 19: Limits, and what comes next (45 s)

To close. I cannot claim yet that my ranking beats the simple history rule, that the time gain holds for real developers, that the classifier works on unseen projects, or that injected debt behaves like natural debt. The COCOMO multipliers are not calibrated, so person-months are relative.

Next: measured fix times, richer features such as change-proneness and ownership to try to beat persistence, a cost-aware metric, more projects, and a test on AI-generated code, where I started.

The status: a working, reproducible way to build and evaluate a prioritisation, with a ranking that beats chance and is not yet better than a simple rule. Thank you.

