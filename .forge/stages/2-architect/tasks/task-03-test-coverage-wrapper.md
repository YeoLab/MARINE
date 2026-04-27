# TASK-03: Add unit test for get_coverage_wrapper filename (C4)

<!-- DEPENDENCIES: task-01 -->
<!-- COVERS: FR-10, AC-8 -->
<!-- BUG: C4 (test-first) -->

## Goal

Write a unit test that verifies the filename construction logic of `get_coverage_wrapper()` does not include `header=False` as a `.format()` keyword argument. The test uses static source inspection to avoid running pysam/polars I/O.

## Steps

1. Edit `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests/unittests.py`.
2. Add a new method to the `TestUtilsFunctions` class created in TASK-02. Insert it after the three `get_intervals` tests, still inside the same class.
3. The test must NOT actually call `get_coverage_wrapper()` (it requires polars DataFrames and a contig coverage tuple). Instead it inspects the source.

## Required Test Code (Insert Verbatim)

```python
    def test_get_coverage_wrapper_no_header_kwarg(self):
        # C4 regression: .format() call must not pass header=False
        import inspect
        from utils import get_coverage_wrapper
        source = inspect.getsource(get_coverage_wrapper)
        # The bug was: '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)
        # The fix is:  '{}/coverage/{}.tsv'.format(output_folder, contig)
        self.assertNotIn('header=False', source,
                         ".format() must not receive header keyword argument")
        self.assertIn(".format(output_folder, contig)", source,
                      "Filename must be built with two positional .format() args")
```

## Acceptance Criteria

- AC-T03-1: `TestUtilsFunctions` class contains a method `test_get_coverage_wrapper_no_header_kwarg`.
- AC-T03-2: Running `cd tests && python -m pytest unittests.py::TestUtilsFunctions::test_get_coverage_wrapper_no_header_kwarg -v` FAILS (because C4 fix is not yet applied, so `header=False` is still in the source).
- AC-T03-3: All four tests in `TestUtilsFunctions` so far are collected (3 from task-02 + 1 from this task).

## Verification Command

```
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py::TestUtilsFunctions::test_get_coverage_wrapper_no_header_kwarg -v 2>&1 | tee /tmp/task-03-out.txt; \
grep -q 'FAIL' /tmp/task-03-out.txt && echo "RED-AS-EXPECTED"
```

## Notes

- `import inspect` and `from utils import get_coverage_wrapper` are inside the method body so the test stays self-contained and does not affect other tests' import surface.
- Do not add the import at module top.
- This is a static-source assertion test, not a behavioral test. The behavioral test is implicitly covered by the integration suite when `--all_cells_coverage` is used.
