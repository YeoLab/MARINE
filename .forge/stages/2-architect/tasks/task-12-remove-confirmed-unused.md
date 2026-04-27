# TASK-12: Remove confirmed-unused functions and add regression tests

<!-- DEPENDENCIES: task-11 -->
<!-- COVERS: FR-13, FR-14, AC-13, AC-14 -->
<!-- BUG: dead-code accumulation (cleanup half) -->

## Goal

For each function classified `REMOVE_CANDIDATE` in `unused-functions-audit.json` (produced by task-11), delete it from its source file. Add a regression test that asserts the surviving public API of each affected file still imports and is callable.

This task makes only the deletions justified by the audit. No "while we're at it" cleanup.

## Pre-condition

- `task-11` is complete.
- `unused-functions-audit.json` has been read and reviewed by a human reviewer (the build agent should pause for confirmation before this task starts).
- For each REMOVE_CANDIDATE, the human reviewer has either left it as REMOVE_CANDIDATE (approving deletion) or downgraded it to KEEP (vetoing deletion). The agent must re-read the audit JSON at task start to pick up any human edits.

## Steps

1. Re-read `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/.forge/stages/2-architect/unused-functions-audit.json`.
2. Build the deletion list: every entry where `classification == "REMOVE_CANDIDATE"`.
3. If the deletion list is empty, mark the task complete and emit `TASK-12: PASS - no removals needed`. Skip remaining steps.
4. Group deletions by file. For each file, delete each function's `def <name>(...):` line and its body (terminating at the next top-level `def`, top-level `class`, or end-of-file).
5. After each file's deletions, run `python -c "import <module>"` to confirm the file still parses and imports cleanly.
6. Add unit tests to `tests/unittests.py` in a new class `TestPublicAPIPreserved(unittest.TestCase)`:
   - One test method per affected file: `test_<file>_imports_still_work`.
   - Each test imports the module and asserts that every KEEP-classified function from that file is still accessible by name (`assertTrue(hasattr(<module>, '<name>'))` for each KEEP entry).
   - This is a thin regression net: it does not exercise behavior, only presence. The existing integration tests cover behavior.
7. Run the full verification command and confirm green.

## Constraints

- Delete ONLY functions explicitly classified `REMOVE_CANDIDATE` in the (post-review) audit. Do not delete imports the function used unless the import itself is now unused (per `pyflakes` or equivalent static check).
- Do not modify any function that is being kept.
- Do not change function ordering within a file. Closing the gap is fine; reordering is not.
- Do not change blank-line spacing between surviving functions beyond what is required to match the existing 2-blank-lines-between-functions style.
- If deleting a function leaves a now-unused `import` at the top of the file, remove that import too — but only that import. Verify with:
  ```bash
  python -m pyflakes /tscc/projects/ps-yeolab3/bay001/codebase/MARINE/<file>
  ```
  No `imported but unused` warnings should be added by this task; pre-existing warnings should be left alone.

## Acceptance Criteria

- AC-T12-1: For every entry in the audit's REMOVE_CANDIDATE list (post-review), the function definition no longer exists in its source file. Verifiable by re-running the audit script and confirming `function_count_remove_candidate == 0`.
- AC-T12-2: All KEEP-classified functions are still importable. The new `TestPublicAPIPreserved` class in `tests/unittests.py` verifies this for all four target files.
- AC-T12-3: All existing unit tests pass: `cd tests && python -m pytest unittests.py -v` exits 0.
- AC-T12-4: All existing integration tests pass: `cd tests && bash integration_tests_run.sh python` exits 0.
- AC-T12-5: `python -m pyflakes marine.py src/core.py src/utils.py src/read_process.py` introduces zero new warnings relative to the pre-task baseline. (Capture baseline before deletion; diff after.)
- AC-T12-6: `git diff` shows changes ONLY in (a) the four target source files and (b) `tests/unittests.py`. No other file is modified.
- AC-T12-7: For each deleted function, `git log -p -S '<function_name>'` shows the function being removed in this commit (audit trail).
- AC-T12-8: The newly added `TestPublicAPIPreserved` class contains exactly four test methods (one per file), each running in <1 second.

## Verification Command

```bash
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE && \
# Pre-deletion pyflakes baseline
python -m pyflakes marine.py src/core.py src/utils.py src/read_process.py 2>&1 | tee /tmp/pyflakes-after.txt && \
# Confirm no new warnings (build agent must compare to /tmp/pyflakes-before.txt captured before this task)
# Re-run audit script
python -c "
import ast, json
data = json.load(open('.forge/stages/2-architect/unused-functions-audit.json'))
removed = [f['name'] for f in data['functions'] if f['classification'] == 'REMOVE_CANDIDATE']
files = {f['name']: f['file'] for f in data['functions']}
for name in removed:
    path = files[name]
    tree = ast.parse(open(path).read())
    present = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert name not in present, f'{name} still in {path}'
print(f'Confirmed {len(removed)} functions removed.')
" && \
cd tests && python -m pytest unittests.py -v && bash integration_tests_run.sh python
```

## Test Stub for `TestPublicAPIPreserved`

Insert this class above `unittest.main()` in `tests/unittests.py`:

```python
class TestPublicAPIPreserved(unittest.TestCase):
    """Regression net for task-12 unused-function removals.

    Asserts that every function classified KEEP in
    .forge/stages/2-architect/unused-functions-audit.json is still
    accessible after the cleanup. If a future deletion accidentally
    removes a KEEP function, this test fails before integration.
    """

    @classmethod
    def setUpClass(cls):
        import json, pathlib
        audit_path = pathlib.Path(__file__).parent.parent / '.forge/stages/2-architect/unused-functions-audit.json'
        cls.audit = json.loads(audit_path.read_text())
        cls.keep_by_file = {}
        for f in cls.audit['functions']:
            if f['classification'] == 'KEEP':
                cls.keep_by_file.setdefault(f['file'], []).append(f['name'])

    def _assert_all_present(self, module, file_key):
        for name in self.keep_by_file.get(file_key, []):
            self.assertTrue(hasattr(module, name), f'{file_key}::{name} missing after cleanup')

    def test_marine_keeps_present(self):
        import marine
        self._assert_all_present(marine, 'marine.py')

    def test_core_keeps_present(self):
        import core
        self._assert_all_present(core, 'src/core.py')

    def test_utils_keeps_present(self):
        import utils
        self._assert_all_present(utils, 'src/utils.py')

    def test_read_process_keeps_present(self):
        import read_process
        self._assert_all_present(read_process, 'src/read_process.py')
```

## Notes

- If, after re-reading the post-review audit, the REMOVE_CANDIDATE list is empty, this task still adds the `TestPublicAPIPreserved` class — that gives future cleanup passes a regression net.
- If the integration test fails after deletion, do NOT restore the deleted function silently. Instead: revert the specific deletion, downgrade that function's classification to KEEP in the audit JSON with note `"removed_caused_integration_failure"`, and re-run the task.
- The four test methods together must run in <1 second total. They do not exercise function bodies, only presence.
