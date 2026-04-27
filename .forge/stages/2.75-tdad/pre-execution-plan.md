## Pre-Execution Plan: 2.75-tdad

1. **Three most likely failure modes**:
   - Import errors during static analysis: pysam/pybedtools may not be importable in the analysis env, causing ast-based coverage mapping to fail. Signal: empty or missing impact-report.json. Mitigation: TDAD should use AST-only analysis, not runtime import.
   - Over-broad impact set: every task flagged as "touches all tests" because utils.py functions are called transitively everywhere. Signal: all 12 tasks show impact=HIGH. Watch for false positives from transitive call chains.
   - Missing test files: only unittests.py and integration_tests_auto_check.py exist; if TDAD looks for pytest fixtures or conftest.py it may report incomplete coverage. Signal: 0 test functions mapped.

2. **First verification steps**: Confirm impact-report.json was written, has entries for each of the 12 tasks, and maps to at least the 6 unit tests in unittests.py.

3. **Context dependencies**:
   - .forge/stages/2.5-spec/TASKS.md
   - .forge/stages/2-architect/tasks/ (12 task files)
   - tests/unittests.py
   - tests/integration_tests_auto_check.py
