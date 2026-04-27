# ADR-01: Per-bug Sequenced Commits with Verification Between
Date: 2026-04-25
Status: Accepted

## Context
Five independent bugs (C1, C2, C3, C4, H5 plus M2 tracemalloc move) plus four-to-six new unit tests must be applied. We can either apply them all in one commit or split across commits.

## Decision
Apply the fixes in nine sequenced tasks (Approach B). Run unit tests after every task and integration tests as a final gate. Test-first ordering for the testable bugs (H5 and C4): write the test red, then apply the fix to turn green.

## Alternatives Considered
- **Approach A (one-shot)**: All fixes plus all tests in a single commit. Rejected: any integration regression would be ambiguous in attribution.
- **Approach C (quarantine + swap)**: Build alongside, then swap. Rejected: massive over-engineering for a 30-line diff.

## Consequences
- Positive: Each commit is independently revertable. Regressions attributable to most recent commit. Test-first discipline naturally enforced.
- Negative: More CI invocations; longer wall-clock time.
- Risks: A change in test infrastructure between tasks could cause confusing intermediate-state failures. Mitigation: each task's verification command is self-contained.

## References
- Architecture plan section: 2 (Approaches), 6 (Task Decomposition), 8 (Verification Plan)
- Assumptions: A-8, A-9
