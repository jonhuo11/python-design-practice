"""In-memory database. See SPEC.md. Implement level by level."""

from __future__ import annotations


class InMemoryDB:
    def __init__(self) -> None:
        pass

    # ---------- Level 1 ----------
    def set(self, key: str, field: str, value: str) -> None:
        raise NotImplementedError

    def get(self, key: str, field: str) -> str | None:
        raise NotImplementedError

    def delete(self, key: str, field: str) -> bool:
        raise NotImplementedError

    # ---------- Level 2 ----------
    def scan(self, key: str) -> list[str]:
        raise NotImplementedError

    def scan_by_prefix(self, key: str, prefix: str) -> list[str]:
        raise NotImplementedError

    # ---------- Level 3 ----------
    def set_at(self, timestamp: int, key: str, field: str, value: str) -> None:
        raise NotImplementedError

    def set_at_with_ttl(self, timestamp: int, key: str, field: str, value: str, ttl: int) -> None:
        raise NotImplementedError

    def get_at(self, timestamp: int, key: str, field: str) -> str | None:
        raise NotImplementedError

    def delete_at(self, timestamp: int, key: str, field: str) -> bool:
        raise NotImplementedError

    def scan_at(self, timestamp: int, key: str) -> list[str]:
        raise NotImplementedError

    def scan_by_prefix_at(self, timestamp: int, key: str, prefix: str) -> list[str]:
        raise NotImplementedError

    def compare_and_set_at(self, timestamp: int, key: str, field: str,
                           expected_value: str, new_value: str) -> bool:
        raise NotImplementedError

    def compare_and_delete_at(self, timestamp: int, key: str, field: str,
                              expected_value: str) -> bool:
        raise NotImplementedError

    # ---------- Level 4 ----------
    def backup(self, timestamp: int) -> int:
        raise NotImplementedError

    def restore(self, timestamp: int, timestamp_to_restore: int) -> bool:
        raise NotImplementedError

    # ---------- Level 5 (stretch) ----------
    def get_when(self, timestamp: int, key: str, field: str, at_timestamp: int) -> str | None:
        raise NotImplementedError
