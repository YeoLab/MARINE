# Review Fixup Prompt — Stage 4 Round 1

<!-- FORGE_STAGE: 4-review -->
<!-- INTENDED_FOR: 4.5-revision -->
<!-- BASE_REPORT: review-report.md -->

The reviewer found 1 CRITICAL and 3 MAJOR issues plus 4 MINOR cleanups. Apply these fixes in order. Re-run unit tests after each fix. After all CRITICAL+MAJOR fixes are applied, re-run `/forge review` for re-verification.

## CRITICAL — must fix

### C-1: Revert out-of-scope rewrite of `marine_environment2.yaml`

The architecture plan Section 11 explicitly forbids changing this file. The working tree has rewritten it from a 281-line pinned conda env to a 20-line unpinned env. Either revert it, or open a separate change with a recorded ADR.

```bash
# Option A: revert (recommended)
git checkout HEAD -- marine_environment2.yaml

# Option B: keep the change but record an ADR. If choosing this, also:
#   - add .forge/stages/2-architect/adrs/ADR-09-conda-env-modernization.md
#   - update architecture-plan.md Section 11 to remove the prohibition
#   - update DECISIONS_SUMMARY.md
#   - add a deviation record under .forge/stages/3-implement/spec-deviations.json
```

**Verification**: `git diff HEAD -- marine_environment2.yaml | wc -l` must return `0`.

## MAJOR — must fix

### M-1: Replace hardcoded absolute path in `tests/unittests.py`

Two new tests insert `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE` into `sys.path`. This will fail on every other host.

In `tests/unittests.py`, replace BOTH occurrences of:
```python
_sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE')
```
with:
```python
_marine_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _marine_root not in _sys.path:
    _sys.path.insert(0, _marine_root)
```

(Or factor the path setup into a helper at module top — the existing `directory_path` block at lines 5-7 already uses the relative-path idiom; mirror that.)

**Verification**: `grep -n "/tscc/" tests/unittests.py` must return `0` lines.

### M-2: Document `tests/conftest.py` in the implementation report

The new file `tests/conftest.py` exists in the working tree but is not mentioned in `implementation-report.md`. Either:
- Add a row to the "Files Modified" table in `.forge/stages/3-implement/implementation-report.md`, or
- Move the explanation into `.forge/stages/2-architect/tasks/task-XX.md` if it deserves its own task entry.

**Verification**: `grep conftest .forge/stages/3-implement/implementation-report.md` must return at least 1 match.

### M-3: Commit the working tree as the per-bug commit sequence

ADR-01 / DR-6 mandate per-bug-group commits. The working tree currently has all changes in one uncommitted blob. Split into at least:
- Commit 1: Task 1 — delete marine2.py
- Commit 2: Tasks 2-5 — H5 + C4 fixes plus their tests (`src/utils.py`, `tests/unittests.py`)
- Commit 3: Tasks 6-8 — C3 + C2/M2 fixes plus their static-source tests (`marine.py`)
- Commit 4: Task 10 — Google docstrings (4 files, docstring-only)
- Commit 5: Tasks 11-12 — audit JSON + dead-code removal + regression test
- Commit 6: `tests/conftest.py` (separate concern, with its justification)
- Commit 7 (only if C-1 is kept under Option B): `marine_environment2.yaml` modernization, with ADR-09 reference

Each commit message must reference its task ID and the AC(s) it covers.

**Verification**: `git log --oneline 5cd3dafc..HEAD` must show at least 5 commits with task-aligned subjects.

## MINOR — recommended but not blocking

### M-4: Correct the function-count numbers in the implementation report

In `implementation-report.md` Task 10 entry, update the per-file counts to reflect the actual AST-walk numbers:
- marine.py: 9 (correct)
- src/core.py: 17 (was reported as 3)
- src/read_process.py: 13 top-level + 3 nested = 16 (was reported as 12)
- src/utils.py: 52 (was reported as 35)
- Total: 91 top-level + 3 nested = 94 (was reported as 59)

### M-5: Add `affects_files` frontmatter to ADRs

In each `.forge/stages/2-architect/adrs/ADR-*.md`, add YAML frontmatter:
```yaml
---
affects_files:
  - "marine.py"           # adjust per ADR scope
  - "src/utils.py"
---
```

This enables automated ADR-drift detection in future review rounds.

### M-6: Reword Task 6 entry in the implementation report

Current text implies both `marine.py:153` and `marine.py:290` were buggy. Only line 290 (now 291) was the C3 bug. Suggested edit:
> Task 6 — C3 Fix: marine.py:291 changed from `Pool(processes=cores)` (where `cores` was undefined inside `generate_and_split_bed_files_for_all_positions`) to `Pool(processes)`. marine.py:154 was already correct (`Pool(processes)`); its line number shifted from 142 to 154 due to docstring insertions.

### M-7: No action required — adversarial Stage 2 confirmed test_marine_pool_uses_processes_param is correct

## Re-Review Checklist

After fixes are applied, the reviewer will re-run:

- [ ] `git diff HEAD -- marine_environment2.yaml | wc -l` returns 0
- [ ] `grep -n "/tscc/" tests/unittests.py` returns 0 matches
- [ ] `grep conftest .forge/stages/3-implement/implementation-report.md` returns at least 1
- [ ] `git log --oneline 5cd3dafc..HEAD` returns at least 5 commits
- [ ] `python -m pytest unittests.py -v` returns 13/13 PASS

If all five pass, the verdict moves to APPROVED.
