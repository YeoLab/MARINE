# Technical Constraints

## Language and Runtime

- **Python 3.10 only** — do not use Python 3.11+ syntax (match/case, ParamSpec, etc.)
- **Conda environment** — `marine_environment2.yaml` is the source of truth for dependencies
- **No new pip/conda packages** — all fixes must use imports already present in each file

## Existing Imports Available (no new imports needed)

### marine.py already imports:
- `time` (for `time.time()`)
- `tracemalloc` (for `tracemalloc.start()`, `get_traced_memory()`)
- `multiprocessing.Pool` (already imported via `from multiprocessing import Pool`)
- `os`, `sys`, `glob`, `argparse`, `collections`, `subprocess`, `shutil`

### src/utils.py already imports:
- All needed libraries; the C4 fix just removes a bad keyword argument

### tests/unittests.py already imports:
- `unittest`, `os`, `sys`
- `from utils import get_contig_lengths_dict` (sys.path already set to `../src/`)
- `from read_process import ...`
- New tests need `from utils import get_intervals` — already in scope since `utils` is
  imported

## Test Framework Constraints

- Tests must use `unittest.TestCase` subclass pattern
- No pytest fixtures, marks, or parametrize decorators
- `unittest.main()` must remain at the bottom of `tests/unittests.py`
- New tests can be added as methods to the existing `TestReadProcessFunctions` class
  OR to a new class (e.g., `TestUtilsFunctions`) in the same file

## Code Style Constraints

- Do not reformat code not being changed (no whitespace normalization, no comment removal)
- Match existing style: `.format()` in older functions, f-strings in newer code
- Do not add or remove blank lines outside the changed lines
- Keep existing docstrings unchanged

## CI Constraints

- `.github/workflows/main.yml` runs integration tests via conda — must not break
- Branch: `brian_dev` (current working branch)
- No changes to `.github/workflows/main.yml`

## Architecture Constraints

- `src/` module imports use `sys.path.append('../src/')` or `sys.path.append('src/')` pattern
  (not package-style `from src.utils import ...`)
- Multiprocessing uses spawn context (set in `core.py`); no changes to this
- `CB_N = 1` remains hardcoded in `utils.py` (H6 out of scope)
