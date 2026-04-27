# Review Report: MARINE Bug Fixes (C1-C4 + H5 + Tracemalloc + Tests) + Documentation & Cleanup

<!-- FORGE_STAGE: 4-review -->
<!-- STATUS: CHANGES_REQUIRED -->
<!-- REVIEWER: forge-reviewer (Opus, fresh context, adversarial persona) -->
<!-- BASE_COMMIT: 5cd3dafc3185db2d38b24dbce9cd8558e4e50f6c -->
<!-- REVIEW_ROUND: 1 -->

## Executive Summary

| Verdict | CHANGES_REQUIRED |
|---|---|
| Critical findings | 1 |
| Major findings | 3 |
| Minor findings | 4 |
| Acceptance Criteria | 10/10 PASS (functionally), but evidence sufficiency varies |
| Tests | 13/13 PASS in `marine_environment` (Python 3.10) |

The bug fixes (C1-C4, H5, C2/M2) and the docstring/cleanup pass are correctly implemented and verified by an adequate test suite. **However, the working tree contains an out-of-scope rewrite of `marine_environment2.yaml` (281-line pinned conda env -> 20-line unpinned env) that the architecture plan explicitly forbids in Section 11.** That rewrite must be either (a) reverted, (b) split into a separately-justified change, or (c) added to the plan with a recorded ADR before this work merges. There is also one hardcoded absolute path inside the test suite that will break for any other developer.

## Spec Compliance

`spec-deviations.json` was not present. Spec-compliance review relied on diff-vs-plan analysis. **REVIEW WARNING: spec-deviations.json not found. Spec compliance review will rely on diff analysis only.**

| Plan section | Reality | Verdict |
|---|---|---|
| Sec. 11 Out-of-Scope: "Any change to `marine_environment2.yaml` Python version" | yaml rewritten end-to-end including channels reordered, ALL pinned versions removed, Python now `>=3.10` (was `=3.8.x`) | **DEVIATION (UNAPPROVED)** |
| Sec. 12 DoD: "Total source-code diff (excluding new tests and the marine2.py deletion) is no more than 12 added/modified lines" for Package A | True for Package A bug-fix lines only (5 fix lines + ~1 line shifts). Package B docstring-only diff is allowed by NFR-4 carve-out | PASS |
| Sec. 12 DoD: "no new imports" for Package A | The new test file imports `inspect` (architectural-plan-permitted as a test concern) and adds `get_intervals` to the existing import line. Source files: no new imports | PASS |
| Sec. 11: `tests/integration_tests_run.sh` and `tests/integration_tests_auto_check.py` remain unchanged | Confirmed unchanged | PASS |
| Sec. 11: `src/annotate.py` not in scope | Confirmed unchanged | PASS |
| Sec. 11: No code reformatting | Reviewed sample regions: only docstring additions in the four target files | PASS |

## Decision Compliance (DR-1 .. DR-12)

| DR | Decision | Status | Evidence |
|----|----------|--------|----------|
| DR-1 | C3 fix `Pool(processes)` positional | FOLLOWED | `marine.py:154`, `marine.py:291` both `Pool(processes)` |
| DR-2 | C4 keep `.format()`, drop `header=False` | FOLLOWED | `src/utils.py:878` `'{}/coverage/{}.tsv'.format(output_folder, contig)` |
| DR-3 | tracemalloc + start_time at top of `run()`, no guard | FOLLOWED | `marine.py:337-338` are the first two executable statements of `run()` body |
| DR-4 | New `TestUtilsFunctions` class in same file | FOLLOWED | `tests/unittests.py:80` |
| DR-5 | C2/C3 verification via `inspect.getsource()` | FOLLOWED | `tests/unittests.py:108` and `:124` |
| DR-6 | Per-bug commit sequencing (Approach A2) | UNVERIFIABLE | Source changes in working tree are uncommitted; cannot inspect commit boundaries. Implementation report claims sequencing was followed. **Minor finding M-3.** |
| DR-7 | Google-style docstrings throughout | FOLLOWED | All 94 functions in 4 files have Google-style docstrings (verified via AST). One borderline case (`prepare_combinations_for_split`) uses summary-then-Args style; acceptable. |
| DR-8 | Pool worker docstring marker "Worker function for Pool.map" | FOLLOWED | All 6 pool workers (`get_unique_barcodes_for_reads_in_bamfile`, `process_combination_for_split`, `find_edits_and_split_bams_wrapper`, `concat_and_write_bams_wrapper`, `get_coverage_wrapper`, `merge_files_by_chromosome`) carry the marker |
| DR-9 | Audit/action split (task-11 read-only, task-12 acts) | FOLLOWED | `unused-functions-audit.json` is a separate artifact; only one REMOVE_CANDIDATE was acted on |
| DR-10 | Grep + AST detection method | FOLLOWED | Audit JSON shows `imported_by_name` / `called_internally` / `referenced_in_tests` rules |
| DR-11 | Conservative-keep bias | FOLLOWED | 94 KEEP / 1 REMOVE_CANDIDATE; only an empty-body no-op was removed |
| DR-12 | `TestPublicAPIPreserved` regression test | FOLLOWED | `tests/unittests.py:142` — `test_generate_empty_matrix_file_removed` |

## Assumption Audit (A-1 .. A-15)

| ID | Assumption | Status | Evidence |
|----|-----------|--------|----------|
| A-1 | `processes=4` distinct from `cores=64`, intentional | HOLDS | `marine.py:227` signature unchanged |
| A-2 | `tracemalloc.start()` re-entrant safe | HOLDS | Python 3.10 stdlib confirms; tests pass when calling `run` shape |
| A-3 | `start_time` not referenced in `__main__` after `run()` | HOLDS | Verified `marine.py` after line 556: zero references |
| A-4 | `marine2.py` safely deletable | HOLDS | File is gone; no import errors observed in tests |
| A-5 | Removing `header=False` is bug-fix only, no behavior change | HOLDS | Filename string is unchanged; `.format()` would have raised `TypeError` previously |
| A-6 | New `get_intervals` tests need no fixtures | HOLDS | Tests pass on dict-only inputs |
| A-7 | `inspect.getsource()` is stable | HOLDS | Tests pass; bytecode-only deployment is not a current concern |
| A-8 | Test-first ordering preferred | UNVERIFIABLE | Same as DR-6: no commit history. **Minor M-3.** |
| A-9 | Integration tests green at baseline | UNVERIFIABLE in this review | Implementation report claims integration suite passed; not re-run here |
| A-10 | Google-style docstrings appropriate | HOLDS | Project still has no Sphinx config |
| A-11 | 96-function count at task-10 start | DEVIATED (minor) | Actual top-level count = 91 (9 + 17 + 13 + 52). Plan estimated 96 (11 + 18 + 53 + 14). Off by 5; not material. **Minor M-4.** |
| A-12 | grep + AST sufficient (no dynamic dispatch) | HOLDS | `grep -nE "globals\(\)\|getattr\|eval\(\|exec\(\|importlib\|__import__"` across 4 files: 0 matches |
| A-13 | No `__all__` in target files | HOLDS | `grep '^__all__'`: 0 matches |
| A-14 | External consumers may exist; risk accepted | HOLDS as a risk acceptance |
| A-15 | Conservative-keep bias correct | HOLDS as a policy |

## ADR Drift Detection

| ADR | Decision | Status | Detail |
|---|---|---|---|
| ADR-01 per-bug-sequencing | UNVERIFIABLE (no `affects_files`, no commit history) | None of the 8 ADRs declare an `affects_files` field. **Minor M-5.** |
| ADR-02 pool-processes-positional | CONSISTENT | Both targeted call sites use `Pool(processes)` |
| ADR-03 format-style-preserved | CONSISTENT | `get_coverage_wrapper` keeps `.format()` |
| ADR-04 tracemalloc-placement | CONSISTENT | `run()` begins with `start_time` then `tracemalloc.start()` |
| ADR-05 static-source-tests | CONSISTENT | `tests/unittests.py:107-135` uses `inspect.getsource()` |
| ADR-06 google-docstring-style | CONSISTENT | All 94 functions documented in Google style |
| ADR-07 cleanup-analysis-action-split | CONSISTENT | Audit JSON exists; deletion task acted on its output |
| ADR-08 conservative-keep-bias | CONSISTENT | 94 KEEP / 1 REMOVE_CANDIDATE |

## Pass 1: Contract Compliance Findings

### CRITICAL

#### C-1: Out-of-scope rewrite of `marine_environment2.yaml`
- **File**: `marine_environment2.yaml` (working tree)
- **Severity**: CRITICAL
- **Category**: SCOPE_VIOLATION
- **Plan reference**: Section 11 Out-of-Scope explicitly lists "Any change to `marine_environment2.yaml` Python version".
- **Evidence**: `git diff HEAD -- marine_environment2.yaml` shows -281 / +20 lines. The new file:
  - Removes ALL pinned package versions (281 -> 20 lines)
  - Reorders channels (`anaconda` removed, `r` removed, `conda-forge` promoted to top)
  - Switches from `python=3.8` (implied by `_cp38` build strings throughout the original) to `python=3.10`
- **Why this matters**: This is the production conda environment that downstream users `conda env create -f` against. Replacing pinned versions with floating versions can silently break reproducibility. None of the 14 acceptance criteria in the plan request this change. There is no DR for it. There is no ADR for it. There is no entry in any task file.
- **Suggested fix**: Either (a) `git checkout HEAD -- marine_environment2.yaml` to revert, or (b) add a separate task/ADR documenting the rationale, the migration plan, and explicit reviewer approval.
- **Verification command**: `git diff HEAD -- marine_environment2.yaml | wc -l` should return 0 after revert.

### MAJOR

#### M-1: Hardcoded absolute path in test file
- **File**: `tests/unittests.py:113` and `tests/unittests.py:130`
- **Severity**: MAJOR
- **Category**: PORTABILITY
- **Evidence**:
  ```python
  _sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE')
  ```
  appears in two new tests (`test_marine_run_starts_time_at_top` and `test_marine_pool_uses_processes_param`).
- **Why this matters**: This path is specific to the original developer's filesystem. It will:
  - Cause CI to fail on any other host (the existing `.github/workflows/main.yml` runs on GitHub-hosted runners; this path does not exist there).
  - Confuse any maintainer who tries to run tests locally.
  - Bypass the existing `sys.path` setup at the top of the file (line 5-7) which already adds `../src/` cleanly via a relative path.
- **Suggested fix**: Replace with the same idiom used at top-of-file:
  ```python
  marine_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
  if marine_root not in _sys.path:
      _sys.path.insert(0, marine_root)
  ```
  Better yet, factor the `sys.path` setup into a module-level block run once.
- **Verification**: `grep -n "/tscc/" tests/unittests.py` should return zero matches after fix.

#### M-2: `conftest.py` added but not declared in any plan/task/report
- **File**: `tests/conftest.py` (new, untracked)
- **Severity**: MAJOR
- **Category**: SCOPE / DOCUMENTATION
- **Evidence**: New file present in `tests/` directory; not mentioned in:
  - architecture-plan.md
  - implementation-report.md
  - polish-report.md
  - any task file
- **Why this matters**: The file monkey-patches `unittest.main` to make pytest collection succeed when `unittests.py` calls `unittest.main()` at module bottom. This is a real fix for a real problem (pytest would otherwise SystemExit during collection), but its addition is undocumented. A reviewer cannot tell whether this was intentional or an accidental commit.
- **Suggested fix**: Either (a) add a one-line note to the implementation report referencing the file, or (b) document its purpose in a task file. The file's docstring is acceptable.
- **Verification**: implementation-report.md should reference `tests/conftest.py` in the "Files Modified" table.

#### M-3: Source changes are uncommitted; per-bug-commit sequencing (DR-6/Approach A2) is unverifiable
- **File**: All source changes are in the working tree, not committed
- **Severity**: MAJOR
- **Category**: PROCESS / TRACEABILITY
- **Evidence**: `git diff HEAD --name-status` shows `M marine.py`, `M src/utils.py`, etc. `git log` has no commits since the base commit.
- **Why this matters**: ADR-01 (per-bug sequencing) and DR-6 explicitly say: "each commit is independently revertable; regressions are attributable to the most recent group". Without commits, reverting a single bug-fix group requires re-implementing it manually. The auditability the plan justifies is lost.
- **Suggested fix**: Before merging, split the working-tree changes into the 12-task commit sequence specified in the plan. At minimum, separate (a) bug-fixes (Package A), (b) docstring pass (task-10), (c) audit JSON (task-11), and (d) deletion + regression test (task-12) into distinct commits. Conftest.py and the marine_environment2.yaml change (if kept) each need their own commit with a justification.
- **Verification**: `git log --oneline 5cd3dafc..HEAD` should show at least 4 commits with task-aligned messages.

### MINOR

#### M-4: Function count discrepancy in implementation report
- **File**: `.forge/stages/3-implement/implementation-report.md`
- **Severity**: MINOR
- **Category**: DOCUMENTATION
- **Evidence**: Implementation report states "Google-style docstrings (Args/Returns/Raises) added to all public functions across 4 files: marine.py: 9 functions / src/core.py: 3 functions / src/read_process.py: 12 functions/methods / src/utils.py: 35 functions". Actual AST count: 9 / 17 / 13(+3 nested) / 52. The 3+12+35 numbers do not match reality — they appear to count only functions newly-documented in this session, while the architect plan A-11 expected 96 total.
- **Why this matters**: A reviewer or future maintainer reading the report will be misled about coverage scope.
- **Suggested fix**: Update the implementation report's per-file counts to reflect the actual AST count (9, 17, 13, 52 = 91 top-level + 3 nested in `incorporate_replaced_pos_info`). Note A-11's 96-estimate is also off by 5; either update the assumption note or add a brief reconciliation in the polish report.
- **Verification**: AST count command in this report's Step 1 evidence; numbers should match the report's table.

#### M-5: ADRs lack `affects_files` frontmatter
- **File**: `.forge/stages/2-architect/adrs/ADR-01-*.md` through `ADR-08-*.md`
- **Severity**: MINOR
- **Category**: TOOLING / PROCESS
- **Evidence**: `grep affects_files .forge/stages/2-architect/adrs/*.md` returns zero matches.
- **Why this matters**: The forge review skill cannot perform automated ADR-drift detection without `affects_files`. Manual drift detection was performed in this report, but future review iterations will not benefit.
- **Suggested fix**: Add an `affects_files` YAML frontmatter block to each ADR listing the file globs it governs. Example:
  ```yaml
  ---
  affects_files:
    - "marine.py"
    - "src/utils.py"
  ---
  ```
- **Verification**: `grep -l affects_files .forge/stages/2-architect/adrs/*.md | wc -l` should equal 8.

#### M-6: marine.py:153/154 was already correct pre-fix, but implementation report implies it was fixed
- **File**: `marine.py:154` and implementation report Task 6 entry
- **Severity**: MINOR (cosmetic accuracy)
- **Category**: DOCUMENTATION
- **Evidence**: `git show HEAD:marine.py | grep -n "Pool("` (HEAD = 5cd3daf base) shows line 142 was already `Pool(processes)` and only line 279 was `Pool(processes=cores)`. Implementation report says "marine.py:153 and marine.py:290: Pool(processes) (was Pool(processes=cores) — cores undefined, raised NameError)" — implying both lines were the bug. Only one line was the bug.
- **Suggested fix**: Reword: "marine.py:290: Pool(processes) (was Pool(processes=cores)). marine.py:153 was already correct; line shifted to 154 due to docstring insertions."
- **Verification**: implementation-report.md should distinguish the buggy site from the already-correct site.

#### M-7: Static-source test for C3 inadvertently covers the wrong function (still passes, but not per spec)
- **File**: `tests/unittests.py:124-135` (`test_marine_pool_uses_processes_param`)
- **Severity**: MINOR
- **Category**: TEST_QUALITY
- **Evidence**: The test asserts on `inspect.getsource(marine.generate_and_split_bed_files_for_all_positions)`. This is the right function (the C3 bug was at line 290 inside this function, post-fix). Confirmed: the function source contains `Pool(processes)` and not `Pool(processes=cores)`. The test PASSES correctly. No defect.
- **Suggested fix**: None required. Recorded for future-reviewer trust only — I challenged this finding adversarially in Stage 2 and it remains a true PASS.

## Pass 2: Security Findings

The original threat model (`.forge/stages/2-architect/threat-model.md`, not re-read in this review) addresses the offline-batch trust boundaries. The bug-fix package itself adds **no new attack surface**: no new imports, no new I/O paths, no new subprocess invocations, no network calls. The docstring pass is by definition non-executable.

### Findings

| Severity | Finding | Notes |
|---|---|---|
| LOW | `tests/unittests.py:113,130` hardcoded absolute path could leak filesystem layout if the file is shared publicly | Already covered as M-1; mentioned here for completeness |
| INFO | `marine_environment2.yaml` rewrite (C-1) removes pinned versions, weakening reproducibility — **not strictly a security finding**, but supply-chain hygiene degrades when versions are unpinned (a downstream `conda env create` will pull in the latest available `pysam`, `pandas`, etc., which may have known CVEs not present in the previously-pinned versions) | Resolved if C-1 is reverted |

No SQL injection (no SQL), no SSRF (no network), no XSS (no UI), no path traversal beyond user-provided `output_folder` (caller-controlled trust boundary, per architect plan Sec. 10). No secrets in diff.

## Adversarial Spec Verification

| AC | Reviewer Verdict | Evidence | Challenge | Sufficiency |
|----|------------------|----------|-----------|-------------|
| AC-1 (delete marine2.py) | PASS | `ls marine2.py` -> No such file | A naive impl could `mv` instead of `rm`; checked git status shows no rename | STRONG |
| AC-2 (H5 end=contig_length) | PASS | `src/utils.py:548-549` `if end > contig_length: end = contig_length`; test_get_intervals_partial_last_window asserts `intervals[-1][1] == 100` for length=100/interval=30 | Could a wrong impl pass? Only if the test fixture had length divisible by interval; the partial-window test specifically uses 100/30 to force the remainder branch | STRONG |
| AC-3 (C4 header=False removed) | PASS | `src/utils.py:878` shows `'{}/coverage/{}.tsv'.format(output_folder, contig)`; test asserts `'header=False' not in source` | Test is static-source, not behavioral. A compiled-only deployment defeats it (A-7), but not relevant here | STRONG |
| AC-4 (C3 Pool(processes) fix) | PASS | `marine.py:291` `Pool(processes)`; static-source test asserts both presence and absence | STRONG |
| AC-5 (C2/M2 tracemalloc/start_time at top of run) | PASS | `marine.py:337-338`; static-source test asserts `idx_start < idx_zero` | A wrong impl could place `start_time` after the first early-return; the test catches by ordering | STRONG |
| AC-6 (all unit tests pass) | PASS | `python -m pytest unittests.py -v` -> 13 passed in 3.76s (verified independently in marine_environment) | STRONG (re-run independently) |
| AC-7 (integration tests pass) | PASS (self-reported) | Implementation report claims pass; not re-run in review | WEAK (self-reported only) |
| AC-8 (Google docstrings on all functions in 4 files) | PASS | AST walk: 0 missing docstrings across 94 functions/methods | STRONG (verified independently via AST) |
| AC-9 (unused function audit produced) | PASS | `unused-functions-audit.json` exists, validates structurally, contains 95 entries with KEEP/REMOVE classification | STRONG |
| AC-10 (dead code removed + regression test) | PASS | `generate_empty_matrix_file` absent from `src/utils.py` (was line 929 in HEAD); `TestPublicAPIPreserved.test_generate_empty_matrix_file_removed` passes; verifies via `hasattr(utils, 'generate_empty_matrix_file') is False` | STRONG |

**Sufficiency tally**: 9/10 STRONG, 1/10 WEAK (AC-7 integration tests). 90% STRONG-or-better; well above the 50% WEAK threshold. The single WEAK item (integration tests) is acceptable because (a) integration tests have heavy fixture requirements and (b) they were re-run during the implementation stage, just not in this review pass.

## Quality Judge (B-037)

| Dimension | Verdict | Rationale |
|-----------|---------|-----------|
| Correctness | PASS_WITH_NOTES | All 10 ACs functionally pass; M-1 hardcoded path will fail in CI on hosts other than the developer's |
| Completeness | PASS_WITH_NOTES | Plan implemented; conftest.py and yaml changes are completeness gaps in the documentation, not the code |
| Maintainability | PASS_WITH_NOTES | Docstrings excellent; uncommitted working tree (M-3) reduces traceability for future maintainers |
| Security | PASS | No new attack surface; one supply-chain hygiene observation (C-1 yaml unpinning) which resolves on revert |

**Overall**: PASS_WITH_NOTES on three dimensions. Per Step 3.5, dimension PASSES (even with notes) do not auto-fail the review; the CHANGES_REQUIRED verdict is driven by C-1 (critical) and M-1 (CI-breaking).

## Verification Results

| Check | Result |
|-------|--------|
| Unit tests (marine_environment, Python 3.10) | PASS — 13 passed in 3.76s |
| Integration tests | NOT RE-RUN in this review (implementation report claims PASS) |
| Lint (`bandit -r src/ marine.py`) | NOT RUN in this review |
| Docstring AST coverage | PASS — 94/94 functions documented |
| Pool worker D-8 marker | PASS — 6/6 marked |
| Build | N/A (pure-Python project, no build) |

## Required Fixes Before Merge

In priority order:

1. **C-1**: Revert `marine_environment2.yaml` to base (or open a separate change with a recorded ADR).
2. **M-1**: Replace hardcoded `/tscc/projects/...` paths in `tests/unittests.py:113,130` with the relative-path idiom already in use at the top of the file.
3. **M-2**: Document `tests/conftest.py` in the implementation report's "Files Modified" table.
4. **M-3**: Stage and commit the working tree as the per-bug commit sequence specified by ADR-01/DR-6.
5. **M-4 .. M-6**: Optional documentation cleanups; not blocking.
6. **M-5**: Optional ADR `affects_files` frontmatter; only blocking if the project intends to rely on automated drift detection.

## Verified-Clean Patterns (input to next review round)

The following are confirmed clean and may be skipped in any re-review unless the revision touches them:
- AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-8, AC-9, AC-10 (functional behavior)
- All 8 ADRs (decision compliance)
- DR-1 through DR-12 (decision register)
- All Pool worker docstring D-8 markers (6/6)
- AST docstring coverage (94/94)
- Static-source-test mechanism (DR-5 / ADR-05)
- Audit JSON shape and conservative-keep classification (ADR-08)

## Re-Review Plan

After revision applies the C-1 revert and M-1 path fix:
- Re-run `python -m pytest unittests.py -v` (must remain 13/13)
- Re-run `git diff HEAD -- marine_environment2.yaml` (must be empty)
- Re-grep `tests/unittests.py` for `/tscc/` (must be 0 matches)

If those three checks pass, the verdict moves to APPROVED for Stage 4.
