# Security Requirements

## N/A — Justified

MARINE is an offline bioinformatics data pipeline that:
- Reads only local BAM, BED, and annotation files provided by the researcher
- Writes output TSV, BED, bedGraph, and h5ad files to a local output folder
- Has no network interface, no authentication, no web surface, no user accounts
- Is run by researchers on HPC clusters or local machines under their own credentials

None of the bug fixes in this task (C1-C4, H5, tracemalloc) touch security-sensitive code
paths. No new file permissions, subprocess calls, or external inputs are introduced.

**SEC-1**: N/A — No security surface exists or is modified by this task.
