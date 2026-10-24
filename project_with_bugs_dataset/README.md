# project_with_bugs_dataset - the same pairs, with bugs

Every pair of `../project_dataset` appears again here with **3 injected bugs, the same 3 bugs in the project without and in the project with the technical debt**.
The bugs are the reason a "time to fix" exists: fixing the same bug costs a different amount of time in the clean project and in the TD project.

```
project_with_bugs_dataset/
  Python/P1..P41/    C_C++/P1..P20/
      P#_clean_bug/   P#_clean with the 3 bugs applied
      P#_TD_bug/      P#_TD with the same 3 bugs applied
      P#_bugs/        bug1.patch bug2.patch bug3.patch   the bugs as patches (apply to P#_clean and to P#_TD alike)
                      bugs.json                          for each bug: file, line, function, kind, description, in_td_file
```
183 bugs in total. Kinds: negate_cond 58, const_off_by_one 35, arith 27, cmp_equality 23, bool_op 23, cmp_boundary 17. In 70 of the 183 bugs the file is one that the technical-debt change also touches (so the debt and the bug are close together); the others are elsewhere in the project.

## What a bug is
One small semantic change in one function, produced by `../pipeline/bug_injection/mutate.py`:
| kind | change |
|---|---|
| `cmp_boundary` | `<` <-> `<=`, `>` <-> `>=` (off by one at a boundary) |
| `cmp_equality` | `==` <-> `!=` |
| `bool_op` | `and` <-> `or`, `&&` <-> `||` |
| `arith` | `+` <-> `-` (Python expressions), `+ 1` <-> `- 1` (C) |
| `negate_cond` | `if (c)` becomes `if (not c)` / `if (!(c))` |
| `const_off_by_one` | an integer constant in a comparison, index or `range()` gets +1 |

## Rules the injection follows (`../pipeline/bug_injection/inject_bugs.py`)
* 3 bugs per pair, in different functions, different kinds where possible, the first one in a file that the TD change touches when there is one;
* a bug never overlaps the lines the TD change modified, and its patch applies to **both** the clean and the TD project;
* the choice is seeded by the pair id, so running the injection again gives the same bugs (checked).

## Checks done
* in all 61 pairs the bugged folders differ from the original folders exactly in the bug files, and `P#_clean_bug` and `P#_TD_bug` differ exactly in the files of `td.patch`;
* all 246 bugged Python files parse; the 59 bugged C files pass a syntax compile with no new error.
* **Not done:** the bugs were not validated with the projects' test suites (the dataset has no tests folders). A bug is valid code but a test is not guaranteed to notice it.
