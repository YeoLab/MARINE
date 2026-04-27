# TASK-01: Delete marine2.py

<!-- DEPENDENCIES: -->
<!-- COVERS: FR-1, AC-1 -->
<!-- BUG: C1 -->

## Goal

Remove the dead-code experimental file `marine2.py` from the repository root.

## Steps

1. From the repo root `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE`, run:
   ```
   git rm marine2.py
   ```
2. Do not commit yet — wait until verification passes.

## Acceptance Criteria

- AC-T01-1: The file `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine2.py` does not exist.
- AC-T01-2: `git status` shows `marine2.py` as a deleted file (staged).
- AC-T01-3: `cd tests && python -m pytest unittests.py -v` exits 0 and reports the existing 6 tests pass (no new tests yet).
- AC-T01-4: `cd tests && bash integration_tests_run.sh python` exits 0 (regression gate).

## Verification Command

```
test ! -e /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine2.py && \
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py -v && \
bash integration_tests_run.sh python
```

## Notes

- Do not delete any other file.
- Do not edit `marine.py` or any other file in this task.
- The codebase audit confirms `marine2.py` is not imported anywhere; verified via `grep -r 'marine2' .` returning only self-references.
