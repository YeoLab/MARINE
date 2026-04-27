# ADR-06: Google-style docstrings for marine.py / src/core.py / src/utils.py / src/read_process.py

Date: 2026-04-25
Status: Accepted

## Context

The four files in scope contain 96 top-level functions, none of which currently have docstrings. A user-driven scope expansion requested that every function be documented. The architect must lock a docstring style at this stage so the build agent (task-10) does not re-litigate per file.

## Decision

Use Google-style docstrings with `Args:`, `Returns:`, and `Raises:` sections. Pool worker functions additionally state "Worker function for Pool.map/imap_unordered" in their summary line and document the tuple-unpacking contract.

## Alternatives Considered

- **NumPy-style**: heavier visual structure (separator lines), more verbose for short functions. Better for scientific docstrings rendered by Sphinx; worse for plain-text reading. Rejected because the project does not currently render docs.
- **reST/Sphinx native (`:param x:` syntax)**: most compact when rendered, ugliest in source. Rejected for the same reason.
- **Freeform prose / Python's stdlib style**: inconsistent across the 96 functions; harder to lint. Rejected.

## Consequences

- Positive: All four files are uniformly documented. Pool worker conventions become discoverable from the source. If Sphinx is adopted later, `napoleon` (included by default in modern Sphinx) renders Google-style natively.
- Negative: Adds ~600-1100 lines of docstring text across the four files. Worth the cost given the FR-12 requirement.
- Risks: A typo in a docstring goes unnoticed. Mitigation: `git diff` review at task-10 verification gate; AST `get_docstring` check rules out missing docstrings.

## References

- Architecture plan section: 2 (Approaches Considered, Package B), 5 (Decision Register D-7, D-8), 13 (Pool worker inventory).
- Assumptions: A-10, A-11.
