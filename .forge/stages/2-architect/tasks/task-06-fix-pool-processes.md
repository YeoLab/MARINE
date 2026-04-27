# TASK-06: Apply C3 fix in marine.py:generate_and_split_bed_files_for_all_positions

<!-- DEPENDENCIES: task-05 -->
<!-- COVERS: FR-5, AC-5 -->
<!-- BUG: C3 -->

## Goal

Replace `Pool(processes=cores)` with `Pool(processes)` at `marine.py` line 279.

## Steps

1. Open `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py`.
2. Locate line 279. The exact current text is:
   ```
       with Pool(processes=cores) as pool:
   ```
3. Change it to:
   ```
       with Pool(processes) as pool:
   ```
   (replace `processes=cores` with `processes`)

## Acceptance Criteria

- AC-T06-1: Line 279 of `marine.py` reads `    with Pool(processes) as pool:`.
- AC-T06-2: `grep 'Pool(processes=cores)' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py` returns no match.
- AC-T06-3: `grep 'Pool(processes)' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py` returns at least one match (line 279).
- AC-T06-4: `cd tests && python -m pytest unittests.py -v` continues to pass for all collected tests.
- AC-T06-5: `python -c "import sys; sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE'); import marine"` does not raise.

## Verification Command

```
grep -n 'with Pool(processes) as pool:' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py && \
! grep 'Pool(processes=cores)' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py && \
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && \
python -m pytest unittests.py -v
```

## Notes

- This uses positional argument (D-1). Do NOT use `Pool(processes=processes)` — that adds keyword noise without value.
- The function signature on line 214 already declares `processes=4` as the default; keep that declaration unchanged.
- Do not change the indentation or the `as pool:` portion.
