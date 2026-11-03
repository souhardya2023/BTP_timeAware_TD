# generator - how the synthetic projects are made

```
domains.py          150 project domains (88 from the public app-ideas list, 62 classic tasks) with their entities and fields
blocks.py           code model (Fn, Cls, Module, ImportLine), the 11 clean function archetypes, the editing operations
debt.py             the debt templates of four types (complexity, concurrency, security, coupling_cohesion) and their clean variants
simulate.py         the project builder, the debt schedule, the release clock, the edit process, the git history, the manifest; + the dependency templates
build.py            builds all (or some) projects in parallel:  python build.py --out <dir> [--n 8 | --only slug,slug] [--workers 4]
ground_truth.py     interest per release pair from the git history and the manifest, in the format of interest_exp/data/transitions
validate.py         checks the whole dataset against the specification (VALIDATION.md)
insight_check.py    measures the patterns of insights/INSIGHTS.md on the generated histories, per regime (insight_check.md)
extract_features.py the 133 features of the pairs (parent/child of every debt introduction) and of every release
check_project.py    compile + smoke test of one project
```

## 1. One project
1. **Domain and tier.** The domain gives the entities (2 to 4 text / numeric / flag fields each). The tier sets the size: small (5 python files, 5-6 releases), medium (8 files, 10-15 releases), large (15 files, 20-30 releases), xlarge (about 30 files, 25-30 releases). Tiers of the public list (beginner, intermediate, advanced) map to small, medium, large; the 62 classic tasks fill the four tiers.
2. **Layered package.** `utils < config < models < validators < rules / storage < reports < events < svc_* < feat_* < services < cli` (small projects: `models < core < services < cli`). Clean code imports only from lower layers.
3. **Clean code.** 11 function archetypes (validator, aggregator, ranker, tiered score, formatter, parser, in-memory store, job queue, cache lookup, search, notifier) instantiated for every entity, plus a workflow per entity that calls the lower layers. Each project has its own writing habits (verb choices, docstrings, record variable name). Growth during the history adds more functions.
4. **Debt instances.** One *major* type with 5 to 10 instances (5-6 small, 5-8 medium, 7-10 large, 8-10 xlarge) and **one instance each of two other types**, in 23 templates:

| type | templates | granularity |
|---|---|---|
| complexity | ladder of 11-16 branches, nested conditionals, 7-9 parameters, 60+ line function | function |
| concurrency | unlocked counter, check-then-act cache, lock-order inversion, lock not released, shared list | function(s) + module state |
| security | SQL by string formatting, shell=True, eval of input, md5 + hard-coded secret, random token, path traversal, pickle | function |
| coupling_cohesion | feature envy, god class (9 unrelated methods), message chain, private-state access | function / class |
| dependency_structure | import cycle (back edge), wildcard import, lower layer importing a higher one | import line / function |

   Each template has a clean variant: when the debt is repaid the function is replaced by it (class and import regions are removed).
5. **Schedule.** 40 % of the instances are introduced in release 1 (after the scaffold commit), the others at random releases up to 60 % of the history, so that each lives for at least 2 releases. A debt introduction is a commit; in about two thirds of the cases (64 %) it is a *mixed* commit that also edits unrelated functions.
6. **Editing.** Every function and every instance has a latent edit rate; every release has an activity level (the *release clock*). In a release a unit is edited Poisson(rate x activity) times. An edit either *modifies* a literal inside the function (rework inside the region: this is what the interest method counts as interest) or *adds a statement* (growth of the region = principal increase). Debt instances are repaid at random (more likely when they are hot).
7. **Git.** One real commit per group of 1-3 events, with dates (a release every 30 days), 4 authors with module ownership, messages that do not reveal the debt type, a tag per release (`v0.1` ... `v0.N`). Repositories are bare and packed.

## 2. Where the insights of the real data are built in
The patterns of `insights/INSIGHTS.md` are made **properties of the generator**, so that methods can be developed and tested against known truth. They are not discoveries about developers: the real-data results remain the evidence, and `insight_check.md` reports how close the synthetic histories are.

| insight (real data) | in the generator | how to see it |
|---|---|---|
| A. the clean twin cancels the host; the delta of an edit is host-independent | a debt introduction is a commit; its parent is the clean twin; the debt text does not depend on the host code | `pairs.csv` (parent, child); features in `features/pairs_delta.csv` |
| B. one change is tiny next to natural drift | the median introduction adds 14 lines (1.8 % of a project that has 250-3,700 lines); 64 % are mixed commits with unrelated edits; this is far less diluted than in the real pairs (0.086 %), see README of the dataset | `pairs.csv` (lines_added, mixed), `features/releases/` for the drift |
| C. project and type are not collinear | each type is the major type of 30 projects; the domain is independent of the type; 5-10 instances of the major type per project instead of 24 pairs in one project | VALIDATION.md section 5 |
| D. the generator leaves a fingerprint | 23 templates in 5 types, 3 to 7 per type, and a different style per project; template and style are in the manifest so that *held-out-template* splits are possible | `pairs.csv` (template); manifest `style` |
| E. a file graph sees only structural debt | dependency and coupling instances change the import graph or classes; concurrency, security, complexity live inside functions | `granularity`, `region_kind` |
| F. debt is avoided (32 % of the code, 12 % of the edits) | live debt rates are lower than clean rates and 46 % of the instances are frozen | `insight_check.md` (enrichment) |
| G. interest is a persistent, very concentrated hot-spot trait | a latent rate per instance, mixture of frozen (46 %) and gamma-distributed live rates; the lag table is flat | `insight_check.md` (Gini, never pay, P(event given an event)) |
| H. "where" is at its ceiling, "when" is random | a release clock shared by all instances, with big releases; its autocorrelation is zero | `insight_check.md` (ceiling, ICC, clock autocorrelation) |
| I. history features help only at larger budgets | the latent rates are known, so the ceiling of any history-based ranking can be computed exactly | `manifests/*.json` (`latent_rate`, only for evaluation) |

## 3. Regimes: patterns that are absent on purpose
60 % of the projects (90) follow the baseline above. The other 60 are in four *counter-regimes* (15 each), so that a method which only works under the assumed patterns is exposed:

| regime | what changes | what it tests |
|---|---|---|
| `sticky` | debt attracts work (rates 6x higher, few frozen) | the claim that debt is avoided |
| `ar_clock` | the release clock is autocorrelated (AR(1), 0.9 in the log) | whether timing can be predicted from the last release |
| `decay` | self-exciting: an edit raises the next releases' rates and the effect fades (half-life 1 release) | the claim that memory does not fade |
| `contagion` | a debt instance is 8x likelier to be edited after another instance in the same file was | the claim that interest is local to the function |

The regime of every project is in its manifest and in `projects.csv`.

## 4. What is simulated and what is not
- The code is assembled from archetypes and templates. It is valid, imports, and runs (smoke test), but it is not written by developers and has less variety than real code. Domains differ in names and entities, and in which archetypes they use; they do not differ in algorithms.
- The **history is simulated**. The edit process, the release clock and the latent rates are the generator's assumptions. Interest measured from git is real *given* the edits; whether developers behave like this is exactly what the real histories have to say. Use this dataset to develop and test methods (known ground truth, many regimes), not to make claims about developers.
- Interest uses the same definition as `interest_exp` (lines modified inside the region beyond its growth, COCOMO II nominal constants). Instances are the injected debts (known), not detector output.
- The latent rates, regimes and templates are labels for evaluation. A method must not read them.

## 5. Reproduce
`python build.py --out ../` is deterministic (seeds are derived from the domain and the global seed 2026; the validation rebuilds one project and compares the HEAD hash). Then `python ground_truth.py ..` (needs a Python with lizard), `python validate.py ..`, `python insight_check.py ..`. About 3 minutes on 4 cores in total, 40 MB for the 150 packed repositories.
