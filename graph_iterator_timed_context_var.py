"""
Using decorators and iterators to build flamegraph generation!

Context var
"""

from contextvars import ContextVar
from functools import wraps
import random
import time


class TimerContext:
    __slots__ = ("_name", "_stack", "_t")

    def __init__(self, name: str = "unknown"):
        self._name: str = name
        self._stack: list[TimerContext] = []
        self._t: int = 0

    def call(self, name: str) -> "TimerContext":
        nc = TimerContext(name)
        self._stack.append(nc)
        return nc

    def done(self, t_elapsed: int) -> None:
        self._t = t_elapsed

    def __iter__(self):  # dfs traversal of tree
        q = list[tuple[TimerContext, int]]([(self, 0)])
        while q:
            top, lvl = q.pop(-1)
            yield (top._name, top._t, lvl)
            for child_call in reversed(top._stack):
                q.append((child_call, lvl + 1))


# Context Vars might be better here
_current: ContextVar[TimerContext] = ContextVar(
    "timer_current",
)


def timed(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        child = _current.get().call(fn.__name__)
        token = _current.set(child)
        t = time.perf_counter_ns()
        try:
            return fn(*args, **kwargs)
        finally:
            child.done(time.perf_counter_ns() - t)
            _current.reset(token)

    return inner


# ===== EXAMPLE USE =====


@timed
def funny_fun():
    print("funny fun")
    funnier_fun()
    funnier_fun(True)
    funnier_fun(True)
    funnier_fun()
    print("funny fun done")


@timed
def funnier_fun(do_wow: bool = False):
    print("funnier fun")
    if do_wow:
        wow()


@timed
def wow():
    print("wow")
    for _ in range(random.randint(0, 5)):
        sub_wow()


@timed
def sub_wow():
    c = 0
    for _ in range(random.randint(0, 9999)):
        c += 1
    print(f"sub wow: {c}")


def main():
    base_ctx = _current.set(TimerContext())
    funny_fun()

    print("=====")
    for name, t_ns, lvl in _current.get(base_ctx):
        print(f"{lvl * "\t"}{name} ({t_ns} ns)")


if __name__ == "__main__":
    main()
