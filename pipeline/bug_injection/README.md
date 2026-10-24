# bug_injection

`mutate.py` - candidate bugs; `inject_bugs.py` - picks 3 per pair (same bugs on the clean and the TD project) and writes `project_with_bugs_dataset`; `sample_times.py` - the ground-truth fix-time model.
Details and rules: `../README.md` and `../../project_with_bugs_dataset/README.md`. The time generator is documented at the top of `sample_times.py`; its slow-down factors are assumptions.
