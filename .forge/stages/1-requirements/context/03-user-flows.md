# User Flows

## Primary Flow: CLI Bulk RNA-seq Run

```
User invokes marine.py via CLI
  → __main__ parses args
  → __main__ calls run(bam_filepath, ...)
  → run() opens logging_folder/manifest.txt
  → run() identifies edits (run_edit_finding → core.py)
  → run() calculates coverage (generate_depths → utils.py → get_coverage_wrapper)
  → run() generates site-level information
  → [if zero edits found] zero_edit_found() called — NEEDS start_time (C2 bug)
  → run() writes final_filtered_site_info.tsv
  → run() annotates with pybedtools (annotate_sites)
  → run() generates bedgraphs / SAILOR files
  → run() checks memory (tracemalloc.get_traced_memory) — NEEDS tracemalloc.start (M2 bug)
  → [if all_cells_coverage] generate_and_split_bed_files_for_all_positions()
      → Pool(processes=cores) — CRASHES (C3 bug)
  → run() returns 'Done!'
```

## Secondary Flow: Library / Programmatic Use

```
Python script: from marine import run
  → run(bam_filepath, ...) called
  → Same flow as CLI but start_time never set (C2 bug crashes on zero-edit path)
```

## Supporting Flow: get_intervals (used inside edit_finder)

```
core.py:edit_finder() calls get_intervals(contig, contig_lengths_dict, interval_length)
  → get_intervals computes start/end pairs for pysam pileup windows
  → Bug H5: last window end not clamped to contig_length
  → pysam silently handles but wastes CPU; semantically wrong output
```

## Supporting Flow: Coverage calculation (Paired-End)

```
run() → generate_depths() → get_coverage_wrapper(parameters)
  → get_coverage_wrapper() constructs output_filename
  → Bug C4: .format() called with header=False keyword → TypeError
  → Entire paired-end coverage path crashes
```

## Flows Not in Scope (Unchanged)

- Annotation-only mode (`--annotation_only`)
- Filtering-only mode (`--filtering_only`)
- Coverage-only mode (`--coverage_only`)
- Single-cell mode (CB/IS/IB barcode tag handling)
- BAM reconfiguration and split_bams generation
