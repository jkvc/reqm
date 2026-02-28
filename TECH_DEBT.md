# Tech Debt

Items to review and resolve. Each has a clear action.

---

## 1. `__init__.py` exports nothing yet

**File:** `src/reqm/__init__.py`

The public API (`Quant`, `register`, `get`, and optionally `overrides_ext` symbols)
is not exported from the package. `import reqm` currently gives you nothing.

**Action:** Wire up exports once all three modules (`quant.py`, `registry.py`,
`factory.py`) are implemented.
