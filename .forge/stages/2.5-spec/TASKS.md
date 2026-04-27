# Task Breakdown
<!-- FORGE_STAGE: 2.5-spec -->
<!-- SOURCE: .forge/stages/2-architect/architecture-plan.md and .forge/stages/2-architect/tasks/ -->

## Execution order

Tasks must run in numeric order (task-01 -> task-02 -> ... -> task-12). Test-first discipline (tasks 02/03/07 written before tasks 04/05/08) is preserved. A mandatory human-review halt sits between Task-11 and Task-12 — see the `HUMAN-REVIEW-HALT` block.

---

## Task-01: Delete marine2.py
**Dependencies:** none
**Files:** `marine2.py` (DELETE)
**Acceptance Criteria:** AC-001
**Estimated Complexity:** S

### Implementation Notes
- `git rm marine2.py` from the repo root.
- The file is dead code; `grep -r 'marine2' .` returns only self-references.
- Do not commit until the unit and integration suites pass.

### Done When
- [ ] `marine2.py` does not exist on disk.
- [ ] `git status` shows `marine2.py` as a staged deletion.
- [ ] `cd tests && python -m pytest unittests.py -v` exits 0 (existing 6 tests pass).
- [ ] `cd tests && bash integration_tests_run.sh python` exits 0.

---

## Task-02: Add unit tests for get_intervals (H5, test-first)
**Dependencies:** Task-01
**Files:** `tests/unittests.py` (MODIFY)
**Acceptance Criteria:** AC-008, AC-009, AC-010
**Estimated Complexity:** S

### Implementation Notes
- Update the `from utils import get_contig_lengths_dict` line to also import `get_intervals`.
- Insert a new class `TestUtilsFunctions(unittest.TestCase)` immediately above `unittest.main()`.
- Add exactly three test methods (verbatim from `.forge/stages/2-architect/tasks/task-02-tests-get-intervals.md`): `test_get_intervals_partial_last_window`, `test_get_intervals_exact_division`, `test_get_intervals_short_contig`.
- Anti-pattern: do NOT add helper methods or class attributes. Only the three test methods.
- Expected outcome at this task's completion: `test_get_intervals_partial_last_window` is RED (the H5 fix has not landed yet); the other two pass.

### Done When
- [ ] AC-008, AC-009, AC-010 verification commands behave as documented (the partial-last-window test is RED here).
- [ ] `unittest.main()` remains the final non-blank line.
- [ ] No other test class or file was modified.

---

## Task-03: Add unit test for get_coverage_wrapper filename (C4, test-first)
**Dependencies:** Task-01
**Files:** `tests/unittests.py` (MODIFY)
**Acceptance Criteria:** AC-008
**Estimated Complexity:** S

### Implementation Notes
- Append the method `test_get_coverage_wrapper_no_header_kwarg` to `TestUtilsFunctions`. The method body uses `inspect.getsource` and is fully self-contained (`import inspect` and `from utils import get_coverage_wrapper` go inside the method, not at module top).
- Anti-pattern: do not add `import inspect` or `from utils import get_coverage_wrapper` at the module top — keep the heavy imports gated inside the test method.
- Expected outcome: this test is RED until task-05 lands.

### Done When
- [ ] `TestUtilsFunctions::test_get_coverage_wrapper_no_header_kwarg` is collected by pytest and currently FAILS.
- [ ] The other tests in `TestUtilsFunctions` continue to behave as in task-02.
- [ ] `unittest.main()` is still last non-blank line.

---

## Task-04: Apply H5 fix in src/utils.py:get_intervals
**Dependencies:** Task-02
**Files:** `src/utils.py` (MODIFY)
**Acceptance Criteria:** AC-007, AC-009, AC-010
**Estimated Complexity:** S

### Implementation Notes
- Single-character edit at line 440: `==` -> `=`.
- Indentation is 12 leading spaces; preserve exactly.
- Anti-pattern: do not change the `if end > contig_length:` guard above; do not add comments about the fix; do not touch surrounding whitespace.
- Expected outcome: `test_get_intervals_partial_last_window` turns GREEN; `test_get_coverage_wrapper_no_header_kwarg` is still RED until task-05.

### Done When
- [ ] AC-007 verification command passes (`grep -n 'end = contig_length'` matches at line 440; `grep 'end == contig_length'` returns no match).
- [ ] AC-009 and AC-010 unit tests pass.
- [ ] All existing tests still pass.

---

## Task-05: Apply C4 fix in src/utils.py:get_coverage_wrapper
**Dependencies:** Task-03
**Files:** `src/utils.py` (MODIFY)
**Acceptance Criteria:** AC-006, AC-008
**Estimated Complexity:** S

### Implementation Notes
- Delete the literal `, header=False` (14 characters) from the `.format()` call at line 663.
- Anti-pattern: do not switch to f-string; the surrounding code uses `.format()` per decision D-2.
- Anti-pattern: do not edit the docstring block at lines 665-673.

### Done When
- [ ] AC-006 verification command passes.
- [ ] `test_get_coverage_wrapper_no_header_kwarg` is GREEN.
- [ ] All other tests still pass.

---

## Task-06: Apply C3 fix in marine.py:generate_and_split_bed_files_for_all_positions
**Dependencies:** Task-05
**Files:** `marine.py` (MODIFY)
**Acceptance Criteria:** AC-005
**Estimated Complexity:** S

### Implementation Notes
- Single-line edit at line 279: `with Pool(processes=cores) as pool:` -> `with Pool(processes) as pool:`.
- Use positional argument per decision D-1 (matches the function's parameter name without keyword noise).
- Anti-pattern: do not use `Pool(processes=processes)`.
- Function signature on line 214 already declares `processes=4` default; do not touch.

### Done When
- [ ] AC-005 verification command passes.
- [ ] `python -c "import marine"` does not raise.
- [ ] All existing unit tests still pass.

---

## Task-07: Add static-source unit tests for C2 and C3
**Dependencies:** Task-06
**Files:** `tests/unittests.py` (MODIFY)
**Acceptance Criteria:** AC-005, AC-008
**Estimated Complexity:** S

### Implementation Notes
- Append two methods to `TestUtilsFunctions`: `test_marine_run_starts_time_at_top` and `test_marine_pool_uses_processes_param`.
- Each method does its own `sys.path.insert` and `import marine` inside the method body. Do NOT add `import marine` at module top — `marine` is heavy (subprocess/pysam side effects) and would slow read_process tests.
- Expected outcome: `test_marine_pool_uses_processes_param` is GREEN (C3 fix in task-06 already landed). `test_marine_run_starts_time_at_top` is RED until task-08.

### Done When
- [ ] Both new methods are collected by pytest.
- [ ] `test_marine_pool_uses_processes_param` PASSES; `test_marine_run_starts_time_at_top` FAILS.
- [ ] `unittest.main()` is still the final non-blank line.

---

## Task-08: Apply C2 + M2 — move start_time and tracemalloc.start() into run()
**Dependencies:** Task-07
**Files:** `marine.py` (MODIFY)
**Acceptance Criteria:** AC-002, AC-003, AC-004, AC-008
**Estimated Complexity:** S

### Implementation Notes
- Insert two lines as the first executable statements of `run()`'s body, with a 4-space indent: `start_time = time.time()` then `tracemalloc.start()`. Place a single blank line between `tracemalloc.start()` and the existing `logging_folder = ...` line.
- Delete those two lines from the `__main__` block (lines 652-653 pre-edit).
- Order matters per decision D-3: `start_time` first, `tracemalloc.start()` second. This satisfies all early-return paths through `run()` without conditional guards.
- Anti-pattern: do not add `if not tracemalloc.is_tracing()` guard — assumption A-2 confirms multiple `start()` calls are harmless.
- Anti-pattern: do not add a comment explaining the move.

### Done When
- [ ] AC-002, AC-003, AC-004 verification commands pass.
- [ ] `test_marine_run_starts_time_at_top` is GREEN.
- [ ] `cd tests && python -m pytest unittests.py -v` exits 0 with at least 12 tests passing.

---

## Task-09: Package A integration test gate
**Dependencies:** Task-08
**Files:** none (verification only)
**Acceptance Criteria:** AC-011
**Estimated Complexity:** S

### Implementation Notes
- Run `cd tests && bash integration_tests_run.sh python` and confirm exit code 0.
- Re-run `python -m pytest unittests.py -v`.
- Anti-pattern: if integration tests fail, do NOT alter source code to make them pass. Bisect by reverting the most-recent committed task and re-run.

### Done When
- [ ] AC-011 verification command passes.
- [ ] `git status` shows only the expected staged set: `marine2.py` deleted; `marine.py`, `src/utils.py`, `tests/unittests.py` modified; nothing else.

---

## Task-10: Add Google-style docstrings to four target source files
**Dependencies:** Task-09
**Files:** `marine.py`, `src/core.py`, `src/utils.py`, `src/read_process.py` (MODIFY)
**Acceptance Criteria:** AC-012, AC-018
**Estimated Complexity:** L

### Implementation Notes
- Walk each of the four files in source order; for every `FunctionDef` and `AsyncFunctionDef` lacking a docstring, insert a Google-style docstring as the first statement of the function body.
- Match existing 4-space body indentation precisely.
- Function-count baseline (architect-time): marine.py=11, src/core.py=18, src/utils.py=53, src/read_process.py=14, total=96. If the live count differs, halt and report — task-08 or another task may have shifted the inventory.
- Pool-worker functions (per decision D-8): the first sentence must reference Pool dispatch (e.g., `"Worker function for Pool.imap_unordered"`) and document the tuple-unpacking contract. The six Pool workers are: `get_unique_barcodes_for_reads_in_bamfile`, `process_combination_for_split` (marine.py), `find_edits_and_split_bams_wrapper` (src/core.py), `concat_and_write_bams_wrapper`, `get_coverage_wrapper`, `merge_files_by_chromosome` (src/utils.py).
- Anti-pattern: do NOT add type hints (decision excludes M1).
- Anti-pattern: do NOT add module-level docstrings (only function-level).
- Anti-pattern: do NOT touch any function that already has a docstring; audit-and-skip.
- Anti-pattern: do NOT modify `src/annotate.py` or any test file.
- Anti-pattern: do NOT introduce any new `import`/`from` line (AC-012 enforces this).
- The diff will be ~600-1100 added lines; AC-012 enforces zero non-docstring DELETIONS via the `git diff -U0 ... | grep '^-' | grep -v '^---' | grep -vE '^-\s*("""|\s*$)' | wc -l` check.

### Done When
- [ ] AC-012 AST traversal exits 0 (every function has a docstring).
- [ ] AC-018 first-sentence Pool-dispatch check passes for the six Pool workers.
- [ ] `git diff -U0 ... | grep ^- ...` line returns 0 (zero non-docstring deletions).
- [ ] `git diff --stat` shows ONLY the four target files modified.
- [ ] No new `import`/`from` lines introduced (AC-012 import-set diff check returns empty).
- [ ] Full unit + integration suites pass.

---

## Task-11: Audit unused functions; produce unused-functions-audit.json (read-only)
**Dependencies:** Task-10
**Files:** `.forge/stages/2-architect/unused-functions-audit.json` (CREATE) — no source files modified
**Acceptance Criteria:** AC-013
**Estimated Complexity:** M

### Implementation Notes
- Build the function inventory by parsing each of the four files with `ast`. Record `{name, file, line}` for every `FunctionDef`/`AsyncFunctionDef`.
- For each function, run all KEEP rules (full list in `.forge/stages/2-architect/tasks/task-11-unused-function-audit.md` Section "Classification Rules"):
  1. Imported by name (must follow backslash-continued imports — use `ast.parse` `ImportFrom` walk, not naive `grep`).
  2. Called by name (whole-word match, exclude the `def` line itself).
  3. Pool worker target (the six are KEEP unconditionally).
  4. CLI entry point (`run` in marine.py is KEEP unconditionally).
  5. Referenced in `tests/`.
  6. Referenced in `.github/workflows/main.yml`, `tests/integration_tests_run.sh`, `tests/integration_tests_auto_check.py`.
  7. Dynamic dispatch suspicion (currently NONE in the four files per assumption A-13; the audit must still log the check).
- Write the JSON artifact at `.forge/stages/2-architect/unused-functions-audit.json` matching the schema in AC-013 / task-11.md.
- For each REMOVE_CANDIDATE, manually read the function body and add a `removal_note` explaining what it does and why removal is judged safe. If the auditor cannot confidently explain the function's purpose, downgrade to KEEP with `{"rule": "uncertain_purpose"}` evidence — uncertainty defaults to KEEP per decision D-11.
- Anti-pattern: do NOT modify any `.py` file. AC-013 (h) enforces this via `git status` filter.
- Anti-pattern: do NOT name any candidate as removable in advance — the audit decides at runtime.

### Done When
- [ ] AC-013 schema/count/coverage checks all pass.
- [ ] All six Pool workers and `run` are KEEP with proper evidence rules.
- [ ] No source `.py` files are modified.
- [ ] Existing unit + integration suites still pass (sanity check).
- [ ] Summary printed to stdout listing total/keep/remove counts and the REMOVE_CANDIDATE list.

---

## HUMAN-REVIEW-HALT (between Task-11 and Task-12)

**MANDATORY GATE — task-12 MUST NOT begin until this halt is satisfied.**

This halt is encoded by:
- Decisions D-9, D-10, D-12 in `.forge/stages/2-architect/architecture-plan.md`.
- Risk R-10 in the architecture plan ("audit JSON consumed by task-12 without human review").
- AC-015 in `.forge/stages/2.5-spec/SPEC.md`.
- Task-11 step 8 ("halt for human review; do not auto-advance to task-12").
- Task-12 pre-condition ("`unused-functions-audit.json` has been read and reviewed by a human reviewer").

### Required reviewer actions

1. Open `.forge/stages/2-architect/unused-functions-audit.json` and read every entry where `classification == "REMOVE_CANDIDATE"`.
2. For each REMOVE_CANDIDATE:
   - Read the function body in its source file.
   - Read the `removal_note` justification.
   - Decide: APPROVE (leave as REMOVE_CANDIDATE) or VETO (downgrade to KEEP).
3. To VETO, edit the JSON in place: change `classification` to `"KEEP"`, append `{"rule": "human_review_keep", "location": null}` to `evidence`, and set `removal_note` to `null`.
4. Save the file. The post-review JSON is the authoritative input to task-12.
5. Confirm to the build agent (e.g., respond "y" to the `/forge build` interactive prompt) that the audit has been reviewed.

### Halt enforcement contract for orchestration

- The `/forge build` skill MUST treat the `task-11 -> task-12` boundary as a forced human-checkpoint pair. Auto-advance is forbidden.
- If orchestration is non-interactive (CI), task-12 must be skipped (exit code 0, status `BLOCKED_ON_HUMAN_REVIEW`) and a separate manual run must complete the deletion phase.
- Task-12 begins by RE-READING the JSON to pick up any human edits. The agent MUST NOT cache the pre-review JSON.

### Halt-completion criteria

- [ ] A human reviewer has confirmed the audit JSON has been reviewed.
- [ ] Any vetoed REMOVE_CANDIDATEs have been downgraded to KEEP in the JSON.
- [ ] The build agent has explicit confirmation (logged) before invoking task-12.

---

## Task-12: Remove confirmed-unused functions; add TestPublicAPIPreserved
**Dependencies:** Task-11 AND HUMAN-REVIEW-HALT satisfied
**Files:** `marine.py`, `src/core.py`, `src/utils.py`, `src/read_process.py` (MODIFY — only files containing post-review REMOVE_CANDIDATEs); `tests/unittests.py` (MODIFY — append `TestPublicAPIPreserved` class)
**Acceptance Criteria:** AC-014, AC-017
**Estimated Complexity:** M

### Implementation Notes
- Re-read `.forge/stages/2-architect/unused-functions-audit.json` at task start. The audit's post-review state is the authoritative deletion list.
- Build the deletion list = all entries with `classification == "REMOVE_CANDIDATE"` in the post-review JSON.
- If the deletion list is empty, still add the `TestPublicAPIPreserved` class to `tests/unittests.py` — that gives future cleanup passes a regression net (per task-12.md notes).
- Group deletions by file. For each file, delete each function's `def <name>(...):` line and its body (terminating at the next top-level `def`, top-level `class`, or end-of-file).
- After each file's deletions, run `python -c "import <module>"` to confirm the file still parses.
- Capture pyflakes baseline at task start (before any deletions). After deletions, re-run pyflakes; the diff must show zero new `imported but unused` warnings introduced by this task. If a deleted function was the only consumer of a top-level import, remove that import too — but only that import.
- Add `TestPublicAPIPreserved(unittest.TestCase)` to `tests/unittests.py` immediately above `unittest.main()`. The class loads the audit JSON in `setUpClass` and exposes exactly four test methods (`test_marine_keeps_present`, `test_core_keeps_present`, `test_utils_keeps_present`, `test_read_process_keeps_present`), each asserting `hasattr(<module>, <name>)` for every KEEP entry in that file. The reference implementation is in `.forge/stages/2-architect/tasks/task-12-remove-confirmed-unused.md` Section "Test Stub for `TestPublicAPIPreserved`".
- Anti-pattern: do NOT delete any KEEP-classified function.
- Anti-pattern: do NOT reorder surviving functions; closing the gap is fine, reordering is not.
- Anti-pattern: do NOT change blank-line spacing between surviving functions beyond what is needed to preserve the existing 2-blank-lines-between-functions style.
- Anti-pattern: do NOT modify `src/annotate.py` or integration test scripts.
- Anti-pattern: if a deletion causes integration failure, do NOT silently restore the function. Revert the specific deletion, downgrade that function's classification to KEEP in the audit JSON with note `"removed_caused_integration_failure"`, and re-run.

### Done When
- [ ] AC-014 verification: every post-review REMOVE_CANDIDATE is gone (re-run audit script confirms `function_count_remove_candidate == 0`).
- [ ] AC-014 (b): `TestPublicAPIPreserved` exists with exactly four test methods and all four pass.
- [ ] AC-014 (c): pyflakes baseline-vs-post diff shows zero new warnings.
- [ ] AC-014 (d): `git diff` shows changes only in the four target source files plus `tests/unittests.py`.
- [ ] AC-014 (e): `TestPublicAPIPreserved` runs in <1 second total.
- [ ] AC-017: changed-file set is a subset of the allowed list.
- [ ] All existing unit + integration tests still pass.

---

## DAG validity check

Dependency edges (extracted from each `Dependencies:` field):
- task-01: none
- task-02 -> task-01
- task-03 -> task-01
- task-04 -> task-02
- task-05 -> task-03
- task-06 -> task-05
- task-07 -> task-06
- task-08 -> task-07
- task-09 -> task-08
- task-10 -> task-09
- task-11 -> task-10
- task-12 -> task-11 (gated by HUMAN-REVIEW-HALT)

Walk: task-01 is the root. All other tasks have exactly one direct predecessor. The graph is a tree (a special case of DAG) with no cycles. Valid.

## Complexity inventory

| Bucket | Tasks |
|--------|-------|
| S | task-01, task-02, task-03, task-04, task-05, task-06, task-07, task-08, task-09 (9 tasks) |
| M | task-11, task-12 (2 tasks) |
| L | task-10 (1 task) |
| XL | none |

No XL tasks; no split required.

## AC linkage inventory

Every task references at least one AC. Every AC from SPEC.md is referenced by at least one task in the table above:

| AC | Tasks |
|----|-------|
| AC-001 | task-01 |
| AC-002 | task-08 |
| AC-003 | task-08 |
| AC-004 | task-08 |
| AC-005 | task-06, task-07 |
| AC-006 | task-05 |
| AC-007 | task-04 |
| AC-008 | task-02, task-03, task-05, task-07, task-08 |
| AC-009 | task-02, task-04 |
| AC-010 | task-02, task-04 |
| AC-011 | task-09 |
| AC-012 | task-10 |
| AC-013 | task-11 |
| AC-014 | task-12 |
| AC-015 | HUMAN-REVIEW-HALT block (between task-11 and task-12) |
| AC-016 | task-09 (verification gate); task-04, task-05, task-06, task-08 (each contributes lines) |
| AC-017 | task-10, task-11, task-12 |
| AC-018 | task-10 |
