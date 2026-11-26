"""Tests for SPEC.md.  Run one level at a time:  pytest test_kvdb.py -k Level1 -q

Set KVDB_IMPL=<module> to test a different module (default: kvdb).
"""

import importlib
import json
import os
from pathlib import Path

import pytest

_mod = importlib.import_module(os.environ.get("KVDB_IMPL", "kvdb"))
DB = _mod.InMemoryDB


# =====================================================================
# Level 1
# =====================================================================
class TestLevel1:
    def test_basic_set_get(self):
        db = DB()
        db.set("u1", "name", "alice")
        assert db.get("u1", "name") == "alice"

    def test_missing_key_and_field(self):
        db = DB()
        assert db.get("nope", "x") is None
        db.set("u1", "a", "1")
        assert db.get("u1", "b") is None

    def test_overwrite(self):
        db = DB()
        db.set("u1", "a", "1")
        db.set("u1", "a", "2")
        assert db.get("u1", "a") == "2"

    def test_delete(self):
        db = DB()
        db.set("u1", "a", "1")
        assert db.delete("u1", "a") is True
        assert db.get("u1", "a") is None
        assert db.delete("u1", "a") is False
        assert db.delete("ghost", "a") is False

    def test_fields_independent_across_keys(self):
        db = DB()
        db.set("k1", "f", "x")
        db.set("k2", "f", "y")
        db.delete("k1", "f")
        assert db.get("k2", "f") == "y"

    def test_reinsert_after_delete(self):
        db = DB()
        db.set("k", "f", "1")
        db.delete("k", "f")
        db.set("k", "f", "2")
        assert db.get("k", "f") == "2"


# =====================================================================
# Level 2
# =====================================================================
class TestLevel2:
    def test_scan_sorted(self):
        db = DB()
        db.set("k", "b", "2")
        db.set("k", "a", "1")
        db.set("k", "c", "3")
        assert db.scan("k") == ["a(1)", "b(2)", "c(3)"]

    def test_scan_lexicographic_not_numeric(self):
        db = DB()
        for f in ["f10", "f2", "f1", "F3", "_x"]:
            db.set("k", f, f.lower())
        assert db.scan("k") == ["F3(f3)", "_x(_x)", "f1(f1)", "f10(f10)", "f2(f2)"]

    def test_scan_missing_and_emptied_key(self):
        db = DB()
        assert db.scan("nope") == []
        db.set("k", "a", "1")
        db.delete("k", "a")
        assert db.scan("k") == []

    def test_scan_by_prefix(self):
        db = DB()
        for f, v in [("ab", "1"), ("abc", "2"), ("a", "3"), ("b", "4"), ("xab", "5")]:
            db.set("k", f, v)
        assert db.scan_by_prefix("k", "ab") == ["ab(1)", "abc(2)"]
        assert db.scan_by_prefix("k", "a") == ["a(3)", "ab(1)", "abc(2)"]
        assert db.scan_by_prefix("k", "abc") == ["abc(2)"]
        assert db.scan_by_prefix("k", "abcd") == []
        assert db.scan_by_prefix("k", "") == db.scan("k")
        assert db.scan_by_prefix("other", "a") == []

    def test_prefix_is_on_field_not_key(self):
        db = DB()
        db.set("apple", "x", "1")
        assert db.scan_by_prefix("apple", "a") == []

    def test_scan_reflects_overwrite(self):
        db = DB()
        db.set("k", "a", "1")
        db.set("k", "a", "9")
        assert db.scan("k") == ["a(9)"]


# =====================================================================
# Level 3
# =====================================================================
class TestLevel3:
    def test_ttl_half_open_boundary(self):
        db = DB()
        db.set_at_with_ttl(10, "k", "f", "v", 5)  # live in [10, 15)
        assert db.get_at(14, "k", "f") == "v"
        assert db.get_at(15, "k", "f") is None

    def test_ttl_one(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v", 1)
        assert db.get_at(2, "k", "f") is None

    def test_set_at_clears_ttl(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v1", 3)
        db.set_at(2, "k", "f", "v2")
        assert db.get_at(1000, "k", "f") == "v2"

    def test_ttl_overwrite_replaces_expiry(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v1", 100)
        db.set_at_with_ttl(2, "k", "f", "v2", 3)  # now expires at 5
        assert db.get_at(4, "k", "f") == "v2"
        assert db.get_at(5, "k", "f") is None

    def test_ttl_can_be_extended(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v", 2)
        db.set_at_with_ttl(2, "k", "f", "v", 10)
        assert db.get_at(11, "k", "f") == "v"
        assert db.get_at(12, "k", "f") is None

    def test_delete_expired_returns_false(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v", 2)
        assert db.delete_at(3, "k", "f") is False
        assert db.delete_at(4, "k", "f") is False

    def test_set_after_expiry(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "old", 2)
        assert db.get_at(5, "k", "f") is None
        db.set_at(6, "k", "f", "new")
        assert db.get_at(7, "k", "f") == "new"

    def test_scan_excludes_expired(self):
        db = DB()
        db.set_at(1, "k", "a", "1")
        db.set_at_with_ttl(2, "k", "b", "2", 3)  # dies at 5
        db.set_at_with_ttl(3, "k", "c", "3", 10)
        assert db.scan_at(4, "k") == ["a(1)", "b(2)", "c(3)"]
        assert db.scan_at(5, "k") == ["a(1)", "c(3)"]
        assert db.scan_by_prefix_at(6, "k", "b") == []
        assert db.scan_at(13, "k") == ["a(1)"]

    def test_key_with_all_fields_expired_is_gone(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "a", "1", 2)
        db.set_at_with_ttl(2, "k", "b", "2", 2)
        assert db.scan_at(4, "k") == []
        assert db.get_at(5, "k", "a") is None

    def test_cas_success_and_failure(self):
        db = DB()
        db.set_at(1, "k", "f", "1")
        assert db.compare_and_set_at(2, "k", "f", "0", "2") is False
        assert db.get_at(3, "k", "f") == "1"
        assert db.compare_and_set_at(4, "k", "f", "1", "2") is True
        assert db.get_at(5, "k", "f") == "2"

    def test_cas_missing(self):
        db = DB()
        assert db.compare_and_set_at(1, "k", "f", "x", "y") is False
        assert db.get_at(2, "k", "f") is None

    def test_cas_preserves_ttl(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "a", 5)  # dies at 6
        assert db.compare_and_set_at(3, "k", "f", "a", "b") is True
        assert db.get_at(5, "k", "f") == "b"
        assert db.get_at(6, "k", "f") is None

    def test_cas_on_non_ttl_stays_non_ttl(self):
        db = DB()
        db.set_at(1, "k", "f", "a")
        db.compare_and_set_at(2, "k", "f", "a", "b")
        assert db.get_at(10_000, "k", "f") == "b"

    def test_cas_on_expired_fails(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "a", 2)
        assert db.compare_and_set_at(3, "k", "f", "a", "b") is False
        assert db.get_at(4, "k", "f") is None

    def test_compare_and_delete(self):
        db = DB()
        db.set_at(1, "k", "f", "a")
        assert db.compare_and_delete_at(2, "k", "f", "z") is False
        assert db.get_at(3, "k", "f") == "a"
        assert db.compare_and_delete_at(4, "k", "f", "a") is True
        assert db.get_at(5, "k", "f") is None
        assert db.compare_and_delete_at(6, "k", "f", "a") is False

    def test_compare_and_delete_expired(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "a", 1)
        assert db.compare_and_delete_at(2, "k", "f", "a") is False

    def test_chained_cas_then_expiry(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "0", 10)  # dies at 11
        for t in range(2, 10):
            assert db.compare_and_set_at(t, "k", "f", str(t - 2), str(t - 1)) is True
        assert db.get_at(10, "k", "f") == "8"
        assert db.compare_and_set_at(11, "k", "f", "8", "9") is False


# =====================================================================
# Level 4
# =====================================================================
class TestLevel4:
    def test_backup_counts_live_keys(self):
        db = DB()
        assert db.backup(1) == 0
        db.set_at(2, "a", "f", "1")
        db.set_at_with_ttl(3, "b", "f", "1", 2)  # dies at 5
        db.set_at(4, "c", "f", "1")
        db.delete_at(5, "c", "f")
        assert db.backup(6) == 1

    def test_backup_counts_keys_not_fields(self):
        db = DB()
        db.set_at(1, "a", "x", "1")
        db.set_at(2, "a", "y", "1")
        db.set_at(3, "b", "x", "1")
        assert db.backup(4) == 2

    def test_restore_no_backup(self):
        db = DB()
        db.set_at(1, "k", "f", "v")
        db.backup(5)
        assert db.restore(6, 4) is False
        assert db.get_at(7, "k", "f") == "v"

    def test_restore_picks_latest_at_or_before(self):
        db = DB()
        db.set_at(1, "k", "f", "v1")
        db.backup(2)
        db.set_at(3, "k", "f", "v2")
        db.backup(4)
        db.set_at(5, "k", "f", "v3")
        db.backup(6)
        assert db.restore(7, 5) is True   # -> backup@4
        assert db.get_at(8, "k", "f") == "v2"
        assert db.restore(9, 2) is True   # inclusive -> backup@2
        assert db.get_at(10, "k", "f") == "v1"
        assert db.restore(11, 100) is True  # -> backup@6, still exists after earlier restores
        assert db.get_at(12, "k", "f") == "v3"

    def test_restore_replaces_entire_state(self):
        db = DB()
        db.set_at(1, "a", "f", "1")
        db.backup(2)
        db.set_at(3, "b", "f", "2")
        db.set_at(4, "a", "g", "3")
        db.delete_at(5, "a", "f")
        db.restore(6, 2)
        assert db.get_at(7, "b", "f") is None
        assert db.scan_at(8, "a") == ["f(1)"]

    def test_restore_empty_backup_clears(self):
        db = DB()
        db.backup(1)
        db.set_at(2, "k", "f", "v")
        assert db.restore(3, 1) is True
        assert db.get_at(4, "k", "f") is None
        assert db.backup(5) == 0

    def test_restore_recalculates_ttl(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v", 10)  # expiry 11
        db.backup(5)                               # remaining 6
        db.restore(20, 5)                          # new expiry 26
        assert db.get_at(25, "k", "f") == "v"
        assert db.get_at(26, "k", "f") is None

    def test_expired_before_backup_not_restored(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v", 2)  # dies at 3
        db.set_at(2, "k", "g", "w")
        assert db.backup(3) == 1
        db.restore(4, 3)
        assert db.scan_at(5, "k") == ["g(w)"]

    def test_backup_is_isolated_from_later_writes(self):
        db = DB()
        db.set_at(1, "k", "f", "orig")
        db.backup(2)
        db.set_at(3, "k", "f", "changed")
        db.set_at(4, "k", "g", "new")
        db.restore(5, 2)
        assert db.scan_at(6, "k") == ["f(orig)"]

    def test_restore_twice_from_same_backup(self):
        db = DB()
        db.set_at(1, "k", "f", "orig")
        db.backup(2)
        db.restore(3, 2)
        db.set_at(4, "k", "f", "mutated")
        db.set_at(5, "k", "x", "extra")
        db.restore(6, 2)
        assert db.scan_at(7, "k") == ["f(orig)"]

    def test_restore_ttl_relative_each_time(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v", 4)  # expiry 5
        db.backup(2)                              # remaining 3
        db.restore(10, 2)                         # expiry 13
        assert db.get_at(12, "k", "f") == "v"
        assert db.get_at(13, "k", "f") is None
        db.restore(50, 2)                         # expiry 53 (not 13 + anything)
        assert db.get_at(52, "k", "f") == "v"
        assert db.get_at(53, "k", "f") is None

    def test_restore_does_not_resurrect_by_old_expiry(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "v", 100)  # expiry 101
        db.backup(99)                               # remaining 2
        db.restore(100, 99)                         # expiry 102
        assert db.get_at(101, "k", "f") == "v"
        assert db.get_at(102, "k", "f") is None

    def test_cas_after_restore_keeps_recalculated_ttl(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "a", 10)  # expiry 11
        db.backup(3)                               # remaining 8
        db.restore(30, 3)                          # expiry 38
        assert db.compare_and_set_at(31, "k", "f", "a", "b") is True
        assert db.get_at(37, "k", "f") == "b"
        assert db.get_at(38, "k", "f") is None

    def test_backup_after_restore_counts_restored_state(self):
        db = DB()
        db.set_at(1, "a", "f", "1")
        db.backup(2)
        db.set_at(3, "b", "f", "1")
        db.set_at(4, "c", "f", "1")
        assert db.backup(5) == 3
        db.restore(6, 2)
        assert db.backup(7) == 1
        db.restore(8, 5)
        assert db.backup(9) == 3

    def test_delete_restored_field(self):
        db = DB()
        db.set_at(1, "k", "f", "v")
        db.backup(2)
        db.restore(3, 2)
        assert db.delete_at(4, "k", "f") is True
        db.restore(5, 2)
        assert db.get_at(6, "k", "f") == "v"


# =====================================================================
# Level 5 (stretch)
# =====================================================================
class TestLevel5:
    def test_before_anything(self):
        db = DB()
        db.set_at(5, "k", "f", "v")
        assert db.get_when(6, "k", "f", 4) is None
        assert db.get_when(7, "k", "f", 5) == "v"
        assert db.get_when(8, "nope", "f", 5) is None

    def test_versions(self):
        db = DB()
        db.set_at(1, "k", "f", "a")
        db.set_at(3, "k", "f", "b")
        db.delete_at(5, "k", "f")
        db.set_at(7, "k", "f", "c")
        expect = {0: None, 1: "a", 2: "a", 3: "b", 4: "b", 5: None, 6: None, 7: "c", 8: "c"}
        for at, want in expect.items():
            assert db.get_when(9 + at, "k", "f", at) == want, at

    def test_ttl_in_history(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "a", 3)  # [1, 4)
        db.set_at(10, "k", "f", "b")
        assert db.get_when(11, "k", "f", 3) == "a"
        assert db.get_when(12, "k", "f", 4) is None
        assert db.get_when(13, "k", "f", 9) is None
        assert db.get_when(14, "k", "f", 10) == "b"

    def test_cas_in_history_keeps_expiry(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "a", 5)  # [1, 6)
        db.compare_and_set_at(3, "k", "f", "a", "b")
        assert db.get_when(10, "k", "f", 2) == "a"
        assert db.get_when(11, "k", "f", 5) == "b"
        assert db.get_when(12, "k", "f", 6) is None

    def test_failed_ops_dont_create_versions(self):
        db = DB()
        db.set_at(1, "k", "f", "a")
        db.compare_and_set_at(2, "k", "f", "zzz", "b")
        db.compare_and_delete_at(3, "k", "f", "zzz")
        db.delete_at(4, "k", "nope")
        db.backup(5)
        for at in range(1, 6):
            assert db.get_when(10 + at, "k", "f", at) == "a"
        assert db.get_when(20, "k", "nope", 4) is None

    def test_restore_is_a_mutation_at_restore_time(self):
        db = DB()
        db.set_at(1, "k", "f", "a")
        db.backup(2)
        db.set_at(3, "k", "f", "b")
        db.set_at(4, "k", "g", "x")
        db.restore(6, 2)
        assert db.get_when(10, "k", "f", 2) == "a"
        assert db.get_when(11, "k", "f", 5) == "b"
        assert db.get_when(12, "k", "f", 6) == "a"
        assert db.get_when(13, "k", "g", 5) == "x"
        assert db.get_when(14, "k", "g", 6) is None  # wiped by restore

    def test_restore_ttl_in_history(self):
        db = DB()
        db.set_at_with_ttl(1, "k", "f", "a", 4)  # [1, 5)
        db.backup(2)                              # remaining 3
        db.restore(10, 2)                         # [10, 13)
        assert db.get_when(20, "k", "f", 4) == "a"
        assert db.get_when(21, "k", "f", 7) is None
        assert db.get_when(22, "k", "f", 12) == "a"
        assert db.get_when(23, "k", "f", 13) is None

    def test_restore_wipes_field_created_after_backup_then_rewrite(self):
        db = DB()
        db.backup(1)
        db.set_at(2, "k", "f", "a")
        db.restore(3, 1)
        db.set_at(4, "k", "f", "b")
        assert [db.get_when(10 + t, "k", "f", t) for t in range(1, 6)] == [None, "a", None, "b", "b"]


# =====================================================================
# Randomized differential tests (expected outputs from a reference impl)
# =====================================================================
_CASES = json.loads((Path(__file__).parent / "fuzz_cases.json").read_text())


def _replay(case):
    db = DB()
    for i, (op, expected) in enumerate(zip(case["ops"], case["expected"])):
        method, *args = op
        got = getattr(db, method)(*args)
        if got != expected:
            ctx = case["ops"][max(0, i - 15): i + 1]
            pytest.fail(
                f"op #{i} {method}{tuple(args)} -> {got!r}, expected {expected!r}\n"
                f"last ops:\n" + "\n".join(f"  {o}" for o in ctx)
            )


def _ids(level):
    return [c for c in _CASES if c["level"] == level]


@pytest.mark.parametrize("case", _ids(3), ids=lambda c: c["name"])
def test_Fuzz3(case):
    _replay(case)


@pytest.mark.parametrize("case", _ids(4), ids=lambda c: c["name"])
def test_Fuzz4(case):
    _replay(case)


@pytest.mark.parametrize("case", _ids(5), ids=lambda c: c["name"])
def test_Fuzz5(case):
    _replay(case)
