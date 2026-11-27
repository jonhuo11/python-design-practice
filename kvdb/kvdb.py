"""In-memory database. See SPEC.md. Implement level by level."""

from __future__ import annotations

import bisect
from dataclasses import dataclass
import math

@dataclass
class SetEntry:
    t: int
    key: str
    field: str
    value: str
    ttl: int

@dataclass
class DelEntry:
    t: int
    key: str
    field: str

@dataclass
class CASEntry:
    t: int
    key: str
    field: str
    expected_val: str
    new_val: str

@dataclass
class CADEntry:
    t: int
    key: str
    field: str
    expected_val: str
    

class InMemoryDB:
    def __init__(self) -> None:
        self.db: dict[str, list[list[str,str,int]]] = {} # (field, value, ttlu)
        # invariants
        # no key has len 0 - we always delete keys with len 0 on the last field removal
        self.log: list[SetEntry|DelEntry|CASEntry] = []


    # ---------- Level 1 ----------
    def set(self, key: str, field: str, value: str, ttlu: int | None = None) -> None: # ttl until
        if key not in self.db:
            self.db[key] = []
        insert_i = bisect.bisect_left(self.db[key], [field,])
        ttlu = math.inf if ttlu is None else ttlu

        if insert_i < len(self.db[key]) and self.db[key][insert_i][0] == field: # update the val in place
            self.db[key][insert_i][1] = value
            self.db[key][insert_i][2] = ttlu
        else: # not already there
            self.db[key].insert(insert_i, [field, value, ttlu])
        #print(self.db[key])

    def get(self, key: str, field: str, t: int | None = None) -> str | None:
        if key not in self.db:
            return None
        i = bisect.bisect_left(self.db[key], [field,])
        return self.db[key][i][1] if (
            i < len(self.db[key]) and
            self.db[key][i][0] == field and
            (t is None or t < self.db[key][i][2]) # within ttl interval
        ) else None


    def delete(self, key: str, field: str, t: int | None = None) -> bool:
        if key not in self.db:
            return False
        i = bisect.bisect_left(self.db[key], [field,])
        if i < len(self.db[key]) and self.db[key][i][0] == field and (t is None or t < self.db[key][i][2]):
            # a valid entry, to be deleted

            self.db[key].pop(i)
            if len(self.db[key]) == 0:
                del self.db[key] # empty key gets removed
            return True
        return False

    # ---------- Level 2 ----------
    def scan(self, key: str, t: int | None = None) -> list[str]:
        if key not in self.db:
            return []
        return [f"{field}({value})" for field, value, ttlu in self.db[key] if t < ttlu]

    def scan_by_prefix(self, key: str, prefix: str, t: int | None = None) -> list[str]:
        if key not in self.db:
            return []
        return [f"{field}({value})" for field, value, ttlu in self.db[key] if field.startswith(prefix) and (t is None or t < ttlu)]

    # ---------- Level 3 ----------
    def set_at(self, timestamp: int, key: str, field: str, value: str) -> None:
        v = self.set(key, field, value)
        self.log.append(SetEntry(timestamp, key, field, value, math.inf))
        return v

    def set_at_with_ttl(self, timestamp: int, key: str, field: str, value: str, ttl: int) -> None:
        v = self.set(key, field, value, timestamp + ttl)
        self.log.append(SetEntry(timestamp, key, field, value, ttl))
        return v

    def get_at(self, timestamp: int, key: str, field: str) -> str | None:
        print(self.db)
        return self.get(key, field, timestamp)

    def delete_at(self, timestamp: int, key: str, field: str) -> bool:
        v = self.delete(key, field, timestamp)
        self.log.append(DelEntry(timestamp, key, field))
        return v

    def scan_at(self, timestamp: int, key: str) -> list[str]:
        return self.scan(key, timestamp)

    def scan_by_prefix_at(self, timestamp: int, key: str, prefix: str) -> list[str]:
        return self.scan_by_prefix(key, prefix, timestamp)

    def compare_and_set_at(self, timestamp: int, key: str, field: str,
                           expected_value: str, new_value: str) -> bool:
        self.log.append(CASEntry(timestamp, key, field, expected_value, new_value))
        if key not in self.db:
            return False
        insert_i = bisect.bisect_left(self.db[key], [field,])
        if insert_i < len(self.db[key]) and self.db[key][insert_i][0] == field: # update the val in place
            val = self.db[key][insert_i][1]
            ttlu = self.db[key][insert_i][2]
            if timestamp < ttlu and val == expected_value: # has not expired + CAS
                self.db[key][insert_i][1] = new_value
                return True
            return False # failed CAS or ttl
        else: # not already there
            self.db[key].insert(insert_i, [field, new_value, math.inf])
            return True

    def compare_and_delete_at(self, timestamp: int, key: str, field: str,
                              expected_value: str) -> bool:
        self.log.append(CADEntry(timestamp, key, field, expected_value))
        if key not in self.db:
            return False
        rm_i = bisect.bisect_left(self.db[key], [field,])
        if rm_i < len(self.db[key]) and self.db[key][rm_i][0] == field: # update the val in place
            val = self.db[key][rm_i][1]
            ttlu = self.db[key][rm_i][2]
            if timestamp < ttlu and val == expected_value: # has not expired + CAS
                self.db[key][rm_i].pop(rm_i)
                return True
            return False # failed CAS or ttl
        return False
        

    # ---------- Level 4 ----------
    def backup(self, timestamp: int) -> int:
        raise NotImplementedError

    def restore(self, timestamp: int, timestamp_to_restore: int) -> bool:
        raise NotImplementedError

    # ---------- Level 5 (stretch) ----------
    def get_when(self, timestamp: int, key: str, field: str, at_timestamp: int) -> str | None:
        raise NotImplementedError
