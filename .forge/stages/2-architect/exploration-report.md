# Exploration Report: MARINE Bug Fixes

Generated: 2026-04-25
Mode: focused (bug fixes — scope is precisely 5 named bugs + tracemalloc move + tests)

## 1. Files Requiring Modification

| File | Modification | Confirmed Lines |
|------|-------------|-----------------|
| `marine.py` | Insert two lines at start of `run()`; fix `Pool` call; remove two lines from `__main__` | 279, 285-292, 652-653 |
| `src/utils.py` | Two single-token fixes | 440, 663 |
| `marine2.py` | Delete file | entire file |
| `tests/unittests.py` | Add new unit tests | append after line 75 (before `unittest.main()`) |

## 2. Verified Source Locations

### marine.py:279 — C3 fix site
```python
# Run the processing with multiprocessing
with Pool(processes=cores) as pool:    # `cores` is undefined in this scope
    pool.map(process_combination_for_split, combinations)
```
Function signature (line 214) declares `processes=4`. The call site (line 464ish) does not pass an explicit count — uses default. **Verified**: replacing `processes=cores` with `processes=processes` (or positional `processes`) is safe.

### marine.py:285-292 — C2 fix site
```python
def run(bam_filepath, ..., tabulation_bed=None
       ):
        
    logging_folder = "{}/metadata".format(output_folder)
```
The first executable line of `run()` is `logging_folder = ...` (line 292). Insertion point is between line 290 (`):`) and line 292.

### marine.py:652-653 — C2/M2 fix site (removal)
```python
start_time = time.time()
tracemalloc.start()

run(bam_filepath, ...)
```
Both lines must be deleted from `__main__` after being moved into `run()`. No subsequent references to `start_time` in `__main__` (verified by reading lines 654-682).

### src/utils.py:440 — H5 fix site
```python
while start < contig_length:
    if end > contig_length:
        end == contig_length    # BUG: comparison, should be `end = contig_length`
    interval = [start, end]
    ...
```
Pure single-character fix.

### src/utils.py:663 — C4 fix site
```python
output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)
```
Pure delete-3-tokens fix: remove `, header=False`.

## 3. Existing Patterns (must follow)

- **Test framework**: `unittest.TestCase` subclass; `unittest.main()` at bottom of file. No pytest fixtures. (`tests/unittests.py:14, 77`)
- **Sys.path setup for tests**: `sys.path.append(os.path.abspath('../src/'))` already done at top of `unittests.py`. `from utils import X` works.
- **String formatting**: `marine.py` `run()` body uses `.format()` (e.g., line 292, 295). `__main__` block uses f-strings (e.g., line 446-449). For C4 fix in `src/utils.py:get_coverage_wrapper`, the surrounding code uses `.format()` (line 663 itself) — keep `.format()` style.
- **Imports already available**: `marine.py` imports `time`, `tracemalloc`, `multiprocessing.Pool`. `src/utils.py` requires no new imports for C4/H5. `tests/unittests.py` already has `from utils import get_contig_lengths_dict` — adding `get_intervals` is just a name addition.

## 4. Integration Points / Data Flow

- `run()` is called by:
  - `__main__` block in `marine.py` (line 655) — only caller
  - Programmatic library usage (the C2 bug breaks this; no current internal callers exist)
- `generate_and_split_bed_files_for_all_positions()` is called by:
  - `marine.py` line ~464 (inside `run()`) — single caller, uses default `processes=4`
- `get_intervals()` is called by:
  - `src/core.py:edit_finder()` — passes `interval_length` from `run()`'s parameter
- `get_coverage_wrapper()` is called by:
  - `src/utils.py` itself, inside coverage processing pipeline (Pool.map workers)

## 5. Constraints Identified

- **No new imports** (NFR-5).
- **Surgical changes only** (CLAUDE.md, NFR-4): line-count of diff must be minimal.
- **Test framework: unittest only**; no pytest decorators.
- **`unittest.main()` placement**: must remain final statement of `tests/unittests.py`.
- **Style match**: `.format()` in older functions, f-strings only in newer code. Each fix matches its local context.
- **CI uses conda + integration tests**: must not break `.github/workflows/main.yml`.

## 6. Patterns to Preserve

- Function-level docstrings (do not edit).
- Existing print/log statements (no removal).
- Existing comment blocks adjacent to bug lines (no edits).
- Trailing blank-line conventions.

## 7. Risk Areas

| Risk | Severity | Mitigation |
|------|----------|------------|
| `tracemalloc.start()` placed at top of `run()` may interfere if tests/integration call `run()` repeatedly | Low | Python stdlib allows multiple `start()` calls without error (A-2) |
| Removing `start_time = time.time()` from `__main__` could break unobserved CLI logging | Low | Verified: no post-`run()` reference exists at lines 654-682 |
| `Pool(processes)` change could shift behavior if a future caller passes explicit kwarg | Low | Existing call at line 464 uses default — no behavioral change today |
| Integration tests must still pass | High | Run `bash integration_tests_run.sh python` as the final gate |
| Tests using `os.path.join('../src/')` are CWD-dependent | Medium | Existing constraint; honor by running tests from `tests/` directory only |

## 8. Hotspot Notes

`.forge/hotspot/hotspots.json` does not exist — no churn-based risk overrides applied.

## 9. Conflicts Resolution Notes

`.forge/stages/0-research/conflicts-resolved.md` does not exist. No prior-decided trade-offs to honor; all decisions in this stage are fresh.

## 10. Key Findings (Top 3)

1. **Bug-fix scope is unambiguous**: every fix has confirmed file, line number, and exact replacement. No ambiguity in the requirements package; design degrees of freedom are limited to test placement and a small set of minor stylistic choices.
2. **No code re-architecture needed**: All five bugs are local single-line/single-block edits. The "architecture" is mostly a test-design decision (where to put new unit tests) and a sequencing decision (in what order to apply edits to keep integration tests green between commits).
3. **Risk concentration is in integration tests, not unit tests**: New unit tests are pure-Python arithmetic over a contig-length dict; they cannot regress. The real gate is `tests/integration_tests_run.sh python` continuing to exit 0.
