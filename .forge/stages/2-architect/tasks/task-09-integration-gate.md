# TASK-09: Integration Test Gate

<!-- DEPENDENCIES: task-08 -->
<!-- COVERS: NFR-1, NFR-2, AC-11 -->
<!-- BUG: regression sentinel for C1-C4, H5, M2 -->

## Goal

Run the full integration test suite as the final regression gate. No code changes in this task — only verification.

## Steps

1. From `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests/`, run:
   ```
   bash integration_tests_run.sh python
   ```
2. Confirm exit code is 0.
3. Run unit tests one more time:
   ```
   python -m pytest unittests.py -v
   ```
4. Confirm exit code is 0 and at least 9 tests are collected and passing.

## Acceptance Criteria

- AC-T09-1: `bash integration_tests_run.sh python` exits 0.
- AC-T09-2: `python -m pytest unittests.py -v` exits 0 with at least 9 tests passing.
- AC-T09-3: `git status` shows the expected staged changes only:
  - Deleted: `marine2.py`
  - Modified: `marine.py`, `src/utils.py`, `tests/unittests.py`
  - No other changes.

## Verification Command

```
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
bash integration_tests_run.sh python && \
python -m pytest unittests.py -v && \
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE && \
git status --short
```

## Notes

- If integration tests fail, do NOT alter source code to make them pass. Bisect by reverting the most-recent committed task and re-run.
- Do NOT touch any file in this task — verification only.
- This task is the final regression gate. Once passed, the architect stage's deliverable is fully verified at runtime, and the build stage can hand off to review.
