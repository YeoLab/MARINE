# Discovery Log: MARINE
<!-- FORGE_STAGE: 0-research -->
<!-- STARTED_UTC: 2026-04-24T00:00:00Z -->
<!-- QUESTION_COUNT: 0 -->
<!-- ROUND: 0 -->

## Project Summary
MARINE (Multi-Core Algorithm for Rapid Identification of Nucleotide Edits) is a Python bioinformatics tool for detecting RNA editing events (primarily A-to-I and other nucleotide conversions) from single-cell and bulk RNA-seq datasets. It processes BAM files, compares sequencing data against reference genome sequences via MD/CIGAR tags, and outputs BED/bedGraph/h5ad files with editing sites and statistics.

## Archetype
data-pipeline (existing codebase, feature-addition context)

## Stack
- Language: Python 3.10
- Key libraries: pysam, polars, pandas, pybedtools, anndata/scanpy, scipy, numpy, multiprocessing
- External tools: samtools (via subprocess), bedtools (via pybedtools)
- Test framework: unittest + bash integration tests
- Package manager: conda (marine_environment2.yaml)
- CI: GitHub Actions (.github/workflows/main.yml)

## Key Structural Facts
1. Primary entry point: marine.py (CLI)
2. Core logic: src/core.py (parallel BAM traversal), src/read_process.py (MD/CIGAR parsing)
3. Utility catch-all: src/utils.py (1536 lines, 53+ functions)
4. Annotation: src/annotate.py (pybedtools)
5. marine2.py: experimental refactor, not in production or CI
6. Supports: bulk, single-cell (10x CB tag), single-cell long-read (IS/IB tags)
7. Parallelism: multiprocessing spawn context (not fork) to avoid polars/pysam conflicts
8. CB_N=1 hardcoded → 4 BAM suffix buckets for single-cell coverage splitting

## Critical Bugs Found in Audit
- C1: marine2.py is an undocumented parallel implementation
- C2: start_time NameError in run() function (programmatic use crashes)
- C3: cores NameError in generate_and_split_bed_files_for_all_positions()
- C4: .format(header=False) TypeError in get_coverage_wrapper()

## Rounds

(No rounds completed yet — pre-flight complete, structural indexing complete, audit complete)
