# In-Memory Database — 4 levels + stretch (90 min, no AI)

Mirrors the CodeSignal "Industry Coding Assessment" format. In the real thing you only
see level N+1 after passing level N, so **read one level at a time**.

Suggested pacing: L1 10 min · L2 15 min · L3 30 min · L4 35 min · L5 is a stretch goal you
attempt afterwards.

Run tests: `pytest test_kvdb.py -k Level1 -q` (Level2 … Level5, `Fuzz3` / `Fuzz4` / `Fuzz5`).

---

## Data model

A record is identified by a string `key` and holds string `field -> value` pairs.
Keys, fields and values are non-empty strings of `[A-Za-z0-9_]`. A key "exists" only
while it holds at least one live field.

---

## Level 1 — CRUD

- `set(key, field, value) -> None`: insert or overwrite.
- `get(key, field) -> str | None`: value, or `None` if the key or field is missing.
- `delete(key, field) -> bool`: `True` if the field existed and was removed, else `False`.

---

## Level 2 — Scans

- `scan(key) -> list[str]`: every field of `key` formatted as `"field(value)"`, sorted by
  field name in **lexicographic (Python string) order**. Missing key: `[]`.
- `scan_by_prefix(key, prefix) -> list[str]`: the same, keeping only fields that start
  with `prefix`. An empty prefix matches everything.

---

## Level 3 — Timestamps, TTL, compare-and-swap

Every operation now takes a leading `timestamp: int`. Across all calls on one instance,
timestamps are **strictly increasing**. Tests for L3+ use only `*_at` methods. Implement
the L1/L2 methods in terms of these if you like.

- `set_at(timestamp, key, field, value) -> None`: the field never expires. **This also
  clears any TTL the field had before.**
- `set_at_with_ttl(timestamp, key, field, value, ttl) -> None`: `ttl >= 1`. The field is
  live during the half-open interval `[timestamp, timestamp + ttl)`. This replaces any
  previous value and expiry.
- `get_at(timestamp, key, field) -> str | None`
- `delete_at(timestamp, key, field) -> bool`: `False` if the field is missing or expired.
- `scan_at(timestamp, key) -> list[str]`
- `scan_by_prefix_at(timestamp, key, prefix) -> list[str]`
- `compare_and_set_at(timestamp, key, field, expected_value, new_value) -> bool`: if the
  field is live and equals `expected_value`, set it to `new_value` and return `True`.
  **The field keeps its existing expiry** (or stays non-expiring). Otherwise change
  nothing and return `False`.
- `compare_and_delete_at(timestamp, key, field, expected_value) -> bool`: delete the field
  if it is live and equals `expected_value`.

Expired fields behave exactly as if they were deleted, everywhere.

---

## Level 4 — Backup / restore

- `backup(timestamp) -> int`: snapshot the live state at `timestamp`. Return the number
  of keys that have at least one live field. Store each field's **remaining** TTL
  (`expiry - timestamp`), not its absolute expiry.
- `restore(timestamp, timestamp_to_restore) -> bool`: find the **latest** backup taken at
  a time `<= timestamp_to_restore`.
  - If there is none, change nothing and return `False`.
  - Otherwise replace the **entire** database with that snapshot and return `True`. Every
    restored field with a TTL gets the new expiry `timestamp + remaining_ttl_at_backup`.
  - Restoring does not delete any backups, including backups taken after the one
    restored. The same backup can be restored more than once, and every restore must
    yield the same state.

---

## Level 5 (stretch) — Point-in-time reads

- `get_when(timestamp, key, field, at_timestamp) -> str | None`, with
  `0 <= at_timestamp <= timestamp`. Return the value that `get_at` would have returned
  for `(key, field)` at time `at_timestamp`. That means: apply every mutation with
  timestamp `<= at_timestamp`, then evaluate TTL expiry at `at_timestamp`.
  - Restores count as mutations. They happen at the restore's `timestamp`, not at the
    backup's time.
  - Queries never mutate anything. Neither do failed CAS calls, failed deletes or
    `backup`.
  - `at_timestamp` can come before the instance's first operation, which gives `None`.

Target: about O(log n) per `get_when`. A restore may cost O(fields).
