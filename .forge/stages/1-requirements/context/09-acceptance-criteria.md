# Acceptance Criteria (Detailed)

## C1: marine2.py deleted

**AC-1**: File `marine2.py` does not exist at the repo root.
- Verification: `ls /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine2.py` →
  `No such file or directory`
- Alternative: `git status` shows `marine2.py` as deleted

## C2: start_time defined in run()

**AC-2**: `run()` in `marine.py` has `start_time = time.time()` as the first statement
in the function body (before the `logging_folder = ...` line that was previously first).
- Verification: `grep -n 'start_time = time.time()' marine.py` shows a line number inside
  `run()` (not in `__main__`)

**AC-4**: `start_time = time.time()` does NOT appear in `__main__` block.
- Verification: The only `start_time = time.time()` in `marine.py` is inside `run()`

## C3: tracemalloc moved into run()

**AC-3**: `tracemalloc.start()` appears inside `run()` and not in `__main__`.
- Verification: `grep -n 'tracemalloc.start' marine.py` → shows a line inside `run()`
  function, not after the `if __name__ == '__main__':` line

## C3: Pool uses processes not cores

**AC-5**: `Pool(processes)` appears in `generate_and_split_bed_files_for_all_positions()`.
- Verification: `grep 'Pool(processes' marine.py` → matches `Pool(processes)` or
  `Pool(processes=processes)`, not `Pool(processes=cores)`

## C4: get_coverage_wrapper filename construction

**AC-6**: Line 663 of `src/utils.py` reads exactly:
  `output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig)`
- Verification: `grep 'header=False' src/utils.py` → no match on the format line

## H5: get_intervals off-by-one

**AC-7**: Line 440 of `src/utils.py` reads `end = contig_length` (assignment).
- Verification: `grep 'end == contig_length' src/utils.py` → no match

**AC-9**: `get_intervals('chr1', {'chr1': 100}, 30)[-1][1] == 100`
- Verification: Run the one-liner in the Verification Environment table

**AC-10**: `get_intervals('chr1', {'chr1': 60}, 30) == [[0, 30], [30, 60]]`

## Tests

**AC-8**: `cd tests && python -m pytest unittests.py -v` exits 0, ≥9 tests collected.

## Integration

**AC-11**: `cd tests && bash integration_tests_run.sh python` exits 0.
