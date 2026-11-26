"""Tests for SPEC.md.  Run one level at a time:  pytest test_executor.py -k Level1 -q

EXECUTOR_IMPL=<module> tests a different module (default: executor).
Every blocking call in here has a timeout, so a deadlock fails instead of hanging.
"""

import faulthandler
import importlib
import itertools
import os
import random
import sys
import threading
import time
from collections import Counter, defaultdict

import pytest

m = importlib.import_module(os.environ.get("EXECUTOR_IMPL", "executor"))
Queue, ThreadPool = m.BoundedBlockingQueue, m.ThreadPool
Closed, DependencyFailed, CancelledError = m.Closed, m.DependencyFailed, m.CancelledError

sys.setswitchinterval(1e-5)  # force frequent thread switches to surface races
T = 2.0                      # generous "should have happened by now" timeout


# ----------------------------------------------------------------- helpers
def wait_until(pred, timeout=T):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.002)
    return pred()


def in_thread(fn):
    """Run fn in a daemon thread; returns (thread, box) where box holds result/exception."""
    box = {}

    def run():
        try:
            box["value"] = fn()
        except BaseException as e:  # noqa: BLE001
            box["exc"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t, box


class Tracker:
    """Records starts, concurrency, and per-key peaks from inside tasks."""

    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0
        self.key_active = defaultdict(int)
        self.key_peak = defaultdict(int)
        self.started = []

    def task(self, name, gate=None, key=None, ret=None, exc=None, sleep=0.0):
        def fn():
            with self.lock:
                self.started.append(name)
                self.active += 1
                self.peak = max(self.peak, self.active)
                if key is not None:
                    self.key_active[key] += 1
                    self.key_peak[key] = max(self.key_peak[key], self.key_active[key])
            try:
                if gate is not None:
                    assert gate.wait(T), f"gate for {name} never opened"
                if sleep:
                    time.sleep(sleep)
                if exc is not None:
                    raise exc
                return name if ret is None else ret
            finally:
                with self.lock:
                    self.active -= 1
                    if key is not None:
                        self.key_active[key] -= 1
        return fn


@pytest.fixture(autouse=True)
def watchdog():
    """Backstop: if a test hangs >20s (e.g. a deadlock in a non-timeout call), dump every
    thread's stack and abort the run. The dump is useful for finding the deadlock."""
    faulthandler.dump_traceback_later(20, exit=True)
    yield
    faulthandler.cancel_dump_traceback_later()


@pytest.fixture
def make_pool():
    pools = []

    def make(n):
        p = ThreadPool(n)
        pools.append(p)
        return p

    yield make
    for p in pools:  # shutdown in a side thread: a deadlocked pool must not hang teardown
        in_thread(lambda p=p: p.shutdown(wait=False))[0].join(0.5)


# =====================================================================
# Level 1 — BoundedBlockingQueue
# =====================================================================
class TestLevel1:
    def test_fifo(self):
        q = Queue(3)
        for i in range(3):
            assert q.put(i) is True
        assert len(q) == 3
        assert [q.get(), q.get(), q.get()] == [0, 1, 2]
        assert len(q) == 0

    def test_put_blocks_when_full(self):
        q = Queue(2)
        q.put(1)
        q.put(2)
        t, box = in_thread(lambda: q.put(3))
        time.sleep(0.1)
        assert t.is_alive(), "put should block on a full queue"
        assert q.get() == 1
        t.join(T)
        assert box.get("value") is True
        assert [q.get(), q.get()] == [2, 3]

    def test_get_blocks_when_empty(self):
        q = Queue(1)
        t, box = in_thread(lambda: q.get())
        time.sleep(0.1)
        assert t.is_alive()
        q.put("x")
        t.join(T)
        assert box.get("value") == "x"

    def test_put_timeout(self):
        q = Queue(1)
        q.put(1)
        start = time.monotonic()
        assert q.put(2, timeout=0.15) is False
        assert time.monotonic() - start >= 0.14
        assert len(q) == 1
        assert q.get() == 1

    def test_get_timeout(self):
        q = Queue(1)
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            q.get(timeout=0.15)
        assert time.monotonic() - start >= 0.14

    def test_zero_timeout_nonblocking(self):
        q = Queue(1)
        with pytest.raises(TimeoutError):
            q.get(timeout=0)
        assert q.put(1, timeout=0) is True
        assert q.put(2, timeout=0) is False

    def test_close_wakes_blocked_getters(self):
        q = Queue(1)
        threads = [in_thread(lambda: q.get()) for _ in range(3)]
        time.sleep(0.1)
        q.close()
        for t, box in threads:
            t.join(T)
            assert not t.is_alive()
            assert isinstance(box.get("exc"), Closed)

    def test_close_wakes_blocked_putters(self):
        q = Queue(1)
        q.put("a")
        threads = [in_thread(lambda i=i: q.put(i)) for i in range(3)]
        time.sleep(0.1)
        q.close()
        for t, box in threads:
            t.join(T)
            assert isinstance(box.get("exc"), Closed)
        assert len(q) == 1

    def test_close_drains_then_raises(self):
        q = Queue(3)
        q.put(1)
        q.put(2)
        q.close()
        q.close()  # idempotent
        with pytest.raises(Closed):
            q.put(3)
        assert q.get() == 1
        assert q.get(timeout=0.1) == 2
        with pytest.raises(Closed):
            q.get()
        with pytest.raises(Closed):
            q.get(timeout=0.1)

    def test_mpmc_stress(self):
        q = Queue(3)
        P, C, N = 4, 4, 500
        received = [[] for _ in range(C)]

        def producer(p):
            for i in range(N):
                assert q.put((p, i), timeout=T)

        def consumer(c):
            while True:
                try:
                    received[c].append(q.get(timeout=T))
                except Closed:
                    return

        prods = [in_thread(lambda p=p: producer(p))[0] for p in range(P)]
        cons = [in_thread(lambda c=c: consumer(c))[0] for c in range(C)]
        for t in prods:
            t.join(10)
            assert not t.is_alive()
        q.close()
        for t in cons:
            t.join(T)
            assert not t.is_alive()
        allitems = [x for r in received for x in r]
        assert sorted(allitems) == sorted((p, i) for p in range(P) for i in range(N))
        for r in received:  # FIFO: each consumer sees each producer's items in order
            for p in range(P):
                seq = [i for (pp, i) in r if pp == p]
                assert seq == sorted(seq)


# =====================================================================
# Level 2 — ThreadPool basics
# =====================================================================
class TestLevel2:
    def test_result(self, make_pool):
        pool = make_pool(2)
        assert pool.submit(lambda: 41 + 1).result(T) == 42

    def test_exception_propagates_and_worker_survives(self, make_pool):
        pool = make_pool(1)
        err = ValueError("boom")

        def bad():
            raise err

        f = pool.submit(bad)
        with pytest.raises(ValueError) as ei:
            f.result(T)
        assert ei.value is err
        assert pool.submit(lambda: "alive").result(T) == "alive"

    def test_result_timeout_and_done(self, make_pool):
        pool = make_pool(1)
        gate = threading.Event()
        f = pool.submit(lambda: gate.wait(T) and "ok")
        assert f.done() is False
        with pytest.raises(TimeoutError):
            f.result(timeout=0.1)
        gate.set()
        assert f.result(T) == "ok"
        assert f.done() is True

    def test_exactly_n_workers(self, make_pool):
        pool = make_pool(3)
        tr, gate = Tracker(), threading.Event()
        futs = [pool.submit(tr.task(i, gate)) for i in range(9)]
        assert wait_until(lambda: tr.active == 3)
        time.sleep(0.1)
        assert tr.active == 3
        gate.set()
        assert [f.result(T) for f in futs] == list(range(9))
        assert tr.peak == 3

    def test_fifo_single_worker(self, make_pool):
        pool = make_pool(1)
        tr = Tracker()
        futs = [pool.submit(tr.task(i)) for i in range(30)]
        for f in futs:
            f.result(T)
        assert tr.started == list(range(30))

    def test_submit_after_shutdown(self, make_pool):
        pool = make_pool(1)
        pool.shutdown()
        with pytest.raises(RuntimeError):
            pool.submit(lambda: 1)
        pool.shutdown()  # idempotent

    def test_shutdown_wait_runs_queued_and_joins_threads(self):
        before = set(threading.enumerate())
        pool = ThreadPool(2)
        tr = Tracker()
        futs = [pool.submit(tr.task(i, sleep=0.01)) for i in range(10)]
        t, _ = in_thread(lambda: pool.shutdown(wait=True))
        t.join(T)
        assert not t.is_alive(), "shutdown(wait=True) hung"
        assert all(f.done() for f in futs)
        leftover = [th for th in set(threading.enumerate()) - before if th is not t]
        assert leftover == [], "worker threads still alive after shutdown(wait=True)"

    def test_workers_are_daemon(self):
        before = set(threading.enumerate())
        pool = ThreadPool(2)
        try:
            new = set(threading.enumerate()) - before
            assert len(new) == 2 and all(th.daemon for th in new)
        finally:
            pool.shutdown()

    def test_shutdown_nowait_returns_immediately(self, make_pool):
        pool = make_pool(1)
        gate = threading.Event()
        f = pool.submit(lambda: gate.wait(T) and 7)
        start = time.monotonic()
        pool.shutdown(wait=False)
        assert time.monotonic() - start < 0.2
        gate.set()
        assert f.result(T) == 7

    def test_many_tasks(self, make_pool):
        pool = make_pool(8)
        lock, total = threading.Lock(), [0]

        def inc(i):
            with lock:
                total[0] += 1
            return i * i

        futs = [pool.submit(lambda i=i: inc(i)) for i in range(2000)]
        assert [f.result(T) for f in futs] == [i * i for i in range(2000)]
        assert total[0] == 2000


# =====================================================================
# Level 3 — deps, cancel, callbacks
# =====================================================================
class TestLevel3:
    def test_dep_order(self, make_pool):
        pool = make_pool(4)
        tr = Tracker()
        a = pool.submit(tr.task("A", sleep=0.05))
        b = pool.submit(tr.task("B"), deps=[a])
        assert b.result(T) == "B"
        assert tr.started == ["A", "B"]

    def test_ready_order_not_submit_order(self, make_pool):
        pool = make_pool(1)
        tr, gate = Tracker(), threading.Event()
        a = pool.submit(tr.task("A", gate))
        b = pool.submit(tr.task("B"), deps=[a])
        c = pool.submit(tr.task("C"))
        gate.set()
        b.result(T)
        c.result(T)
        assert tr.started == ["A", "C", "B"]

    def test_waiting_task_does_not_hold_worker(self, make_pool):
        pool = make_pool(2)
        tr, gate = Tracker(), threading.Event()
        a = pool.submit(tr.task("A", gate))
        pool.submit(tr.task("B"), deps=[a])
        c = pool.submit(tr.task("C"))
        assert c.result(T) == "C", "C starved: a dep-waiting task is holding a worker"
        gate.set()

    def test_failure_propagates_transitively(self, make_pool):
        pool = make_pool(2)
        tr = Tracker()
        a = pool.submit(tr.task("A", exc=ValueError()))
        b = pool.submit(tr.task("B"), deps=[a])
        c = pool.submit(tr.task("C"), deps=[b])
        with pytest.raises(ValueError):
            a.result(T)
        with pytest.raises(DependencyFailed):
            b.result(T)
        with pytest.raises(DependencyFailed):
            c.result(T)
        assert tr.started == ["A"]

    def test_fail_fast(self, make_pool):
        pool = make_pool(2)
        gate = threading.Event()
        tr = Tracker()
        slow = pool.submit(tr.task("slow", gate))
        bad = pool.submit(tr.task("bad", exc=RuntimeError()))
        b = pool.submit(tr.task("B"), deps=[slow, bad])
        with pytest.raises(DependencyFailed):
            b.result(T)  # must not wait for `slow`
        assert not slow.done()
        gate.set()
        slow.result(T)
        assert "B" not in tr.started

    def test_deps_already_done(self, make_pool):
        pool = make_pool(2)
        ok = pool.submit(lambda: 1)
        bad = pool.submit(lambda: 1 / 0)
        ok.result(T)
        with pytest.raises(ZeroDivisionError):
            bad.result(T)
        assert pool.submit(lambda: 2, deps=[ok]).result(T) == 2
        f = pool.submit(lambda: 3, deps=[ok, bad])
        assert f.done(), "should be failed synchronously at submit"
        with pytest.raises(DependencyFailed):
            f.result(0)

    def test_diamond_runs_once(self, make_pool):
        pool = make_pool(4)
        tr = Tracker()
        a = pool.submit(tr.task("A", sleep=0.02))
        b = pool.submit(tr.task("B", sleep=0.02), deps=[a])
        c = pool.submit(tr.task("C"), deps=[a])
        d = pool.submit(tr.task("D"), deps=[b, c, a])
        d.result(T)
        assert Counter(tr.started) == Counter("ABCD")
        assert tr.started[0] == "A" and tr.started[-1] == "D"

    def test_cancel_queued(self, make_pool):
        pool = make_pool(1)
        tr, gate = Tracker(), threading.Event()
        a = pool.submit(tr.task("A", gate))
        b = pool.submit(tr.task("B"))
        assert wait_until(lambda: tr.active == 1)
        assert b.cancel() is True
        assert b.cancel() is True  # already cancelled
        assert b.done()
        with pytest.raises(CancelledError):
            b.result(0)
        assert a.cancel() is False  # running
        gate.set()
        a.result(T)
        assert a.cancel() is False  # finished
        assert pool.submit(tr.task("C")).result(T) == "C"
        assert "B" not in tr.started

    def test_cancel_dep_waiting_and_propagation(self, make_pool):
        pool = make_pool(2)
        tr, gate = Tracker(), threading.Event()
        a = pool.submit(tr.task("A", gate))
        b = pool.submit(tr.task("B"), deps=[a])
        c = pool.submit(tr.task("C"), deps=[b])
        assert b.cancel() is True
        with pytest.raises(DependencyFailed):
            c.result(T)
        gate.set()
        a.result(T)
        time.sleep(0.05)
        assert tr.started == ["A"]

    def test_callbacks_exactly_once(self, make_pool):
        pool = make_pool(2)
        gate = threading.Event()
        calls = Counter()
        lock = threading.Lock()

        def cb(name):
            def f(fut):
                assert fut.done()
                with lock:
                    calls[name] += 1
            return f

        ok = pool.submit(lambda: gate.wait(T))
        bad = pool.submit(lambda: 1 / 0)
        dep = pool.submit(lambda: 1, deps=[bad])
        blocker = pool.submit(lambda: gate.wait(T))
        cancelled = pool.submit(lambda: 1, deps=[blocker])
        for name, f in [("ok", ok), ("bad", bad), ("dep", dep), ("cancelled", cancelled)]:
            f.add_done_callback(cb(name))
            f.add_done_callback(cb(name + "2"))
        cancelled.cancel()
        gate.set()
        assert wait_until(lambda: len(calls) == 8)
        time.sleep(0.05)
        assert set(calls.values()) == {1}

    def test_callback_after_done_runs_in_caller(self, make_pool):
        pool = make_pool(1)
        f = pool.submit(lambda: 1)
        f.result(T)
        seen = []
        f.add_done_callback(lambda fut: seen.append(threading.current_thread()))
        assert seen == [threading.current_thread()]

    def test_reentrant_callback(self, make_pool):
        pool = make_pool(1)
        gate = threading.Event()
        out = []

        def cb(fut):
            out.append(fut.result(0))
            out.append(pool.submit(lambda: 42))
            out.append(fut.cancel())

        a = pool.submit(lambda: gate.wait(T) and 1)
        a.add_done_callback(cb)
        gate.set()
        assert wait_until(lambda: len(out) == 3), "callback deadlocked (lock held while calling it?)"
        assert out[0] == 1 and out[2] is False
        assert out[1].result(T) == 42

    def test_callback_exception_swallowed(self, make_pool):
        pool = make_pool(1)
        gate = threading.Event()
        hits = []

        def boom(_):
            raise RuntimeError("cb")

        a = pool.submit(lambda: gate.wait(T))
        a.add_done_callback(boom)
        a.add_done_callback(lambda _: hits.append(1))
        gate.set()
        assert wait_until(lambda: hits == [1])
        assert pool.submit(lambda: "alive").result(T) == "alive"

    @pytest.mark.parametrize("seed", range(5))
    def test_random_dag_stress(self, make_pool, seed):
        rng = random.Random(seed)
        N = 300
        pool = make_pool(6)
        lock, clock = threading.Lock(), itertools.count()
        runs, start, end = Counter(), {}, {}
        fail = {i for i in range(N) if rng.random() < 0.05}
        deps = [rng.sample(range(i), k=min(i, rng.randint(0, 3))) for i in range(N)]
        sleepy = {i for i in range(N) if rng.random() < 0.1}

        def make(i):
            def fn():
                with lock:
                    runs[i] += 1
                    start[i] = next(clock)
                if i in sleepy:
                    time.sleep(0.001)
                with lock:
                    end[i] = next(clock)
                if i in fail:
                    raise ValueError(i)
                return i
            return fn

        futs = []
        for i in range(N):
            futs.append(pool.submit(make(i), deps=[futs[j] for j in deps[i]]))

        poisoned = [False] * N
        for i in range(N):
            poisoned[i] = any(j in fail or poisoned[j] for j in deps[i])

        for i, f in enumerate(futs):
            if poisoned[i]:
                with pytest.raises(DependencyFailed):
                    f.result(5)
                assert runs[i] == 0
            elif i in fail:
                with pytest.raises(ValueError):
                    f.result(5)
                assert runs[i] == 1
            else:
                assert f.result(5) == i
                assert runs[i] == 1
                assert all(end[j] < start[i] for j in deps[i]), f"task {i} started before a dep finished"


# =====================================================================
# Level 4 — priority + per-key limits
# =====================================================================
class TestLevel4:
    def test_priority(self, make_pool):
        pool = make_pool(1)
        tr, gate = Tracker(), threading.Event()
        pool.submit(tr.task("blocker", gate))
        assert wait_until(lambda: tr.active == 1)
        futs = [pool.submit(tr.task(n), priority=p)
                for n, p in [("p1", 1), ("p5a", 5), ("p3", 3), ("p5b", 5), ("p0", 0), ("n1", -1)]]
        gate.set()
        for f in futs:
            f.result(T)
        assert tr.started == ["blocker", "p5a", "p5b", "p3", "p1", "p0", "n1"]

    def test_priority_uses_ready_time_for_ties(self, make_pool):
        pool = make_pool(1)
        tr, gate, g2 = Tracker(), threading.Event(), threading.Event()
        blocker = pool.submit(tr.task("blocker", gate))
        assert wait_until(lambda: tr.active == 1)
        late = pool.submit(tr.task("late"), deps=[blocker], priority=1)  # ready when blocker finishes
        early = pool.submit(tr.task("early"), priority=1)                # ready now
        gate.set()
        late.result(T)
        early.result(T)
        assert tr.started == ["blocker", "early", "late"]

    def test_key_limit(self, make_pool):
        pool = make_pool(6)
        pool.set_limit("db", 2)
        tr, gate = Tracker(), threading.Event()
        futs = [pool.submit(tr.task(i, gate, key="db"), key="db") for i in range(6)]
        assert wait_until(lambda: tr.active == 2)
        time.sleep(0.1)
        assert tr.active == 2
        gate.set()
        for f in futs:
            f.result(T)
        assert tr.key_peak["db"] == 2

    def test_no_head_of_line_blocking(self, make_pool):
        pool = make_pool(2)
        pool.set_limit("db", 1)
        tr, gate = Tracker(), threading.Event()
        pool.submit(tr.task("db1", gate, key="db"), key="db")
        assert wait_until(lambda: tr.active == 1)
        db2 = pool.submit(tr.task("db2", key="db"), key="db", priority=10)
        x = pool.submit(tr.task("x"), priority=0)
        assert x.result(T) == "x", "low-priority task blocked behind a key-limited one"
        assert not db2.done()
        gate.set()
        db2.result(T)

    def test_key_waiters_do_not_hold_workers(self, make_pool):
        pool = make_pool(2)
        pool.set_limit("db", 1)
        tr, gate = Tracker(), threading.Event()
        dbs = [pool.submit(tr.task(f"db{i}", gate, key="db"), key="db") for i in range(4)]
        xs = [pool.submit(tr.task(f"x{i}")) for i in range(3)]
        for x in xs:
            x.result(T)
        gate.set()
        for f in dbs:
            f.result(T)
        assert tr.key_peak["db"] == 1

    def test_priority_within_key(self, make_pool):
        pool = make_pool(3)
        pool.set_limit("db", 1)
        tr, gate = Tracker(), threading.Event()
        pool.submit(tr.task("a", gate, key="db"), key="db")
        assert wait_until(lambda: tr.active == 1)
        low = pool.submit(tr.task("low", key="db"), key="db", priority=0)
        high = pool.submit(tr.task("high", key="db"), key="db", priority=5)
        time.sleep(0.05)
        gate.set()
        low.result(T)
        high.result(T)
        assert tr.started == ["a", "high", "low"]

    def test_raise_limit_dispatches(self, make_pool):
        pool = make_pool(3)
        pool.set_limit("db", 1)
        tr, gate = Tracker(), threading.Event()
        pool.submit(tr.task("db1", gate, key="db"), key="db")
        pool.submit(tr.task("db2", gate, key="db"), key="db")
        assert wait_until(lambda: tr.active == 1)
        time.sleep(0.05)
        assert tr.started == ["db1"]
        pool.set_limit("db", 2)
        assert wait_until(lambda: tr.active == 2), "raising the limit didn't start the waiter"
        gate.set()

    def test_lower_limit_no_preempt(self, make_pool):
        pool = make_pool(4)
        pool.set_limit("db", 3)
        tr = Tracker()
        gates = [threading.Event() for _ in range(3)]
        for i, g in enumerate(gates):
            pool.submit(tr.task(f"r{i}", g, key="db"), key="db")
        assert wait_until(lambda: tr.active == 3)
        nxt = pool.submit(tr.task("next", key="db"), key="db")
        pool.set_limit("db", 1)
        time.sleep(0.05)
        assert tr.active == 3, "lowering a limit must not interrupt running tasks"
        gates[0].set()
        assert wait_until(lambda: tr.active == 2)
        time.sleep(0.1)
        assert "next" not in tr.started
        gates[1].set()
        assert wait_until(lambda: tr.active == 1)
        time.sleep(0.1)
        assert "next" not in tr.started
        gates[2].set()
        assert nxt.result(T) == "next"

    def test_keys_independent(self, make_pool):
        pool = make_pool(4)
        pool.set_limit("a", 1)
        pool.set_limit("b", 1)
        tr, gate = Tracker(), threading.Event()
        for i in range(3):
            pool.submit(tr.task(f"a{i}", gate, key="a"), key="a")
            pool.submit(tr.task(f"b{i}", gate, key="b"), key="b")
        assert wait_until(lambda: tr.active == 2)
        assert sorted(tr.started) == ["a0", "b0"]
        gate.set()

    def test_cancel_key_waiter(self, make_pool):
        pool = make_pool(2)
        pool.set_limit("db", 1)
        tr, gate = Tracker(), threading.Event()
        pool.submit(tr.task("db1", gate, key="db"), key="db")
        assert wait_until(lambda: tr.active == 1)
        w = pool.submit(tr.task("w", key="db"), key="db")
        time.sleep(0.05)
        assert w.cancel() is True
        z = pool.submit(tr.task("z", key="db"), key="db")
        gate.set()
        z.result(T)
        assert "w" not in tr.started

    @pytest.mark.parametrize("seed", range(3))
    def test_stress(self, make_pool, seed):
        rng = random.Random(seed)
        pool = make_pool(8)
        limits = {"k0": 1, "k1": 2, "k2": 3}
        for k, n in limits.items():
            pool.set_limit(k, n)
        tr = Tracker()
        futs = []
        for i in range(400):
            key = rng.choice(["k0", "k1", "k2", None])
            d = [futs[j] for j in rng.sample(range(len(futs)), k=min(len(futs), rng.randint(0, 2)))]
            futs.append(pool.submit(tr.task(i, key=key, sleep=0.0005 if i % 5 == 0 else 0),
                                    key=key, deps=d, priority=rng.randint(-3, 3)))
            if i == 200:
                pool.set_limit("k0", 2)
        for i, f in enumerate(futs):
            assert f.result(10) == i
        assert tr.key_peak["k0"] <= 2 and tr.key_peak["k1"] <= 2 and tr.key_peak["k2"] <= 3
        assert Counter(tr.started) == Counter(range(400))


# =====================================================================
# Level 5 (stretch) — resize, cancelling shutdown
# =====================================================================
class TestLevel5:
    def test_grow(self, make_pool):
        pool = make_pool(1)
        tr, gate = Tracker(), threading.Event()
        futs = [pool.submit(tr.task(i, gate)) for i in range(3)]
        assert wait_until(lambda: tr.active == 1)
        pool.resize(3)
        assert wait_until(lambda: tr.active == 3)
        gate.set()
        for f in futs:
            f.result(T)

    def test_shrink_finishes_running_then_retires(self):
        before = set(threading.enumerate())
        pool = ThreadPool(4)
        try:
            tr, gate = Tracker(), threading.Event()
            first = [pool.submit(tr.task(f"f{i}", gate)) for i in range(4)]
            assert wait_until(lambda: tr.active == 4)
            pool.resize(1)
            time.sleep(0.05)
            assert tr.active == 4
            gate.set()
            assert [f.result(T) for f in first] == [f"f{i}" for i in range(4)]
            assert wait_until(lambda: len(set(threading.enumerate()) - before) == 1), \
                "surplus workers did not exit"
            tr2, gate2 = Tracker(), threading.Event()
            second = [pool.submit(tr2.task(i, gate2)) for i in range(4)]
            assert wait_until(lambda: tr2.active == 1)
            time.sleep(0.1)
            assert tr2.active == 1
            gate2.set()
            for f in second:
                f.result(T)
        finally:
            pool.shutdown(wait=False)

    def test_shrink_then_grow(self, make_pool):
        pool = make_pool(3)
        pool.resize(1)
        pool.resize(4)
        tr, gate = Tracker(), threading.Event()
        futs = [pool.submit(tr.task(i, gate)) for i in range(6)]
        assert wait_until(lambda: tr.active == 4)
        time.sleep(0.1)
        assert tr.active == 4
        gate.set()
        for f in futs:
            f.result(T)

    def test_resize_after_shutdown(self, make_pool):
        pool = make_pool(1)
        pool.shutdown()
        with pytest.raises(RuntimeError):
            pool.resize(2)

    def test_shutdown_cancel_pending(self, make_pool):
        pool = make_pool(2)
        pool.set_limit("k", 1)
        tr, gate = Tracker(), threading.Event()
        a = pool.submit(tr.task("A", gate))
        kr = pool.submit(tr.task("KR", gate, key="k"), key="k")
        assert wait_until(lambda: tr.active == 2)
        b = pool.submit(tr.task("B"))
        c = pool.submit(tr.task("C"), deps=[b])
        d = pool.submit(tr.task("D", key="k"), key="k", priority=9)
        e = pool.submit(tr.task("E"), deps=[a])
        calls = Counter()
        for name, f in zip("BCDE", [b, c, d, e]):
            f.add_done_callback(lambda _f, n=name: calls.update([n]))
        pool.shutdown(wait=False, cancel_pending=True)
        for f in (b, c, d, e):
            with pytest.raises(CancelledError):
                f.result(T)
        with pytest.raises(RuntimeError):
            pool.submit(lambda: 1)
        gate.set()
        assert a.result(T) == "A" and kr.result(T) == "KR"
        t, _ = in_thread(lambda: pool.shutdown(wait=True))
        t.join(T)
        assert not t.is_alive()
        assert calls == Counter("BCDE")
        assert sorted(tr.started) == ["A", "KR"]

    def test_shutdown_default_still_runs_dep_waiters(self, make_pool):
        pool = make_pool(2)
        gate = threading.Event()
        a = pool.submit(lambda: gate.wait(T) and 1)
        b = pool.submit(lambda: 2, deps=[a])
        t, _ = in_thread(lambda: pool.shutdown(wait=True))
        time.sleep(0.05)
        assert t.is_alive()
        gate.set()
        t.join(T)
        assert not t.is_alive()
        assert b.result(0) == 2
