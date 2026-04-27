# Vision and Goals

## Project Vision

MARINE (Multi-Core Algorithm for Rapid Identification of Nucleotide Edits) is a production
bioinformatics tool for detecting RNA editing events (primarily A-to-I and other nucleotide
conversions) from single-cell and bulk RNA-seq datasets. It is used in peer-reviewed research.

## Task Scope

**Bug fixes only.** No new features. No refactoring beyond what is required to fix the
named bugs. The goal is to restore correctness to four critical code paths that currently
crash at runtime, fix one high-severity logic bug that produces incorrect interval
boundaries, and ensure tracemalloc is properly initialized so memory profiling works.

## Goals (Ranked)

1. **G1 (Critical)**: Fix 4 runtime crashes (C1-C4) so MARINE can be used as both a CLI
   tool and a library without NameError or TypeError
2. **G2 (High)**: Fix interval boundary bug (H5) so `get_intervals()` produces correct
   endpoint for the last interval in each contig
3. **G3 (High)**: Fix memory profiling so `tracemalloc` is actually started before
   `get_traced_memory()` is called (M2)
4. **G4 (High)**: Remove dead-code confusion (`marine2.py`) to eliminate maintenance burden
5. **G5 (Medium)**: Add unit tests covering all changed code paths so CI catches regressions

## Non-Goals

- Refactoring `utils.py` god module
- Adding type annotations
- Fixing deprecated pandas APIs
- Changing the CLI interface
- Changing the conda environment
- Adding new features
