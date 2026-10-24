# Dataset index

P<n> = one pair. Inside each: P<n>_clean (original project), P<n>_TD (same project + one technical-debt change), P<n>_prop (properties.txt + td.patch).

## Python  (`Python/`, 41 pairs)

| pair | TD type | subtype | project | files changed | tier | validation |
|---|---|---|---|---|---|---|
| P1 | security | predictable_salt | werkzeug | 1 | main | validated_full_test_suite |
| P2 | security | weak_hash | werkzeug | 1 | main | validated_full_test_suite |
| P3 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P4 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P5 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P6 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P7 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P8 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P9 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P10 | concurrency | lock_removed | boltons | 1 | main | validated_full_test_suite |
| P11 | coupling_cohesion | shotgun_surgery | click | 3 | main | validated_full_test_suite |
| P12 | coupling_cohesion | shotgun_surgery | click | 5 | main | validated_full_test_suite |
| P13 | coupling_cohesion | shotgun_surgery | click | 9 | main | validated_full_test_suite |
| P14 | coupling_cohesion | feature_envy | jinja | 1 | main | validated_full_test_suite |
| P15 | coupling_cohesion | feature_envy | jinja | 2 | main | validated_full_test_suite |
| P16 | coupling_cohesion | shotgun_surgery | jinja | 4 | main | validated_full_test_suite |
| P17 | dependency_structure | data_clumps | click | 5 | main | validated_full_test_suite |
| P18 | dependency_structure | dead_code_elimination | click | 5 | main | validated_full_test_suite |
| P19 | dependency_structure | dead_code_elimination | click | 3 | main | validated_full_test_suite |
| P20 | dependency_structure | interface_segregation | click | 5 | main | validated_full_test_suite |
| P21 | complexity | deeply_inlined_method | click | 2 | main | validated_full_test_suite |
| P22 | complexity | deeply_inlined_method | click | 5 | main | validated_full_test_suite |
| P23 | complexity | deeply_inlined_method | click | 2 | main | validated_full_test_suite |
| P24 | complexity | deeply_inlined_method | jinja | 2 | main | validated_full_test_suite |
| P25 | complexity | deeply_inlined_method | jinja | 4 | main | validated_full_test_suite |
| P26 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P27 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P28 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P29 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P30 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P31 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P32 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P33 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P34 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P35 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P36 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P37 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P38 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P39 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P40 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |
| P41 | concurrency | lock_removed | boltons | 1 | extra | validated_full_test_suite |

## C/C++  (`C_C++/`, 20 pairs)

| pair | TD type | subtype | project | files changed | tier | validation |
|---|---|---|---|---|---|---|
| P1 | security | bounded_to_unbounded_copy | jansson | 1 | main | validated_build_and_ctest_at_generation |
| P2 | security | bounded_to_unbounded_copy | jansson | 1 | main | validated_build_and_ctest_at_generation |
| P3 | security | bounded_to_unbounded_copy | jansson | 1 | main | validated_build_and_ctest_at_generation |
| P4 | security | bounded_to_unbounded_copy | jansson | 1 | main | validated_build_and_ctest_at_generation |
| P5 | security | bounded_to_unbounded_copy | zlib | 1 | main | validated_build_and_ctest_at_generation |
| P6 | security | bounded_to_unbounded_copy | zlib | 1 | main | validated_build_and_ctest_at_generation |
| P7 | dependency_structure | cyclic_header_dependency | cJSON | 1 | main | validated_build_and_ctest_at_generation |
| P8 | dependency_structure | cyclic_header_dependency | jansson | 1 | main | validated_build_and_ctest_at_generation |
| P9 | dependency_structure | cyclic_header_dependency | zlib | 1 | main | validated_build_and_ctest_at_generation |
| P10 | complexity | nested_flag_logic | jansson | 1 | main | validated_build_and_ctest_at_generation |
| P11 | concurrency | lock_pair_removed | C-Thread-Pool | 1 | main | validated_build_and_tests_at_generation |
| P12 | concurrency | lock_pair_removed | C-Thread-Pool | 1 | main | validated_build_and_tests_at_generation |
| P13 | security | null_check_removed | C-Thread-Pool | 1 | main | validated_build_and_tests_at_generation |
| P14 | security | null_check_removed | C-Thread-Pool | 1 | main | validated_build_and_tests_at_generation |
| P15 | security | bounds_check_removed | libyaml | 1 | main | validated_build_and_tests_at_generation |
| P16 | security | null_check_removed | libyaml | 1 | main | validated_build_and_tests_at_generation |
| P17 | security | bounds_check_removed | libyaml | 1 | main | validated_build_and_tests_at_generation |
| P18 | security | null_check_removed | libyaml | 1 | main | validated_build_and_tests_at_generation |
| P19 | security | bounds_check_removed | libyaml | 1 | main | validated_build_and_tests_at_generation |
| P20 | security | temporal_memory | libpng | 2 | main | natural_pair_both_sides_build_and_ctest |
