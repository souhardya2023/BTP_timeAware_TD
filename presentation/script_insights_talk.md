# Talk script: 10 minutes + 2 minutes questions

Deck: `btp_report/TD-presentation-insights.pdf` (30 pages). Speak about 140 words a minute. Total planned talk time: 9:40, so you have 20 seconds spare.

| slides (PDF page) | topic | time | clock |
|---|---|---|---|
| 1-3 | motivation | 0:35 | 0:35 |
| 4-6 | literature | 0:25 | 1:00 |
| 7 | architecture, three topics | 0:35 | 1:35 |
| 8-9 | data and features | 0:45 | 2:20 |
| 10 | bugs and fix time | 0:25 | 2:45 |
| 11-12 | Level 1 classifier and protocols | 0:45 | 3:30 |
| 13-14 | Level 2 interest and ranking | 0:45 | 4:15 |
| 15-17 | results | 1:10 | 5:25 |
| 18-20 | insights | 0:55 | 6:20 |
| 21-22 | scenarios and code traits | 1:10 | 7:30 |
| 23-26 | code insights | 1:10 | 8:40 |
| 27 | reverse engineering | 0:30 | 9:10 |
| 28 | limits and future work | 0:30 | 9:40 |

How to read the blocks: **SAY** is what you speak. **PLOT** is what is drawn and why. **SEE** is what the audience should take from it.

---

## Slides 1-3: motivation (0:35)

**SAY**
Good morning. My project is about technical debt in the time of AI-written code. AI tools write code very fast, and the debt they add grows faster than teams can repay it. The incidents on this slide show what rushed changes can cost. So a team has a simple problem: there is a lot of debt, I can fix only some of it, so which should I fix first, and how do I know my choice is good? That is what I worked on.

---

## Slides 4-6: literature (0:25), go fast

**SAY**
The literature is in three tables. First, how debt is prioritised today, mostly by rules and tools like SonarQube. Second, debt as a loan, with principal and interest. I follow the method of Wiriyakul and Senivongse and use COCOMO II to turn changed lines into person-months. Third, AI-era debt and benchmarks. The gap I take is this: very few works check a ranking against what really happened later. So my focus is on evaluation.

---

## Slide 7: architecture (0:35)

**SAY**
This is the whole work on one slide. I look into three topics: classify the debt, rank it, and evaluate the ranking. From left to right: data creation, then the characteristics of each project, then the prediction, then the output, then the evaluation. Classification says what kind of debt it is. Ranking says which debt to repay first. Evaluation says if that ranking is really better than a simple rule.

**PLOT** a flow diagram, one box per stage. **SEE** that every stage has a tool and a question it answers.

---

## Slides 8-9: data and features (0:45)

**SAY**
For classification I needed pairs: a clean project and the same project with debt, so the answer is known. I built 61 pairs from open-source Python and C projects, in five debt types. Sixty were made by injecting debt and one is natural, and I will come back to that limit. Each project becomes a vector of 133 numbers. These come from the AST of the code: counts of node types, structure and complexity, together with the debt-type information. The debt itself is the difference between the debt vector and the clean vector.

---

## Slide 10: bugs and fix time (0:25)

**SAY**
I thought one more signal could improve the classification: the extra time needed to remove a bug that the debt causes. So I created bugs in the copies, measured the time to fix them, and added that time as a feature. The question is simple: does the time help the classifier?

---

## Slides 11-12: Level 1 classifier and protocols (0:45)

**SAY**
Level 1 is the classifier. I compared seven models. The final one uses the ten best features with a random forest. I tested it with four protocols, from easy to hard: stratified folds, 20 random splits, split by project, and leave one project out. The last two protocols are the honest ones, because they ask if the model works on a project it has never seen.

---

## Slides 13-14: Level 2, interest and ranking (0:45)

**SAY**
Level 2 is ranking. For every debt instance I measure its interest from the git history: the lines changed inside the debt function while the debt stays, converted to person-months with COCOMO II. Then, for one release, I rank the instances by predicted interest and check how much of the next release's interest sits in the top k percent. I compare against random, against persistence, which means rank by the interest already paid, and against an oracle. I evaluate by leaving one repository out, and also by time.

---

## Slide 15: Result 1 (0:25)

**SAY**
Result 1, the classifier. With the fix time, accuracy goes from 0.79 to 0.92 on stratified folds, and from 0.84 to 0.94 on random splits. So time helps when the project is known. But on a new project the accuracy is 0.43 to 0.51, close to the majority class of 0.43. So the type is learnable inside known projects, not yet across projects.

**PLOT** bars of accuracy for each protocol, grey = without fix time, blue = with it, dashed line = majority class. **WHY** to show the drop from easy protocols to hard ones. **SEE** the blue bars are high on the left and fall to the dashed line on the right.

## Slide 16: Result 2 (0:25)

**SAY**
Result 2, ranking, on 9 repositories. If a team repays the top 20 percent by persistence, it captures 39 percent of the next release's interest, while random gets 20. My two-part model gets 38, so it is not better than persistence. The simple rule is already strong.

**PLOT** bars of captured interest at the top 10, 20 and 30 percent for random, persistence and the model, and a small table with lift. **SEE** persistence and the model have the same height, and both are well above random.

## Slide 17: Result 3 (0:20)

**SAY**
Result 3 moves to 33 repositories, the table on the slide. Size plus history captures 41.5 percent against 39.8 for persistence. This is a small gain, about two points, and it is clear only at the top 30 percent. The AUC for where interest goes is 0.62 for size, 0.75 for persistence, 0.79 for size plus history.

**PLOT** bars of capture for random, size, persistence and size plus history, and an AUC table. **SEE** history matters more than size, and the combination is only slightly better than history.

---

## Slide 18: switch to insight mode (0:20)

**SAY (the bridge, say this slowly)**
From here I change mode. The results show that with 61 pairs and a few repositories, I cannot say much more. So I asked a different question: what does real technical debt actually look like in real projects? I analysed 33 real repositories, and I had two reasons. First, to find the patterns in real data. Second, to put those patterns into a synthetic dataset, so I can build a benchmark where the truth is known and I can test ideas safely. Here are my top three insights.

**SAY (Insight 1)**
One: interest is concentrated. The top 10 percent of instances hold 80 percent of all interest. And an instance that paid before tends to pay again: 8 percent with no past event, 43 percent with five or more. I should be honest that this memory effect is strong in C and C++ and not clear in Python.

**PLOT** left: instances sorted by interest against the share of all interest (a Lorenz curve). Right: share paying in the next release by the number of past events. **SEE** a steep curve far above the diagonal, and bars that rise with history.

## Slide 19: Insight 2 (0:15)

**SAY**
Two: debt is not avoided. My earlier number of 0.33 came from counting new and deleted code in the denominator. When I compare functions of the same size, a debt function is edited as often as a clean one, odds ratio 1.07. So size is exposure: bigger functions are edited more.

**PLOT** left: the share of edits in debt code compared with its share of code, 0.33 before and 1.11 after the correction. Right: edit rate by function size, clean against debt. **SEE** the bars of clean and debt are almost the same height at every size.

## Slide 20: Insight 3 (0:20)

**SAY**
Three: the release type is the clock. In a patch release 9 percent of debt pays interest, in a minor release 28, in a major release 31. The release type and the days since the last tag are known in advance and explain 0.27 of the interest. Commits and changed lines explain more, but we know them only after the release.

**PLOT** left: share paying by release type. Right: how much of the release interest each predictor explains. **SEE** patch is quiet; the predictors known in advance explain less than the ones known afterwards.

---

## Slide 21: scenarios (0:40)

**SAY**
Then I chose patterns and tested if they are really present. I call each pattern a scenario: a group of functions, debt instances or commits picked by a condition. For each scenario I measure a rate ratio, which says how many times more often the event happens in the group than in the rest of the same repository. One means no effect. I measure Python and C and C++ separately. If the effect is clear in both languages and in most repositories, the scenario repeats. If it is clear in one language, it is language-specific. If the interval includes one in both, it is noise.

**PLOT** a forest plot: one row per scenario, a grey circle for Python and a blue square for C and C++, with 95 percent intervals, and the dashed line at 1. **SEE** the top rows sit to the right of the line in both colours. The bottom rows sit on the line, and that is noise.

**SAY (results of the test)**
I tested 23 scenarios: 7 repeat, 9 are language-specific, 7 are noise. Two that repeat: larger functions are edited more, rate ratio about 1.4 in Python and 1.8 in C and C++, and a busy release makes debt pay more, 4.4 and 2.8. One that is noise: a debt function is edited more or less than a clean one. It is present in single repositories, but it has no stable direction. I also checked the synthetic benchmark: it shows the same direction in 11 of the 15 scenarios it can express, and in all four repeating ones among them.

## Slide 22: code traits (0:30)

**SAY**
Now the code itself. The debt label only says that a function is long, branchy or has many parameters. So I read the code text of those functions and asked: which visible trait goes with more interest at the same size? The table gives the rate ratios for C and C++ and for Python. Most clear effects are in C and C++, so I present them as C and C++ findings. For Python I have much less data and nothing is clear, except one thing that works in both languages: copied code.

**PLOT** a table of traits against rate ratio with intervals. **SEE** rows whose interval excludes 1 (calls, pointer fields, repeated lines, clones) and rows that stay near 1 (goto, unsafe calls, malloc and free, nesting).

---

## Slide 23: Code insight 1, copied code (0:30)

**SAY**
Insight one is copied code. I first tested clones with a crude method and found nothing. With a proper whole-repository near-clone detector the picture changes in two parts. A clone alone is not edited more, in C and C++ it is even edited less. But when one copy is edited, its partner is edited in the same release 81 percent of the time in C and C++ and 96 percent in Python, against 47 and 49 percent for a function of the same size that is not a clone. The rate ratio is 1.7 and 2.0. So the cost is hidden: each change has to be repeated. On the slide, the two jinja functions are near-copies, and both changed in the same release.

**PLOT** two code boxes, the lines changed in the next release marked with a greater-than sign. **SEE** the two functions look the same, and both are marked.

## Slide 24: Code insight 2, touches many things (0:20)

**SAY**
Insight two, in C and C++: a function that calls many different functions pays interest more often, 27 percent against 18 expected, in 15 of 17 repositories. On the left, extent_init sets ten fields with ten different calls, so any new field means an edit here. On the right, a function of the same length calls only three different functions, and nothing changed. By size or by the debt label, they look alike. In Python this is not confirmed.

## Slide 25: Code insight 3, repeated lines (0:10)

**SAY**
Insight three: functions that repeat the same lines are touched less, 17 percent against 23. The function on the right repeats mirrored checks and looks like bad debt, yet it was not touched. I think a fixed list of cases rarely changes, but I have not tested that.

## Slide 26: Code insight 4, noise (0:10)

**SAY**
And one noise case: goto, unsafe string calls, malloc and free, and deep nesting all have rate ratios between 0.96 and 1.04. They look like debt to a reader, but they do not predict how often code is edited. They matter for bugs and safety, which I did not measure.

---

## Slide 27: reverse engineering (0:30)

**SAY**
Instead of choosing scenarios myself, I let the data propose them. I fit a decision tree on some repositories, and each leaf with a high or low event rate is a rule. Then I check the rule on repositories the tree has never seen. Rules found in Python hold in C and C++ in 5 of 5 cases, but rules found in C and C++ hold in Python in only 1 of 5, because the history effect is stronger in C and C++. On random halves, 89 percent of the 161 rules repeat. But one warning: with shuffled labels 80 percent of rules still repeat. So this test alone does not separate signal from noise, and that is why I rely on the named scenarios.

**PLOT** four bars: the share of discovered rules that repeat for each split. **SEE** the grey bar (C and C++ to Python) is the low one.

---

## Slide 28: limits and future work (0:30)

**SAY**
Limits. The 61 pairs are mostly injected. The type classifier is not yet better than the majority class on new projects. Smells are a proxy for debt, and interest is implied effort, not measured time. The synthetic benchmark matches the real histories for ranking, but a classifier trained on it fails on the real pairs. Next: more natural pairs, smaller debt changes in the synthetic pairs, ranking with size and history and the release clock, and a test on AI-written code across several GPT models, where the same scenarios should repeat or be noise. I have also started comparing embeddings from several code models, and I plan to explore the image and time-series ideas in the next phase. I have also submitted a paper from this domain to FIRE 2026. Thank you. I am happy to take questions.

---

## Questions: short answers (2 minutes)

- **Why not just use persistence?** On the 9 repositories it is as good as my model. On 33 repositories size plus history is slightly better, about two points, so the honest answer is that persistence is a very strong baseline.
- **Is the synthetic benchmark realistic?** For ranking, yes: the AUC values are close to real (0.62, 0.73, 0.79 against 0.62, 0.75, 0.79). For the type classifier, no: a model trained on it gets 0.15 on the 61 real pairs, because debt changes are still too visible. I tuned it against my own tests, so that is a fit, not an independent test.
- **Why does memory differ by language?** I measured it, I did not explain it. In C and C++ the odds ratio is about 4.6, in Python about 1.4 and not significant. Python also has much less data.
- **Is a smell really debt?** No, it is a proxy: a threshold on size, complexity and parameters. Interest is implied effort from changed lines, not measured time.
- **Why only 61 pairs, and injected?** Natural clean and debt pairs are hard to find with a known answer. That is why I also mined natural pairs from commits, and why this is the first item of future work.
- **What does noise mean here?** A pattern whose interval includes 1 in both languages. It can show in single repositories but has no stable direction.
- **Can the clone result be something else?** Yes: "edited in the same release" does not prove the same fix was applied to both. It could be a shared refactor. The jinja pair is one case where both changed.
- **What about GPT models?** Not tested, because I have no GPT-written code yet. The plan is the same tests with the model in place of the language.

## Numbers to remember
61 pairs, 133 features. 0.79 to 0.92 (stratified), 0.43 to 0.51 (new projects), majority 0.43. 9 repos: persistence 38.8, model 38.5, random 20. 33 repos: size plus history 41.5, persistence 39.8, AUC 0.62 / 0.75 / 0.79. Top 10 percent hold 80 percent. 9 / 28 / 31 percent by release type. 23 scenarios: 7 / 9 / 7. Clones: 81 vs 47 percent (C and C++), 96 vs 49 (Python). Rules: 5 of 5, 1 of 5, 89 percent, control 80 percent.
