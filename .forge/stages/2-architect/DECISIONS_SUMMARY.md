# Decisions Summary: MARINE Bug Fixes + Documentation & Cleanup

<!-- Stage: 2-architect -->
<!-- For: implementers, reviewers, on-call engineers -->
<!-- Generated: 2026-04-25 (extended same day to add Package B decisions) -->

Top decisions with rationale, alternatives, and risks. Decisions 1-5 are from Package A (bug fixes); decisions 6-9 are from Package B (documentation and cleanup), added in the 2026-04-25 extension.

## 1. Sequencing: Per-bug commits with verification between (Approach B)

- **Decision**: Apply fixes in groups (C1 alone; C4+H5 with their tests; C3; C2/M2 with its test) and run tests between groups.
- **Alternatives**: One-shot patch (Approach A); quarantine-and-swap (Approach C).
- **Why**: Per-bug commits give the build agent diagnostic feedback between groups; failures are localized to the most recent group; each commit is independently revertable.
- **Risk**: More CI runs (acceptable given task is small).

## 2. C3 fix form: positional `Pool(processes)` (D-1)

- **Decision**: Replace `Pool(processes=cores)` with `Pool(processes)` (positional).
- **Alternatives**: `Pool(processes=processes)` explicit kwarg.
- **Why**: Minimum-edit principle. The function parameter is named `processes`; positional is the shortest correct expression. No downstream code reads the call style.
- **Risk**: None.

## 3. C4 fix style: keep `.format()` (D-2)

- **Decision**: Remove the bad kwarg from the existing `.format()` call rather than rewriting as f-string.
- **Alternatives**: Switch to f-string.
- **Why**: NFR-4 requires minimal diff. The surrounding function uses `.format()`. Style-match existing code.
- **Risk**: None.

## 4. tracemalloc placement: top of `run()`, no guard (D-3)

- **Decision**: Place `start_time = time.time()` and `tracemalloc.start()` as the first two executable statements of `run()`, with no `is_tracing()` guard.
- **Alternatives**: Place just before `tracemalloc.get_traced_memory()`; guard with `if not tracemalloc.is_tracing()`.
- **Why**: Both early-return paths (zero_edit_found at lines 378 and 411) need `start_time` defined. Placing at top covers all paths with no branching. Python stdlib documents that re-calling `tracemalloc.start()` while tracing is a no-op.
- **Risk**: If a future Python version raises on re-call, double-start is still cheap to guard later. (See A-2.)

## 5. Test approach for C2/C3: static source inspection (D-5)

- **Decision**: Verify C2 (start_time placement) and C3 (Pool kwarg) using `inspect.getsource()` and string-presence assertions in unit tests.
- **Alternatives**: Mock-call `run()` (heavy due to subprocess/pysam); rely on integration tests only (no regression signal).
- **Why**: Static-source assertions run in milliseconds, require no mocks, and directly verify the AC text. They are appropriate for placement-style fixes that have no observable behavior change in non-bug-trigger paths.
- **Risk**: If `marine.py` is later compiled to bytecode without source, `inspect.getsource()` fails. (See A-7.)

## 6. Docstring style: Google-style (D-7)

- **Decision**: Use Google-style docstrings with `Args:`/`Returns:`/`Raises:` sections for the 96-function documentation pass.
- **Alternatives**: NumPy-style; reST/Sphinx style; freeform prose.
- **Why**: Google-style is highly readable in plain text, requires no Sphinx setup, and was explicitly requested. Locking the choice once at the architect stage prevents per-file re-litigation by the build agent.
- **Risk**: If the project later adopts Sphinx without `napoleon`, the docstrings would need conversion. Mitigation: `napoleon` is included in modern Sphinx by default. (See A-10.)

## 7. Pool-worker docstring marking (D-8)

- **Decision**: Every Pool worker function's docstring summary explicitly states "Worker function for Pool.map/imap_unordered" and documents the tuple-unpacking contract.
- **Alternatives**: Treat Pool workers identically to other functions.
- **Why**: Pool workers have a non-obvious calling convention (single tuple arg unpacked into N variables). The signature alone gives no hint. The docstring is the only place future maintainers will learn this.
- **Risk**: None.

## 8. Cleanup analysis vs. action split (D-9)

- **Decision**: Two tasks. Task-11 produces `unused-functions-audit.json` (read-only). Task-12 acts on the post-review audit.
- **Alternatives**: Single combined task; vulture/pyflakes-driven automated removal.
- **Why**: The split creates an explicit human-review checkpoint at the JSON artifact. A reviewer can downgrade any REMOVE_CANDIDATE to KEEP without re-running the audit. Reduces blast radius of a misclassification.
- **Risk**: Two-step process is slower. (See FM-04 — the build agent must NOT auto-advance from task-11 to task-12.)

## 9. Conservative-keep bias (D-11)

- **Decision**: Any uncertainty in unused-function classification defaults to KEEP. The audit explicitly allowlists Pool workers, the `run` CLI entry, and any function imported anywhere in the repo.
- **Alternatives**: Symmetric or REMOVE-biased classification.
- **Why**: Asymmetric cost. A wrongly-kept dead function is bytes; a wrongly-removed live function is a runtime crash. The asymmetry justifies the bias.
- **Risk**: A function genuinely dead but not detected as such will survive. That is acceptable — a future audit pass can revisit. (See A-15, R-9.)
