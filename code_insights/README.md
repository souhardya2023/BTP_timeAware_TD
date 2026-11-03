# code_insights - what in the code text goes with interest

Reads the source of the debt functions (33 repositories, every 3rd release pair) and tests which visible traits go with more interest at equal size.

| file | what |
|---|---|
| `code/c1_extract.py` | function text from git (lizard line ranges) -> trait features (repeated lines, look-alike runs, clones, nesting, calls, pointer / NULL / goto / unsafe / malloc counts, Python try / isinstance / self attributes) -> `results/c1_features.csv`, `c1_texts.jsonl` |
| `code/c2_traits.py` | trait high (top quarter within repository and size bin) vs the rest: size-matched rate ratio, per language, repository-cluster bootstrap -> `results/c2_traits.csv` |
| `code/c3_examples.py` | code examples by a fixed rule (same repo and release, same size, one paid interest, one did not) with changed lines marked -> `examples/` |
| `code/c4_rates.py` | share with interest vs size-matched expectation -> `results/c4_rates.json` |

Findings (C/C++ only; Python, 5,359 rows, shows nothing clear): many different callees 1.47 (1.31-1.61); pointer field accesses 1.34; repeated lines 0.74 (lower); goto / unsafe calls / malloc-free / nesting / clones 0.96-1.04 (noise).
Bug fixed on the way: .py scripts inside C repositories were counted as Python; all scripts now keep only files in the repository's own language.

## Clones, tested properly (k1-k3)
| file | what |
|---|---|
| `code/k1_clones.py` | whole-repository near-clone detection (token shingles, identifiers/numbers/strings normalised, generic boilerplate dropped, Jaccard >= 0.6), every 4th release pair -> `results/k1_funcs.csv`, `k1_pairs.csv` |
| `code/k2_clone_tests.py` | Test A: is a function with a clone partner edited more? Test B: is the partner edited in the same release (co-change) vs same-size non-clone controls? -> `results/k2_tests.csv` |
| `code/k3_example.py` | the jinja parse_math1 / parse_math2 example -> `examples/ex4_clone_cochange.*` |

Result: a clone alone is NOT edited more (C/C++ 0.82, Python 1.17 unclear), but its partner is edited in the same release 81% (C/C++) and 96% (Python) of the time vs 47% / 49% for same-size non-clone controls (rate ratio 1.74 and 1.98, every repository agrees). The earlier 'no effect' came from a crude clone measure (4-line shingles, only files with debt).
