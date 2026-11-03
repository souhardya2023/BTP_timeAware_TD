# Script and Q&A for TD_prioritisation_presentation_f.pptx

Written for: you, as the presenter, with an examiner or panel asking questions afterwards.

How to use it. Part A is the spoken text, slide by slide, for about 13 to 14 minutes at a calm pace (about 1,950 words). Part B is the question bank, grouped by type, with a short answer you can say aloud and a "if pushed" line where a follow-up is likely. Part C is a cheat sheet of numbers, and Part D is the rules for answering.

Slide numbers below are the position in the file (1 to 20). The number printed on some slides differs (the file has no "Result 2" slide, so printed numbers jump from 14 to 16). If someone says "slide 16", they mean the printed number, which is position 15.

Timing guide: slides 1-2 about 1:30, 3-5 about 1:40, 6 about 0:40, 7-8 about 1:40, 9 about 1:00, 10-11 about 1:50, 12-13 about 1:50, 14-17 about 3:30, 18 about 0:50. Slides 19-20 are references and are not spoken.

---

# PART A: SPOKEN SCRIPT

## Slide 1: title and motivation (about 55 s)

Good morning. My project is about technical debt, and the question behind it is simple: when a team has more debt than it can repay, what should it fix first?

This matters more now because of AI-generated code. The Stanford AI Index counted 233 reported AI incidents in 2024, 56 percent more than the year before. Veracode found a security flaw in 45 percent of the AI-generated code samples in its benchmark. And a study of more than 6,000 repositories found that 22.7 percent of the issues introduced by AI-written commits are still in the code at the latest revision. The note on the slide matters: these numbers come from different studies and samples, so I show them as signals, not as one population.

So debt builds up faster, nobody can repay all of it, and the team has to rank. My work is about building such a ranking, and mostly about measuring whether the ranking is any good.

## Slide 2: incidents (about 35 s)

A few concrete cases, with causes as reported by the sources. In December 2025 the Financial Times reported a long AWS outage after a change by an AI coding agent. Amazon disputes the AI framing and blames an access misconfiguration, so I present it as reported, not proven. A Replit agent deleted a production database during a code freeze in 2025. GitClear reports more duplicated code and less refactoring in the AI period.

What I take from these: changes land faster than people can review them, failures are cheap to create and expensive to repay, and there is no ground truth for which debt really costs the most. So my question is: does a ranking by predicted cost beat chance, and does it beat a simple rule?

## Slide 3: literature, part 1 (about 35 s)

I read twelve papers in three groups. The first group is prioritisation. Lenarduzzi and colleagues reviewed 44 primary studies and found that approaches optimise different criteria, with no consensus and no validated tools. Alfayez and colleagues found that how teams value debt is subjective. Baldassarre and colleagues showed that SonarQube's remediation time estimates are often inaccurate. Biazotto and colleagues reviewed 178 studies on automation and found that the pieces are not integrated.

So I need ranking criteria that I can measure, and a way to test them.

## Slide 4: literature, part 2 (about 35 s)

The second group is interest, the extra cost that debt causes while it stays. Ampatzoglou and colleagues call interest the central idea but hard to measure. Digkas and colleagues propose a risk-of-interest metric that helps prioritise repayment. Lenarduzzi and colleagues found that SonarQube issues have a significant but small effect on faults, so counting violations is a weak ranking.

The method I implemented is from Wiriyakul and Senivongse: interest is the rework inside a code smell that persists, converted to effort with COCOMO II, which gives person-months.

## Slide 5: literature, part 3 (about 35 s)

The third group is the AI era and data. Liu and colleagues studied 302 thousand AI-written commits, found 484 thousand issues, and 22.7 percent are still present. Ehsani and colleagues reviewed 104 sources and found no standard benchmark or metric. SmellBench injects smells into clean real code so every case has a known answer. Li and colleagues detect self-admitted debt from comments, which I use as features.

What is missing is a benchmark where the debt type, the cost and the future interest are known. I follow the injection idea, but with whole projects, five debt types and a time label.

## Slide 6: architecture (about 40 s)

This is the whole work, left to right. One: data creation, ten open-source projects with a clean copy and a debt copy of each, plus the git history of nine real projects. Two: the characteristics, 133 numbers per project, a fix-time label, and an interest value in person-months per debt instance. Three: the prediction, two levels. Level one says what kind of debt a change introduces. Level two says which debt instance will absorb future work. Four: the output, a ranking of debt types by cost, and a ranking of instances in a release. Five: the evaluation, which is the main goal: protocols that avoid leakage, and comparison with random, a simple rule and a perfect order. The last line on each column says what that stage signifies.

## Slide 7: dataset creation (about 55 s)

How I built the dataset. A snippet cannot show an import cycle or a fan-in, so each data point is a pair of whole projects, one clean and one with a single injected debt.

I took ten open-source projects with test suites. For each pair I made one small change that introduces a debt of one of five types, so type, place and clean twin are known. Sixty are injected, 45 by scripts and 15 in the SmellBench style, and one is a real libpng fix. The debt copy must pass the project's own tests, because real debt does not break behaviour.

Then the audit. Can a one or two line change really be debt? I keep a pair only if a metric of its own type moved. Of 102 candidates, 52 stayed. The 50 dropped are "not visible to these metrics", which is not the same as "not debt". I then added nine pairs from two more projects, C-Thread-Pool and libyaml, giving 61. Natural debt is future work.

## Slide 8: the dataset as it stands (about 45 s)

This is the dataset as it stands. Each row is one pair, and the model sees the difference between the debt copy and the clean copy: 133 numbers in three blocks. Structure, 46: layout, and the dependency graph with fan-in, fan-out, cycles, modularity and spectral values. Code, 50: size, function length, complexity, parameters, and language idioms. Debt, 37: smells and their COCOMO principal, class cohesion, locks and threads, security findings, self-admitted debt and duplication. Plus one time number and the target, the type.

The data is clean: no missing values, no infinite values, no pairs with identical vectors. Remember one thing from this slide: 24 of the 26 concurrency pairs come from one project, boltons. That comes back in the results.

## Slide 9: bugs and the fix-time label (about 60 s)

Why a time number? Debt makes later work slower. So the same bug goes into the clean copy and into the debt copy, and the extra time to fix it is the cost of the debt. There are three bugs per pair, 183 in total, small mutations such as negated conditions and off-by-one constants, and the same patch goes into both copies. I checked that all 246 bugged Python files parse, and all 59 C files pass a syntax compile.

The time itself comes from a ground-truth time model with a slowdown factor per type: concurrency 3.4, security 2.4, complexity 1.8, coupling 1.4 and dependency 1.05. That gives about 162 extra minutes per concurrency pair and 3 minutes per dependency pair. I did not have developers fix 183 bugs on 122 project versions, so these are model times, not measured developer times. And time alone predicts the type with 0.93 accuracy, so any gain from time is conditional on this model.

## Slide 10: Level 1 classifier (about 55 s)

Level one: which of five types does a pair introduce. The final model takes the 133 delta features plus time, a selector keeps the ten best by ANOVA F, and a random forest with 300 trees and balanced class weights gives the type. With 61 rows and 134 columns a model drowns in noise, so the selector helps, and it is fitted inside each training fold, so the test fold never decides which features are kept.

I compared seven classifiers to see whether the time effect depends on the algorithm. Classes are unequal, 26, 16, 7, 6 and 6, so I report accuracy, macro F1 and balanced accuracy, against a majority baseline of 0.426. To test whether a gain is real I use the McNemar test on the same predictions and a bootstrap interval for the difference. In total 656 runs, with nothing tuned on a test fold.

## Slide 11: the four protocols (about 55 s)

Why four protocols? Because pairs of one project look alike. In boltons, 24 pairs are all concurrency, so if one is in training and another in testing, the model can recognise the project instead of the debt.

The first two, stratified folds and 20 repeated random splits, keep type proportions. They are optimistic, because pairs of the same project sit on both sides. The last two hold out whole projects: by-project folds, and leave-one-project-out, where each project is tested once after training on the other nine. These are the honest numbers for new projects. Also, the debt change is tiny, 0.008 standard deviations on average, so projects differ far more than debt does. That is why the project leak is a real risk.

## Slide 12: interest from git history (about 60 s)

Level two works on real projects, because the injected pairs have no later history. I follow the 2025 method. Take the last 20 releases of nine projects. A debt instance is a SonarQube issue for Python, and for C and C++ a structural smell: a method over 50 lines, complexity over 10, or more than five parameters. Between two releases, git diff gives the lines changed inside that function.

If the instance disappears, that is repayment. If it is new, or the function grew, the principal increased. If it persists, the other changed lines are interest. COCOMO II turns lines into person-months: 2.94 times thousands of lines to the power 1.0997. I compute effort per event, because one hundred lines in one event costs more than ten events of ten lines.

Result: 10.52 person-months over nine projects, about 6 percent of the effort to rewrite all the debt once. The multipliers are one, so this is a relative estimate, not measured developer time.

## Slide 13: interest models and evaluation design (about 55 s)

Now the interest models and the evaluation. A row is one debt instance in one release. Targets: whether any interest happens next, how many person-months, and a two-part model that combines both.

The evaluation is the core. In each repository and release I rank the instances by predicted interest and look at what happened next. Capture at k is the share of all real next-release interest inside my top k percent; random gets k. Lift says how much more likely the top items are to pay interest. NDCG rewards putting big ones first. The baselines are random, persistence, which ranks by interest already paid, and the oracle, which sorts by the truth. Uncertainty comes from a bootstrap over groups. Two protocols: leave-one-repo-out with 123 groups, and temporal with 57. The hard part: 92 percent of instance-releases have zero interest.

## Slide 14: Result 1, debt type (about 55 s)

Results. On the left, the final model with and without time, for the four protocols. With stratified folds, accuracy goes from 0.79 to 0.92, with 20 random splits from 0.84 to 0.94. For the stratified case the interval of the gain is 0.05 to 0.23 and McNemar gives p of 0.008.

On the right, the seven classifiers on the same splits. Only the selector models gain a lot. The plain random forest is already at 0.885 and does not move. My reading, not tested separately, is that time is the top-ranked feature, so the selector always keeps it, while the forest mixes it with 133 weaker ones.

Look at the unseen-project bars: without time 0.43, the same as always guessing concurrency, and 0.51 with time. The model does not generalise across projects yet.

## Slide 15: Result 3, ranking instances (about 55 s)

The main result. For every repository and release I ranked the instances and checked how much of the next release's interest falls into the top 10, 20 and 30 percent.

Random gets 10, 20 and 30. The two-part model captures 38.5 percent in the top 20, interval 32 to 44, about 1.9 times random. A perfect order gets 95.8. The zero model lands on random, as it should.

But the simple rule, rank by interest already paid, gets 38.8 percent. So my learned models are clearly better than chance, and I cannot show that they beat that rule at this budget. NDCG is only 0.21, so the order inside the top group is weak.

## Slide 16: Result 4, capture curve (about 55 s)

This is the whole curve, in the plot and in the table: if the team repays the top k percent, how much of the future interest do they catch. Random is the diagonal, the oracle is the top line.

All methods sit well above random. Persistence is as good or slightly ahead at small budgets, but the two-part model pulls ahead for larger ones: at 50 percent it captures 73.5 against 67.0. A paired bootstrap over 123 groups gives plus 5.6 points, interval 0.4 to 10.7. That is positive but marginal, and I looked at several budgets, so I would not oversell it. At 20 percent the difference is minus 2.2 points and the interval includes zero. Honest reading: the model adds something at larger budgets, and nothing demonstrated at small ones.

## Slide 17: Result 5, what is predictable (about 40 s)

Last result. Whether an instance absorbs any work in the next release is weakly predictable: AUC 0.59 on unseen repositories and 0.71 on later releases. How many person-months is not predictable per instance: no model beats predicting zero, because 92 percent of instance-releases have no interest and the rest is heavy-tailed. The predicted project total is 1.14 times the actual, which is useful for budgeting a portfolio, not for single items. In one line: ranking is possible, amount estimation is not.

## Slide 18: limits and next steps (about 50 s)

To close. I cannot claim yet that my ranking beats the simple history rule, that the time gain holds for real developers, that the classifier works on unseen projects, or that injected debt behaves like natural debt. Sixty of 61 pairs are injected, the data is small, the COCOMO multipliers are one, and the bugs were checked for syntax, not by running tests.

Next: more natural pairs and projects, richer features such as change-proneness, ownership and tests to try to beat persistence, running the project tests on the bugged copies, measured fix times, a cost-aware metric, and applying the ranking to AI-written changes, where I started.

The status: a working, reproducible way to build and evaluate a prioritisation, with a ranking that beats chance and is not yet better than a simple rule. Thank you. I am happy to take questions.

## Slides 19-20: references (not spoken)

If asked, [1]-[12] are the literature and [13]-[27] are methods and motivation sources. The motivation figures are from secondary sources, and [12] still needs its full citation.

---

# PART B: QUESTION BANK

Format: Q, then A (say this), then "If pushed" where a follow-up is likely.

## B1. Motivation and problem

**Q1. Why technical debt, and why AI-generated code?**
A: Teams always have more debt than time, so ranking is the daily decision. AI-generated code makes debt arrive faster. Liu et al. found 22.7 percent of the issues from AI commits still present, so ranking is needed more, not less.
If pushed: my experiments do not yet use AI-written code. AI is the motivation and a next step, and I say so on the limits slide.

**Q2. Where do the motivation numbers come from, are they reliable?**
A: They come from the Stanford AI Index, Veracode, IBM, GitClear, CISQ and one primary paper [9] that I checked. The note on slide 1 says they have different samples. I use them to show the problem exists, not as results.
If pushed: the Amazon retail wording is marked "to be re-checked" on the slide, and I would not rely on it. Amazon disputes the AI cause of the AWS case.

**Q3. What exactly is your research question?**
A: Given more debt than can be repaid, can a model rank debt items so that the ones that cost the most are repaid first, and how do we test that ranking? The main contribution is the construction and the evaluation, not a new model.

**Q4. Why is "which first" hard, why not just use SonarQube's remediation time?**
A: Baldassarre et al. showed those estimates are inaccurate, and Lenarduzzi et al. showed violation counts have a small effect on faults. Remediation time is the cost to fix, not the cost of leaving it, which is interest.

**Q5. What is the practical use?**
A: A team gets a ranked list of debt instances per release, plus an estimate of which type of debt is most expensive. Today the list beats random by about 1.9 times and equals a simple history rule, so I do not claim a deployable tool.

## B2. Literature and novelty

**Q6. What is new compared with the 12 papers?**
A: Three things together. A paired whole-project clean and debt dataset with known type, place and a time label. An interest pipeline from git history in person-months. And a ranking evaluation with baselines and confidence intervals. The literature (Ehsani, Lenarduzzi) says benchmarks and validated tools are missing.
If pushed: individually these are not new methods. The value is putting them together so a ranking can be tested.

**Q7. How is this different from SmellBench?**
A: SmellBench evaluates code agents on refactoring, with injected smells at snippet or file level and 7 smell types. I inject at whole-project level, five debt types, and use the pairs for vectors and a time label. I took the injection idea and 15 pairs in that style from it.

**Q8. How is this different from Wiriyakul and Senivongse?**
A: I implement their interest method on nine projects, with my own instance definition for C and C++ (lizard thresholds). Then I add a prediction and a ranking evaluation on top. Their citation on my slide is still incomplete and I will fix it.

**Q9. Is effort-aware ranking evaluation new?**
A: No. Capture at k, lift and NDCG are standard in defect prediction and information retrieval. I apply them to debt instances with a persistence baseline. The novelty is the setting, not the metric.

**Q10. Why these 12 papers?**
A: Three groups matching the three gaps: prioritisation, interest and cost, and AI-era data and benchmarks. Years run from 2015 to 2026. Four of them are recent preprints, which I note as arXiv.

**Q11. Why are some references arXiv preprints, are they peer reviewed?**
A: [9], [10] and [11] are arXiv 2026 preprints, not peer reviewed yet. I use them for the problem statement and the injection idea. I checked their numbers against the papers, but they could change.

## B3. Dataset

**Q12. Why whole projects instead of snippets or commits?**
A: Debt such as cycles, fan-in and layout exists only at project level. A snippet cannot show an import cycle.

**Q13. Is injected debt real debt? Can a 1 or 2 line change be debt?**
A: That is why there is an audit. A pair is kept only if a metric of its own type moved, so the change is visible as debt: 52 of 102 kept. But injected debt is still not natural, and I say it is the main limit. One pair, libpng, is natural.
If pushed: I cannot claim injected behaves like natural debt. Adding natural pairs is my first next step.

**Q14. The audit used metrics of the same family the model uses. Is that circular?**
A: Partly, yes. The audit keeps pairs where a type-related metric moved, and the features include such metrics. That makes the type easier to see and may overstate Level 1. It is a reason I read the unseen-project numbers as the honest ones, and those are weak.

**Q15. What happened to the 50 dropped pairs?**
A: Their own-type metric did not move, so they are "not visible to these metrics". I do not say they are not debt. It also means the dataset is biased toward detectable debt.

**Q16. Why only 61 pairs, why 10 projects?**
A: Each pair needs a working clean and a working debt copy, passing tests, and an audit. Many projects were removed as too large or with weak tests. 61 is small, so my intervals are about plus or minus 0.10.

**Q17. Class imbalance and boltons?**
A: Classes are 26, 16, 7, 6, 6, and 24 of the 26 concurrency pairs are from boltons. So project and type are tangled, and the model can learn "boltons means concurrency". That is why I use project-held-out protocols. The majority baseline is 0.426.

**Q18. Why those 10 projects?**
A: Four Python (boltons, click, jinja, werkzeug) and six C/C++ (C-Thread-Pool, cJSON, jansson, libpng, libyaml, zlib), all with working tests and manageable size. C-Thread-Pool and libyaml were added to get more C concurrency and security cases.

**Q19. How were the 45 scripted and 15 SmellBench-style injections made?**
A: The scripted ones apply a fixed transformation per type, for example adding a lock pattern, an unsafe call, a cycle in imports, or deep nesting. The SmellBench-style ones follow the benchmark's smell definitions. Each is a small, controlled diff.

**Q20. Did you test that the debt copies still work?**
A: Yes, the debt copy must pass the project's own tests. The bugged copies, however, were only checked for parsing (246 of 246 Python) and syntax compile (59 of 59 C), not for tests.

**Q21. Can others reproduce the dataset?**
A: The pipeline is scripted, and re-running the bug injection gives identical patches. The code is in the repository, which has the pipeline and the README for each step. The interest folder and presentation are not yet pushed.

**Q22. Data leakage between clean and debt copies?**
A: Both copies are in the same row as one delta, so they cannot be split across train and test. The leak I worry about is between pairs of the same project, which is why I hold out projects.

## B4. Features

**Q23. Why 133 features, and why the delta?**
A: Structure 46, code 50, debt 37, covering what the five debt types would change. I use the delta, debt minus clean, because it isolates what the injection changed. The "full" layout (399 columns) is also tested.

**Q24. Delta is 0.008 standard deviations on average. Is there any signal?**
A: Yes, in a few features that are specific to the type, such as lock counts for concurrency. On average the change is tiny, which is why the selector keeps ten features and why project differences dominate.

**Q25. Which features matter most?**
A: With time included, time is the top feature (ANOVA F about 120). Without time, the type-specific counts (locks and threads, security findings, nesting or complexity, import-graph cycles) lead. I would show the importance table if asked, and I would not claim a causal reading.

**Q26. Could features just be encoding the project?**
A: Possibly, that is the risk, and the reason the unseen-project accuracy is only the majority baseline (0.43).

## B5. Time label (expect the hardest questions here)

**Q27. Is the fix time measured from real developers?**
A: No. The times come from a ground-truth time model with a slowdown factor per type (3.4, 2.4, 1.8, 1.4, 1.05) and a touched-file factor, applied to bug patches. I did not have developers fix 183 bugs on 122 versions. I state that on slide 9.
If pushed: so the time is an assumption that I treat as ground truth for the experiment, as in the question "what if time were known". It is not evidence about developers.

**Q28. Then isn't the time gain circular?**
A: Partly, yes. The time depends on the type, so adding it gives the classifier the answer in another form. Time alone gives 0.93 accuracy. That is why I call the gain conditional on the time model, and why I do not claim it as a finding about real developers.
If pushed: what the experiment does show is the mechanism: if cost differences between types are large and known, a type classifier uses them. The real question is whether real fix times separate the types. That needs measured times.

**Q29. Why those factors, who decided them?**
A: I set them from the idea that concurrency and security bugs take longer to debug, and complexity somewhat longer. I calibrated them after seeing the classifiers, and replaced one weak setting that gave almost no gain. That is a selection I disclose.
If pushed: with the weakest setting the gain was only +0.03, and with the one I use +0.11 (accuracy of time alone 0.60 versus 0.96 on random splits). So the headline depends on this choice.

**Q30. Did you check the gain is not a leak?**
A: Yes. Shuffling the time between pairs gives no gain (0.840 against 0.839), so the gain comes from the real time-to-type link. Adding noise to the time shrinks the gain and it is gone at log-noise 1.0. This control was on a slide in an earlier version of the deck and I can show it on request.

**Q31. Why is the time model so simple, only type and a touched flag?**
A: I wanted the label to depend on the debt, with a small factor if the bug is in a file the debt change did not touch (0.85). A richer model would need data that I do not have.

**Q32. Could you have used real fix times, for example SZZ or issue resolution times?**
A: Yes, it is in my next steps. SZZ (reference [14]) or issue resolution times would give real lifetimes for natural bugs. It needs natural debt and bug-fix history, which the injected pairs do not have.

**Q33. Why not run a small study with developers?**
A: Cost and time within the BTP. It is the best way to replace the model and it would be the strongest next step, even with 20 to 30 pairs.

**Q34. Why do you call it "ground truth"?**
A: For the experiment, the model time is the reference against which the classifier is trained and evaluated, so I call it ground-truth time model. I do not mean it was measured.

## B6. Models and metrics

**Q35. Why random forest?**
A: It is a strong default for small tabular data, handles mixed scales, needs little tuning, and has balanced class weights for my imbalance [24].

**Q36. Why the 10-best selector and why k = 10?**
A: With 61 rows and 134 columns, noise features hurt. The selector is fitted inside each fold. k = 10 was fixed in advance, not tuned on test folds.
If pushed: I did not scan k, so I cannot say 10 is optimal. The result might vary with k.

**Q37. Why did the plain random forest not gain from time?**
A: My reading is that the selector always keeps time because it has the top F, while the forest spreads attention over 133 weaker features. I did not test that separately, so I call it a reading.

**Q38. Why those seven classifiers?**
A: To see whether the time effect depends on the algorithm: tree ensembles, boosting, linear, margin-based, distance-based, and two with the selector. Settings are fixed and not tuned.

**Q39. Why accuracy, macro F1 and balanced accuracy?**
A: Classes are unequal (26/16/7/6/6), so accuracy alone favours concurrency. Macro F1 and balanced accuracy weight classes equally. The majority baseline of 0.426 is the floor.

**Q40. What is McNemar's test here?**
A: It compares two models on the same test items by counting the items one gets right and the other wrong [21]. For time versus no time with stratified folds, p = 0.008.
If pushed: with 61 items and many comparisons I do not correct for multiple testing, so I treat single p-values as indications.

**Q41. What is the bootstrap used for?**
A: A 95 percent interval of the accuracy gain (0.05 to 0.23) and, for ranking, an interval over repo-release groups [22].

**Q42. 656 runs: is there a multiple-comparison problem?**
A: Yes, in principle. I did not tune on test folds, and I report all runs in the tables rather than pick one, but I did not correct p-values. I treat only the stratified time gain as a tested claim.

**Q43. Why not deep learning or a pretrained code model?**
A: With 61 rows it would overfit. Pretrained models are a possible direction with more data, for example embeddings as features, but I have not run that.

## B7. Protocols and statistics

**Q44. Why four protocols, isn't one enough?**
A: Each answers a different question: stable average (20 repeats), same splits for all models (stratified), and unseen projects (by project and leave-one-project-out). Only the last two are honest for new projects.

**Q45. Which number should I believe?**
A: For unseen projects: 0.43 without time and 0.51 with time, at the 0.426 majority baseline. The 0.92 is optimistic, because the same project is in train and test.

**Q46. Isn't it a problem that your headline number is the optimistic one?**
A: It is shown for comparison with time, with the honest numbers next to it on the same chart, and I state which is which on slides 11 and 14. I do not use 0.92 as a claim about new projects.

**Q47. How does the temporal protocol work?**
A: Train on earlier releases of the instances, test on later ones. 57 groups. It avoids using the future to predict the past, and gives a higher AUC (0.71) than leave-one-repo-out (0.59).

## B8. Interest

**Q48. What is "interest" in your work?**
A: Extra rework effort spent on a debt instance while it persists: lines changed inside the smelly function between releases, minus changes that are pure growth, converted to person-months with COCOMO II.

**Q49. Why COCOMO II, why is it valid?**
A: It is the method of [12] and a standard size-to-effort model [13]. I use nominal constants (A = 2.94, E = 1.0997) with multipliers one, so values are relative, and I did not calibrate them for these projects.

**Q50. Why compute effort per event instead of summing lines?**
A: COCOMO is non-linear (exponent above 1): 100 lines in one event gives 0.234 PM, while ten events of ten lines give 0.186. So summing lines first would overstate effort.

**Q51. How do you define a debt instance?**
A: Python: a SonarQube issue. C and C++: a structural smell, method over 50 lines, CCN over 10, or over 5 parameters, found with lizard. The thresholds are common defaults, not tuned. It is my choice, and different thresholds would change the counts.

**Q52. Is changed code in a smelly function always interest?**
A: No. A change might be a feature or a bug fix, not an extra cost caused by the smell. I count all non-growth changes inside the function as interest, which is the method's assumption. That inflates interest and is a limit.

**Q53. Why is 6 percent of principal meaningful?**
A: It says the observed rework over 20 releases is about 6 percent of what it would cost to rewrite all the debt once. It is only a relative scale, as the constants are nominal.

**Q54. Why is C-Thread-Pool missing from the interest part?**
A: It has no release tags, so there is no release history. Nine of the ten projects are used.

**Q55. Why can't the injected pairs have interest?**
A: They have no later history, so interest is undefined for them. That is why Level 2 uses real projects, and why Level 1 and Level 2 are two separate experiments, not one pipeline.

**Q56. So the two levels are not connected?**
A: Correct. Level one predicts type on injected pairs with a time label. Level two ranks real instances by interest. They meet only at the idea of ranking by cost. A single model joining both needs natural debt with history and times. I should say that clearly.

## B9. Results

**Q57. Is 38.5 percent good?**
A: It is about 1.9 times random (20 percent), but equal to the simple persistence rule at 38.8 percent. Against a perfect order (95.8) it is far away.

**Q58. So what does your model add over persistence?**
A: At small budgets, nothing demonstrated. At 50 percent, +5.6 points with a CI of +0.4 to +10.7, which is marginal, and I looked at several budgets. I do not claim it.
If pushed: it also works for instances with no interest history yet, where persistence ranks all of them equal, but I did not test that separately.

**Q59. Why is NDCG only 0.21?**
A: Because the order inside the top group is weak. Spearman is about 0.14. Many instances have zero interest, and the amounts are heavy-tailed.

**Q60. Why can the amount not be predicted?**
A: 92 percent of instance-releases have zero interest, and the rest is heavy-tailed, so no regressor beats predicting zero. The two-part model helps for ranking but not for amounts. The project total is 1.14 times the actual, so only portfolio level is usable.

**Q61. Is AUC 0.59 useful?**
A: It is weak but real (chance is 0.5). 0.71 on the temporal protocol is better. It is enough for the 1.9 times capture, not for decisions on single items.

**Q62. Are results stable across projects?**
A: I report averages over groups with bootstrap intervals, not per project. A per-project breakdown is worth adding, as larger projects with many groups may dominate.

**Q63. Do the leave-one-repo-out and temporal results agree?**
A: Yes in direction: hurdle 28.2 and 41.9 percent at top 10 and 20 with temporal, persistence 23.4 and 39.1, with overlapping intervals. Again no clear win over persistence.

**Q64. Why did you remove the earlier model with R² 0.90?**
A: It predicted the COCOMO effort of the patch, which is an exact function of lines added, so it was leakage. Under leave-one-project-out R² was negative. I replaced it with the instance-ranking task.

## B10. Limits and threats to validity

**Q65. What are the biggest threats to validity?**
A: Internal: time model chosen after seeing results, audit circularity, bugs not run through tests. External: 10 projects, 60 of 61 injected, one project gives 24 pairs. Construct: person-months from nominal COCOMO, and interest assuming all changes in a smelly function are interest.

**Q66. Is the dataset big enough to conclude anything?**
A: Not for strong claims. The intervals are about plus or minus 0.10. It is enough to show the method works and to find where it fails.

**Q67. Did you choose the models or settings after seeing test results?**
A: The time setting, yes, and I disclose it. The classifier settings were fixed, and feature selection is inside folds. The k values for the paired comparison were several, which I flag.

**Q68. Would this work on other languages?**
A: I tested Python and C/C++ only. The features include language idioms, so other languages need new extractors.

**Q69. Would it work on AI-generated code?**
A: Untested. It is my motivation and the last next step. The ranking would run on AI-written changes if the history exists.

## B11. Future work and positioning

**Q70. What would you do first with more time?**
A: First, measured or real-proxy fix times, even for 20 to 30 pairs. Second, more natural debt pairs. Third, richer features such as change-proneness and ownership to try to beat persistence. Fourth, run the tests on the bugged copies.

**Q71. Is this publishable?**
A: As a benchmark and evaluation-method paper with honest negative results, at a workshop or data-track level, yes. For a full empirical paper I need measured costs, more natural debt and a model that beats persistence.

**Q72. What is your single main finding?**
A: Ranking debt instances by learned interest beats chance by about 1.9 times but not yet a simple history rule, and amounts cannot be predicted. The second finding is the method: pairs plus time plus protocols to test it.

**Q73. What would change your conclusion?**
A: If real fix times did not separate the types, the time gain would vanish. If richer features beat persistence in a paired test, the ranking claim would change.

## B12. Curveballs

**Q74. Why should anyone trust a model trained on injected data?**
A: They should not yet for deployment. I use injection to get a known answer for evaluation, and say the transfer to natural debt is untested.

**Q75. You said time alone gives 0.93. Then the type classifier is useless, isn't it?**
A: As a predictor of type with time given, yes, it adds little. The time is not known before fixing, so it is a probe of the cost-type link, not a deployed input. For prioritisation, the useful target is cost itself, which is where I would go next.

**Q76. Why present results that are negative?**
A: Because the goal is to test the ranking, and an honest comparison with persistence is the point of the evaluation.

**Q77. Did you use an AI assistant for the project?**
A: Say honestly what you used and what you did yourself. Be ready to explain every number on the slides, since the examiner will ask.

**Q78. Can you explain the formula 2.94 × (KLOC)^1.0997?**
A: It is the COCOMO II.2000 nominal post-architecture equation with A = 2.94 and scale exponent E from nominal scale factors, with effort multipliers set to one. Size is in thousands of lines.

**Q79. What is SelectKBest with ANOVA F?**
A: It scores each feature by the ratio of between-class to within-class variance, and keeps the 10 highest. Done inside the training fold only.

**Q80. What is a hurdle model?**
A: A two-part model: one part predicts whether the outcome is above zero, the second part predicts the amount given that it is positive. It suits data with many zeros [27].

**Q81. What are capture@k, lift and NDCG in one line each?**
A: Capture@k: share of all real interest inside my top k percent. Lift: precision in the top k divided by the base rate. NDCG: ranking quality that rewards putting large amounts first [26].

**Q82. What is persistence and why use it as the baseline?**
A: Rank instances by the interest they have already paid. It is cheap and uses the same history, so any model must beat it to be worth building.

---

# PART C: NUMBERS CHEAT SHEET

- Dataset: 61 pairs, 10 projects (4 Python, 6 C/C++), 60 injected (45 scripted, 15 SmellBench-style) and 1 natural (libpng). Classes: concurrency 26, security 16, dependency 7, coupling 6, complexity 6. Funnel: 102 candidates, 52 kept, plus 9 added = 61. Bugs: 183 (3 per pair), 70 in a touched file. Checks: 246 of 246 parse, 59 of 59 compile.
- Features: 133 = structure 46, code 50, debt 37. Layouts: delta_only 133, full 399.
- Time model factors: concurrency 3.4, security 2.4, complexity 1.8, coupling 1.4, dependency 1.05. Mean extra minutes: 161.6, 92.0, 53.5, 22.7, 3.2. Time alone: 0.93 accuracy.
- Level 1, 10-best + RF: stratified 0.787 to 0.918; 20 splits 0.840 to 0.938; by project 0.311 to 0.508; leave-one-project-out 0.426 to 0.508. Majority 0.426. Gain CI +0.05 to +0.23, McNemar p = 0.008. Plain RF 0.885 both. 656 runs.
- Seven classifiers (without, with time): RF 0.885/0.885; GB 0.836/0.918; LR 0.721/0.787; SVM 0.705/0.705; kNN 0.639/0.639; 10-best+LR 0.525/0.803; 10-best+RF 0.787/0.918.
- Time controls (backup): shuffled 0.839 against 0.840; noise 0.25 gives 0.926, 0.5 gives 0.884, 1.0 gives 0.839. Settings: weak +0.03, used +0.11, strong +0.12, near-deterministic +0.12.
- Interest: 10.52 PM, about 6 percent of principal, 20,853 instance-releases, 1,557 instances, 1,607 events, 9 projects (0.09 to 2.44 PM each), 92 percent zeros.
- Ranking, leave-one-repo-out, 123 groups: top 10/20/30 percent: two-part 20.0/38.5/51.5; persistence 21.7/38.8/46.9; RF regression 17.2/35.0/48.9; zero 9.6/18.6/30.6; oracle 89.9/95.8/98.1. Two-part at top 20: CI 32-44, lift 1.86, NDCG@20 0.21 (persistence 0.23). At 50 percent: 73.5 against 67.0, difference +5.6 (0.4 to 10.7). Differences at 10, 20, 30: -2.0, -2.2, +3.3, all with CIs including zero.
- Temporal (57 groups): two-part 28.2 and 41.9 at top 10 and 20; persistence 23.4 and 39.1.
- Predictability: any-interest AUC 0.59 / 0.71; function level 0.57 / 0.62; amount: no gain over zero; project total ratio 1.14.

# PART D: RULES FOR ANSWERING

1. Answer the question asked in the first sentence, then add one supporting number.
2. When the criticism is right, say so and give the limit as already written on slide 18. Examples: injected data, time model, persistence not beaten, no unseen-project generalisation. Do not defend what the data does not show.
3. Never describe the fix times as measured from developers or from a survey. They come from the time model.
4. Do not call the 50 dropped pairs "not debt"; say "not visible to these metrics".
5. Do not claim the model beats persistence, and call the +5.6 points at 50 percent marginal.
6. If you do not know, say "I did not test that" and name how you would (for example, scan k, or per-project breakdown). A clear "not tested" is better than a guess.
7. Keep to the printed numbers in Part C; if a number is not there, say you would check it in the results files rather than estimate.
