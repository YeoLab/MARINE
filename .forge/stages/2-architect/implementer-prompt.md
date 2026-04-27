# Implementer Prompt: MARINE Bug Fixes (C1-C4 + H5 + Tracemalloc + Tests) + Documentation & Cleanup

<!-- STAGE: 2-architect -> 3-implement -->
<!-- STATUS: READY_FOR_BUILD -->
<!-- UPDATED_UTC: 2026-04-25T10:00:00Z -->
<!-- REVISION: Extended 2026-04-25 to cover tasks 10-12 (Google docstrings, unused-function audit, cleanup). The bug-fix tasks 1-9 are unchanged. -->

## 1. Mission

Apply the changes specified in `architecture-plan.md` and the per-task files in `tasks/`. The work runs in two packages, sequentially:

- **Package A (tasks 1-9)**: bug fixes for C1-C4, H5, and the tracemalloc/start_time placement issue. Original scope.
- **Package B (tasks 10-12)**: Google-style docstrings on every function in `marine.py`, `src/core.py`, `src/utils.py`, `src/read_process.py`; an audit identifying genuinely-unused functions; and surgical removal of the audit-confirmed unused functions with a regression test.

Make NO changes outside the scope of the listed tasks. Stop and surface any ambiguity rather than guess.

## 2. Operating Constraints

**Global (apply to every task):**

- Work strictly task-by-task in the order given in `architecture-plan.md` Section 6 (1, 2, 3, ..., 12).
- After each task, run the verification command listed in the task file. Do not advance until it passes.
- Do not modify function signatures in any task.
- Do not touch `.github/workflows/main.yml`, `marine_environment2.yaml`, `src/annotate.py`, or any context file under `.forge/` (except the audit JSON written by task-11).
- Do not reformat, do not normalize whitespace, do not modernize string formatting elsewhere.
- For any uncertainty, halt and emit a question. Do not improvise.
- Python 3.10 syntax only.

**Package A (tasks 1-9, bug fixes):**

- Do not edit lines outside the explicit fix locations.
- Do not add `import` statements. Every needed import is already present.
- Do not add docstrings, type hints, or comments unless an acceptance criterion explicitly requires it. (Docstrings come in task-10, not earlier.)

**Package B (tasks 10-12, docs and cleanup):**

- Task-10 may add docstrings (only). Every other line in the four target files must be byte-identical to its pre-task-10 state. Verified by `git diff` review (AC-T10-6).
- Task-11 writes `unused-functions-audit.json` and modifies NO source files.
- Task-12 may delete functions classified `REMOVE_CANDIDATE` in the post-review audit, may delete imports that become unused as a result, and adds the `TestPublicAPIPreserved` class to `tests/unittests.py`. It modifies no other source files.
- Between task-11 and task-12, halt for human review of the audit JSON. The audit JSON is the contract; do not act on it without human confirmation.

## 3. Inputs You Have

- `.forge/stages/1-requirements/architect-prompt.md` (Stage 1 output)
- `.forge/stages/1-requirements/context/01..11-*.md` (deep context)
- `.forge/stages/2-architect/architecture-plan.md` (this stage's plan)
- `.forge/stages/2-architect/tasks/task-NN-*.md` (one per task)
- `.forge/stages/2-architect/assumptions.json`
- `.forge/stages/2-architect/threat-model.md`
- `.forge/project.json` (verification commands)

## 4. Verification Commands (Authoritative)

| Purpose | Command | Pass |
|---------|---------|------|
| Unit tests | `cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && python -m pytest unittests.py -v` | All tests pass; >=9 collected after task-08; >=13 collected after task-12 |
| Unit tests (alt) | `cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && python -m unittest unittests.py` | OK |
| Integration tests | `cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/tests && bash integration_tests_run.sh python` | exit 0 |
| C1 verification | `test ! -e /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine2.py` | exit 0 |
| C3 verification | `! grep 'Pool(processes=cores)' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py` | exit 0 (no match) |
| C4 verification | `! grep 'header=False' /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py \| grep '\.format'` | exit 0 |
| H5 verification | `python -c "import sys; sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src'); from utils import get_intervals; r=get_intervals('c', {'c': 100}, 30); assert r[-1][1]==100, r"` | no AssertionError |
| Tracemalloc placement | `python -c "import inspect, sys; sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE'); import marine; src=inspect.getsource(marine.run); assert 'tracemalloc.start()' in src and 'start_time = time.time()' in src"` | no AssertionError |
| Docstring coverage (task-10) | `cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE && python -c "import ast; [exec('tree=ast.parse(open(p).read()); [exec(\"assert ast.get_docstring(n) is not None, p+\\\"::\\\"+n.name\") for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]') for p in ['marine.py','src/core.py','src/utils.py','src/read_process.py']]"` | no AssertionError |
| Audit JSON valid (task-11) | `cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE && python -c "import json; d=json.load(open('.forge/stages/2-architect/unused-functions-audit.json')); assert d['function_count_keep']+d['function_count_remove_candidate']==d['function_count_total']"` | no AssertionError |
| Cleanup applied (task-12) | `cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE && python -c "import ast,json; d=json.load(open('.forge/stages/2-architect/unused-functions-audit.json')); rm=[(f['name'],f['file']) for f in d['functions'] if f['classification']=='REMOVE_CANDIDATE']; [exec('t=ast.parse(open(p).read()); assert n not in {x.name for x in ast.walk(t) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}, n') for n,p in rm]"` | no AssertionError |

## 5. What "Done" Looks Like

For each task:
1. Edit the file as specified (or, for task-11, write the audit JSON).
2. Run the task's verification command.
3. Confirm exit 0.
4. Move to the next task.

**Mandatory pause after task-11**: do NOT auto-advance to task-12. The audit JSON requires human review. The build agent must surface the audit summary and wait for explicit confirmation (or downgraded REMOVE_CANDIDATE entries in the JSON) before starting task-12.

For the whole change:
- All 14 acceptance criteria from `architecture-plan.md` Section 12 satisfied (AC-1..AC-14).
- One file deleted: `marine2.py` (task-01).
- One file added: `.forge/stages/2-architect/unused-functions-audit.json` (task-11).
- Up to N functions deleted from the four target source files (N = post-review REMOVE_CANDIDATE count from the audit; could be 0).
- Four target source files have docstrings on every function (task-10).
- `tests/unittests.py` has new test classes from tasks 02, 03, 07, and 12.

## 6. Failure-Mode Awareness

- **FM-01 (scope expansion)**: If you find yourself wanting to fix anything not on the explicit list, STOP and surface it. Do not silently include it. In task-10 specifically, this means: do not "improve" function bodies while writing docstrings.
- **FM-02 (silent regression)**: If integration tests fail at task-09, task-10, or task-12, do NOT alter unrelated code to make them pass. Bisect by reverting the most-recent task and report.
- **FM-03 (test discovery breakage)**: If `unittest.main()` ends up not at the bottom of `tests/unittests.py`, fix that immediately — it is required by the existing test framework setup. Tasks 02, 03, 07, and 12 all add test classes; each must insert ABOVE `unittest.main()`.
- **FM-04 (audit-action conflation)**: Do NOT delete any function in task-11. Task-11 is read-only. Deletion is task-12's job and only after human review.
- **FM-05 (Pool worker over-removal)**: All six Pool worker functions are listed in `architecture-plan.md` Section 13 with their dispatch sites. If the audit somehow classifies one of them as REMOVE_CANDIDATE, that is a bug in the audit script — do NOT delete; halt and report.
- **FM-06 (continuation-line import miss)**: The codebase uses backslash-continued `from X import a, b, \\\n c, d` patterns extensively. Naive grep misses names on continuation lines. The audit must use `ast.parse` + `ast.ImportFrom.names[].name`, not grep, to enumerate imports.

## 7. Reporting Format

After each task, emit a one-line report:
```
TASK-NN: [PASS|FAIL] - <one-line summary> - <verification cmd exit code>
```

After all tasks, emit a final summary listing each AC-N with PASS/FAIL.
