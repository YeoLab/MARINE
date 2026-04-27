# Data Models

## Key Data Structures Relevant to Bug Fixes

### Contig Intervals (H5 bug — get_intervals)

`get_intervals(contig, contig_lengths_dict, interval_length)` returns a list of `[start, end]`
pairs that partition the contig into windows for parallel pysam pileup.

**Current (buggy) behavior** for contig_length=100, interval_length=30:
```
[[0, 30], [30, 60], [60, 90], [90, 120]]  # last end=120, not 100
```

**Expected (correct) behavior**:
```
[[0, 30], [30, 60], [60, 90], [90, 100]]  # last end=100 (clamped to contig_length)
```

**Input type**: `contig_lengths_dict` is a plain Python dict mapping contig name (str) to
length (int). Example: `{'chr1': 248956422, 'chr2': 242193529, ...}`

### Coverage Output Filename (C4 bug — get_coverage_wrapper)

`get_coverage_wrapper(parameters)` receives a tuple and constructs:
```python
output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)  # BUG
output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig)               # FIX
```
The file is a TSV with columns: `barcode_position_index, barcode, contig, position, ref,
alt, read_id, strand, dist_from_end, base_quality, mapping_quality, barcode_position,
coverage, source, position_barcode`

### Timing and Memory Tracking Variables (C2 bug — run())

`start_time` is a float (unix timestamp from `time.time()`). Used in:
- `zero_edit_found(..., start_time, ...)` — called at lines 378 and 411
- `time.time() - start_time` — called at lines 446 and 449

`tracemalloc` state is process-global. `tracemalloc.start()` must precede
`tracemalloc.get_traced_memory()`.

### Pool parallelism (C3 bug — generate_and_split_bed_files_for_all_positions)

`Pool(processes)` context manager where `processes` is an int (function parameter,
default=4). The `combinations` list is passed to `pool.map(process_combination_for_split,
combinations)`. Each element is a tuple passed to `process_combination_for_split(args)`.
