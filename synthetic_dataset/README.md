# synthetic_dataset - 150 small projects with git histories, debt of known type and known interest

A benchmark built to test the ideas of `../insights/INSIGHTS.md` (and the models of `../interest_exp`) on data where the truth is known: **150 Python projects from 150 different domains, each with a real git history, 7 to 12 injected technical-debt instances (5-10 of one major type, one each of two other types), and the interest of every instance in every release computed from git.**

It is **synthetic**: the code is assembled from archetypes and templates by `generator/`, and the histories are simulated (see section 6). Use it to develop and compare methods under controlled conditions; the real histories of `interest_exp/` remain the evidence about how developers behave.

```
synthetic_dataset/
  README.md              this file
  VALIDATION.md          the checks against the specification (result: PASS)
  insight_check.md/.csv  which patterns of the real data appear in the synthetic histories, per regime
  projects.csv           one row per project (150)
  instances.csv          one row per debt instance (1,321)
  pairs.csv              one row per debt introduction: parent commit, child commit (1,321 pairs)
  manifests/<id>.json    ground truth of a project: modules, commits, releases, instances (type, template, region, introduction, repayment, latent rate)
  transitions/<id>.csv   interest per instance and release pair, from git (same columns as interest_exp/data/transitions)
  releases/<id>.csv      per release pair: total added lines, total lines, debt-region lines and changes (for the enrichment)
  drift_check.txt        the debt change against the natural drift of the features
  features/              133 features of the pairs (parent, child, delta) and of every release (time series)
  repos/<id>.git         the 150 bare git repositories (tags v0.1 ... v0.N); not committed, rebuilt by generator/build.py
  generator/             the code that builds all of it (generator/README.md)
```

## 1. What you asked for, and what is there

| requirement | in the dataset |
|---|---|
| around 150 projects | **150** |
| each with 5-10 instances of a major debt type and 1 instance each of two other types | every project: major type 5-10 instances (small 5-6, medium 5-8, large 7-10, xlarge 8-10) + exactly 2 other types with 1 instance each (checked by `VALIDATION.md` 1: 0 violations). 1,321 instances: complexity 272, security 270, coupling_cohesion 265, concurrency 265, dependency_structure 249 |
| around 6-7 files, some more, some less, some very large | small: 5 python files (246-550 lines); medium: 8 (474-1,152); large: 15 (974-2,407); xlarge: 29-34 files (2,083-3,702 lines) |
| domains from tasks on the internet, in different domains of work | 150 distinct domains: **88 are the ideas of the public list github.com/florinpop17/app-ideas** (35 beginner -> small, 33 intermediate -> medium, 20 advanced -> large); 62 are classic programming tasks added by me (library, bank ledger, parking lot, CI pipeline, ...). The domain gives entities and fields; the algorithms of the code do not differ between domains (section 6) |
| a proper history: 20-30 releases for large, at least 5-6 for small | small 5-6 releases (10-47 commits), medium 10-15 (44-160), large 21-30 (128-539), xlarge 25-30 (298-782); one real commit per group of edits, dated, 4 authors, a tag per release |
| keep in mind the insights; make sure they are present | section 3 and `insight_check.md` |

## 2. One project, in short
A layered package (`utils < models < validators < rules < storage < reports < services < cli`, with per-entity service modules and feature modules in the larger tiers), 11 clean function archetypes per entity, plus debt instances from 23 templates (complexity: ladder, nested, many parameters, long function; concurrency: unlocked counter, check-then-act, lock-order inversion, lock not released, shared list; security: SQL injection, shell=True, eval, md5 + hard-coded secret, insecure random, path traversal, pickle; coupling/cohesion: feature envy, god class, message chain, private access; dependency structure: import cycle, wildcard import, layer violation). Each instance has a clean variant that replaces it when the debt is repaid. 40 % of the instances are introduced in release 1 (after the scaffold commit), the others later; about two thirds of the introductions (64 %) are *mixed* commits that also edit unrelated code. Details: `generator/README.md`.

## 3. The insights, and where to find them in the data
`insight_check.md` measures them on the git ground truth. Numbers for the 90 baseline projects (real data of the 9 projects in brackets):

| insight of the real data | what the synthetic data does | baseline | real |
|---|---|---|---|
| A. the clean twin cancels the host | every debt introduction has a parent commit (the twin); features of both are in `features/pairs_delta.csv` | 1,321 pairs | 61 pairs |
| B. a debt change is tiny against natural drift | **not reproduced**: the median introduction adds 14 lines (0 deleted), 1.8 % of the project (90th percentile 6.2 %), because the projects are small; 64 % are mixed commits. Against the natural drift between releases (`generator/drift_check.py`): a pair changes 34 of 133 features and **13 exceed the drift** (median ratio 0.72), in the real pairs 1 did (ratio 0.01) | 13 features above drift | 1 |
| C. project and type are not collinear | each type is the major type of exactly 30 projects, in every tier and regime mix (VALIDATION.md 5) | 30 each | boltons = 24 of 61 |
| D. the generator leaves a fingerprint | 23 templates; `template` and `style` in the manifests, so that held-out-template and held-out-domain splits exist | - | scripted 0.95 / LLM 0.47 |
| E. a file graph sees only structural debt | `granularity` and `region_kind` per instance; only dependency and coupling instances change imports or classes | - | 14 of 61 |
| F. debt is avoided | enrichment (share of edits in debt regions / share of code) | **0.29** | 0.39 |
| G. interest is a persistent, concentrated hot-spot trait | Gini of interest per instance; share never paying; P(event given an event) flat over lags (0.33, 0.34, 0.29) against 0.09 | **0.78**, 56 %, flat | 0.83, 46 %, flat |
| H. persistence is at the ceiling for "where"; the release clock is random | capture in the top 20 %: persistence 0.576, true long-run rate 0.635, random 0.263; autocorrelation of the event rate 0.00 | close, not equal | 0.39 = 0.38; -0.01 |
| H'. the release clock explains more variance than the instance | **not reproduced**: ICC by release 0.12, by instance 0.24 (real: 0.28 and 0.13) | weaker | stronger |

**Not reproduced:** the dilution of the debt change (B: the synthetic debt is about 20 times larger relative to its project, and 13 features rise above the drift instead of 1: a single snapshot is far easier here than in real code), the strength of the release clock (H'), the event rate (12 % against 7.8 %), and the share of the code that is debt (11 % against 32 %: the synthetic debt functions are small). The comparison between persistence and the true long-run rate is close but not equal in the synthetic data (a gap of 6 points), so a better estimator of the hot-spot rate has some room to win here.

## 4. Counter-regimes: the patterns are absent on purpose in 60 projects
| regime | projects | what changes | what `insight_check.md` shows |
|---|---|---|---|
| baseline | 90 | the patterns of section 3 | - |
| `sticky` | 15 | debt attracts work, few instances frozen | enrichment 0.75 (baseline 0.29), never pay 16 % |
| `ar_clock` | 15 | the release clock is autocorrelated | autocorrelation of the clock 0.44 (baseline -0.17), of the event rate 0.21 (0.00) |
| `decay` | 15 | an edit makes the next ones likelier for a while (self-exciting) | P(event given the last event 5+ releases ago) 0.01 (baseline 0.20) |
| `contagion` | 15 | an edit of an instance raises the rates of the other instances of the same file | neighbour ratio 1.8 (baseline 0.8) |

A method that works only on the baseline is exposed by these. The regime is in `projects.csv` and the manifests.

## 5. Files and columns
- **`projects.csv`**: project, title, domain, domain_source (A public list / C classic), tier (S M L X), regime, seed, python_files, loc, releases, commits, major_type, n_major, minor_types, instances, repaid, frozen_instances, interest_events, interest_pm.
- **`instances.csv`**: project, instance, ptype (complexity, concurrency, coupling_cohesion, dependency_structure, security), major (1/0), template, granularity (function / class / module), region_kind (function / class / import), file, entity, intro_release, intro_commit, parent_commit, mixed, repaid_release, latent_rate, frozen, regime, tier.
- **`pairs.csv`**: the pair of commits of every introduction (parent = clean twin; child), with files_changed, lines_added, lines_deleted, mixed.
- **`transitions/<id>.csv`**: columns of `interest_exp/data/transitions` (`repo, v0, v1, vi, key, file, func, rule, severity, sonar_effort_min, nloc0, ccn0, age, past_il, past_n, principal_pm, cls, persisted, nloc1, changed, interest_lines, pm_interest`): one row per instance that is alive at `v0`; interest lines = lines of the instance's region added or modified by git between the two tags, beyond the growth of the region; `pm_interest` = COCOMO II (A = 2.94, E = 1.0997). The existing interest code runs on these files unchanged (the SonarQube columns are constants).
- **`manifests/<id>.json`**: the generator's truth: `instances[*]` (`latent_rate`, `frozen`, `sim_edits` are labels for evaluation and must not be used as features), `commits`, `release_table` (tag, commit, `activity` = release clock), `regime`, `style`, and the `smoke` script that calls every function.
- **`features/pairs_delta.csv`**, **`features/releases/<id>.csv`**: the 133 features of `pipeline/extract.py` (see `../out_dataset/FEATURES.md`) for the parent and child commits and for every release tag.

## 6. What this dataset can and cannot do
**Can:** train and compare rankers of debt instances with a known ceiling; test whether a method depends on the patterns of section 3 (regimes); run the Level 1 experiments (type of a debt change, with held-out templates, domains and tiers) on 1,321 pairs instead of 61; study natural drift against injected change; test models for how they scale with project size.
**Cannot:** say how developers really behave. The edit process, the release clock and the latent rates are my assumptions, tuned to resemble the real histories of nine projects (section 3 lists where they do not). Also:
- The code is valid and runs (smoke test) but is assembled from 11 archetypes and 23 templates: domains differ in names and entities, not in algorithms. A model can learn the generator (insight D); evaluate with held-out templates.
- Interest edits are small literal changes inside a function; real rework is richer.
- Debt instances are the injected ones, not detector output; the structural-smell definition of `interest_exp` is not applied.
- No fix-time label and no bugs (the time model of Level 1 is not part of this dataset).
- The motivation of the project, AI-generated code, is not represented: the code is generated by a program, not by an LLM.

## 7. What has been verified, and what has not
Verified (`VALIDATION.md`, `detection_audit.txt`):
- 150 projects, tiers, file counts, release counts, instance counts (major 5-10 plus two minors of one each): 0 violations.
- **Every release of every project (2,038 tags) compiles and runs** (the smoke test calls every function that exists in that release; former debt functions are allowed to reject the unsafe sample input).
- A rebuild of one project from its seed gives the same HEAD hash (only one project was rebuilt, not all).
- Interest from git agrees with the simulator's edit log on 99.6 % of 11,927 instance-releases.
- The interest code of `interest_exp` loads these transitions (`model_next_release.load`, `model_pm.load`: 11,927 rows, all feature columns present). The models themselves were **not** run on them.
- Detection audit (are the injected debts visible to an objective tool?): complexity 272 of 272 flagged by lizard (CCN > 10, NLOC > 50 or > 5 parameters); security 229 of 270 flagged by bandit; the 41 `path_traversal` instances are **not** flagged (bandit does not flag `open(os.path.join(base, name))`). Concurrency (265), coupling_cohesion (265) and dependency_structure (249) instances were **not** checked with any detector.

Not done: no model was trained or evaluated on this dataset (no baseline results); the scripts of `insights/` were not run on it; the instance counts are counts of *introduced* instances (360 of the 1,321 are repaid later, so the number alive at the last release is lower); the growth edits insert lines such as `_trace_123 = 4`, which no developer would write.

## 8. Reproduce
```
cd synthetic_dataset/generator
PY=/path/to/python-with-numpy-pandas-lizard ./make_all.sh ..     # about 10 minutes on 4 cores: repos, manifests, transitions, pairs, VALIDATION.md, insight_check.md
$PY extract_features.py .. pairs && $PY extract_features.py .. releases     # the 133 features (needs the packages of pipeline/requirements.txt)
```
The build is deterministic (global seed 2026; `VALIDATION.md` 3 rebuilds one project and compares the HEAD hash). Repositories are bare; clone one with `git clone repos/<id>.git` or inspect it with `git -C repos/<id>.git log --stat`.
