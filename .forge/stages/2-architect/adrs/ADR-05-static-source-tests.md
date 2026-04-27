# ADR-05: Verify C2/C3 via inspect.getsource() Static Assertions
Date: 2026-04-25
Status: Accepted

## Context
C2 (`start_time` defined inside `run()`) and C3 (`Pool` uses `processes`) are fixes whose presence is most directly verifiable as text in the source rather than as observable behavior. Calling `run()` to behaviorally observe `start_time` would require mocking the entire pipeline (subprocess, pysam, polars, pybedtools).

## Decision
Add unit tests that read `inspect.getsource(marine.run)` and `inspect.getsource(marine.generate_and_split_bed_files_for_all_positions)` and assert string presence/absence:
- `start_time = time.time()` precedes the first `zero_edit_found` reference.
- `Pool(processes=cores)` is absent; `Pool(processes)` is present.

## Alternatives Considered
- Mock-call `run()` with stub args: Rejected — fragile and slow; high maintenance cost.
- Skip C2/C3 unit tests, rely on integration tests: Rejected — provides no regression signal until the bug re-occurs in CI on a real BAM.

## Consequences
- Positive: <50 ms test runtime, no fixtures, no mocks. Direct AC verification.
- Negative: Tests are placement-textual, not behavioral. A refactor that preserves the bug-free behavior but changes the source layout could fail the test.
- Risks: If `marine.py` is later distributed as bytecode without source, `inspect.getsource()` fails (would need to switch to behavioral tests at that point).

## References
- Architecture plan section: 5 (Decision Register, D-5)
- Assumptions: A-7
