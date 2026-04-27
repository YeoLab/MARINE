# TASK-11: Audit unused functions and produce a removal candidate list

<!-- DEPENDENCIES: task-10 -->
<!-- COVERS: FR-13, AC-13 -->
<!-- BUG: dead-code accumulation in marine.py / src/core.py / src/utils.py / src/read_process.py -->

## Goal

Produce a single artifact — `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/.forge/stages/2-architect/unused-functions-audit.json` — that lists every top-level function in the four target files, classifies each as KEEP or REMOVE_CANDIDATE, and provides the evidence used for that classification. NO source files are modified in this task.

This task is the analysis pass. Removal happens in task-12 only after the audit has been reviewed.

## Scope

Files audited:

- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py`
- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/core.py`
- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py`
- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/read_process.py`

## Classification Rules

A function is classified as **KEEP** if ANY of the following hold:

1. **Imported by name** in any other module under `MARINE/` (search: `marine.py`, `src/*.py`, `tests/*.py`). Match against:
   ```bash
   grep -rE "from (utils|core|read_process|marine|annotate) import .*\b<NAME>\b" /tscc/projects/ps-yeolab3/bay001/codebase/MARINE
   ```
   Including continuation lines (the existing code uses backslash-continued imports — the audit MUST follow continuations).
2. **Called by name** in any module under `MARINE/` (excluding the function's own definition line):
   ```bash
   grep -rE "\b<NAME>\s*\(" /tscc/projects/ps-yeolab3/bay001/codebase/MARINE
   ```
3. **Pool worker target** — the function name appears as the first argument of `pool.map`, `pool.imap`, `pool.imap_unordered`, or `pool.apply_async` anywhere in the codebase. The known Pool workers (KEEP unconditionally):
   - `get_unique_barcodes_for_reads_in_bamfile` (marine.py:57)
   - `process_combination_for_split` (marine.py:159)
   - `find_edits_and_split_bams_wrapper` (src/core.py:496)
   - `concat_and_write_bams_wrapper` (src/utils.py:867)
   - `get_coverage_wrapper` (src/utils.py:660)
   - `merge_files_by_chromosome` (src/utils.py:978)
4. **CLI entry point** — referenced by `argparse` setup or invoked by the `if __name__ == "__main__"` block in `marine.py`. The MARINE codebase uses argparse (not click); the relevant entry is `run()` itself, called from `marine.py:__main__`.
5. **Referenced in tests/** — name appears in `tests/unittests.py` or any test file. Even if the function is only test-imported, it is KEEP because removing it would break the test.
6. **Referenced in CI/scripts** — name appears in `.github/workflows/main.yml`, `tests/integration_tests_run.sh`, or `tests/integration_tests_auto_check.py`.
7. **Dynamic dispatch suspicion** — the codebase uses `getattr`, `globals()`, `eval`, `exec`, or `importlib` near the function's module. (Verified at this stage: NONE of the four files use dynamic dispatch — see `architecture-plan.md` Section 13. So this rule will not produce any KEEP votes here, but the audit script must still log the check.)

A function is classified as **REMOVE_CANDIDATE** only if ALL of the following hold:

- None of the KEEP rules above match.
- The function is not the module's `if __name__ == "__main__"` block (those are not `def`s anyway).
- The function name does not start with `_` and end with `_` (those are dunder-style; out of scope).
- A manual code-reading note has been added to `unused-functions-audit.json` explaining what the function appears to do and why the auditor believes it is dead.

## Audit Output Schema

`/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/.forge/stages/2-architect/unused-functions-audit.json`:

```json
{
  "schema_version": "1.0.0",
  "generated_utc": "<ISO8601>",
  "files_audited": ["marine.py", "src/core.py", "src/utils.py", "src/read_process.py"],
  "function_count_total": 96,
  "function_count_keep": <int>,
  "function_count_remove_candidate": <int>,
  "functions": [
    {
      "name": "get_unique_barcodes",
      "file": "marine.py",
      "line": 39,
      "classification": "KEEP",
      "evidence": [
        {"rule": "called_internally", "location": "marine.py:307"}
      ],
      "removal_note": null
    },
    {
      "name": "<example_unused>",
      "file": "src/utils.py",
      "line": 1234,
      "classification": "REMOVE_CANDIDATE",
      "evidence": [
        {"rule": "no_imports_found", "location": null},
        {"rule": "no_internal_calls_found", "location": null},
        {"rule": "no_test_references", "location": null},
        {"rule": "not_a_pool_worker", "location": null},
        {"rule": "not_a_cli_entry", "location": null}
      ],
      "removal_note": "Helper for an earlier code path that was refactored away. No callers remain after task-08."
    }
  ]
}
```

## Steps

1. Build the function inventory by parsing each of the four files with `ast`. For each `FunctionDef` and `AsyncFunctionDef` node, record `name`, `file`, `line`.
2. For each function, run all KEEP-rule checks listed above. Use `grep -rn` from the repo root, scoped to `marine.py`, `src/`, and `tests/`. Always match whole-word (`\b<name>\b`) to avoid substring false positives (e.g., `find` vs `find_edits`).
3. For each match, record `{"rule": <rule_name>, "location": "<file>:<line>"}` in the function's `evidence` list.
4. If a function accumulates ANY KEEP evidence, classify as KEEP. Otherwise classify as REMOVE_CANDIDATE.
5. For each REMOVE_CANDIDATE, manually read its body and add a `removal_note` explaining what the function does and why removal is safe. If the auditor cannot confidently explain the function's purpose, downgrade the classification to KEEP and add `{"rule": "uncertain_purpose", "location": null}` to evidence — uncertainty defaults to keep.
6. Write the JSON artifact.
7. Print a summary to stdout:
   ```
   Audit complete:
     Total functions: 96
     Keep: <N>
     Remove candidates: <M>
   Remove candidates list:
     - <file>:<line> <name>
     - ...
   ```
8. Halt for human review (the build agent will prompt; do not auto-advance to task-12).

## Acceptance Criteria

- AC-T11-1: `unused-functions-audit.json` exists at the path above and is valid JSON.
- AC-T11-2: `function_count_total` equals the actual `def` count in the four files (currently 96; may differ if task-10 inventory drift occurred — halt and report if so).
- AC-T11-3: `function_count_keep + function_count_remove_candidate == function_count_total`.
- AC-T11-4: Every entry in `functions[]` has at least one item in `evidence[]`.
- AC-T11-5: All six known Pool workers are classified KEEP with `pool_worker` in their evidence.
- AC-T11-6: `run` (marine.py:285) is classified KEEP with `cli_entry_point` in its evidence.
- AC-T11-7: All functions imported in the existing `from utils import ...`, `from core import ...`, `from read_process import ...` statements (in marine.py, src/core.py, tests/unittests.py) are classified KEEP.
- AC-T11-8: NO source files (`marine.py`, `src/*.py`) are modified in this task. `git status` shows the only new file is the JSON audit. Verifiable:
  ```bash
  git status --short | grep -vE "^\?\? \.forge/stages/2-architect/unused-functions-audit\.json$" | grep -E "(marine\.py|src/.*\.py|core\.py|utils\.py|read_process\.py)" | wc -l
  ```
  Must return `0`.
- AC-T11-9: All existing unit and integration tests still pass (sanity check that no accidental edits crept in):
  ```
  cd tests && python -m pytest unittests.py -v && bash integration_tests_run.sh python
  ```

## Verification Command

```bash
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE && \
python -c "
import json
data = json.load(open('.forge/stages/2-architect/unused-functions-audit.json'))
assert data['function_count_keep'] + data['function_count_remove_candidate'] == data['function_count_total'], 'Counts do not sum'
for f in data['functions']:
    assert f['evidence'], f'No evidence for {f[\"name\"]}'
    if f['classification'] == 'REMOVE_CANDIDATE':
        assert f['removal_note'], f'Missing removal_note for {f[\"name\"]}'
print(f'Audit valid. KEEP={data[\"function_count_keep\"]} REMOVE_CANDIDATE={data[\"function_count_remove_candidate\"]}')
" && \
cd tests && python -m pytest unittests.py -v && bash integration_tests_run.sh python
```

## Notes

- This task is intentionally conservative: any uncertainty maps to KEEP. The cost of falsely keeping a dead function is a few KB of source; the cost of falsely removing a live function is a runtime crash. The asymmetry justifies the bias.
- The audit JSON becomes the input contract for task-12. Do not move on until the audit is reviewed.
- Continuation-line imports MUST be parsed. `marine.py:27-30` uses backslash continuations; `src/core.py:15-22` uses backslash continuations; `tests/unittests.py:10-12` uses backslash continuations. A naive `grep "from utils import"` will miss names on continuation lines. Use a Python-side import collector that walks `ast.parse(...)` to enumerate `ImportFrom` nodes — this captures all `alias.name` entries regardless of source-line layout.
