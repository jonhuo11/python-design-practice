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

@dataclass
class WipeEntry:
    t: int
    

class InMemoryDB:
    def __init__(self) -> None:
        self.db: dict[str, list[list[str,str,int]]] = {} # (field, value, ttlu)
        # invariants
        # no key has len 0 - we always delete keys with len 0 on the last field removal
        self.log: list[SetEntry|DelEntry|CASEntry|CADEntry|WipeEntry] = []

        self.backups: list[int] = [] # times when backups happened


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
        return [f"{field}({value})" for field, value, ttlu in self.db[key] if t is None or t < ttlu]

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
        #print(self.db)
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
        return False # field not there

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
                self.db[key].pop(rm_i)
                return True
            return False # failed CAS or ttl
        return False
        

    # ---------- Level 4 ----------
    def backup(self, timestamp: int) -> int:
        self.backups.append(timestamp)

        n_with_one_field = 0
        for k in self.db:
            for _, _, ttlu in self.db[k]:
                if timestamp < ttlu:
                    n_with_one_field += 1
                    break # this key has at least 1 field
        return n_with_one_field

    def __replay(self, action_time: int, target_timestamp: int): # inclusive
        sim_db = InMemoryDB()

        # play until state
        l = []
        for log_entry in self.log:
            if log_entry.t > target_timestamp:
                break # stop
            l.append(log_entry)
            if isinstance(log_entry, SetEntry):
                sim_db.set_at_with_ttl(log_entry.t, log_entry.key, log_entry.field, log_entry.value, log_entry.ttl)
            elif isinstance(log_entry, DelEntry):
                sim_db.delete_at(log_entry.t, log_entry.key, log_entry.field)
            elif isinstance(log_entry, CASEntry):
                sim_db.compare_and_set_at(log_entry.t, log_entry.key, log_entry.field, log_entry.expected_val, log_entry.new_val)
            elif isinstance(log_entry, CADEntry):
                sim_db.compare_and_delete_at(log_entry.t, log_entry.key, log_entry.field, log_entry.expected_val)
            elif isinstance(log_entry, WipeEntry):
                sim_db.log.append(WipeEntry(log_entry.t))
                sim_db.db = {}
        #print(l)
        #print(sim_db.db)

        # copy state into current
        self.db = {} # wipe, but dont wipe logs
        self.log.append(WipeEntry(action_time))
        for k in sim_db.db:
            for field, value, ttlu in sim_db.db[k]:
                if target_timestamp >= ttlu:
                    continue # expired
                self.set(k, field, value, action_time + ttlu - target_timestamp)
                #print(action_time, ttlu, target_timestamp, action_time + ttlu - target_timestamp)
                self.log.append(SetEntry(action_time, k, field, value, ttlu - target_timestamp))
        

    def restore(self, timestamp: int, timestamp_to_restore: int) -> bool: # no restore log entry type exists, just sets
        backup_i = bisect.bisect_right(self.backups, timestamp_to_restore)
        #print(self.backups, backup_i)
        if backup_i > len(self.backups) or backup_i <= 0: # out of band
            return False
        self.__replay(timestamp, self.backups[backup_i-1])
        return True

    # ---------- Level 5 (stretch) ----------
    def get_when(self, timestamp: int, key: str, field: str, at_timestamp: int) -> str | None:
        raise NotImplementedError
