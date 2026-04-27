# Threat Model: MARINE Bug Fixes + Documentation & Cleanup

<!-- STAGE: 2-architect -->
<!-- ARCHETYPE: data-pipeline (offline) -->
<!-- UPDATED_UTC: 2026-04-25T10:00:00Z -->
<!-- REVISION: Extended 2026-04-25 to confirm tasks 10-12 introduce no new trust boundaries. -->

## 1. Scope

MARINE is an offline command-line bioinformatics pipeline. It reads local files (BAM, BED, whitelist, annotation) and writes local outputs (TSV, h5ad, BED, JSON). It has:
- No network surface
- No authentication
- No user-facing web/UI
- No persistent service
- No multi-tenancy

Per `context/07-security-requirements.md`, the project's security requirements section is N/A. The threat model below is therefore minimal but completed for completeness.

## 2. Trust Boundary Diagram

```
+----------------------+         +-----------------+        +------------------+
| Caller (shell user)  | ---CLI->| marine.py       |--->fork| Pool worker(s)   |
| filesystem perms     |  args   | run()           | pickle | core.py funcs    |
+----------------------+         +-----------------+        +------------------+
                                          |
                                          v
                                 +-----------------+
                                 | Local FS        |
                                 | output_folder   |
                                 +-----------------+

Trust boundaries (TB-N):
  TB-1: shell -> marine.py (CLI args, file paths, BAM contents)
  TB-2: marine.py main process -> Pool worker subprocesses (pickled args)
  TB-3: marine.py -> filesystem (path traversal via output_folder)
```

## 3. STRIDE Analysis per Trust Boundary

### TB-1: Shell -> marine.py (CLI inputs, BAM/BED/whitelist files)

| Threat | Applicable? | Notes |
|--------|------------|-------|
| Spoofing (S) | No | Single user, single process; OS authenticates user. |
| Tampering (T) | No | Local files; user already owns them. |
| Repudiation (R) | No | No audit/log requirements; offline tool. |
| Information Disclosure (I) | No | Outputs go to user-specified folder; user controls access. |
| Denial of Service (D) | Low | A pathologically large or malformed BAM could exhaust memory. Out of scope: M4 was deferred. |
| Elevation of Privilege (E) | No | No privileged operations performed. |

### TB-2: marine.py -> Pool worker subprocesses

| Threat | Applicable? | Notes |
|--------|------------|-------|
| Spoofing (S) | No | Same UID, same machine. |
| Tampering (T) | No | Pickle channel is in-process IPC. |
| Repudiation (R) | No | n/a. |
| Information Disclosure (I) | No | Same trust domain. |
| Denial of Service (D) | Low | C3 fix changes the Pool size source from undefined `cores` to function param `processes` (default=4). This REDUCES (not increases) parallelism for the all_cells split step versus the buggy state where the call would have raised NameError. No DoS uplift. |
| Elevation of Privilege (E) | No | No privilege transitions. |

### TB-3: marine.py -> Filesystem

| Threat | Applicable? | Notes |
|--------|------------|-------|
| Spoofing (S) | No | n/a. |
| Tampering (T) | No | Caller controls output_folder. |
| Repudiation (R) | No | n/a. |
| Information Disclosure (I) | Low | If `output_folder` includes a path traversal (e.g., `../../sensitive`), the tool will write there. Pre-existing condition; not introduced by these fixes. Out of scope. |
| Denial of Service (D) | Low | Disk fill — pre-existing. |
| Elevation of Privilege (E) | No | n/a. |

## 4. DREAD Scoring (Applicable Threats Only)

| ID | Threat | Damage | Reproducibility | Exploitability | Affected Users | Discoverability | Total | Priority |
|----|--------|--------|------------------|-----------------|------------------|-------------------|-------|----------|
| T1 | TB-1 DoS via malformed BAM | 1 (process crash) | 5 (specific malformed input) | 5 (anyone with BAM) | 1 (single user) | 5 | 17 | LOW |
| T2 | TB-3 path traversal via output_folder | 5 (data write outside intended dir) | 10 (always works) | 1 (caller is the only attacker) | 1 | 1 | 18 | LOW |

No threat scores >= 30. No `[SECURITY]` acceptance criteria are added to implementation tasks.

## 5. Notes on Bug-Fix Scope

The five bugs being fixed in this stage have NO security implications:

| Bug | Security Impact |
|-----|-----------------|
| C1 (delete marine2.py) | Removes dead code — slight reduction in maintenance attack surface (fewer files to audit). |
| C2 (start_time NameError) | Reliability bug; not a security bug. |
| C3 (Pool processes) | Reliability bug; the fix reduces parallelism (default=4) which mildly *reduces* DoS risk versus the buggy crash. |
| C4 (.format header=False) | Reliability bug; fix prevents a TypeError. |
| H5 (off-by-one) | Reliability bug; previous behavior caused pysam to silently clamp — not exploitable. |

## 6. AI-specific Threat Modeling

Not applicable. MARINE is not an AI/ML system; it is a deterministic statistical pipeline. MAESTRO analysis omitted.

## 7. Security ACs

None. No threat exceeded DREAD score 30.

## 8. Out-of-Scope Security Items (Pre-Existing)

The following pre-existing concerns are out of scope and should be addressed in a future security-focused work cycle:
- Input validation for BAM file existence and index (M4)
- Path traversal hardening for `output_folder`
- Bash subprocess with constructed paths (H3)

## 9. Documentation & Cleanup Pass (tasks 10-12) — Security Impact

| Task | Security Impact |
|------|-----------------|
| Task-10 (Google docstrings) | None. Docstrings are inert text. Reading them does not change runtime behavior. The `inspect.getsource()` patterns used elsewhere in the codebase already expose function source; docstrings are part of that source. |
| Task-11 (audit JSON) | None. The audit script reads source files via `ast.parse` and writes a JSON report. It does not execute any function under audit. The script must run from the trusted repo working tree (no untrusted input). |
| Task-12 (delete unused functions) | Net REDUCTION in attack surface. Removing dead code reduces the volume of maintained source; reviewers and security scanners have less to audit in future passes. The `TestPublicAPIPreserved` regression test does not change runtime behavior — it asserts presence via `hasattr`. |

No new trust boundaries. No new threats. No `[SECURITY]` acceptance criteria are added by Package B.
