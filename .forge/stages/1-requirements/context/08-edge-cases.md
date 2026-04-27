# Edge Cases

## get_intervals() (H5 fix)

### EC-1: Contig length exactly divisible by interval_length
- Input: `contig_length=60, interval_length=30`
- Expected: `[[0, 30], [30, 60]]`
- Risk: The `if end > contig_length` branch never fires, so the fix does not interfere
- Verify: `get_intervals('c', {'c': 60}, 30)` == `[[0, 30], [30, 60]]`

### EC-2: Contig shorter than interval_length
- Input: `contig_length=100, interval_length=2000000`
- Expected: `[[0, 100]]` (single interval, clipped to contig_length)
- Current handling: `if interval_length > contig_length: interval_length = contig_length`
  at top of function handles this correctly already
- Verify: `get_intervals('c', {'c': 100}, 2000000)` == `[[0, 100]]`

### EC-3: Last interval partial (most common case)
- Input: `contig_length=100, interval_length=30`
- Expected: `[[0, 30], [30, 60], [60, 90], [90, 100]]`
- The fix must make this work
- Verify: `r[-1][1] == 100`

### EC-4: Single-base contig
- Input: `contig_length=1, interval_length=30`
- Expected: `[[0, 1]]`
- After fix: works via the `if interval_length > contig_length` guard at function top

## tracemalloc (M2/C9 fix)

### EC-5: run() called multiple times
- `tracemalloc.start()` can be called multiple times without error (Python stdlib behavior)
- If needed, guard with `if not tracemalloc.is_tracing()` but preference is to not add
  conditional branches (A-2 assumption: harmless re-call)

### EC-6: Zero-edit code path
- Lines 377-379 and 410-412 call `zero_edit_found(..., start_time, ...)` and `return`
- `start_time` must be defined before these lines execute
- The fix places `start_time = time.time()` as the first statement in `run()`, so both
  early-return paths are covered

## Pool parallelism (C3 fix)

### EC-7: processes parameter passed explicitly at call site
- Confirmed via reading marine.py line 464: call uses default `processes=4`
- If a future caller passes `processes=64`, the Pool will now correctly use 64 workers
  (previously it would crash with NameError)

## get_coverage_wrapper (C4 fix)

### EC-8: output_folder or contig contains special characters
- The format string `'{}/coverage/{}.tsv'.format(output_folder, contig)` is unchanged
  except for removing the invalid keyword argument
- Special characters in paths are handled exactly as before
