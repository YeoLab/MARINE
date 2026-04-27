# ADR-07: Split unused-function cleanup into a read-only audit (task-11) and a separate action task (task-12)

Date: 2026-04-25
Status: Accepted

## Context

The cleanup pass needs to identify and remove genuinely-unused functions in `marine.py`, `src/core.py`, `src/utils.py`, and `src/read_process.py`. The user explicitly excluded Pool worker targets, CLI entry points (the project uses argparse, not click — `run` in `marine.py`), and dynamic-dispatch callables. A naive single-task implementation that audits and deletes in one pass risks over-removal because:

- The audit's KEEP rules (especially "imported by name" through backslash continuations) require careful AST walking. A missed import means a falsely-classified REMOVE_CANDIDATE.
- The cost asymmetry is severe: a wrongly-kept dead function costs bytes, a wrongly-removed live function crashes the pipeline at runtime.
- A human reviewer's check between identification and deletion is the cheapest mitigation.

## Decision

Two tasks:

1. **Task-11**: produces `.forge/stages/2-architect/unused-functions-audit.json` containing every function classified KEEP or REMOVE_CANDIDATE with explicit evidence per entry. Modifies NO source files.
2. **Task-12**: re-reads the (post-review) audit and deletes only the entries still classified REMOVE_CANDIDATE. Adds `TestPublicAPIPreserved` to `tests/unittests.py` as a thin presence-test net.

Between the two, the build agent halts for human review (FM-04 in the implementer prompt).

## Alternatives Considered

- **Single combined task** (audit + delete in one pass): faster, but no human-review checkpoint. Higher risk of unobserved misclassification. Rejected.
- **Use `vulture` or another static analyzer**: adds a dependency, and the analyzer's heuristics still need allowlist tuning for Pool workers and CLI entries — same human-review burden. Rejected.
- **Manual code reading by the architect with no automation**: at 96 functions, this scales poorly and is error-prone. Rejected.

## Consequences

- Positive: explicit checkpoint for the user to veto a deletion before it happens. The audit JSON is a permanent artifact; future cleanup passes can use it as a baseline. The `TestPublicAPIPreserved` regression test pins the surviving public API.
- Negative: two tasks instead of one. Slightly higher build-stage runtime.
- Risks: build agent forgets to pause between task-11 and task-12. Mitigation: implementer-prompt FM-04 explicitly requires the pause; task-12 step 1 re-reads the JSON to pick up reviewer edits.

## References

- Architecture plan section: 2 (Approaches Considered, Package B, Approach B2), 5 (Decision Register D-9, D-12), 9 (Risk Register R-7, R-10, R-11), 13 (Pool worker / dynamic dispatch evidence).
- Assumptions: A-12, A-13, A-14, A-15.
