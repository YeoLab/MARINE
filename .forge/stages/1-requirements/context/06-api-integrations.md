# API Integrations

## N/A

MARINE is an offline bioinformatics data pipeline. It does not call any external HTTP APIs.

## Local Tool Dependencies (unchanged by this task)

- **pysam**: C wrapper for samtools/htslib; used for BAM traversal and interval-based
  pileup. No API changes in scope.
- **pybedtools**: Python wrapper for BEDTools; used in `annotate.py` for feature
  intersection. No API changes in scope.
- **samtools** (subprocess): Used via `subprocess.run()` for `samtools depth`. No changes.
- **polars / pandas**: DataFrame libraries for site-level information. No changes.

## Function Interfaces (internal "APIs") Changed by This Task

### `run()` in marine.py
- **Signature**: Unchanged
- **Behavioral change**: Now defines `start_time` and starts `tracemalloc` internally,
  so programmatic callers no longer need to do so

### `generate_and_split_bed_files_for_all_positions()` in marine.py
- **Signature**: Unchanged (`processes=4` parameter already existed)
- **Behavioral change**: Pool now uses `processes` parameter instead of crashing

### `get_coverage_wrapper()` in src/utils.py
- **Signature**: Unchanged
- **Behavioral change**: No longer raises TypeError; constructs filename correctly

### `get_intervals()` in src/utils.py
- **Signature**: Unchanged
- **Behavioral change**: Last interval now ends at `contig_length`, not `start + interval_length`
