# ADR-02: C3 Fix Uses Positional `Pool(processes)`
Date: 2026-04-25
Status: Accepted

## Context
`marine.py:279` reads `Pool(processes=cores)`, but `cores` is not a parameter of `generate_and_split_bed_files_for_all_positions()`. The function signature does declare `processes=4`. We need to fix the bug with a minimum-surface edit.

## Decision
Replace `Pool(processes=cores)` with `Pool(processes)` (positional).

## Alternatives Considered
- `Pool(processes=processes)`: Adds keyword noise without value. The function-parameter name and the kwarg name are identical, so positional is unambiguous.

## Consequences
- Positive: Smallest possible diff (replace one identifier).
- Negative: None.
- Risks: None — `multiprocessing.Pool`'s first parameter is `processes`.

## References
- Architecture plan section: 5 (Decision Register, D-1)
- Assumptions: A-1
