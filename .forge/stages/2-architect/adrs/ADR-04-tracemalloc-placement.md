# ADR-04: tracemalloc.start() at Top of run() Without Guard
Date: 2026-04-25
Status: Accepted

## Context
`tracemalloc.start()` and `start_time = time.time()` are currently in the `__main__` block of `marine.py`. C2 means `run()` calls `zero_edit_found(... start_time ...)` on early-return paths but `start_time` is never defined inside `run()`. M2 means `tracemalloc.get_traced_memory()` inside `run()` is reached before `tracemalloc.start()` because the start() call comes after `run()` in `__main__`.

## Decision
Place `start_time = time.time()` as the first executable statement of `run()` and `tracemalloc.start()` as the second. Remove both from `__main__`. Do NOT add an `if not tracemalloc.is_tracing()` guard.

## Alternatives Considered
- Place the calls just before `tracemalloc.get_traced_memory()`: Rejected because the early-return paths at lines 378 and 411 still use `start_time` and would NameError.
- Add `if not tracemalloc.is_tracing()` guard: Rejected because Python stdlib documents that re-calling `start()` while tracing is a no-op; the guard adds noise without benefit.

## Consequences
- Positive: All call paths through `run()` have `start_time` and tracemalloc tracing available. No new branches.
- Negative: If `run()` is called repeatedly within one Python process, `tracemalloc.start()` is called repeatedly (harmless per Python stdlib).
- Risks: Future Python releases could change the no-op behavior. Mitigation: add the guard if needed (cheap retrofit).

## References
- Architecture plan section: 5 (Decision Register, D-3)
- Assumptions: A-2, A-3
