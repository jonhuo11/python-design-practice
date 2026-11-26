"""Task executor. See SPEC.md. Keep the public API; internals are up to you."""

from __future__ import annotations

import threading  # noqa: F401
from typing import Any, Callable, Iterable


class Closed(Exception):
    pass


class DependencyFailed(Exception):
    pass


class CancelledError(Exception):
    pass


# ---------------- Level 1 ----------------
class BoundedBlockingQueue:
    def __init__(self, capacity: int) -> None:
        pass

    def put(self, item: Any, timeout: float | None = None) -> bool:
        raise NotImplementedError

    def get(self, timeout: float | None = None) -> Any:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


# ---------------- Level 2+ ----------------
class Future:
    def result(self, timeout: float | None = None) -> Any:
        raise NotImplementedError

    def done(self) -> bool:
        raise NotImplementedError

    # Level 3
    def cancel(self) -> bool:
        raise NotImplementedError

    def add_done_callback(self, cb: Callable[["Future"], None]) -> None:
        raise NotImplementedError


class ThreadPool:
    def __init__(self, num_workers: int) -> None:
        pass

    def submit(self, fn: Callable[[], Any], *, deps: Iterable[Future] = (),
               key: str | None = None, priority: int = 0) -> Future:
        raise NotImplementedError

    def shutdown(self, wait: bool = True, cancel_pending: bool = False) -> None:
        raise NotImplementedError

    # Level 4
    def set_limit(self, key: str, n: int) -> None:
        raise NotImplementedError

    # Level 5
    def resize(self, n: int) -> None:
        raise NotImplementedError
