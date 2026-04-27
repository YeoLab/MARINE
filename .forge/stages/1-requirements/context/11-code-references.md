# Code References

All paths are absolute. Line numbers are from the current `brian_dev` branch state.

## Bug Locations

### C1: marine2.py dead code
- **File**: `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine2.py`
- **Action**: Delete via `git rm marine2.py`
- **Confirmed not imported**: `grep -r 'marine2' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/` → only self-references

### C2: start_time NameError
- **File**: `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py`
- **Bug lines** (usage without definition inside run()):
  - Line 378: `zero_edit_found(..., start_time, ...)`
  - Line 411: `zero_edit_found(..., start_time, ...)`
  - Line 446: `f'time_elapsed_seconds\t{time.time()-start_time:.2f}s\n'`
  - Line 449: `f'Time elapsed: {time.time()-start_time:.2f}s'`
- **Definition location** (wrong — in __main__ not run()):
  - Line 652: `start_time = time.time()`
- **Fix**: Insert `start_time = time.time()` as first line of `run()` body (before line 292)

### C3: cores NameError in Pool
- **File**: `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py`
- **Bug line**: Line 279: `with Pool(processes=cores) as pool:`
- **Function signature** (line 214):
  `def generate_and_split_bed_files_for_all_positions(output_folder, bam_filepaths, tabulation_bed=None, processes=4, output_suffix="all_cells"):`
- **Fix**: Change `Pool(processes=cores)` to `Pool(processes)`
- **Call site** (line ~464): Uses default `processes=4`

### C4: format() TypeError
- **File**: `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py`
- **Bug line**: Line 663:
  `output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)`
- **Fix**: Change to:
  `output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig)`
- **Function**: `get_coverage_wrapper(parameters)` starting at line 660

### H5: get_intervals off-by-one
- **File**: `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py`
- **Bug line**: Line 440: `end == contig_length`  (comparison, not assignment)
- **Fix**: Change to: `end = contig_length`
- **Function**: `get_intervals(contig, contig_lengths_dict, interval_length=2000000)`
  starting at line 425
- **Context** (lines 438-446):
  ```python
  while start < contig_length:
      if end > contig_length:
          end == contig_length  # BUG: should be end = contig_length
      interval = [start, end]
      ...
  ```

### M2/C9: tracemalloc placement
- **File**: `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py`
- **Bug lines** (in __main__, AFTER run() call):
  - Line 652: `start_time = time.time()` — remove from here
  - Line 653: `tracemalloc.start()` — remove from here, move into run()
- **Usage** (inside run(), before start()):
  - Line 440: `current, peak = tracemalloc.get_traced_memory()`

## Test File

- **File**: `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests/unittests.py`
- **Existing class**: `TestReadProcessFunctions(unittest.TestCase)` (6 test methods)
- **Sys.path setup** (lines 4-7):
  ```python
  directory_path = os.path.abspath(os.path.join('../src/'))
  if directory_path not in sys.path:
      sys.path.append(directory_path)
  ```
- **Existing imports available**: `from utils import get_contig_lengths_dict` (utils already importable)
- **New import needed**: `from utils import get_intervals` — no new sys.path manipulation needed

## Verification Commands (from project.json)

- Unit tests: `cd tests && python -m pytest unittests.py -v`
- Integration tests: `cd tests && bash integration_tests_run.sh python`
