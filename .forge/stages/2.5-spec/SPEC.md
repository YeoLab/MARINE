# Specification: MARINE Bug Fixes (C1-C4 + H5 + Tracemalloc + Tests) + Documentation & Cleanup
<!-- FORGE_STAGE: 2.5-spec -->
<!-- SOURCE: .forge/stages/2-architect/architecture-plan.md -->
<!-- UPDATED_UTC: 2026-04-25T15:10:00Z -->

## Overview

This specification covers two sequentially executed work packages on the MARINE RNA-editing detection pipeline.

**Package A (tasks 1-9)** fixes five confirmed defects (C1: dead `marine2.py` file; C2: `start_time` NameError in `__main__`; C3: `Pool(processes=cores)` NameError; C4: invalid `header=False` kwarg in a `.format()` call; H5: off-by-one in `get_intervals` last window) plus M2 (move `tracemalloc.start()` into `run()`) and adds unit tests covering every changed code path. Source-code diff is bounded at 12 added/modified lines plus one whole-file deletion plus ~80 lines of additive test code. No architectural change, no new dependencies, no signature changes.

**Package B (tasks 10-12)** adds Google-style docstrings to every top-level function in `marine.py`, `src/core.py`, `src/utils.py`, and `src/read_process.py` (96 functions inventoried at architect time), then performs a conservative read-only audit identifying genuinely unused functions, then surgically removes only the post-human-review confirmed candidates. The split between task-11 (analysis, read-only) and task-12 (action, deletion) is a mandatory human-review halt — the build agent MUST pause for human confirmation between these tasks. Specific functions targeted for removal are determined at runtime by the audit and are intentionally NOT enumerated in this specification (see Decision Register entry D-11 in the architecture plan: uncertainty defaults to KEEP).

## Acceptance Criteria

### AC-001: Delete marine2.py from the repository
**Source:** FR-1; task-01

**Given** the MARINE repository at HEAD on branch `brian_dev` contains the file `marine2.py` at the repository root
**When** task-01 completes
**Then** the file `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine2.py` does not exist on disk and `git status` reports it as a staged deletion

**Verification:** Shell check `test ! -e marine2.py` plus `git status --short | grep "^D  marine2.py"` plus existing unit suite (6 tests) and integration suite both exit 0
**Priority:** P0

### AC-002: Move start_time assignment into run() body
**Source:** FR-2; task-08

**Given** `marine.py` defines a function `run(...)` and currently assigns `start_time = time.time()` only in the `__main__` block
**When** task-08 completes
**Then** `start_time = time.time()` appears exactly once in `marine.py`, located as an executable statement inside the `run()` function body, with a 4-space indent

**Verification:** `grep -c '^    start_time = time.time()' marine.py` returns exactly `1`; `grep -c 'start_time = time.time()' marine.py` returns exactly `1`; static-source unit test `test_marine_run_starts_time_at_top` passes
**Priority:** P0

### AC-003: Move tracemalloc.start() into run() body
**Source:** FR-3; task-08

**Given** `marine.py` currently calls `tracemalloc.start()` only in the `__main__` block
**When** task-08 completes
**Then** `tracemalloc.start()` appears exactly once in `marine.py`, located as the second executable statement inside the `run()` function body (immediately after `start_time = time.time()`), with a 4-space indent

**Verification:** `grep -c '^    tracemalloc.start()' marine.py` returns exactly `1`; `grep -c 'tracemalloc.start()' marine.py` returns exactly `1`; `inspect.getsource(marine.run)` contains `tracemalloc.start()`
**Priority:** P0

### AC-004: Remove start_time and tracemalloc.start from __main__
**Source:** FR-4; task-08

**Given** the pre-task-08 `__main__` block in `marine.py` contains `start_time = time.time()` and `tracemalloc.start()` immediately before the call to `run(...)`
**When** task-08 completes
**Then** neither `start_time = time.time()` nor `tracemalloc.start()` appears in the `__main__` block of `marine.py` (each occurs exactly once total in the file, both inside `run()`)

**Verification:** `python -c "import sys; sys.path.insert(0, '<repo>'); import marine"` does not raise; `grep -c 'start_time = time.time()' marine.py` equals `1`; `grep -c 'tracemalloc.start()' marine.py` equals `1`
**Priority:** P0

### AC-005: Pool uses the processes function parameter
**Source:** FR-5; task-06

**Given** `marine.py` line 279 currently reads `with Pool(processes=cores) as pool:` (where `cores` is undefined inside `generate_and_split_bed_files_for_all_positions`)
**When** task-06 completes
**Then** line 279 reads `    with Pool(processes) as pool:` exactly (positional argument, 4-space indent)

**Verification:** `grep -n 'with Pool(processes) as pool:' marine.py` matches; `grep 'Pool(processes=cores)' marine.py` returns no match; static-source test `test_marine_pool_uses_processes_param` passes
**Priority:** P0

### AC-006: Drop header=False from get_coverage_wrapper .format call
**Source:** FR-6; task-05

**Given** `src/utils.py` line 663 currently reads `output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)`
**When** task-05 completes
**Then** line 663 reads `    output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig)` exactly (no `header=False` kwarg)

**Verification:** `grep "header=False" src/utils.py | grep "\.format"` returns no match; static-source test `test_get_coverage_wrapper_no_header_kwarg` passes
**Priority:** P0

### AC-007: get_intervals last window ends at contig_length
**Source:** FR-7; task-04

**Given** `src/utils.py` line 440 currently reads `            end == contig_length` (comparison, no-op)
**When** task-04 completes
**Then** line 440 reads `            end = contig_length` (assignment), and `get_intervals('chr1', {'chr1': 100}, 30)` returns `[[0, 30], [30, 60], [60, 90], [90, 100]]`

**Verification:** `grep -n 'end = contig_length' src/utils.py` matches at line 440; `grep 'end == contig_length' src/utils.py` returns no match; unit test `test_get_intervals_partial_last_window` passes
**Priority:** P0

### AC-008: New unit tests pass after fixes
**Source:** FR-8, FR-9, FR-10, FR-11, NFR-1; tasks 02, 03, 07

**Given** `tests/unittests.py` after tasks 02, 03, and 07 contains the new `TestUtilsFunctions` class with six test methods (`test_get_intervals_partial_last_window`, `test_get_intervals_exact_division`, `test_get_intervals_short_contig`, `test_get_coverage_wrapper_no_header_kwarg`, `test_marine_run_starts_time_at_top`, `test_marine_pool_uses_processes_param`)
**When** task-08 completes and `cd tests && python -m pytest unittests.py -v` is run
**Then** the command exits with code 0 and at least 12 tests are collected and pass (6 pre-existing in `TestReadProcessFunctions` + 6 new in `TestUtilsFunctions`)

**Verification:** `cd tests && python -m pytest unittests.py -v` exits 0; pytest summary line shows >= 12 passed
**Priority:** P0

### AC-009: get_intervals invariant on partial-last-window contig
**Source:** FR-8, FR-9; tasks 02, 04

**Given** the post-fix `get_intervals` function is called with `contig='chr1'`, `contig_lengths_dict={'chr1': 100}`, `interval_length=30`
**When** the function returns
**Then** the returned list equals `[[0, 30], [30, 60], [60, 90], [90, 100]]` and `result[-1][1]` equals `100` (the contig length, not 120)

**Verification:** Unit test `TestUtilsFunctions::test_get_intervals_partial_last_window` passes; runs in under 1 second
**Priority:** P0

### AC-010: get_intervals invariant on exact-division and short-contig cases
**Source:** FR-11; task-02, task-04

**Given** the post-fix `get_intervals` function is called with (a) `contig_lengths_dict={'chr1': 60}`, `interval_length=30`, and (b) `contig_lengths_dict={'chr1': 100}`, `interval_length=2000000`
**When** the function returns
**Then** case (a) returns exactly `[[0, 30], [30, 60]]` and case (b) returns exactly `[[0, 100]]`

**Verification:** Unit tests `test_get_intervals_exact_division` and `test_get_intervals_short_contig` pass; each runs in under 1 second
**Priority:** P0

### AC-011: Integration test gate passes after Package A
**Source:** NFR-2; task-09

**Given** all Package A tasks (01-08) are complete and the working tree is in the post-fix state
**When** `cd tests && bash integration_tests_run.sh python` is executed
**Then** the script exits with code 0 and `git status --short` shows only the expected staged set (`marine2.py` deleted; `marine.py`, `src/utils.py`, `tests/unittests.py` modified; nothing else)

**Verification:** Integration script exit code 0; `git status --short | grep -vE "^(D  marine2\.py|.M (marine\.py|src/utils\.py|tests/unittests\.py))$"` returns no lines
**Priority:** P0

### AC-012: Every function in the four target files has a Google-style docstring
**Source:** FR-12; task-10

**Given** the four target files `marine.py`, `src/core.py`, `src/utils.py`, `src/read_process.py` after task-10 completes
**When** the following AST check is executed:
```python
import ast
for path in ['marine.py', 'src/core.py', 'src/utils.py', 'src/read_process.py']:
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert ast.get_docstring(node) is not None, f'{path}::{node.name}'
```
**Then** the script exits with code 0 (every `FunctionDef` and `AsyncFunctionDef` returns a non-None docstring), AND `git diff -U0 marine.py src/core.py src/utils.py src/read_process.py | grep '^-' | grep -v '^---' | grep -vE '^-\s*("""|\s*$)' | wc -l` returns `0` (zero non-docstring deletions), AND no new `import` or `from` lines were introduced in any of the four files

**Verification:** AST traversal script exits 0; `git diff --stat` shows changes only in the four target files; `git diff -U0 ... | grep '^-' | grep -v '^---' | grep -vE '^-\s*(""")' | wc -l` returns 0; full unit + integration suites pass
**Priority:** P1

### AC-013: Audit JSON is valid and conservatively classifies every function
**Source:** FR-13; task-11

**Given** task-10 has completed and the four target files are in their post-docstring state
**When** task-11 produces `.forge/stages/2-architect/unused-functions-audit.json`
**Then** the JSON file (a) parses as valid JSON, (b) contains a `functions` array with one entry per top-level `def` in the four files (96 at architect time; halt-and-report if drift), (c) every entry has at least one `evidence[]` item, (d) every REMOVE_CANDIDATE entry has a non-null `removal_note` string explaining what the function does and why removal is judged safe, (e) `function_count_keep + function_count_remove_candidate == function_count_total`, (f) all six known Pool workers (`get_unique_barcodes_for_reads_in_bamfile`, `process_combination_for_split`, `find_edits_and_split_bams_wrapper`, `concat_and_write_bams_wrapper`, `get_coverage_wrapper`, `merge_files_by_chromosome`) are classified KEEP with `pool_worker` rule in their evidence, (g) the CLI entry `run` is classified KEEP with `cli_entry_point` rule in its evidence, (h) NO source `.py` files are modified by this task (`git status` shows only the new audit JSON as added)

**Verification:** `python -c "import json; data=json.load(open('.forge/stages/2-architect/unused-functions-audit.json')); ..."` validates schema and counts; `git status --short` excludes any `.py` file under `marine.py` or `src/`; existing unit + integration suites still pass after task-11
**Priority:** P1

### AC-014: Post-cleanup public-API regression net protects KEEP functions
**Source:** FR-13, FR-14; task-12

**Given** task-11 has completed, the audit JSON has been read by a human reviewer (mandatory halt — see TASKS.md `HUMAN-REVIEW-HALT` block), and any reviewer-vetoed REMOVE_CANDIDATE entries have been downgraded to KEEP in the JSON before task-12 starts
**When** task-12 runs and deletes only the post-review REMOVE_CANDIDATE functions
**Then** (a) every name still classified KEEP in the post-review audit JSON is still importable via `hasattr(<module>, <name>)` for its module, verified by the new `TestPublicAPIPreserved` class added to `tests/unittests.py` containing exactly four test methods (`test_marine_keeps_present`, `test_core_keeps_present`, `test_utils_keeps_present`, `test_read_process_keeps_present`), (b) every name still classified REMOVE_CANDIDATE no longer appears as a `FunctionDef` in its source file, (c) `python -m pyflakes marine.py src/core.py src/utils.py src/read_process.py` introduces zero new warnings versus the pre-task-12 baseline captured at task-12 start, (d) `git diff` shows changes only in the four target source files plus `tests/unittests.py`, (e) all four `TestPublicAPIPreserved` methods together run in under 1 second total

**Verification:** Re-run of the audit script confirms `function_count_remove_candidate == 0` post-deletion; `cd tests && python -m pytest unittests.py::TestPublicAPIPreserved -v` exits 0 in under 1 second wall time; `cd tests && python -m pytest unittests.py -v && bash integration_tests_run.sh python` both exit 0; `python -m pyflakes ...` baseline-vs-post diff shows zero new lines
**Priority:** P1

### AC-015: Mandatory human-review halt between task-11 and task-12
**Source:** Architecture decision D-9, D-10, D-12; ADR ordering constraint added 2026-04-25

**Given** task-11 has produced `unused-functions-audit.json` and printed its summary to stdout
**When** the build agent (or any orchestration) reaches the boundary between task-11 and task-12
**Then** the agent MUST NOT begin task-12 until a human reviewer has explicitly confirmed (via the build skill's interactive prompt or an equivalent gate) that the audit JSON has been reviewed; the agent MUST re-read the audit JSON at the start of task-12 to pick up any human edits (downgrades from REMOVE_CANDIDATE to KEEP); if the post-review REMOVE_CANDIDATE list is empty, task-12 still proceeds to add the `TestPublicAPIPreserved` regression net

**Verification:** TASKS.md contains an explicit `HUMAN-REVIEW-HALT` block between Task-11 and Task-12 listing the required reviewer actions; build skill (`/forge build`) treats task-11 to task-12 as a forced checkpoint pair and halts for explicit confirmation; the implementer-prompt and architecture-plan both document this requirement (verified by `grep -l "human review" .forge/stages/2-architect/`)
**Priority:** P0

### AC-016: Source-code diff stays within the architectural envelope
**Source:** NFR-4, NFR-5, NFR-7; cross-cutting

**Given** Package A tasks (01-09) are complete on the working branch, comparing against the parent of the first Package A commit
**When** `git diff --shortstat <parent>..HEAD -- marine.py src/utils.py` is executed (excluding new tests, the marine2.py deletion, and Package B docstring/cleanup changes)
**Then** the source-code diff for Package A consists of no more than 12 added/modified lines total across `marine.py` and `src/utils.py` combined; no new `import` or `from` statements appear in any source file (`marine.py`, `src/*.py`); no public function signature is altered; no formatter (black/isort/etc.) is invoked

**Verification:** `git diff --shortstat` summed insertions+deletions for source files (excluding tests and marine2.py) <= 12; `diff <(grep -E '^(import|from) ' <files>) <(git show <parent>:<file> | grep -E '^(import|from) ')` returns empty for every source file under Package A scope; signature inspection via `inspect.signature` for changed functions matches pre-fix signatures
**Priority:** P1

### AC-017: Package B touches only the four target source files plus tests/unittests.py
**Source:** NFR-7; cross-cutting (tasks 10, 11, 12)

**Given** Package B tasks (10-12) are complete
**When** `git diff --name-only <parent-of-task-10>..HEAD` is executed
**Then** the changed-file list is a subset of `{marine.py, src/core.py, src/utils.py, src/read_process.py, tests/unittests.py, .forge/stages/2-architect/unused-functions-audit.json}`; `src/annotate.py`, `src/__init__.py`, integration test files, the GitHub workflow, and `marine_environment2.yaml` are unchanged

**Verification:** `git diff --name-only` output diffed against the allowed set returns no extra files; `git diff src/annotate.py tests/integration_tests_run.sh tests/integration_tests_auto_check.py .github/workflows/main.yml marine_environment2.yaml` produces no output
**Priority:** P1

### AC-018: Pool worker functions document their tuple-unpacking contract
**Source:** FR-12, decision D-8; task-10

**Given** the six Pool worker functions (`get_unique_barcodes_for_reads_in_bamfile` in `marine.py:57`, `process_combination_for_split` in `marine.py:159`, `find_edits_and_split_bams_wrapper` in `src/core.py:496`, `concat_and_write_bams_wrapper` in `src/utils.py:867`, `get_coverage_wrapper` in `src/utils.py:660`, `merge_files_by_chromosome` in `src/utils.py:978`) after task-10 completes
**When** the docstring of each is inspected
**Then** the first sentence of each docstring explicitly states that the function is a worker called via `multiprocessing.Pool.map` or `Pool.imap_unordered` (or equivalent Pool dispatch), and names the single tuple-parameter contract that is unpacked inside the function body

**Verification:** `python -c "import inspect; ..."` reads each function's `__doc__` and asserts the first sentence contains both a Pool dispatch reference (e.g., `"Pool.map"`, `"Pool.imap_unordered"`, or `"Pool worker"`) and a tuple-unpacking reference (e.g., `"tuple"`, `"unpacks"`); manual review during task-10 verification step
**Priority:** P2

## Traceability Matrix

| Requirement (architecture-plan.md Section 7) | AC Coverage |
|----------------------------------------------|-------------|
| FR-1 (delete marine2.py) | AC-001 |
| FR-2 (start_time in run) | AC-002 |
| FR-3 (tracemalloc in run) | AC-003 |
| FR-4 (remove start_time from __main__) | AC-004 |
| FR-5 (Pool(processes)) | AC-005 |
| FR-6 (.format C4 fix) | AC-006 |
| FR-7 (end = contig_length) | AC-007 |
| FR-8 (test H5 short contig) | AC-008, AC-009 |
| FR-9 (test H5 length=100, interval=30) | AC-008, AC-009 |
| FR-10 (test C4 filename) | AC-008 |
| FR-11 (test H5 divisible) | AC-008, AC-010 |
| FR-12 (Google-style docstrings on every function in four files) | AC-012, AC-018 |
| FR-13 (Identify and remove genuinely-unused functions) | AC-013, AC-014 |
| FR-14 (Regression test pinning surviving public API) | AC-014 |
| NFR-1 (zero unit-test regression) | AC-008 |
| NFR-2 (integration tests pass) | AC-011 |
| NFR-3 (new tests <1s each) | AC-009, AC-010, AC-014 |
| NFR-4 (minimal diff for source code) | AC-016 |
| NFR-5 (no new imports) | AC-012, AC-016 |
| NFR-7 (surgical changes) | AC-016, AC-017 |
| Architectural ordering constraint (task-11 -> human-review -> task-12) | AC-015 |

Every requirement maps to at least one acceptance criterion.

## Notes on intentional non-enumeration

This specification deliberately does NOT name specific functions as removal targets. The audit in task-11 produces the candidate list at runtime; the human reviewer between task-11 and task-12 either approves or vetoes each candidate. Decision D-11 in the architecture plan establishes "uncertainty defaults to KEEP." Pre-naming functions here would (a) violate that conservative bias by encoding pre-audit guesses into the contract, (b) couple the spec to an inventory snapshot that may be stale, and (c) bypass the human-review halt that AC-015 requires.
