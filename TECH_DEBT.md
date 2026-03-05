# Tech Debt

Consciously taken shortcuts and known issues. Each entry must include what was
skipped, why, and what to do about it. **Delete entries once paid** — this file
should shrink over time. Do not number entries; order doesn't matter and indices
go stale.

---

## `__init__.py` exports nothing yet

**File:** `src/reqm/__init__.py`

The public API (`Quant`, `QuantManager`) is not exported from the package.
`import reqm` currently gives you nothing.

**Action:** Wire up exports once `QuantManager` implementation is complete.

---

## Examples use old registry API

**Files:** `src/reqm/examples/hello_world.py`, `src/reqm/examples/r2p.py`

Both examples still use the removed `reqm.register()` / `reqm.get()` pattern
which no longer exists. They will fail at import time.

**Why:** The examples were written before the design pivot from registry-based
to directory-based config management (`QuantManager`).

**Action:** Rewrite both examples to use `QuantManager` with proper config
module directories. Each example should have its own config module package.

