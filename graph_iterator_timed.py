"""
Using decorators and iterators to build flamegraph generation!
"""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import wraps
import random
import time
from typing import Concatenate, ParamSpec, TypeVar


class TimerContext:
    __slots__ = ("_name", "_stack", "_t_elapsed_ns")

    @dataclass(frozen=True, slots=True)
    class TimedCall:
        name: str
        t_elapsed_ns: int
        lvl: int

    def __init__(self, name: str = "unknown"):
        self._name: str = name
        self._stack: list[TimerContext] = []
        self._t_elapsed_ns: int = 0

    def call(self, name: str) -> "TimerContext":
        nc = TimerContext(name)
        self._stack.append(nc)
        return nc

    def done(self, t_elapsed_ns: int) -> None:
        self._t_elapsed_ns = t_elapsed_ns

    def __iter__(self) -> Iterator[TimedCall]:  # dfs traversal of tree
        q: list[tuple[TimerContext, int]] = [(self, 0)]
        while q:
            top, lvl = q.pop(-1)
            yield TimerContext.TimedCall(top._name, top._t_elapsed_ns, lvl)
            for child_call in reversed(top._stack):
                q.append((child_call, lvl + 1))


P = ParamSpec("P")
R = TypeVar("R")


# Context Vars might be better here
def timed(
    fn: Callable[Concatenate[TimerContext, P], R],
) -> Callable[Concatenate[TimerContext, P], R]:
    @wraps(fn)
    def inner(timer_ctx: TimerContext, *args: P.args, **kwargs: P.kwargs):
        child_timer_ctx = timer_ctx.call(fn.__name__)
        t = time.perf_counter_ns()
        try:
            ret = fn(
                child_timer_ctx, *args, **kwargs
            )  # so that timer_ctx can be passed down
        finally:
            child_timer_ctx.done(time.perf_counter_ns() - t)
            return ret

    return inner


# ===== EXAMPLE USE =====


@timed
def funny_fun(ctx: TimerContext):
    print("funny fun")
    funnier_fun(ctx)
    funnier_fun(ctx, True)
    funnier_fun(ctx, True)
    funnier_fun(ctx)
    print("funny fun done")


@timed
def funnier_fun(ctx: TimerContext, do_wow: bool = False):
    print("funnier fun")
    if do_wow:
        wow(ctx)


@timed
def wow(ctx: TimerContext):
    print("wow")
    for _ in range(random.randint(0, 5)):
        sub_wow(ctx)


@timed
def sub_wow(_: TimerContext):
    c = 0
    for _ in range(random.randint(0, 9999)):
        c += 1
    print(f"sub wow: {c}")


def main():
    tc = TimerContext()
    funny_fun(tc)

    print("=====")
    for tcl in tc:
        print(f"{tcl.lvl * "\t"}{tcl.name} ({tcl.t_elapsed_ns} ns)")


if __name__ == "__main__":
    main()
