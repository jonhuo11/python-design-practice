from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, overload

type Transform[A, B] = Callable[[A], B]


@overload
def compose[A, B, C](f: Transform[A, B], g: Transform[B, C], /) -> Transform[A, B]: ...
@overload
def compose[A, B, C, D](
    f: Transform[A, B], g: Transform[B, C], h: Transform[C, D], /
) -> Transform[A, D]: ...


def compose(*transformations: Transform[..., Any]) -> Transform[..., Any]:
    def composed(x):
        for transformation in transformations:
            x = transformation(x)
        return x

    return composed


# monads
class HBinder(Protocol):
    @overload
    def __call__[A, B](self, f1: Transform[A, B], /) -> Transform[A, B]: ...
    @overload
    def __call__[A, B, C](
        self, f1: Transform[A, B], f2: Transform[B, C], /
    ) -> Transform[A, C]: ...
    @overload
    def __call__[A, B, C, D](
        self, f1: Transform[A, B], f2: Transform[B, C], f3: Transform[C, D], /
    ) -> Transform[A, D]: ...


@dataclass(slots=True)
class MonadState:
    step: int = 0
    caller_name: str = ""


class BoundFunc(Protocol):
    def __call__[T](self, s: MonadState, v: T) -> T: ...


def build_binder(bound_function: BoundFunc) -> HBinder:
    def custom_bind(*transformations: Transform[..., Any]) -> Transform[..., Any]:
        def composed(x: Any) -> Any:
            for i, transformation in enumerate(transformations):
                x = bound_function(
                    MonadState(i, transformation.__qualname__), transformation(x)
                )
            return x

        return composed

    return custom_bind  # type: ignore[return-value]


"""
def exit_on_err(v):
	if v == err_val:
		raise Exception()
	return v
bind = build_binder(exit_on_err)
pipeline = bind(f, g)
pipeline(val)
# this would be like
def pipeline(f, g):
	x = f()
	exit_on_err(x)
	x = g()
	exit_on_err(x)
	return x
"""

if __name__ == "__main__":

    def no_evens(s: MonadState, v: int):
        if v % 2 == 0:
            raise Exception(
                f"Error at pipeline step {s.step} ({s.caller_name}): v == {v} is even"
            )
        return v

    bind = build_binder(no_evens)

    def add1(a):
        return a + 1

    def add2(a):
        return a + 2

    pipeline1 = bind(add1, add1)
    pipeline2 = bind(add2, add2)

    try:
        pipeline1(1)
    except Exception as e:
        print(e)

    try:
        pipeline2(1)
    except Exception as e:
        print(e)
