# TASK-04: Apply H5 fix in src/utils.py:get_intervals

<!-- DEPENDENCIES: task-02 -->
<!-- COVERS: FR-7, AC-7, AC-9, AC-10 -->
<!-- BUG: H5 -->

## Goal

Change `end == contig_length` (comparison) to `end = contig_length` (assignment) in `src/utils.py:get_intervals()`. This single character change makes the H5 unit test from task-02 turn green.

## Steps

1. Open `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py`.
2. Locate line 440. The exact current text (with leading whitespace) is:
   ```
               end == contig_length
   ```
   (12 leading spaces, then `end == contig_length`)
3. Change it to:
   ```
               end = contig_length
   ```
   (12 leading spaces, then `end = contig_length`)

## Acceptance Criteria

- AC-T04-1: Line 440 of `src/utils.py` reads `            end = contig_length` (single `=`).
- AC-T04-2: `grep -n 'end == contig_length' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py` returns no match.
- AC-T04-3: `cd tests && python -m pytest unittests.py::TestUtilsFunctions -v` reports all four `TestUtilsFunctions` tests so far passing EXCEPT `test_get_coverage_wrapper_no_header_kwarg` which is still red.
- AC-T04-4: All 6 existing `TestReadProcessFunctions` tests continue to pass.

## Verification Command

```
grep -n 'end = contig_length' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py && \
! grep -n 'end == contig_length' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py && \
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py::TestUtilsFunctions::test_get_intervals_partial_last_window -v
```

## Notes

- This is a single-character edit (`==` → `=`).
- Do NOT change the surrounding whitespace, comments, or blank lines.
- Do NOT add a comment about the fix.
- Do NOT change the `if end > contig_length:` guard above it.
