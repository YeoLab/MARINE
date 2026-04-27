# User Experience

## Primary Users

- Bioinformatics researchers running MARINE from the command line to analyze RNA-seq data
- Developers who import `run()` from `marine.py` programmatically in Python scripts or
  notebooks

## Current UX Pain Points Caused by Bugs

### C2: `run()` NameError on programmatic use
Any caller that uses `from marine import run; run(...)` and hits the zero-edit-found branch
gets a `NameError: name 'start_time' is not defined`. This means MARINE cannot be used as
a library — only as a CLI (where `start_time` is defined in `__main__`).

### C3: `--all_cells_coverage` flag crashes
When the user passes `--all_cells_coverage`, the pipeline reaches
`generate_and_split_bed_files_for_all_positions()` which tries to use `cores` (not in scope
at that point). This crashes with `NameError: name 'cores' is not defined`.

### C4: Bulk paired-end coverage crashes immediately
Any run with paired-end data (`--paired_end`) hits `get_coverage_wrapper()`, which raises
`TypeError: 'header' is an invalid keyword argument for format()`. The error appears
immediately on the first contig, with an unrelated-looking traceback.

### H5: Incorrect interval endpoints
`get_intervals()` returns a last interval that extends past the contig end (e.g., for a
contig of length 100 with interval_length=30, the last interval is `[90, 120]` instead of
`[90, 100]`). pysam silently clamps this, but it wastes compute and could cause issues with
different reference versions.

## Post-Fix UX

- `run()` works correctly whether called from CLI or imported as a library function
- `--all_cells_coverage` flag functions without NameError
- Paired-end coverage calculation completes without TypeError
- Interval generation produces correct boundaries
- Memory profiling (via `tracemalloc`) reports accurate values
- `marine2.py` no longer confuses users or contributors about the canonical entry point

## UX Invariants (Must Not Change)

- CLI argument names and behavior are unchanged
- Output file formats are unchanged
- `run()` function signature is unchanged
