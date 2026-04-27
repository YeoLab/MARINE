# Business Logic

## Bug-by-Bug Fix Specification

### C1: Delete marine2.py

**File**: `marine2.py` (repo root)
**Action**: `git rm marine2.py`
**Why safe**: Not imported anywhere. Not referenced in `.github/workflows/main.yml`.
Not mentioned in `tests/`. Not in `src/__init__.py`. Not documented in README.

---

### C2: start_time NameError in run()

**File**: `marine.py`
**Bug**: `start_time` is defined only in `__main__` (line 652) but is used inside `run()`
at lines 378, 411, 446, 449. When `run()` is called programmatically, `start_time` is not
defined, causing `NameError`.

**Fix**:
1. Add as first two lines inside `run()` function body:
   ```python
   start_time = time.time()
   tracemalloc.start()
   ```
2. Remove `start_time = time.time()` from `__main__` block (was at line 652)
3. Remove `tracemalloc.start()` from `__main__` block (was at line 653)

**Placement**: Before the `logging_folder` line (which is currently the first line of `run()`).

---

### C3: cores NameError in generate_and_split_bed_files_for_all_positions()

**File**: `marine.py`, line ~279
**Bug**: `Pool(processes=cores)` references `cores`, which is not a parameter of
`generate_and_split_bed_files_for_all_positions()`. The function signature has `processes`
as the relevant parameter (default=4).

**Fix**: Change `Pool(processes=cores)` to `Pool(processes)`.
No other changes needed. The `processes` parameter is already threaded through from the call
site.

**Call site** (marine.py line ~464): The call does not pass a process count, so `processes=4`
default is used, which is correct.

---

### C4: format() TypeError in get_coverage_wrapper()

**File**: `src/utils.py`, line 663
**Bug**: `'{}/coverage/{}.tsv'.format(output_folder, contig, header=False)`
`.format()` on a string does not accept keyword arguments like `header`. This was likely
a copy-paste artifact from a `pd.DataFrame.to_csv()` call that does accept `header=False`.

**Fix**: Change to `'{}/coverage/{}.tsv'.format(output_folder, contig)`.
The `header=False` served no purpose in the format call; the output filename is unaffected.

---

### H5: get_intervals off-by-one (comparison vs assignment)

**File**: `src/utils.py`, line 440
**Bug**: `end == contig_length` is a comparison expression that evaluates to True/False and
is immediately discarded. The intent is to clamp `end` to `contig_length` when the window
extends past the contig end.

**Fix**: Change `end == contig_length` to `end = contig_length`.

**Logic after fix**: When `end > contig_length`, set `end = contig_length` so the last
interval is `[start, contig_length]` instead of `[start, start + interval_length]`.

---

### M2/C9: tracemalloc.start() placement

**File**: `marine.py`
**Bug**: `tracemalloc.start()` is called in `__main__` AFTER `run()` returns, so
`tracemalloc.get_traced_memory()` inside `run()` is called before `tracemalloc` is started.
This returns `(0, 0)` for current and peak memory.

**Fix**: Move `tracemalloc.start()` to inside `run()` as its second statement (after
`start_time = time.time()`). Remove from `__main__`.
