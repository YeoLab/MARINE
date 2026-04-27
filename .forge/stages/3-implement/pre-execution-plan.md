## Pre-Execution Plan: 3-implement

1. **Three most likely failure modes**:
   - Task-11→12 auto-advance: build agent ignores the mandatory HUMAN-REVIEW-HALT between task-11 (audit) and task-12 (removal) and proceeds automatically. Signal: task-12 runs without user confirmation. Must halt and surface unused-functions-audit.json for review.
   - Docstring regression: task-10 accidentally edits non-docstring lines (e.g. reformats function signatures, changes logic). Signal: non-docstring lines appear in git diff. The AC requires a check that only docstring lines changed.
   - Pool fix breaks existing callers: adding `processes=4` parameter to generate_and_split_bed_files_for_all_positions() without updating its call site in run() leaves a TypeError. Signal: test failure after task-06.

2. **First verification steps**: After each task, run `cd tests && python -m pytest unittests.py -v`. After tasks touching marine.py, also run the integration test if feasible.

3. **Context dependencies**:
   - .forge/stages/2-architect/implementer-prompt.md (master build instructions)
   - .forge/stages/2.5-spec/SPEC.md (18 ACs — the definition of done)
   - .forge/stages/2-architect/tasks/ (all 12 task files with line numbers)
   - marine.py, src/core.py, src/utils.py, src/read_process.py, tests/unittests.py
