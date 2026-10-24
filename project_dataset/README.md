# project_dataset - the pairs of projects and everything known about their projects

61 **pairs**. A pair = a real open-source project at one commit (`P#_clean`, no intentionally induced debt) and the same project with ONE technical-debt change applied (`P#_TD`).
The two folders are complete copies of the project files (no `.git`, no tests folder), so they can be read and analysed directly (building a C/C++ project may need its tests folder back, because some CMake files refer to it).

```
project_dataset/
  Python/P1..P41/      C_C++/P1..P20/                 (folder name C_C++ because "/" cannot be used in a name)
      P#_clean/        the project, unchanged
      P#_TD/           the same project with the technical-debt change
      P#_prop/         properties.txt  (what was induced, where, how it was validated)   td.patch  (clean -> TD)
  properties_all_pairs.csv     one row per pair with all the properties of properties.txt (TD type, subtype, CWE, description, files, lines, validation results) + the SonarQube summary of the pair (sonar_* columns)
  INDEX.md                     table of all pairs
  project_details/<project>/   the 10 projects: git history, SonarQube, properties  (see project_details/README.md)
  sonarqube_server/            everything the SonarQube server (localhost:9000/projects) holds: 52 projects, measures, 10727 issues, rules  (see its README.md)
```

## The technical-debt types (the 5 classes)
| type | pairs | what the change does (examples) |
|---|---|---|
| concurrency | 26 | a lock/unlock removed, a wait loop turned into an `if` |
| security | 16 | a bounds / NULL check removed, `snprintf` made unbounded, a weak hash or salt |
| dependency_structure | 7 | a cyclic include, unused abstraction, data clumps, dead code |
| coupling_cohesion | 6 | feature envy, god class, shotgun surgery |
| complexity | 6 | long method inlined, nested flag logic |

By language: Python 41 (concurrency 24, coupling_cohesion 6, complexity 5, dependency_structure 4, security 2), C/C++ 20 (security 14, dependency_structure 3, concurrency 2, complexity 1).

## Where the changes come from
* 15 Python pairs (click, jinja): LLM-written refactorings of the SmellBench dataset (https://huggingface.co/datasets/critical88/SmellBench), re-built as whole projects.
* 45 pairs (boltons, werkzeug, jansson, zlib, cJSON, C-Thread-Pool, libyaml): small scripted or hand-written injections (one controlled change each).
* 1 pair (libpng, C/C++ P20): a real vulnerability-fix commit; `P#_clean` is the fixed code, `P#_TD` the code before the fix (natural, nothing injected).
Every pair differs only in the files of `td.patch`, and every pair kept its project's own test suite passing on the TD side when it was validated (the numbers are in `properties.txt`; the tests folders were removed afterwards).

## The 10 projects
| project | language | pairs | TD types of its pairs | commits | years | bugs mined (SZZ) | SonarQube |
|---|---|---|---|---|---|---|---|
| C-Thread-Pool | C/C++ | 4 | concurrency 2, security 2 | 224 | 2011-2025 |  | no C/C++ analyzer |
| boltons | Python | 24 | concurrency 24 | 1549 | 2013-2026 | 158 | per-release issues (20 releases) |
| cJSON | C/C++ | 1 | dependency_structure 1 | 955 | 2009-2026 | 103 | no C/C++ analyzer |
| click | Python | 10 | dependency_structure 4, coupling_cohesion 3, complexity 3 | 2172 | 2014-2026 | 187 | per-release issues (20 releases) |
| jansson | C/C++ | 6 | security 4, dependency_structure 1, complexity 1 | 874 | 2009-2026 | 45 | no C/C++ analyzer |
| jinja | Python | 5 | coupling_cohesion 3, complexity 2 | 2175 | 2007-2025 | 280 | per-release issues (20 releases) |
| libpng | C/C++ | 1 | security 1 | 4645 | 2009-2026 | 225 | no C/C++ analyzer |
| libyaml | C/C++ | 5 | security 5 | 227 | 2006-2026 | 26 | no C/C++ analyzer |
| werkzeug | Python | 2 | security 2 | 4494 | 2007-2026 | 568 | per-release issues (20 releases) |
| zlib | C/C++ | 3 | security 2, dependency_structure 1 | 1126 | 2011-2026 | 56 | no C/C++ analyzer |

Details of each project (pairs, git history, SonarQube): `project_details/<project>/README.md`.

## Limits
* The debt of 60 of the 61 pairs is injected (synthetic), small and local; only P20 (libpng) is natural.
* Many pairs share one project and one base commit (24 boltons pairs, 10 click pairs): split by project when modelling.
* The properties that say "tests_on_clean / tests_on_TD" were measured before the tests folders were removed.
