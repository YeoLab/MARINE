## Pre-Execution Plan: 2-architect (re-run, scope expansion)

1. **Three most likely failure modes**:
   - Docstring scope creep: architect writes docstrings for every line of every file rather than function-level summaries only. Signal: task count balloons above 15. Watch for.
   - Unused function detection false positives: functions that look unused but are called via dynamic dispatch (e.g. multiprocessing Pool worker targets, click callbacks). Signal: any removal task that touches Pool worker functions or CLI-decorated functions without first verifying call sites.
   - Conflict with existing 9 tasks: new tasks duplicate or contradict the original bug-fix tasks (e.g. removing a function that is also being fixed). Signal: task 10+ references the same line ranges as tasks 1-9.

2. **First verification steps**: After architect completes, confirm task list has original 9 bug-fix tasks intact plus 2-3 new tasks for docstrings and unused function removal. Check that no existing tasks were dropped or renumbered in a way that breaks the requirements trace.

3. **Context dependencies**:
   - .forge/stages/2-architect/architecture-plan.md (existing plan to extend, not replace)
   - .forge/stages/1-requirements/architect-prompt.md (original requirements)
   - .forge/stages/1-requirements/context/05-business-logic.md (bug fix specs)
   - marine.py, src/core.py, src/utils.py, src/read_process.py (source files for unused function analysis)
   - .forge/codemap.md (structural index)
