# TASK-05: Apply C4 fix in src/utils.py:get_coverage_wrapper

<!-- DEPENDENCIES: task-03 -->
<!-- COVERS: FR-6, AC-6, AC-8 -->
<!-- BUG: C4 -->

## Goal

Remove the invalid `header=False` keyword argument from the `.format()` call in `get_coverage_wrapper()` at `src/utils.py` line 663.

## Steps

1. Open `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py`.
2. Locate line 663. The exact current text is:
   ```
       output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)
   ```
3. Change it to:
   ```
       output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig)
   ```
   (delete the 14 characters `, header=False` immediately before the closing parenthesis).

## Acceptance Criteria

- AC-T05-1: Line 663 of `src/utils.py` reads `    output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig)`.
- AC-T05-2: `grep '.format(output_folder, contig, header=False)' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py` returns no match.
- AC-T05-3: `cd tests && python -m pytest unittests.py::TestUtilsFunctions::test_get_coverage_wrapper_no_header_kwarg -v` PASSES.
- AC-T05-4: All other tests still pass.

## Verification Command

```
! grep 'header=False' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py | grep '\.format' && \
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py -v
```

## Notes

- Single-line edit: only `, header=False` is removed.
- Indentation, surrounding code, and the docstring block at lines 665-673 are NOT touched.
- Do NOT change `.format(...)` to an f-string. The surrounding function uses `.format()`; preserve style.
