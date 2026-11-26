"""In-memory database. See SPEC.md. Implement level by level."""

from __future__ import annotations

import bisect

class InMemoryDB:
    def __init__(self) -> None:
        self.db: dict[str, list[list[str,str]]] = {}
        # invariants
        # no key has len 0 - we always delete keys with len 0 on the last field removal


    # ---------- Level 1 ----------
    def set(self, key: str, field: str, value: str) -> None:
        if key not in self.db:
            self.db[key] = []
        insert_i = bisect.bisect_left(self.db[key], [field,])
        if insert_i < len(self.db[key]) and self.db[key][insert_i][0] == field: # update the val in place
            self.db[key][insert_i][1] = value
        else: # not already there
            self.db[key].insert(insert_i, [field, value])
        #print(self.db[key])

    def get(self, key: str, field: str) -> str | None:
        if key not in self.db:
            return None
        i = bisect.bisect_left(self.db[key], [field,])
        return self.db[key][i][1] if (i < len(self.db[key]) and self.db[key][i][0] == field) else None


    def delete(self, key: str, field: str) -> bool:
        if key not in self.db:
            return False
        i = bisect.bisect_left(self.db[key], [field,])
        if i < len(self.db[key]) and self.db[key][i][0] == field:
            self.db[key].pop(i)
            if len(self.db[key]) == 0:
                del self.db[key] # empty key gets removed
            return True
        return False

    # ---------- Level 2 ----------
    def scan(self, key: str) -> list[str]:
        if key not in self.db:
            return []
        return [f"{field}({value})" for field, value in self.db[key]]

    def scan_by_prefix(self, key: str, prefix: str) -> list[str]:
        if key not in self.db:
            return []
        return [f"{field}({value})" for field, value in self.db[key] if field.startswith(prefix)]

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
