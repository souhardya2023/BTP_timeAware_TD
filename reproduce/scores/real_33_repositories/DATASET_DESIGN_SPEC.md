# Design specification of the new dataset, from 33 real projects

Every row says: what the real projects show, what the new dataset must therefore do, and how to check it (an acceptance test run on the finished dataset, with a tolerance).
Source of the numbers: `INSIGHTS_REAL_PROJECTS.txt` (item numbers RP1-RP20) and `results/`. The earlier synthetic benchmark (150 projects) failed several of these (see the last section), so the targets are stated as measurable properties.

## A. Two products

| product | for | content |
|---|---|---|
| **History benchmark** | Level 2 (interest, ranking) | projects with 20+ releases and a commit stream, debt instances with known interest, release types and dates |
| **Pair dataset** | Level 1 (type of debt) | a change (commit) and its parent, with the type, the place and the size of the change; natural pairs first, injected pairs only to fill the gaps |

## B. Properties of the history benchmark

| # | property | real value (33 repositories) | rule for the generator | acceptance test (tolerance) |
|---|---|---|---|---|
| H1 | function sizes | log-normal; C mu 2.47 sigma 1.01 (median 11 lines, p90 46); Python mu 1.78 sigma 0.94 (median 5, p90 22); corr(size, complexity) 0.91 / 0.84 | draw function sizes from these laws; complexity from size with that correlation | median and p90 within 15 % |
| H2 | debt share | 17 % (C) and 8 % (Python) of functions exceed a threshold; debt functions hold a median 41 % of the code lines (10 % to 79 %) | do not insert a few debt functions; let the thresholds select the debt from the size law | share of debt functions 5-20 %; share of debt lines 0.2-0.6 |
| H3 | exposure law | P(event) per release pair: logit slope 0.61 on log size (OR 1.52 per doubling); interest lines ~ size^0.93 | edit rate of a function = base x size^0.6 (logit) for ALL functions | slope 0.45-0.75 (instance level, repository fixed effects) |
| H4 | NO avoidance of debt | at equal size, a debt function is edited with OR 1.07 (0.92-1.25); enrichment among surviving functions 1.11 | edits do not depend on the debt flag, only on size, memory and the release clock | OR of the debt flag 0.85-1.25; matched enrichment 0.9-1.3 |
| H5 | memory | P(event after an event) 0.46 against 0.11-0.13; OR 4.6 (2.8-7.8) with size controlled; flat over lags 1-6 | a latent per-instance rate (heterogeneity), no decay | lag-1 ratio 3-5; lag 6 / lag 1 > 0.6; adjusted OR 3-8 |
| H6 | concentration | Gini 0.72 per repository (0.44-0.88); never-pay (10+ releases) 22 % per repository median; top 10 % of instances 58 % (Python) to 80 % (C) of interest | heavy-tailed instance rates | per-repository Gini median 0.6-0.85; never-pay 15-40 % |
| H7 | event size | median 2.5 lines, p90 16, top 10 % of events 67 % of the interest | log-normal event size with a heavy tail | median 2-4, p90 12-25 |
| H8 | no contagion | OR 1.09 (0.60-1.96) for another instance of the file having paid, own history controlled | no coupling of the rates of different instances of a file | adjusted OR 0.6-1.6 |
| H9 | release types | 58 % patch, 33 % minor, 8 % major release pairs; event rate 0.09 / 0.28 / 0.31; churn 0.6 % / 7.2 % / 13.6 % of the code; days 37 / 104 / 98; commits 10 / 72 / 97 | draw the release type, then the number of commits and the days from it; the activity of a release follows its commits | R2 of log release interest on step + days (leave one project out) 0.15-0.40; correlation with log commits 0.6-0.8 |
| H10 | no autocorrelation of the clock | within-repository correlation with the previous release -0.07 | independent release activity given its type and size | between -0.2 and 0.1 |
| H11 | life cycle | 76 % of new debt in new functions, 24 % by growth over a threshold; survival 0.93 / 0.80 / 0.68 / 0.57 after 1 / 3 / 6 / 12 releases; repayment 6.9 % per release (C 7.5 %, Python 1.6 %); activity falls with age (OR 0.93 per release) | births in new code; repayment hazard about 7 % per release (C) and 2 % (Python); a mild early-life peak | survival at 12 releases 0.45-0.70; age OR 0.85-1.0 |
| H12 | several smells per function | 47 % of debt functions carry 2-3 smells | share smell kinds by one size/complexity draw (no independent draws) | 35-60 % |
| H13 | project dynamics | growth x1.15 over 20 releases (median); churn 1.4 % of the code per release pair (median) | | within 30 % |

Baselines the benchmark must keep honest (the earlier benchmark did not): top-20 % capture with leave-one-project-out should be about **persistence 39-40, size + history model 41-42, size alone 34, random 20** (the real values); the gap size+history over persistence 2-3 points.

## C. Properties of the commit stream (and of the injected / natural pairs)

| # | property | real value | rule | acceptance test |
|---|---|---|---|---|
| C1 | commit size | source lines changed (added + deleted): quartiles 4 / 12 / 38, p90 110, p99 997; 1 file (p90 4); 1 function (p90 6); 39 % single-function | draw commit sizes from this law | quartiles within 25 % |
| C2 | dilution | a commit changes a median 0.149 % of the project's code lines (p90 1.76 %), a bug fix 0.092 % | a debt change must be small against its host: the old benchmark was 1.8 % (about 12-20 times too large) | median 0.05-0.3 % |
| C3 | who creates and removes debt | 6.5 % of the commits create debt, 3.7 % remove it; created in big commits (median 122 lines), removed in big commits (141); net +1,132 per 20,960 commits (13.0 against 7.6 per 100) | most debt arises inside feature commits, not in dedicated 'debt commits' | create/remove ratio 1.2-2.5; median size of creating commits 60-250 |
| C4 | bug fixes | 19 % of commits; median 8 lines against 13; OR 1.35 for a commit that touches a debt function; OR 0.76 for one that creates debt | | share 12-25 % |
| C5 | self-admitted debt | 1.7 % of the commits add a TODO/FIXME-like comment; 21 % of those create debt (6 % otherwise) | optional feature | |
| C6 | type mix | by commit keyword: coupling 0.35, dependency 0.23, complexity 0.18, concurrency 0.14, security 0.09; security is the type of fixes (6.8 % of fix subjects against 0.9 %) | no single project and no single type above 35 % of the pairs (the earlier dataset: concurrency 43 %, one project 39 %) | max type share <= 0.35; max project share <= 0.15 |
| C7 | type sizes | median source lines: security 11, dependency 12, concurrency 17, coupling 18, complexity 27 (0.07 %, 0.14 %, 0.20 %, 0.19 %, 0.34 % of the project) | draw the size of a change of each type from these | per type median within 30 % |
| C8 | mixed commits | only 1-2 % of the commits carry two type keywords | keep pure commits the rule; add 5-10 % mixed ones as a hard test set | |
| C9 | natural pairs | 419 small focused debt-introducing commits, 143 clean refactoring pairs (30 repositories), 244 small security fixes, 121 small concurrency fixes (`results/a4_natural_pair_candidates.csv`) | take these first, label by detector and commit message, check 100 by hand; inject only for the types with too few natural pairs | label agreement of the hand check >= 0.8 |

## D. How the two products are evaluated (unchanged principles)

* Hold out whole projects AND whole templates / origins; report accuracy per template, per project and per origin (natural against injected).
* For every ranking: random, size only, persistence **with the same tie-break**, size + history; paired bootstrap over groups; the number of looks.
* A fixed acceptance panel of the properties above (H1-H13, C1-C9) is computed on the real corpus and on every new version of the generated data; a version that fails more than 2 tests is not used.

## E. What the earlier synthetic benchmark got wrong (and the property that fixes it)

| earlier benchmark | real | property |
|---|---|---|
| no size effect (AUC of size 0.46, Spearman -0.03) | AUC 0.62, Spearman 0.31 | H3 |
| avoidance of debt (enrichment 0.29) | no avoidance at equal size (OR 1.07) | H4 |
| debt change 44 times larger than the real one (1.8 % of the project) | 0.09-0.15 % | C2 |
| release clock from an AR process | from the release type and its size; no autocorrelation | H9, H10 |
| hot tail 12.5 % of instances | 4.8 % (9 original repositories; not re-measured on 33) | H6 |
| concurrency / security / dependency templates all separable (0.94-0.96 accuracy) | real accuracy 0.79-0.89 random split | C7 + natural pairs (C9) |
