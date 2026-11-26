# Task Executor — 4 levels + stretch (90 min, no AI)

Same format as the KV practical. **Read one level at a time.**
Pacing: L1 15 min · L2 20 min · L3 30 min · L4 25 min · L5 stretch.

Run: `pytest test_executor.py -k Level1 -q` (… `Level5`). Tests that check for deadlocks
time out after about 2 s, so a hung implementation fails instead of hanging.

## Ground rules
- Python, using only `threading` primitives (`Lock`, `RLock`, `Condition`, `Event`,
  `Semaphore`, `Thread`) plus `heapq`, `collections` and `itertools`.
- **Banned:** `queue`, `concurrent.futures`, `asyncio`, `multiprocessing`.
- No busy-waiting: no `sleep` loops that poll state.
- Worker threads must be daemon threads.
- Exceptions to use (already defined in the skeleton): `Closed`, `DependencyFailed`,
  `CancelledError`, and the built-in `TimeoutError`.

---

## Level 1 — `BoundedBlockingQueue(capacity)`
FIFO, thread-safe, `capacity >= 1`.
- `put(item, timeout=None) -> bool`: block while the queue is full. Return `True` once
  the item is inserted, or `False` on timeout (the item is not inserted). Raise `Closed` if
  the queue is closed, including when it gets closed while this call is blocked.
- `get(timeout=None) -> item`: block while the queue is empty. Raise `TimeoutError` on
  timeout. Once the queue is closed, `get` keeps returning items until it is empty, then
  raises `Closed`. Getters blocked at the moment of `close()` wake up and raise `Closed`.
- `close() -> None`: idempotent.
- `__len__() -> int`

---

## Level 2 — `ThreadPool(num_workers)` and `Future`
- The constructor starts exactly `num_workers` worker threads.
- `submit(fn) -> Future`: `fn` takes no arguments. With nothing else in play, tasks
  start in submission order (FIFO).
- An exception raised by a task never kills its worker.
- `Future.result(timeout=None)`: return the value, re-raise the task's exception, or raise
  `TimeoutError` if the timeout runs out first.
- `Future.done() -> bool`
- `shutdown(wait=True)`: afterwards, `submit` raises `RuntimeError`. Tasks already
  submitted still run. With `wait=True`, block until every task has finished and every
  worker thread has exited. Idempotent.

---

## Level 3 — Dependencies, cancellation, callbacks
`submit(fn, *, deps=())`: `deps` are Futures from the same pool.
- A task becomes **ready** once all its deps have succeeded. Among ready tasks, the one
  that became ready first starts first. A task with no deps, or whose deps had all
  succeeded already, is ready at submit time.
- **A task waiting on its deps must not occupy a worker thread.**
- If any dep fails or is cancelled, the task completes with `DependencyFailed` and never
  runs. This happens **as soon as** that first dep fails, without waiting for the other
  deps, and it propagates transitively. If a dep had already failed at submit time, the
  returned Future is already done when `submit` returns.
- `Future.cancel() -> bool`: if the task has not started, cancel it and return `True`. Its
  `result()` then raises `CancelledError`, and its dependents get `DependencyFailed`.
  Return `False` if the task is running or finished. Return `True` if it was already
  cancelled.
- `Future.add_done_callback(cb)`: call `cb(future)` exactly once, after the future
  completes in any way. If the future is already done, call `cb` immediately in the
  calling thread. Callbacks may call back into the pool (`submit`, `result` on a done
  future, `cancel`) without deadlocking. An exception raised by a callback is swallowed and
  does not stop the other callbacks.

---

## Level 4 — Priorities and per-key concurrency limits
`submit(fn, *, deps=(), key=None, priority=0)`
- Among ready tasks, higher `priority` starts first. Ties go to whichever became ready
  first.
- `set_limit(key, n)`, with `n >= 1`: at most `n` tasks with that `key` run at the same
  time. Keys without a limit are unlimited.
- A task held back by its key's limit must not occupy a worker thread and **must not block
  any other task**: no head-of-line blocking. When a slot for that key opens up, the
  waiting tasks with that key follow the same priority-then-ready-order rule.
- Calling `set_limit` while tasks are running takes effect immediately. Raising a limit
  starts waiting tasks right away. Lowering a limit never interrupts running tasks; new
  tasks for that key wait until fewer than `n` are running.

---

## Level 5 (stretch) — Resize and cancelling shutdown
- `resize(n)`, with `n >= 1`: growing starts new workers immediately. Shrinking retires
  surplus workers once they finish their current task; running tasks are never
  interrupted. Raise `RuntimeError` if the pool has been shut down.
- `shutdown(wait=True, cancel_pending=False)`: with `cancel_pending=True`, every task
  that has not started is cancelled. That includes tasks waiting on deps and tasks held
  back by a key limit. Every one of them raises **`CancelledError`**, not
  `DependencyFailed`, even when one of its deps was also cancelled. Running tasks still
  finish.
