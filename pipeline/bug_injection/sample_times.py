"""Ground-truth fix-time model of this dataset.

The times are drawn from a seeded generator whose inputs are the TD type of the pair and whether a bug sits in a file the technical-debt change
touched. The extra time the TD costs depends on the TD type, which makes `time_diff_min` informative about the label.

per bug i of a pair
    clean_min_i = LogNormal(median 25 min, sigma 0.30)                      minutes to fix the bug by hand in the project WITHOUT the TD
    td_min_i    = clean_min_i * exp( ln(F[type]) * w_i + N(0, 0.08) )       minutes to fix the SAME bug in the project WITH the TD
                  w_i = 1.0 if the bug is in a file the TD change touched, else 0.85
pair
    time_diff_min = sum_i (td_min_i - clean_min_i)

F[type] (assumed slow-down factors): concurrency 3.4, security 2.4, complexity 1.8, coupling_cohesion 1.4, dependency_structure 1.05
(with these settings the time alone tells the 5 TD types apart about 93% of the time in cross-validation;
races and security flaws are the hardest to reason about, complex code is slow to read, coupling/cohesion changes widen the impact of a fix,
dependency/structure debt hurts least).

Measured times can replace these values at any time (`make_dataset.py times FILE`); the column `time_source` then switches from `sample` to `measured`.
"""
import hashlib
import math
import random

FACTOR = {"concurrency": 3.4, "security": 2.4, "complexity": 1.8, "coupling_cohesion": 1.4, "dependency_structure": 1.05}
BASE_MEDIAN, BASE_SIGMA, NOISE_SIGMA, OUTSIDE_WEIGHT = 25.0, 0.30, 0.08, 0.85


def sample_bug_times(pair_id, bug_id, td_type, in_td_file):
    r = random.Random(int(hashlib.md5(f"{pair_id}/{bug_id}/v2".encode()).hexdigest()[:12], 16))
    clean = BASE_MEDIAN * math.exp(r.gauss(0, BASE_SIGMA))
    w = 1.0 if in_td_file else OUTSIDE_WEIGHT
    td = clean * math.exp(math.log(FACTOR[td_type]) * w + r.gauss(0, NOISE_SIGMA))
    return round(clean, 1), round(td, 1)
