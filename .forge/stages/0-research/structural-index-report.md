# Structural Index Report: MARINE
<!-- Generated: 2026-04-24 -->

## Files Indexed
- 9 Python source files
- 4,060 total lines of production code (+ ~674 lines in marine2.py prototype)
- Compression ratio: 22x (codemap ~2,095 tokens vs ~47,340 to read all files)

## Top-Level Directory Structure
```
MARINE/
├── marine.py           # Primary CLI entry point (682 lines)
├── marine2.py          # Experimental refactored version (543 lines, not production)
├── src/
│   ├── __init__.py     # Module exports
│   ├── core.py         # Parallel edit-finding and BAM reconfiguration (719 lines)
│   ├── read_process.py # Per-read edit extraction via MD/CIGAR tags (497 lines)
│   ├── utils.py        # Coverage, BAM writing, SAILOR, bedgraph utilities (1536 lines)
│   └── annotate.py     # pybedtools-based feature annotation (64 lines)
├── tests/
│   ├── unittests.py    # 6 unit tests for read_process functions
│   ├── integration_tests_auto_check.py
│   ├── integration_tests.ipynb
│   ├── integration_tests_run.sh
│   ├── bam_files/      # Test BAM files
│   ├── singlecell_tests/
│   └── strandedness_tests/
├── examples/           # Example BAMs, annotation BEDs, and expected outputs
├── annotations/        # Reference annotation BED files (hg38, mm10, GRCh37/38)
└── .github/workflows/main.yml  # GitHub Actions CI
```

## Key Entry Points
- `marine.py` — production CLI entrypoint, `run()` function orchestrates the full pipeline
- `src/core.py:find_edits()` — core per-interval edit-finding loop (pysam-based)
- `src/core.py:run_edit_identifier()` — spawns multiprocessing pool for edit-finding jobs
- `src/read_process.py:get_edit_information_wrapper()` — per-read MD/CIGAR edit extraction
- `src/utils.py:make_depth_command_script_single_cell()` — pysam-based coverage calculation
- `src/utils.py:generate_and_run_bash_merge()` — bash-based join of edit info + depth files

## Module Boundary Summary
| Module | Responsibility | Cohesion |
|--------|---------------|----------|
| read_process.py | MD tag parsing, CIGAR handling, per-read edit extraction | High |
| core.py | Parallel BAM traversal, edit accumulation, BAM reconfiguration | High |
| utils.py | Everything else: bedgraph, SAILOR, coverage, BAM writing, formatting | Low (catch-all) |
| annotate.py | Feature annotation via pybedtools intersection | High |
| marine.py | CLI argument parsing, pipeline orchestration | High |

## Key Structural Observations
1. **No dependency graph edges** in codemap — the internal imports (core.py imports read_process and utils) are not resolved by codemap because src/ uses direct module names without package prefix (`from read_process import ...` not `from src.read_process import ...`). This is a sys.path manipulation pattern.
2. **marine2.py** is an experimental refactoring that is NOT wired into the CI or main entry point. It partially reimplements marine.py with slightly different function signatures.
3. **utils.py is a god module** — 1,536 lines covering BAM I/O, coverage calculation, file merging, sparse matrix operations, SAILOR scoring, bedgraph generation, progress printing, and more.
4. **CB_N = 1** constant in utils.py controls the suffix granularity for single-cell BAM splitting (1 nucleotide = 4 suffixes: A/C/G/T).
5. **Multiprocessing uses spawn context** (not fork) to avoid polars/pysam incompatibilities.

## No Initial Knowledge Graph
Graphify not available in this context. No semantic graph generated.
