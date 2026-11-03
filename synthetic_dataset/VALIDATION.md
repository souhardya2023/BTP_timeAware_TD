# Validation of the synthetic dataset

## 1. Structure against the specification
projects: 150 (domains 150 unique)
  S: 50 projects, releases 5-6, commits 10-47 (median 31), LOC 246-550 (median 386), instances 7-8
  M: 60 projects, releases 10-15, commits 44-160 (median 98), LOC 474-1152 (median 779), instances 7-10
  L: 32 projects, releases 21-30, commits 128-539 (median 336), LOC 974-2407 (median 1877), instances 9-12
  X: 8 projects, releases 25-30, commits 298-782 (median 561), LOC 2083-3702 (median 3104), instances 10-12
specification violations: 0 []

## 2. Every release compiles; smoke test (calls every function) at every release
projects with problems: 0 []
  python files at the last release, tier S: 5-5 (median 5)
  python files at the last release, tier M: 8-8 (median 8)
  python files at the last release, tier L: 15-15 (median 15)
  python files at the last release, tier X: 29-34 (median 31)

## 3. Determinism (rebuild of one project from its seed)
project battleship_engine: HEAD c5c495c135 -> identical after rebuild

## 4. Interest from git against the simulator's own edit log
instance-releases compared: 11927, event / no event agreement: 99.58 %

## 5. Balance
major type: {'dependency_structure': 30, 'security': 30, 'concurrency': 30, 'coupling_cohesion': 30, 'complexity': 30}
regime: {'baseline': 90, 'sticky': 15, 'contagion': 15, 'ar_clock': 15, 'decay': 15}
source of the domain (A = public app-ideas list, C = classic task): {'A': 88, 'C': 62}
major type by tier:
  S: {'dependency_structure': 14, 'security': 10, 'complexity': 9, 'concurrency': 11, 'coupling_cohesion': 6}
  M: {'dependency_structure': 11, 'coupling_cohesion': 15, 'concurrency': 11, 'security': 12, 'complexity': 11}
  L: {'security': 7, 'concurrency': 8, 'complexity': 8, 'coupling_cohesion': 5, 'dependency_structure': 4}
  X: {'coupling_cohesion': 4, 'complexity': 2, 'security': 1, 'dependency_structure': 1}
major type by regime:
  baseline: {'dependency_structure': 17, 'security': 21, 'concurrency': 17, 'coupling_cohesion': 18, 'complexity': 17}
  sticky: {'security': 3, 'dependency_structure': 1, 'complexity': 2, 'concurrency': 2, 'coupling_cohesion': 7}
  ar_clock: {'concurrency': 6, 'complexity': 1, 'coupling_cohesion': 2, 'dependency_structure': 6}
  decay: {'concurrency': 3, 'complexity': 7, 'security': 3, 'dependency_structure': 1, 'coupling_cohesion': 1}
  contagion: {'security': 3, 'dependency_structure': 5, 'complexity': 3, 'coupling_cohesion': 2, 'concurrency': 2}
templates (all instances): {'layer_violation': 136, 'god_class': 76, 'feature_envy': 73, 'ladder': 71, 'unlocked_counter': 71, 'params': 68, 'nested': 67, 'long': 66, 'message_chain': 60, 'import_cycle': 57, 'private_access': 56, 'wildcard_import': 56, 'shared_list': 54, 'lock_not_released': 53, 'weak_hash_secret': 47, 'check_then_act': 47, 'unsafe_deserialize': 43, 'path_traversal': 41, 'eval_input': 40, 'shell_injection': 40, 'lock_order': 40, 'insecure_random': 36, 'sql_injection': 23}

RESULT: PASS