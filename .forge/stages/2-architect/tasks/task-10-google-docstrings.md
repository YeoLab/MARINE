# TASK-10: Add Google-style docstrings to marine.py, src/core.py, src/utils.py, src/read_process.py

<!-- DEPENDENCIES: task-09 -->
<!-- COVERS: FR-12, AC-12 -->
<!-- BUG: documentation gap (none of these files carry per-function docs) -->

## Goal

Add a Google-style docstring to every top-level function (and every method, if any) in:

- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/marine.py`
- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/core.py`
- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/utils.py`
- `/tscc/projects/ps-yeolab3/bay001/codebase/MARINE/src/read_process.py`

Docstrings are additive. They do NOT change any function signature, body, behavior, or import.

## Scope

Affected functions (exact count, from `grep -c "^def "` at the start of this stage):

| File | Function count |
|------|---------------|
| `marine.py` | 11 |
| `src/core.py` | 18 |
| `src/utils.py` | 53 |
| `src/read_process.py` | 14 |
| **Total** | **96** |

If the count differs from 96 at execution time, halt and report — that means task-08 (or another task) added or removed functions and the inventory must be re-validated before proceeding.

Functions that already have a docstring should NOT be modified — verify by checking whether the first statement of the function body is a string literal. The inventory above counts all `def` lines; the agent must skip any that already have docstrings and report the count of skipped functions in the verification output.

## Style Specification

Google-style docstring template:

```python
def my_function(arg1, arg2=None):
    """One-line summary in imperative mood, ending with a period.

    Optional longer description explaining the function's role in the
    pipeline. Include enough context that a reader who has not seen
    the call site can understand why the function exists.

    Args:
        arg1: Description of arg1. State the expected type if not
            obvious from the name. Required.
        arg2: Description of arg2. Default is None.

    Returns:
        Description of the return value, including its shape/type.

    Raises:
        ValueError: When arg1 is empty. (Only document raises that
            the function explicitly raises or that callers must
            handle. Do not invent.)
    """
    ...
```

Rules:

1. **Summary line**: one sentence, imperative mood, ends with a period, fits on a single line under 100 chars.
2. **Args section**: list every parameter from the signature, in order. For `*args` and `**kwargs`, document the contract. Mark `Optional` parameters by stating their default.
3. **Returns section**: required if the function returns a non-None value. Omit if the function returns `None` implicitly or is a side-effect-only function (state that fact in the summary instead).
4. **Raises section**: ONLY include if the function body has an explicit `raise` statement. Do not speculate about exceptions from libraries.
5. **No type annotations in the docstring** if the signature already has type hints. State types only when they aid clarity and are not in the signature.
6. **Do not document private implementation details** that the caller does not need. Keep docstrings pragmatic.
7. **Pool worker functions** (see `architecture-plan.md` Section 13): note in the summary line that the function is called via `multiprocessing.Pool.map` or `Pool.imap_unordered`, naming its single tuple parameter contract. Example:
   ```
   """Worker function for Pool.imap_unordered; unpacks a 13-tuple of edit-finding parameters.
   ```

## Steps

1. For each of the four files in scope, walk the function inventory in source order.
2. For each function without an existing docstring, insert a Google-style docstring as the first statement of the function body.
3. Match the existing indentation precisely (4-space indent inside function bodies).
4. Do not change any other text on any line. Do not reformat. Do not add type hints. Do not add comments outside the docstring.
5. After all four files are updated, run the verification commands.

## Acceptance Criteria

- AC-T10-1: Every top-level function in the four target files has a docstring as its first statement. Verifiable via:
  ```python
  python -c "
  import ast, sys
  for path in ['marine.py', 'src/core.py', 'src/utils.py', 'src/read_process.py']:
      tree = ast.parse(open(path).read())
      for node in ast.walk(tree):
          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
              assert ast.get_docstring(node) is not None, f'{path}::{node.name} has no docstring'
  print('OK')
  "
  ```
- AC-T10-2: Every docstring follows Google format — verified by a lightweight regex check that each docstring contains either an `Args:` section (for functions with at least one parameter) OR a one-line summary terminated by a period. Pure-no-arg functions may omit `Args:`.
- AC-T10-3: All existing unit tests pass: `cd tests && python -m pytest unittests.py -v` exits 0.
- AC-T10-4: All existing integration tests pass: `cd tests && bash integration_tests_run.sh python` exits 0.
- AC-T10-5: `git diff --stat` shows changes ONLY in the four target files. No other file is modified.
- AC-T10-6: For each file, `git diff` shows ZERO removed lines outside of docstring insertions (i.e., `git diff --shortstat` reports `0 deletions(-)` for non-docstring contexts). Tooling check:
  ```bash
  git diff -U0 marine.py src/core.py src/utils.py src/read_process.py \
    | grep '^-' | grep -v '^---' | grep -vE '^-\s*("""|\s*$)' | wc -l
  ```
  Must return `0`.
- AC-T10-7: No new imports added in any of the four files. Verifiable via:
  ```bash
  diff <(grep -E '^(import|from) ' marine.py src/core.py src/utils.py src/read_process.py) \
       <(git show HEAD:marine.py HEAD:src/core.py HEAD:src/utils.py HEAD:src/read_process.py | grep -E '^(import|from) ')
  ```
  Must return empty.
- AC-T10-8: Pool worker functions (`get_unique_barcodes_for_reads_in_bamfile`, `process_combination_for_split`, `merge_files_by_chromosome`, `find_edits_and_split_bams_wrapper`, `concat_and_write_bams_wrapper`, `get_coverage_wrapper`) have summary lines that explicitly note their role as Pool workers and document the tuple-unpacking contract.

## Verification Command

```bash
cd /tscc/projects/ps-yeolab3/bay001/codebase/MARINE && \
python -c "
import ast
files = ['marine.py', 'src/core.py', 'src/utils.py', 'src/read_process.py']
missing = []
for path in files:
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if ast.get_docstring(node) is None:
                missing.append(f'{path}::{node.name}')
assert not missing, f'Missing docstrings: {missing}'
print('All functions documented.')
" && \
cd tests && python -m pytest unittests.py -v && \
bash integration_tests_run.sh python
```

## Notes

- This task adds ~6-12 new docstring lines per function, so the diff will be ~600-1100 added lines across the four files. That is acceptable because each line traces directly to the FR-12 requirement.
- Do NOT modify `src/annotate.py` or any test file in this task — those are out of scope.
- Do NOT add module-level docstrings; only function-level. (If module docstrings already exist, do not touch them.)
- If a function has an existing docstring in any format, leave it alone. Audit but do not rewrite.
- This task ships before task-11/12 (the cleanup pass). That order is deliberate: by documenting first, the cleanup task can use the docstrings as a confirmation that "yes, this function is intentional" before considering it for removal.
