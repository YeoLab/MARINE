# TASK-08: Apply C2 + M2 fix — move start_time and tracemalloc.start() into run()

<!-- DEPENDENCIES: task-07 -->
<!-- COVERS: FR-2, FR-3, FR-4, AC-2, AC-3, AC-4 -->
<!-- BUG: C2, M2 -->

## Goal

Move `start_time = time.time()` and `tracemalloc.start()` from the `__main__` block to the top of the `run()` function body. After this task, the `test_marine_run_starts_time_at_top` test from task-07 turns green and AC-2/AC-3/AC-4 are satisfied.

## Steps

### Step A: Add two lines at top of run() body

1. Open `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py`.
2. Locate line 292:
   ```
       logging_folder = "{}/metadata".format(output_folder)
   ```
3. Insert two new lines BEFORE line 292 (so they become the first executable statements of `run()`). The body of `run()` currently starts at line 292; after this edit it will start at line 294 (the original 292), with two new lines preceding.

   The exact replacement: change the block:
   ```
   def run(bam_filepath, annotation_bedfile_path, output_folder, contigs=[], strandedness=True, barcode_tag="CB", paired_end=False, barcode_whitelist_file=None, verbose=False, coverage_only=False, filtering_only=False, annotation_only=False, bedgraphs_list=[], sailor_list=[], min_base_quality = 15, min_read_quality = 0, min_dist_from_end = 10, max_edits_per_read = None, cores = 64, number_of_expected_bams=4, 
           keep_intermediate_files=False,
           num_per_sublist=6,
           skip_coverage=False, interval_length=2000000,
           all_cells_coverage=False, tabulation_bed=None
          ):
           
       logging_folder = "{}/metadata".format(output_folder)
   ```
   to:
   ```
   def run(bam_filepath, annotation_bedfile_path, output_folder, contigs=[], strandedness=True, barcode_tag="CB", paired_end=False, barcode_whitelist_file=None, verbose=False, coverage_only=False, filtering_only=False, annotation_only=False, bedgraphs_list=[], sailor_list=[], min_base_quality = 15, min_read_quality = 0, min_dist_from_end = 10, max_edits_per_read = None, cores = 64, number_of_expected_bams=4, 
           keep_intermediate_files=False,
           num_per_sublist=6,
           skip_coverage=False, interval_length=2000000,
           all_cells_coverage=False, tabulation_bed=None
          ):
       start_time = time.time()
       tracemalloc.start()

       logging_folder = "{}/metadata".format(output_folder)
   ```
   Notes on whitespace:
   - The two new lines are indented with 4 spaces (matching `logging_folder`'s indentation).
   - There is one blank line between `tracemalloc.start()` and `logging_folder = ...` to keep visual separation.
   - The line immediately after `):` was previously a 4-blank-space line then a blank line; replace the 4-blank-space line with `    start_time = time.time()`. Replace the blank line with `    tracemalloc.start()`. Add a fresh blank line before `    logging_folder`.

### Step B: Remove from __main__

1. Locate lines 652-653 in the (now-shifted) file:
   ```
       start_time = time.time()
       tracemalloc.start()
   ```
   These appear in the `__main__` block, immediately before the `run(bam_filepath,` call.
2. Delete BOTH lines. Also delete the blank line that follows `tracemalloc.start()` if it leaves a double blank line.

   The block:
   ```
       start_time = time.time()
       tracemalloc.start()
       
       run(bam_filepath, 
   ```
   becomes:
   ```
       run(bam_filepath, 
   ```

## Acceptance Criteria

- AC-T08-1: `inspect.getsource(marine.run)` contains `start_time = time.time()` AND `tracemalloc.start()` AND the `start_time` line precedes any `zero_edit_found` reference (verified by task-07's `test_marine_run_starts_time_at_top`).
- AC-T08-2: `start_time = time.time()` appears exactly ONCE in `marine.py` (inside `run()`), not in `__main__`.
- AC-T08-3: `tracemalloc.start()` appears exactly ONCE in `marine.py` (inside `run()`), not in `__main__`.
- AC-T08-4: `python -c "import sys; sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE'); import marine; help(marine.run)"` does not raise.
- AC-T08-5: `cd tests && python -m pytest unittests.py -v` exits 0 with at least 9 tests passing (6 existing + 3 `TestUtilsFunctions` from task-02 + 1 from task-03 + 2 from task-07 = at least 12 collected; AC-8 says ≥9).

## Verification Command

```
test $(grep -c '^    start_time = time.time()' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py) = "1" && \
test $(grep -c '^    tracemalloc.start()' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py) = "1" && \
python -c "import sys; sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE'); import marine; help(marine.run)" > /dev/null && \
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py -v
```

## Notes

- Do NOT add a guard like `if not tracemalloc.is_tracing()`. Per assumption A-2, multiple `start()` calls are harmless.
- Do NOT add a comment explaining the move.
- Do NOT change any other line in `run()` or `__main__`.
- The order matters: `start_time` first, `tracemalloc.start()` second. This matches the order listed in `context/05-business-logic.md`.
