# Tech Debt

Consciously taken shortcuts and known issues. Each entry must include what was
skipped, why, and what to do about it. **Delete entries once paid** — this file
should shrink over time. Do not number entries; order doesn't matter and indices
go stale.

---

## `__init__.py` exports nothing yet

**File:** `src/reqm/__init__.py`

The public API (`Quant`, `register`, `get`, and optionally `overrides_ext` symbols)
is not exported from the package. `import reqm` currently gives you nothing.

**Action:** Wire up exports once all three modules (`quant.py`, `registry.py`,
`factory.py`) are implemented.
