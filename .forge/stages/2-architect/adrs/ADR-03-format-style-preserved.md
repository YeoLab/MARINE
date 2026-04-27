# ADR-03: C4 Fix Preserves `.format()` Style
Date: 2026-04-25
Status: Accepted

## Context
`src/utils.py:663` reads `output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)`. The `header=False` kwarg is invalid for `str.format()` and causes a TypeError. We need to fix without violating the surgical-changes rule.

## Decision
Remove `, header=False` from the `.format()` call. Keep the `.format()` style.

## Alternatives Considered
- Switch to f-string `f'{output_folder}/coverage/{contig}.tsv'`: Rejected per NFR-4 (minimal diff) and because the surrounding function uses `.format()`.

## Consequences
- Positive: One-line edit, style-consistent.
- Negative: None.
- Risks: None.

## References
- Architecture plan section: 5 (Decision Register, D-2)
- Assumptions: A-5
