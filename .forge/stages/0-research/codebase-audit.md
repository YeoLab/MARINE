# Codebase Audit: MARINE
<!-- Generated: 2026-04-24 -->

## Summary Scores
- Critical findings: 4
- High findings: 6
- Medium findings: 8
- Low findings: 5

---

## Critical Findings

### C1: `marine2.py` is an undocumented parallel implementation
**File**: `marine2.py`
**Issue**: A second CLI entrypoint exists alongside `marine.py` with different function signatures (e.g., `reverse_stranded` vs `strandedness` param, `num_intervals_per_contig` vs `interval_length`). It is not tested, not in CI, and not mentioned in the README. It represents significant dead/experimental code that could confuse contributors and cause divergence.
**Severity**: Critical
**Impact**: Maintenance burden, confusion about canonical entry point, potential for silent behavioral differences.

### C2: `start_time` used before definition in `marine.py:run()`
**File**: `marine.py`, line ~378 and ~411
**Issue**: `zero_edit_found(... start_time ...)` is called in two places inside `run()`, but `start_time` is never defined within `run()` — it is only defined in `__main__` block. This would raise a `NameError` in any programmatic (non-CLI) use of the `run()` function.
**Severity**: Critical
**Impact**: `run()` cannot be used as a library function; any call that hits the zero-edit path will crash.

### C3: `cores` referenced in `generate_and_split_bed_files_for_all_positions()` but not passed as parameter
**File**: `marine.py`, line ~279
**Issue**: `Pool(processes=cores)` is called inside `generate_and_split_bed_files_for_all_positions()` but `cores` is not in the function signature — it would use whatever `cores` is in the enclosing scope at call time (or raise a `NameError`).
**Severity**: Critical
**Impact**: Runtime crash when `--all_cells_coverage` flag is used.

### C4: `get_coverage_wrapper` has syntax error in output filename
**File**: `src/utils.py`, line ~663
**Issue**: `output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)` — `.format()` does not accept `header` as a keyword argument. This raises a `TypeError` at runtime in any code path using `run_coverage_calculator()`.
**Severity**: Critical
**Impact**: Bulk paired-end coverage calculation path crashes immediately.

---

## High Findings

### H1: Unit test coverage is minimal — only 6 tests for one module
**Files**: `tests/unittests.py`
**Issue**: Only `read_process.py` has any unit tests (6 tests). `core.py`, `utils.py`, `annotate.py`, and `marine.py` have zero unit tests. All testing relies on integration tests.
**Severity**: High
**Impact**: Regressions in core logic (coverage calculation, BAM merging, SAILOR score, bedgraph generation) go undetected until integration tests run.

### H2: `utils.py` is a god module (1,536 lines, 53+ functions)
**File**: `src/utils.py`
**Issue**: Mixes: BAM I/O, coverage calculation, file merging, sparse matrix operations, SAILOR scoring, bedgraph generation, progress printing, interval logic, subprocess management. No internal organization (no classes, no sub-modules, no sections).
**Severity**: High
**Impact**: Hard to navigate, test, or refactor. High coupling between unrelated functions.

### H3: Bash subprocess used for critical merge step
**File**: `src/utils.py:generate_and_run_bash_merge()`
**Issue**: A critical data-merging step (joining edit info with depth info) generates and runs a bash script using `join`, `awk`, and `sort`. This is platform-dependent (different `sort` behavior on macOS vs Linux), hard to test, and silently succeeds even with incorrect joins.
**Severity**: High
**Impact**: Silent data corruption risk on non-Linux platforms; untestable without file fixtures.

### H4: `fill_value=0` in `annotate_sites` may silently overwrite valid annotations
**File**: `src/annotate.py`, line ~59
**Issue**: `annotation_intersect['feature_name'].fillna("noname", inplace=True)` uses deprecated `inplace=True` with `fillna`. Also `annotation_intersect.replace(-1, '.')` globally replaces all -1 values, including potential valid numeric scores.
**Severity**: High
**Impact**: FutureWarning in newer pandas; potential annotation corruption.

### H5: `get_intervals()` has a dead code branch that never executes correctly
**File**: `src/utils.py`, line ~440
**Issue**: `end == contig_length` is a comparison (returns bool), not an assignment — the interval end is never corrected, so the last interval always extends past the actual contig end. pysam handles this gracefully by clamping, but the intent is clearly a bug.
**Severity**: High
**Impact**: Last interval in each contig includes positions beyond the contig end (pysam silently handles this but it wastes processing effort and could cause issues with different reference versions).

### H6: `CB_N = 1` is hardcoded with no configurability
**File**: `src/utils.py`, line ~24
**Issue**: The suffix granularity for BAM splitting (CB_N=1 → 4 buckets; CB_N=2 → 16 buckets) is hardcoded. The `number_of_expected_bams` parameter in several functions is overridden to `4**CB_N` for CB tag, making the parameter effectively dead for the most common use case.
**Severity**: High
**Impact**: Users with very large single-cell datasets have no way to increase parallelism or reduce memory via this mechanism without editing source code.

---

## Medium Findings

### M1: No type annotations throughout the codebase
**All files**: No function signatures have type hints.
**Severity**: Medium
**Impact**: IDE support is poor; refactoring is risky.

### M2: `tracemalloc` started in `__main__` but `get_traced_memory()` called inside `run()`
**File**: `marine.py`
**Issue**: `tracemalloc.start()` is called in `__main__` after `run()` has already been called. `get_traced_memory()` inside `run()` will return (0, 0) or raise if called before start. (Actually in the current code, `start()` is after the `run()` call, so memory tracking never works.)
**Severity**: Medium
**Impact**: Memory profiling is broken.

### M3: Deprecated pandas API usage
**File**: `src/annotate.py`: `fillna(inplace=True)`, `src/utils.py`: multiple `pd.DataFrame` operations
**Issue**: `inplace=True` on chained operations raises FutureWarning in pandas >= 2.0.
**Severity**: Medium
**Impact**: Future pandas upgrades will break these calls.

### M4: No input validation for BAM file existence or index
**File**: `marine.py`
**Issue**: No check that the input BAM file exists or has a `.bai` index before starting. Error surfaces deep in pysam with an opaque message.
**Severity**: Medium
**Impact**: Poor user experience for common errors.

### M5: Integration tests are shell-script based with no assertions on file content
**File**: `tests/integration_tests_run.sh`
**Issue**: Integration tests run the tool and check exit code but do not assert on output file contents (number of sites, coverage values, etc). The `integration_tests_auto_check.py` does check adatas but only for shape consistency.
**Severity**: Medium
**Impact**: Regression in output values (wrong edit calls, wrong counts) would not be caught by CI.

### M6: `marine2.py` imports `read_process`, `utils`, `core`, `annotate` without `src.` prefix
**File**: `marine2.py`
**Issue**: Relies on implicit sys.path manipulation from running in the src/ directory, unlike `marine.py` which uses `sys.path.append`. This means `marine2.py` only works from specific working directories.
**Severity**: Medium

### M7: `write_reads_to_file` uses `sys.stdout.err` (non-existent method)
**File**: `src/utils.py`, line ~764
**Issue**: `sys.stdout.err(...)` is not a valid Python method. This error-handling path would raise an `AttributeError` instead of the intended error message on bad read write failures.
**Severity**: Medium
**Impact**: Error messages on write failures are silently swallowed or replaced with confusing AttributeError.

### M8: `get_sailor_sites` mutates the input dataframe with `['start']` and `['end']` column additions
**File**: `src/utils.py`
**Issue**: Adds columns to the passed-in dataframe in-place without copying. Callers downstream that use the original dataframe may see unexpected new columns.
**Severity**: Medium

---

## Low Findings

### L1: `marine.py` imports `os` twice
**File**: `marine.py`, lines 7 and 22
**Severity**: Low

### L2: `annotate.py` imports `pybedtools` twice
**File**: `src/annotate.py`, lines 1 and 3
**Severity**: Low

### L3: Commented-out debugging code throughout codebase
**Multiple files**: `core.py` has several `#print(...)` blocks and `pass` in verbose branches
**Severity**: Low

### L4: `check_read(read)` stub function always returns True
**File**: `src/utils.py`, line ~524
**Issue**: Empty function with no implementation, never called.
**Severity**: Low

### L5: `generate_empty_matrix_file` stub function
**File**: `src/utils.py`, line ~929
**Issue**: Empty function body with just `pass`.
**Severity**: Low

---

## Question Priority Implications
- **Round 1**: C1 (marine2.py), C2 (run() NameError), C3 (cores NameError), C4 (format TypeError)
- **Round 1-2**: H1 (test coverage), H2 (utils refactor), H3 (bash merge), H5 (interval bug)
- **Round 2-3**: H4 (annotation), H6 (CB_N), M2 (tracemalloc), M5 (integration tests)
- **Round 3+**: Remaining medium/low findings, new features, scalability
