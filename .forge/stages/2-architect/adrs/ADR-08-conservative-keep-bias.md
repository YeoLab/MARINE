# ADR-08: Conservative-keep bias for unused-function classification

Date: 2026-04-25
Status: Accepted

## Context

When the audit script (task-11) cannot determine with certainty whether a function is dead, the policy must specify a default. The two costs are asymmetric:

- A false-keep: the function survives unused. Cost: a few hundred bytes of source, slightly increased cognitive load.
- A false-remove: the function is genuinely live but missed by every KEEP rule. Cost: runtime crash when an importer or external consumer calls the deleted name.

These are not commensurable. A runtime crash in a published RNA-editing pipeline used by collaborators is far worse than an extra ~50 lines of dead code.

## Decision

Uncertainty maps to KEEP. Specifically:

- If the auditor cannot confidently explain in one or two sentences what a function does and why it is dead, the function is KEEP with rule `uncertain_purpose`.
- If a function name appears anywhere in any file under `MARINE/` (whole-word match), it is KEEP. False positives from this rule are acceptable.
- If a function is one of the six known Pool workers (architecture-plan Section 13) or the CLI `run` entry, it is KEEP unconditionally regardless of the grep result.
- External-consumer reachability is not measurable from inside this repository. The audit accepts the residual risk and provides a `git revert`-friendly removal commit so any breakage is one revert away from fixed (R-9, A-14).

## Alternatives Considered

- **Symmetric default (uncertainty -> 50/50 manual review)**: wastes reviewer time on every function the audit can't classify. Rejected.
- **REMOVE-biased**: explicitly rejected. The cost asymmetry forbids this.

## Consequences

- Positive: false-removes approach zero. The audit produces a strict subset of truly-dead functions. Subsequent cleanup passes can revisit and tighten.
- Negative: some genuinely-dead functions survive this pass. Acceptable.
- Risks: reviewer fatigue from a noisy KEEP list. Mitigation: the audit JSON's `evidence` field is concise (one entry per matched rule), so reviewers can scan quickly.

## References

- Architecture plan section: 5 (Decision Register D-11), 9 (Risk Register R-9).
- Assumptions: A-14, A-15.
