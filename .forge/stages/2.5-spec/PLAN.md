# Implementation Plan
<!-- FORGE_STAGE: 2.5-spec -->
<!-- SOURCE: .forge/stages/2-architect/architecture-plan.md -->

## File Touchpoints

| File | Action | Task | AC Coverage |
|------|--------|------|-------------|
| `marine2.py` | DELETE | Task-01 | AC-001 |
| `tests/unittests.py` | MODIFY | Task-02 | AC-008, AC-009, AC-010 |
| `tests/unittests.py` | MODIFY | Task-03 | AC-008 |
| `src/utils.py` | MODIFY | Task-04 | AC-007, AC-009, AC-010 |
| `src/utils.py` | MODIFY | Task-05 | AC-006, AC-008 |
| `marine.py` | MODIFY | Task-06 | AC-005 |
| `tests/unittests.py` | MODIFY | Task-07 | AC-005, AC-008 (static-source assertions for C2/C3) |
| `marine.py` | MODIFY | Task-08 | AC-002, AC-003, AC-004, AC-008 |
| (no file changes — verification only) | — | Task-09 | AC-011 |
| `marine.py` | MODIFY | Task-10 | AC-012, AC-018 |
| `src/core.py` | MODIFY | Task-10 | AC-012, AC-018 |
| `src/utils.py` | MODIFY | Task-10 | AC-012, AC-018 |
| `src/read_process.py` | MODIFY | Task-10 | AC-012 |
| `.forge/stages/2-architect/unused-functions-audit.json` | CREATE | Task-11 | AC-013 |
| `marine.py` | MODIFY | Task-12 | AC-014, AC-017 (only if audit produces REMOVE_CANDIDATEs in this file) |
| `src/core.py` | MODIFY | Task-12 | AC-014, AC-017 (only if audit produces REMOVE_CANDIDATEs in this file) |
| `src/utils.py` | MODIFY | Task-12 | AC-014, AC-017 (only if audit produces REMOVE_CANDIDATEs in this file) |
| `src/read_process.py` | MODIFY | Task-12 | AC-014, AC-017 (only if audit produces REMOVE_CANDIDATEs in this file) |
| `tests/unittests.py` | MODIFY | Task-12 | AC-014 (adds `TestPublicAPIPreserved`) |
| (process gate — no file change) | n/a (HUMAN-REVIEW-HALT) | Task-11 -> Task-12 boundary | AC-015 |
| (cross-cutting verification — diff-size invariant on `marine.py` and `src/utils.py`) | VERIFY | Task-09 (gate spans tasks 04, 05, 06, 08) | AC-016 |

### Files explicitly NOT touched (out-of-scope guard)

- `src/annotate.py` — explicitly excluded from docstring and cleanup scope (architecture-plan Section 11).
- `src/__init__.py` — out of scope.
- `tests/integration_tests_run.sh`, `tests/integration_tests_auto_check.py` — unchanged across all tasks.
- `.github/workflows/main.yml` — unchanged.
- `marine_environment2.yaml` — unchanged.

## Per-File Change Summary

### `marine.py`
- Task-06: line 279 — single-line edit `Pool(processes=cores)` → `Pool(processes)`.
- Task-08: insert two lines (`start_time = time.time()` and `tracemalloc.start()`) at the top of `run()` body; delete the same two lines from the `__main__` block. Net change: zero lines added/removed at the file level for those two statements (they are relocated, not duplicated).
- Task-10: add Google-style docstrings to all 11 top-level functions; six Pool-worker docstrings carry the dispatch-contract sentence (per D-8).
- Task-12 (conditional): if audit produces REMOVE_CANDIDATEs in `marine.py`, delete those `def` blocks and any imports that become unused as a result.

### `src/utils.py`
- Task-04: line 440 — single-character edit `==` → `=` inside `get_intervals`.
- Task-05: line 663 — remove the literal string `, header=False` from a `.format()` call inside `get_coverage_wrapper`.
- Task-10: add Google-style docstrings to all 53 top-level functions; the three Pool workers in this file (`get_coverage_wrapper`, `concat_and_write_bams_wrapper`, `merge_files_by_chromosome`) carry the dispatch-contract sentence.
- Task-12 (conditional): same cleanup pattern as `marine.py`.

### `src/core.py`
- Task-10: add Google-style docstrings to all 18 top-level functions; one Pool worker (`find_edits_and_split_bams_wrapper`) carries the dispatch-contract sentence.
- Task-12 (conditional): same cleanup pattern.

### `src/read_process.py`
- Task-10: add Google-style docstrings to all 14 top-level functions. No Pool workers in this file.
- Task-12 (conditional): same cleanup pattern.

### `tests/unittests.py`
- Task-02: add `from utils import get_intervals` to the existing import line; insert new class `TestUtilsFunctions(unittest.TestCase)` immediately above `unittest.main()` containing three `get_intervals` test methods.
- Task-03: append a fourth method (`test_get_coverage_wrapper_no_header_kwarg`) to `TestUtilsFunctions`.
- Task-07: append two more methods (`test_marine_run_starts_time_at_top` and `test_marine_pool_uses_processes_param`) to `TestUtilsFunctions`.
- Task-12: append a new class `TestPublicAPIPreserved(unittest.TestCase)` immediately above `unittest.main()` with exactly four test methods (one per audited source file).

### `.forge/stages/2-architect/unused-functions-audit.json`
- Task-11: created. Schema documented in task-11.md and AC-013. Read-only inputs to task-12.

## Dependency Map

The task DAG (extracted from each task file's `<!-- DEPENDENCIES: -->` header):

```
task-01 (root)
  task-02 -> task-04 -> task-06 -> task-07 -> task-08 -> task-09 -> task-10 -> task-11 -> [HUMAN-REVIEW-HALT] -> task-12
  task-03 -> task-05 ->^
```

Cycle check: linear chain from task-01 through task-12 with two parallel branches converging at task-06 (task-04 and task-05 both feed task-06's predecessor chain). No cycles. Valid DAG.

Blocking edges that gate review:
- task-04 cannot start until task-02 has demonstrated the H5 test is RED.
- task-05 cannot start until task-03 has demonstrated the C4 test is RED.
- task-08 cannot start until task-07 has demonstrated the C2 static-source test is RED.
- task-12 cannot start until task-11 is complete AND a human reviewer has confirmed the audit JSON.

## Critical Path

The critical path is the longest chain of dependent tasks. With test-first ordering, that chain is:

`task-01 -> task-02 -> task-04 -> task-06 -> task-07 -> task-08 -> task-09 -> task-10 -> task-11 -> [human-review-halt] -> task-12`

Estimated complexity per task (S/M/L/XL — see TASKS.md for per-task estimates):

| Task | Complexity | Rationale |
|------|-----------|-----------|
| task-01 | S | One `git rm` plus regression run |
| task-02 | S | Three test methods, one import edit |
| task-03 | S | One test method appended |
| task-04 | S | Single-character edit |
| task-05 | S | Single-line edit |
| task-06 | S | Single-line edit |
| task-07 | S | Two test methods appended |
| task-08 | S | Two-line move (insert top of run, delete from main) |
| task-09 | S | Verification only — no edits |
| task-10 | L | 96 docstrings across four files; integration regression run; ~600-1100 line additive diff |
| task-11 | M | AST walk + grep matrix + JSON schema + manual reviewer notes for each REMOVE_CANDIDATE |
| task-12 | M | Surgical deletions + new test class + pyflakes baseline diff (size depends on audit output) |

Critical-path wall-clock estimate: dominated by task-10 (large additive diff requires careful no-deletion verification) and task-12 (size depends on audit output). All other Package A tasks are sub-30-minute work units.
