# Tech Debt

Items to review and resolve. Each has a clear action.

---

## 1. `allow_any_override` is duplicated

**File:** `src/reqm/quant.py`

`quant.py` defines its own `allow_any_override` from before `overrides_ext` existed.
`overrides_ext.py` defines a second one. They're identical in effect but diverged in location.

**Action:** Delete `allow_any_override` from `quant.py` and import it from `overrides_ext` instead.

---

## 2. `Quant` doesn't inherit `EnforceOverrides` yet

**File:** `src/reqm/quant.py`

`Quant` currently inherits from `ABC` only. This means subclasses are NOT required to
use `@override` — the whole point of `overrides_ext` isn't enforced on Quant subclasses yet.

**Action:** Change `Quant` to inherit from both `ABC` and `EnforceOverrides` (or just
`EnforceOverrides`, which already implies `ABC`). Update `quant.py` tests accordingly
since concrete subclasses will now need `@override` on `__call__` and `dummy_inputs`.

---

## 3. `__init__.py` exports nothing yet

**File:** `src/reqm/__init__.py`

The public API (`Quant`, `register`, `get`, and optionally `overrides_ext` symbols)
is not exported from the package. `import reqm` currently gives you nothing.

**Action:** Wire up exports once all three modules (`quant.py`, `registry.py`,
`factory.py`) are implemented.

---

## 4. Examples don't use `@override`

**Files:** `src/reqm/examples/hello_world.py`, `src/reqm/examples/r2p.py`

Examples were written before `overrides_ext` existed. Once item #2 is resolved
(`Quant` inherits `EnforceOverrides`), the example subclasses will break at
class-creation time because they don't use `@override`.

**Action:** Update all example Quant subclasses to use `@override` from `overrides_ext`
after item #2 is done.
