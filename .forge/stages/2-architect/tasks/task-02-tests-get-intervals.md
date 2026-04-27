# TASK-02: Add unit tests for get_intervals (H5)

<!-- DEPENDENCIES: task-01 -->
<!-- COVERS: FR-8, FR-9, FR-11, AC-8, AC-9, AC-10 -->
<!-- BUG: H5 (test-first) -->

## Goal

Write unit tests for `get_intervals()` BEFORE applying the H5 fix. After this task, the new tests should FAIL (red), demonstrating they detect the bug. Task-04 will apply the fix and turn them green.

## Steps

1. Edit `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests/unittests.py`.
2. Update the `from utils import ...` line near the top to also import `get_intervals`. Specifically change:
   ```python
   from utils import get_contig_lengths_dict
   ```
   to:
   ```python
   from utils import get_contig_lengths_dict, get_intervals
   ```
3. Insert a new class `TestUtilsFunctions(unittest.TestCase)` immediately ABOVE the `unittest.main()` line at the bottom of the file. The class must contain three test methods exactly as specified below.

## Required Test Code (Insert Verbatim)

```python
class TestUtilsFunctions(unittest.TestCase):
    def test_get_intervals_partial_last_window(self):
        # H5 regression: contig length 100, interval 30 -> last interval ends at 100
        intervals = get_intervals('chr1', {'chr1': 100}, 30)
        self.assertEqual(intervals[-1][1], 100,
                         "Last interval end must equal contig_length, not interval boundary")
        self.assertEqual(intervals, [[0, 30], [30, 60], [60, 90], [90, 100]])

    def test_get_intervals_exact_division(self):
        # H5 edge case: contig length 60, interval 30 -> exactly two clean windows
        intervals = get_intervals('chr1', {'chr1': 60}, 30)
        self.assertEqual(intervals, [[0, 30], [30, 60]])

    def test_get_intervals_short_contig(self):
        # H5 edge case: contig length 100 with interval_length larger than contig
        intervals = get_intervals('chr1', {'chr1': 100}, 2000000)
        self.assertEqual(intervals, [[0, 100]])
```

## Acceptance Criteria

- AC-T02-1: `tests/unittests.py` contains a class `TestUtilsFunctions` with exactly the three methods named above.
- AC-T02-2: `unittest.main()` remains the final non-blank line of the file.
- AC-T02-3: `from utils import` line includes both `get_contig_lengths_dict` and `get_intervals`.
- AC-T02-4: Running `cd tests && python -m pytest unittests.py -v` reports `test_get_intervals_partial_last_window` FAILS (because H5 fix is not yet applied). The other two new tests pass. The 6 existing tests pass.

## Verification Command

```
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py::TestUtilsFunctions -v 2>&1 | tee /tmp/task-02-out.txt; \
grep -q 'test_get_intervals_partial_last_window FAIL' /tmp/task-02-out.txt && echo "RED-AS-EXPECTED"
```

## Notes

- The test must be placed BEFORE `unittest.main()` so it is discovered.
- Do not add any other test methods, no helper functions, no class-level attributes.
- The "FAIL as expected" outcome is the success criterion for this task; the fix follows in task-04.
