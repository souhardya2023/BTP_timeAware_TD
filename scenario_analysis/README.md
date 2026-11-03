# scenario_analysis - which patterns repeat, and which are noise

Scenario = a pattern (a group of debt instances, functions or commits defined by a condition). Tested for repetition across Python (16 repos), C/C++ (17 repos) and the synthetic benchmark.

| file | what |
|---|---|
| `code/s1_scenarios.py` | 23 named scenarios; size-adjusted rate ratio per repo, pooled per language with repository-cluster bootstrap; verdict REPEATS / LANGUAGE-SPECIFIC / NOISE -> `results/s1_scenarios.csv` |
| `code/s2_rules.py` | reverse engineering: decision-tree rules discovered on some repositories, validated on others (python->c, c->python, 20 random halves, real->synthetic) -> `results/s2_*.csv/txt` |
| `code/s3_figures.py` | the two plots in `figures/` |

Results: 7 repeat (6 strong), 9 language-specific, 7 noise. Memory is strong in C/C++ (rate ratio 2.5, odds ratio 4.6) and not significant in Python (1.15; 1.4).
Caveat: the shuffled-label control in s2 replicates 80% of rules, so replication alone does not separate signal from noise there.
Not done: GPT models (no GPT-written code in the project). The earlier pooled memory claim (odds ratio 4.6, "same in both languages") was carried by C/C++.
