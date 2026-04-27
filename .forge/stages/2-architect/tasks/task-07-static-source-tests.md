# TASK-07: Add static-source unit tests for C2 (start_time) and C3 (Pool kwarg)

<!-- DEPENDENCIES: task-06 -->
<!-- COVERS: FR-8 supporting infrastructure; AC-8 contributes -->
<!-- BUG: C2, C3 (test-first for C2; regression-lock for C3) -->

## Goal

Add two unit tests that verify the correctness of the C2 and C3 fixes via static source inspection. The C3 test should pass immediately (task-06 already applied the fix). The C2 test should FAIL (red), demonstrating it detects the unfixed C2 bug. Task-08 will apply the C2 fix and turn it green.

## Steps

1. Edit `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests/unittests.py`.
2. Inside the existing `TestUtilsFunctions` class (created in task-02), add two new methods after the existing methods. Insert verbatim:

```python
    def test_marine_run_starts_time_at_top(self):
        # C2 regression: start_time = time.time() must appear before any zero_edit_found call inside run()
        import inspect
        import sys as _sys
        _sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE')
        import marine
        source = inspect.getsource(marine.run)
        # start_time assignment must precede first zero_edit_found reference
        idx_start = source.find('start_time = time.time()')
        idx_zero = source.find('zero_edit_found')
        self.assertGreaterEqual(idx_start, 0,
                                "run() must define start_time via time.time()")
        self.assertGreaterEqual(idx_zero, 0,
                                "run() must reference zero_edit_found")
        self.assertLess(idx_start, idx_zero,
                        "start_time must be defined before first zero_edit_found call")

    def test_marine_pool_uses_processes_param(self):
        # C3 regression: Pool must use the function's `processes` parameter, not undefined `cores`
        import inspect
        import sys as _sys
        _sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE')
        import marine
        source = inspect.getsource(marine.generate_and_split_bed_files_for_all_positions)
        self.assertNotIn('Pool(processes=cores)', source,
                         "Pool must not reference undefined `cores`")
        self.assertIn('Pool(processes)', source,
                      "Pool must use the `processes` function parameter")
```

## Acceptance Criteria

- AC-T07-1: `TestUtilsFunctions` class contains `test_marine_run_starts_time_at_top` and `test_marine_pool_uses_processes_param`.
- AC-T07-2: `unittest.main()` remains the final non-blank line of the file.
- AC-T07-3: Running `cd tests && python -m pytest unittests.py::TestUtilsFunctions::test_marine_pool_uses_processes_param -v` PASSES (C3 fix already applied in task-06).
- AC-T07-4: Running `cd tests && python -m pytest unittests.py::TestUtilsFunctions::test_marine_run_starts_time_at_top -v` FAILS (C2 not yet fixed).
- AC-T07-5: All 6 existing tests continue to pass; the 4 prior `TestUtilsFunctions` tests continue to pass.

## Verification Command

```
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py::TestUtilsFunctions::test_marine_pool_uses_processes_param -v && \
python -m pytest unittests.py::TestUtilsFunctions::test_marine_run_starts_time_at_top -v 2>&1 | tee /tmp/task-07-out.txt; \
grep -q 'test_marine_run_starts_time_at_top FAIL' /tmp/task-07-out.txt && echo "C2-RED-AS-EXPECTED"
```

## Notes

- The `_sys.path.insert(0, ...)` uses absolute path so the test works regardless of CWD.
- Importing `marine` is gated inside the test methods; do NOT add `import marine` at the top of `unittests.py` (it is a heavy import with subprocess/pysam side effects we want to avoid for the read_process tests).
- Do not modify any other file in this task.
