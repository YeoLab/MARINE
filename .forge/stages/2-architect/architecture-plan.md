# Architecture Plan: MARINE Bug Fixes (C1-C4 + H5 + Tracemalloc + Tests) + Documentation & Cleanup

<!-- STAGE: 2-architect -->
<!-- STATUS: READY_FOR_BUILD -->
<!-- UPDATED_UTC: 2026-04-25T10:00:00Z -->
<!-- ARCHETYPE: data-pipeline -->
<!-- MODE: focused (small-scope bug-fix package + scoped documentation/cleanup pass) -->
<!-- REVISION: Extended 2026-04-25 to add task-10/11/12 (Google docstrings + unused-function audit + cleanup). The original 9 bug-fix tasks (1-9) are unchanged; they remain the integration gate before the documentation/cleanup pass begins. -->

## 1. Executive Summary

This plan covers two work packages, executed sequentially:

**Package A — Bug fixes (tasks 1-9, unchanged from the original plan):**
Fix five confirmed defects in the MARINE RNA-editing detection pipeline (C1, C2, C3, C4, H5), move `tracemalloc.start()` into `run()`, and add unit tests covering every changed code path. All edits are local and surgical — total expected diff is fewer than 30 lines of source code plus one whole-file deletion plus ~80 lines of new test code. No architectural change; no new dependencies; no new modules.

**Package B — Documentation & cleanup (tasks 10-12, added in the 2026-04-25 revision):**
Add Google-style docstrings to every function in `marine.py`, `src/core.py`, `src/utils.py`, and `src/read_process.py` (96 functions total). Then run a conservative audit identifying genuinely unused functions in those files — explicitly excluding Pool worker targets, the `run` CLI entry point, functions imported in any module, and functions referenced by tests or CI. Remove only the confirmed-unused functions, with a regression test that pins the surviving public API.

The plan emphasizes:
- **Sequencing** — Package A's 9 tasks run first and end at task-09 (integration gate). Package B's 3 tasks run after, with their own verification at each step. Each package is independently revertable.
- **Test-first for testable bugs** — write the new unit tests before applying the production fix where possible, so each test starts red and turns green when the fix lands.
- **Minimum-surface edits** — every line in the diff must trace to a named bug, an FR-12 docstring requirement, or an audit-confirmed dead function.
- **Conservative cleanup** — uncertainty about whether a function is dead always defaults to KEEP. The audit (task-11) is read-only; deletion (task-12) only acts on the post-review audit JSON.

## 2. Approaches Considered

### Package A: Bug-fix sequencing

#### Approach A1: One-shot patch (all fixes in a single commit)
Apply all source edits and add all unit tests in a single change set, then run unit + integration tests once.

- Pros: shortest path to merge; minimum CI cost.
- Cons: if integration tests fail, the bisection space is the entire change set; harder to attribute regression to a specific fix.

#### Approach A2: Per-bug commits, build runs after each (SELECTED)
Apply fixes in this order, with verification between groups:
1. C1 (delete `marine2.py`) → unit + integration tests
2. C4 + H5 (`src/utils.py` two-line fixes) plus the new `get_intervals` and `get_coverage_wrapper` unit tests → unit tests
3. C3 (`marine.py` Pool fix) → unit tests
4. C2 + M2 (`marine.py` `start_time` and `tracemalloc` move) plus the new `run()` import-and-no-NameError test → unit tests
5. Final integration test run → gate

- Pros: each commit is independently revertable; regressions are attributable to the most recent group; tests-before-fix discipline is naturally enforced for H5 and C4.
- Cons: more CI runs; longer wall-clock time. Acceptable given the small scope.

#### Approach A3: Quarantine + replace (build a fixed `marine.py`/`utils.py` alongside, swap atomically)
Maintain old and fixed files in parallel until the integration suite passes against the new versions, then swap.

- Pros: zero risk during transition.
- Cons: massively over-engineered for five single-line fixes. Violates simplicity-first.

#### Selection: Approach A2
Chosen for the favorable balance of attributability, surgical-diff hygiene, and the natural fit of the test-first discipline for the two bugs that can be unit-tested directly (H5, C4).

### Package B: Docstring + cleanup ordering

#### Approach B1: Cleanup first, docstrings only on survivors
Identify and delete unused functions first; then add docstrings only to what remains.

- Pros: avoids documenting code that will then be deleted; smallest docstring diff.
- Cons: removes the safety net. If a function is wrongly classified as unused and deleted, the docstring step would have surfaced its purpose during writing — by deleting first, that signal is lost. Also: the audit step needs the auditor to read every function body to write a `removal_note`; doing the docstring pass first means the auditor benefits from the just-written docstring.

#### Approach B2: Docstrings first, then audit, then surgical removal (SELECTED)
1. Task-10: docstring every function in scope. Forces the agent to read every function body. The docstring itself becomes evidence of intent.
2. Task-11: audit (read-only) producing the JSON manifest of REMOVE_CANDIDATEs.
3. Task-12: delete only the post-review REMOVE_CANDIDATEs and add a thin presence-test for KEEPs.

- Pros: each function is read once for documentation and a second time for cleanup classification, giving the agent two passes to catch "this is actually used" signals; the audit JSON provides a human-reviewable artifact between analysis and action; the regression test in task-12 pins the surviving API.
- Cons: docstrings on subsequently-deleted functions are wasted work. Worst case ~5-10 throwaway docstrings — negligible.

#### Approach B3: Single combined task (docstring + delete in one pass)
Walk every function once: write docstring if keeping, delete if not.

- Pros: single pass; smallest agent-runtime cost.
- Cons: blurs the analysis/action boundary. Removes the human-review checkpoint between identification and deletion. Higher risk of accidental removal.

#### Selection: Approach B2
Chosen for the explicit human-review checkpoint at the audit JSON, the asymmetric-risk conservatism (uncertainty → KEEP), and the surviving regression-test net.

## 3. Architecture Overview

No structural change. The codebase remains:

```
MARINE/
  marine.py            # CLI entrypoint + run() orchestration  [EDITED]
  marine2.py           # DELETED
  src/
    __init__.py
    utils.py           # 53 utility functions               [EDITED]
    core.py            # parallel BAM traversal             [unchanged]
    read_process.py    # per-read CIGAR/MD parsing          [unchanged]
    annotate.py        # pybedtools annotation              [unchanged]
  tests/
    unittests.py       # unittest.TestCase suites           [EDITED — additive]
    integration_tests_run.sh                                 [unchanged]
    integration_tests_auto_check.py                          [unchanged]
```

## 4. Data Models / Contracts

This task changes no data structures and no public function signatures. The relevant contracts are:

### `get_intervals(contig: str, contig_lengths_dict: dict[str, int], interval_length: int = 2000000) -> list[list[int]]`
- Pre: `contig` is a key of `contig_lengths_dict`; lengths are positive ints.
- Post (after fix): the returned list partitions `[0, contig_length)` into windows of size `interval_length` except the last, which ends at exactly `contig_length`. The list is non-empty.
- Invariant: `result[0][0] == 0` and `result[-1][1] == contig_lengths_dict[contig]`.

### `get_coverage_wrapper(parameters: tuple) -> pd.DataFrame`
- Pre: `parameters` is a 6-tuple `(edit_info, contig, output_folder, barcode_tag, paired_end, verbose)`.
- Post (after fix): the function constructs `output_filename = '{output_folder}/coverage/{contig}.tsv'` and proceeds without raising `TypeError`.

### `generate_and_split_bed_files_for_all_positions(output_folder, bam_filepaths, tabulation_bed=None, processes: int = 4, output_suffix='all_cells') -> None`
- Pre: caller passes valid bam paths; `processes >= 1`.
- Post (after fix): a `multiprocessing.Pool` with the function-parameter `processes` is used; no reference to undefined `cores`.

### `run(...)` (marine.py)
- Pre: as-is; signature unchanged.
- Post (after fix): `start_time` is bound to `time.time()` as the first executable statement; `tracemalloc.start()` is called as the second executable statement; both calls also occur on every code path that previously hit `zero_edit_found(... start_time ...)` without the prior NameError.

No external API contracts (no HTTP, no DB schema, no message formats).

## 5. Decision Register

| ID | Decision | Selected | Alternatives | Rationale |
|----|----------|----------|--------------|-----------|
| D-1 | C3 Pool call form | `Pool(processes)` (positional) | `Pool(processes=processes)` explicit kwarg | Matches the minimum-edit principle and matches the function's existing parameter name — no extra typing |
| D-2 | C4 fix style | Keep `.format()`, drop `header=False` | Switch to f-string | The surrounding lines in `get_coverage_wrapper()` use `.format()`. Style-match existing code (NFR-4) |
| D-3 | tracemalloc placement | First two lines of `run()`: `start_time = time.time()` then `tracemalloc.start()` | Just before `get_traced_memory()`; or guarded with `is_tracing()` | All early-return paths must have `start_time` defined; placing both at top covers every path with no branching (A-2) |
| D-4 | Unit-test class organization | New class `TestUtilsFunctions(unittest.TestCase)` in the same file `tests/unittests.py` | Add to existing `TestReadProcessFunctions` class; or new file `tests/test_utils.py` | Same file = single CI invocation; new class = clear separation between read_process tests and utils tests |
| D-5 | C2 unit-test approach | Import `run` and assert via `inspect.getsource(run)` that `start_time = time.time()` appears before the first `zero_edit_found` reference | Mock-call `run` with stub args (heavy, fragile); skip and rely on integration test (gives no regression signal) | Static-source assertion runs in <50 ms, requires no mocks, and directly verifies the AC |
| D-6 | Commit/sequencing strategy | Approach A2 (per-bug groups with verification between) | Approach A1 (one-shot); Approach A3 (quarantine) | Best diagnostic feedback for the agent; keeps each group independently revertable |
| D-7 | Docstring style | Google-style with `Args:`/`Returns:`/`Raises:` sections | NumPy-style; reST/Sphinx style; freeform | Google style is the most-readable in plain text and matches the project's existing freeform-comment tone. Docstring-style choice locked here so the build agent does not need to re-decide per file. |
| D-8 | Pool-worker docstring marker | First sentence explicitly states "Worker function for Pool.map/imap_unordered" plus the tuple-unpacking contract | Same docstring style as ordinary functions | Pool workers have a non-obvious calling convention (single tuple arg unpacked into N variables). Future maintainers reading the function in isolation cannot tell from the signature; the docstring is the only place to convey this. |
| D-9 | Cleanup analysis vs. action split | Two tasks: task-11 produces audit JSON (read-only), task-12 acts on it | One task that audits and deletes in a single pass | The split creates a human-review checkpoint at the JSON artifact. The reviewer can downgrade any REMOVE_CANDIDATE to KEEP without re-running the audit. Reduces blast radius of a misclassification. |
| D-10 | Unused-function detection method | Whole-word `grep` plus `ast.parse` of `ImportFrom` nodes, with explicit allowlist for Pool workers and `run` CLI entry | `vulture` static analyzer; `pyflakes`; manual reading only | Whole-word grep + AST import walk is sufficient given the codebase has no dynamic dispatch (verified). Vulture would add a dependency. The known false-positive risks (Pool workers, argparse entry) are explicitly allowlisted. |
| D-11 | Cleanup conservatism bias | Uncertainty maps to KEEP; missing evidence is not evidence of absence | Symmetric or REMOVE-biased | Asymmetric cost: a wrongly-kept dead function is bytes; a wrongly-removed live function is a runtime crash. Bias toward keep is correct. |
| D-12 | Public-API regression test | `TestPublicAPIPreserved` class with one `hasattr` test per file, driven by the audit JSON | Per-function unit tests; integration tests only; no new tests | Thin presence test runs in <1 second total, catches the most likely cleanup error (accidental KEEP deletion), and stays in lockstep with the audit JSON. Behavior coverage is left to existing integration tests. |

## 6. Implementation Task Decomposition

Tasks are listed in execution order. Each task has its own file under `tasks/`. Dependencies are explicit.

**Package A — Bug fixes (unchanged from the original plan):**

| # | Task | File | Depends On |
|---|------|------|-----------|
| 1 | Delete `marine2.py` | `tasks/task-01-delete-marine2.md` | — |
| 2 | Add unit tests for `get_intervals` (H5) | `tasks/task-02-tests-get-intervals.md` | task-01 |
| 3 | Add unit test for `get_coverage_wrapper` filename (C4) | `tasks/task-03-test-coverage-wrapper.md` | task-01 |
| 4 | Apply H5 fix (`src/utils.py` line 440) | `tasks/task-04-fix-get-intervals.md` | task-02 |
| 5 | Apply C4 fix (`src/utils.py` line 663) | `tasks/task-05-fix-coverage-wrapper.md` | task-03 |
| 6 | Apply C3 fix (`marine.py` line 279) | `tasks/task-06-fix-pool-processes.md` | task-05 |
| 7 | Add unit tests for C3 (Pool kwarg) and C2 (`start_time` placement) via static source inspection | `tasks/task-07-static-source-tests.md` | task-06 |
| 8 | Apply C2 + M2 fix (move `start_time` and `tracemalloc.start()` into `run()`; remove from `__main__`) | `tasks/task-08-fix-tracemalloc-and-start-time.md` | task-07 |
| 9 | Run integration test gate (Package A regression gate) | `tasks/task-09-integration-gate.md` | task-08 |

**Package B — Documentation & cleanup (added 2026-04-25):**

| # | Task | File | Depends On |
|---|------|------|-----------|
| 10 | Add Google-style docstrings to every function in `marine.py`, `src/core.py`, `src/utils.py`, `src/read_process.py` | `tasks/task-10-google-docstrings.md` | task-09 |
| 11 | Audit unused functions; produce `unused-functions-audit.json` (read-only, no source edits) | `tasks/task-11-unused-function-audit.md` | task-10 |
| 12 | Remove confirmed-unused functions from the post-review audit; add `TestPublicAPIPreserved` regression test | `tasks/task-12-remove-confirmed-unused.md` | task-11 |

## 7. Requirements Coverage Matrix

| Requirement | Covered by Task(s) | Acceptance Criterion |
|-------------|--------------------|---------------------|
| FR-1 (delete marine2.py) | task-01 | AC-1 |
| FR-2 (start_time in run) | task-08 | AC-2 |
| FR-3 (tracemalloc in run) | task-08 | AC-3 |
| FR-4 (remove start_time from __main__) | task-08 | AC-4 |
| FR-5 (Pool(processes)) | task-06 | AC-5 |
| FR-6 (.format C4 fix) | task-05 | AC-6 |
| FR-7 (end = contig_length) | task-04 | AC-7 |
| FR-8 (test H5 short contig) | task-02 | AC-8, AC-9 |
| FR-9 (test H5 length=100, interval=30) | task-02 | AC-8, AC-9 |
| FR-10 (test C4 filename) | task-03 | AC-8 |
| FR-11 (test H5 divisible) | task-02 | AC-8, AC-10 |
| FR-12 (Google-style docstrings on every function in marine.py, src/core.py, src/utils.py, src/read_process.py) | task-10 | AC-12 |
| FR-13 (Identify and remove genuinely-unused functions in those files; preserve Pool workers, CLI entry, and dynamically dispatched callables) | task-11, task-12 | AC-13 |
| FR-14 (Add a regression test pinning the surviving public API after cleanup) | task-12 | AC-14 |
| NFR-1 (zero unit-test regression) | task-09, task-10, task-11, task-12 | AC-8 |
| NFR-2 (integration tests pass) | task-09, task-10, task-12 | AC-11 |
| NFR-3 (new tests <1s each) | task-02, task-03, task-07, task-12 (presence tests) | — |
| NFR-4 (minimal diff for source code) | tasks 1-9 (bug fixes) and task-12 (cleanup); design constraint. Task-10 docstrings are an explicitly authorized exception. | — |
| NFR-5 (no new imports) | tasks 1-9, task-10. Task-12 may remove imports that become unused after deletion but cannot add new imports. | — |
| NFR-6 (Python 3.10 only — no syntax requiring newer/older versions) | all tasks; design constraint | — |
| NFR-7 (surgical changes — every changed line traces to a named requirement) | all tasks; reinforced by task-10 AC-T10-6 (zero non-docstring deletions in docstring task) and task-12 AC-T12-1 (only audit-confirmed functions removed) | — |
| COMPAT-1 to COMPAT-4 | all tasks honor; no signature changes anywhere | — |

Every requirement maps to at least one task.

## 8. Verification Plan

Run after each task group as defined in Approach A2 (Package A) and Approach B2 (Package B):

| Group | Verification | Pass Criterion |
|-------|-------------|----------------|
| After task-01 | `cd tests && python -m pytest unittests.py -v` then `bash integration_tests_run.sh python` | All existing tests still pass; integration exits 0 |
| After tasks 02-03 (tests added, fix not yet) | `cd tests && python -m pytest unittests.py -v` | New H5 + C4 tests **fail** (red); existing tests pass |
| After tasks 04-05 (fixes applied) | `cd tests && python -m pytest unittests.py -v` | All tests pass (green) |
| After task-06 | `cd tests && python -m pytest unittests.py -v` | All tests pass; `grep 'Pool(processes' marine.py` returns `Pool(processes)` (no `=cores`) |
| After task-07 (static-source tests added) | `cd tests && python -m pytest unittests.py -v` | New static-source tests **fail** for C2 (run() does not yet have `start_time` at top); pass for C3 |
| After task-08 | `cd tests && python -m pytest unittests.py -v` | All tests pass including C2 static-source test |
| After task-09 (Package A regression gate) | `cd tests && bash integration_tests_run.sh python` | Exit code 0 |
| After task-10 (docstrings) | `python -c "import ast; ..."` (see task-10 AC-T10-1) plus full unit + integration tests | Every function has a docstring; all tests pass; `git diff` shows ZERO non-docstring deletions in the four target files |
| After task-11 (audit) | Validate `unused-functions-audit.json` schema; KEEP/REMOVE counts sum to total; all six Pool workers and `run` are KEEP | Audit JSON valid; no source files modified; tests still pass |
| After task-12 (cleanup) | `python -c "import ast; ..."` to confirm REMOVE_CANDIDATEs are gone; `TestPublicAPIPreserved` passes; full unit + integration tests | Every removed function is gone; every KEEP function still importable; all tests pass; pyflakes introduces no new warnings |

## 9. Risk Register

| ID | Risk | Severity | Mitigation | Hotspot? |
|----|------|----------|-----------|----------|
| R-1 | Integration tests fail post-tracemalloc move | Medium | Verified that all existing call paths through `run()` still cover both early-return branches; tracemalloc.start() at top of run() is idempotent | No hotspot file present |
| R-2 | Removing `start_time` from `__main__` accidentally breaks unobserved logging | Low | Verified by reading marine.py 654-682; no post-`run()` reference exists | No |
| R-3 | A test using current working directory not equal to `tests/` would break sys.path setup | Low | All commands documented run from `tests/`; CI does the same | No |
| R-4 | `unittest.main()` placement disturbed by class addition | Low | Tasks specify "insert new class above `unittest.main()` line" | No |
| R-5 | Subtle change in `Pool(processes)` semantics if any caller passed an explicit kwarg | Low | Verified single caller at marine.py:464 uses default | No |
| R-6 | Docstrings introduce a typo or accidental edit to function bodies | Medium | task-10 AC-T10-6 (regex-checked zero non-docstring deletions) gates merge; integration tests run after task-10 | No |
| R-7 | Pool worker function classified as REMOVE_CANDIDATE because it has no static `pool.map(<name>, ...)` reference (false positive) | High if it occurred | Explicit allowlist of all six Pool workers in task-11; task-11 AC-T11-5 verifies all six are KEEP | No, but `src/utils.py` is the largest file (1536 LOC) and the most likely site for an oversight — apply extra reviewer attention here |
| R-8 | A function reachable only via dynamic dispatch (e.g., via `getattr` in a downstream module not under audit) is removed | Medium | Codebase audit at this stage confirmed NONE of `marine.py`, `src/core.py`, `src/utils.py`, `src/read_process.py` use `getattr`/`globals()`/`eval`/`exec`/`importlib`. Recorded in assumption A-13. The audit script must recheck this at execution time. | No |
| R-9 | A function used by a downstream consumer outside this repository (e.g., a notebook or external script that imports `from utils import <X>`) is removed | Medium | Out of scope: this repository's audit cannot see external consumers. Mitigation: the `simplify` task should default to KEEP when no internal usage is found AND the function name appears in any `__all__` declaration, public README example, or top-level export. The four target files do not currently export `__all__`; the audit logs this and treats every name as potentially-public. The remediation if a downstream consumer breaks is to revert task-12. Recorded as assumption A-14. | No |
| R-10 | The audit JSON is consumed by task-12 without human review (the build agent forgets to pause) | Medium | task-11 step 8 explicitly halts for review; task-12 pre-condition explicitly requires re-reading the (post-review) JSON. The build skill (`/forge build`) should treat task-11 → task-12 as a forced human-checkpoint pair. | No |
| R-11 | After deletion, an existing import in another file references a now-deleted name | High if it occurred | task-12 step 5 runs `python -c "import <module>"` after each file's deletions; task-12 AC-T12-2 (`TestPublicAPIPreserved` calls `hasattr` on every KEEP) plus full integration tests catch this. The continuation-line import parser in task-11 (Notes section) ensures the audit's "imported by name" rule sees ALL imports including continuations. | No |

## 10. Trust Boundaries (input to threat model)

The MARINE pipeline is an offline batch tool that reads local BAM files and writes local TSV/h5ad/BED outputs. The trust boundaries are:

1. **Input file → process**: BAM, BED, and whitelist files supplied via CLI args. Trust assumption: caller has filesystem access; pysam parses untrusted BAM headers.
2. **Process → child process** (multiprocessing): `Pool` workers receive pickled args. Trust assumption: process owner controls all workers.
3. **Process → filesystem**: Output written to user-specified `output_folder`. Trust assumption: caller controls path traversal.

No network boundary exists. See `threat-model.md` for STRIDE/DREAD analysis.

## 11. Out-of-Scope (Reaffirmed)

The following remain explicitly out of scope and must NOT be touched by any task:
- H2 (utils.py refactor)
- H3 (bash subprocess merge)
- H4 (deprecated pandas API)
- H6 (CB_N hardcoding)
- M1 (type annotations) — task-10 adds docstrings only; type annotations are NOT added.
- M3 (pandas inplace deprecation)
- M4 (BAM existence validation)
- M5 (integration test content assertions)
- M6 (marine2.py imports — moot since marine2.py is deleted)
- M7 (sys.stdout.err typo)
- M8 (get_sailor_sites in-place mutation)
- L1-L5 (low-severity findings)
- Any change to `.github/workflows/main.yml`
- Any change to `marine_environment2.yaml` Python version
- `src/annotate.py` — explicitly NOT in the docstring or cleanup scope. Only the four named files are touched.
- Any test file other than `tests/unittests.py` — `tests/integration_tests_run.sh` and `tests/integration_tests_auto_check.py` remain unchanged.
- Module-level docstrings — task-10 adds function-level docstrings only.
- Type hints — neither task-10 nor any other task introduces type hints.
- Code reformatting — black/isort/etc. are NOT run as part of any task.

## 12. Definition of Done

**Package A (tasks 1-9):**
- All 9 Package A tasks completed with their per-task acceptance criteria met.
- All 11 original architecture-level acceptance criteria (AC-1 through AC-11) verified.
- `cd tests && python -m pytest unittests.py -v` exits 0 with at least 9 tests collected.
- `cd tests && bash integration_tests_run.sh python` exits 0.
- Total source-code diff (excluding new tests and the marine2.py deletion) is no more than 12 added/modified lines.
- No new imports, no new dependencies, no signature changes, no formatting changes outside the changed lines.

**Package B (tasks 10-12):**
- Task-10 complete: every function in `marine.py`, `src/core.py`, `src/utils.py`, `src/read_process.py` has a Google-style docstring (AC-12). Zero non-docstring source modifications. All tests still pass.
- Task-11 complete: `unused-functions-audit.json` exists, validates against schema, and has been reviewed (AC-13). The audit halts for human review before task-12 begins.
- Task-12 complete: every post-review REMOVE_CANDIDATE function is gone from its source file; `TestPublicAPIPreserved` is added to `tests/unittests.py` and passes (AC-14). All existing unit and integration tests still pass. Pyflakes adds zero new warnings.
- Combined: `git diff main` shows changes ONLY in the four target source files plus `tests/unittests.py` plus the new `.forge/stages/2-architect/unused-functions-audit.json` artifact.

## 13. Pool Workers, CLI Entry Points, and Dynamic Dispatch (Audit Inputs)

These references are pinned here for tasks 10, 11, and 12. They are the result of an exhaustive grep at the start of the documentation/cleanup pass.

### Pool worker functions (must remain, must be docstring-marked)

| Function | File | Line | Dispatched via |
|---|---|---|---|
| `get_unique_barcodes_for_reads_in_bamfile` | `marine.py` | 57 | `pool.map(...)` at `marine.py:143` |
| `process_combination_for_split` | `marine.py` | 159 | `pool.map(...)` at `marine.py:280` (post C3 fix) |
| `find_edits_and_split_bams_wrapper` | `src/core.py` | 496 | `p.imap_unordered(...)` at `src/core.py:197` |
| `concat_and_write_bams_wrapper` | `src/utils.py` | 867 | `p.imap_unordered(...)` at `src/core.py:247` |
| `get_coverage_wrapper` | `src/utils.py` | 660 | `p.imap_unordered(...)` at `src/core.py:579` |
| `merge_files_by_chromosome` | `src/utils.py` | 978 | `pool.map(...)` at `src/utils.py:1157` |

### CLI entry point

| Function | File | Line | Invoked from |
|---|---|---|---|
| `run` | `marine.py` | 285 | `if __name__ == "__main__"` block in `marine.py` (via argparse) |

### Dynamic dispatch presence

`grep -n "globals()\|getattr\|eval(\|exec(\|importlib\|__import__"` across the four files returned **zero matches** at audit time. Recorded as assumption A-13.

### Module-level `__all__` declarations

`grep -n "^__all__"` across the four files returned **zero matches**. The audit treats every top-level function name as potentially-public — see assumption A-14.
