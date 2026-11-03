# new_presentation - only the NEW insights, organised like `presentation/`

`presentation/` holds the current talk (`TD-presentation.pptx`: the 61 real pairs, the interest method, the results on the time feature and on the ranking). This folder holds **everything that is new relative to that talk**: the insights from the real git histories, the 150-project synthetic benchmark and its analysis, the new experiments (code as an image, git history as a time series, sim-to-real, CodeBERT) and the combined real + synthetic analysis. The results that are already in the talk are left out on purpose (see `INSIGHTS_NEW_ONLY.txt`, the note at the top).

```
new_presentation/
  README.md                  this file
  OUTLINE.md                 a proposed slide order for the new insights: one message and one figure per slide
  INSIGHTS_NEW_ONLY.txt      THE FILE TO READ: every new insight, tagged real / synthetic / both / disagree / combined,
                             with evidence, strength, the supporting figure and the source; the ten things to remember;
                             corrections to the talk; the out-of-the-box insights and the next step for each (Part J)
  figures/                   36 matplotlib pictures, grouped as below
  reports/                   the long-form reports behind the figures (markdown), the synthetic benchmark's README, validation and pattern check,
                             and the full insight file including the results that are in the talk (INSIGHTS_ALL_full.txt)
  data/                      the small result tables (txt / csv) behind the numbers, by origin
  build_new_presentation.py  rebuilds this folder from the analyses (copy, select, renumber the figure paths)
```

## figures/
| folder | content | insights |
|---|---|---|
| `01_new_dataset` | how the 150 synthetic projects were made; code drawn as an image; one real instance as a time series; composition of the benchmark (S1 tiers, S2 types and templates, S3 balance, S4 pairs, S5 patterns against the real value by regime, S6 interest by type) | S1, S2, A11 |
| `02_real_data_insights` | concentration, memory, avoided debt, the ceiling, where against when, generalisation by project and origin, drift, context shift, graph visibility, and size against persistence | A1-A9, R1, R7 |
| `03_synthetic_analysis` | ranking by regime, decomposition of the gain, size real against synthetic, time to recognise a hot spot, the type of a change under the splits, the two protocols | S3-S7 |
| `04_new_experiments` | E1 code-image CNN, E2 sim-to-real, E3 time-series features, E4 patterns real against synthetic, E5 history CNN, E6 size and history, E7 CodeBERT | A8, R2, R4, R6, R9, R10, C4, C6 |
| `05_combined` | C1 panel of 20 metrics on real, synthetic and pooled, C2 pooled training (ranking), C3 graph visibility in both, C4 model dependence of the real classifier and pooling | C1-C3, R7, A9 |

Left out of `figures/` because the talk already shows them: the real data set steps, the interest calculation, the Level 1 accuracy by protocol, the time-feature controls, the ranking capture and curve, the predictability chart. The old figure `real_i6` (hotness against persistence) is left out because it shows a claim that was corrected (see Part F of the insight file, X2).

The graphs of the previous talk, redrawn from freshly re-run models (without the fix-time chart), are in `previous_talk_graphs/` (see its README).

## What is in the insight file (INSIGHTS_NEW_ONLY.txt)
- Part 0: ten things to remember.
- Part A: insights that hold in both data sets. Part B: real data only. Part C: synthetic only (a testbed with known truth; many are properties of the generator). Part D: where real and synthetic disagree. Part E: the combined analysis.
- Part F: claims withdrawn or corrected (including statements of the current talk).
- Part G: which figure supports which insight. Part H: what can and cannot be claimed. Part I: next steps.
- **Part J: the out-of-the-box insights and the next step for each, with a success criterion fixed in advance.**

## Rebuild
`python build_new_presentation.py` after the analyses and the figure scripts have been run (`insights/new/run_new.sh`, `insights/synthetic/run_synthetic.sh`, `presentation/new_figures/*.py`). It only copies and renumbers; it computes nothing.

## Two things to know before using it
1. The synthetic results are tests of methods under known truth, not evidence about developers; the real results are the evidence and rest on 9 repositories and 61 pairs.
2. Statements of the current talk that this material corrects: "the classifier does not generalise to unseen projects" (one project, and model dependent), "interest already paid is the strongest baseline" (size ties it), and the earlier "+8 points" for hotness scores (a tie-break artefact).
