# CLAUDE.md — reqm development guide

This file is for AI coding agents working **on** the reqm library itself.
For guidance on using reqm in your own project, see `llms.txt` or `README.md`.

---

## Tech debt policy

Any consciously taken shortcut or design caveat **must** be recorded in `TECH_DEBT.md`
before the code is committed. Each entry must include:
- What was skipped or compromised
- Why (the constraint that forced it)
- The concrete action needed to repay it

Tech debt that is not recorded does not exist — and will bite us later.
Reviewing and repaying `TECH_DEBT.md` items is a normal part of the workflow,
not an afterthought.

---

## What reqm is

`reqm` (Ridiculously Easy Quant Manager) is a directory-based config management
and object factory built on Hydra's `instantiate`. It eliminates "Hydra ceremony"
(context managers, `@hydra.main`, etc.) while keeping Hydra's config composition
power. A `QuantManager` takes an importable Python config module (a directory with
`__init__.py` and YAML files) and provides a uniform API to list, validate, load,
and build objects from those configs.

---

## Core abstractions

### Quant
The unit reqm builds and manages. An abstract base class that users subclass.

Requirements:
- Must be callable (`__call__`)
- Must implement `dummy_inputs() -> dict` returning example inputs
- Constructor args are defined in YAML config, not hardcoded

The factory calls each Quant with its own `dummy_inputs()` at build time.
This makes Quants **auditable** — not just interface-compliant, but provably runnable.

### QuantManager
Directory-based config manager. Takes an importable Python module whose
directory contains YAML config files and treats it as the Hydra config root.

Key methods:
- `list_configs()` — list all YAML configs in the module
- `validate()` — check that all configs have `# @package _global_`
- `get_config(name)` — load and resolve a config as OmegaConf DictConfig
- `get_raw_config(name)` — load and resolve a config as a YAML string
- `build(name)` — instantiate the `_target_` object from a config

All methods accept optional `config_overrides` (dict) and `param_overrides`
(Hydra CLI-style strings) for runtime customization.

See `docs/config_management.md` for detailed design rationale.

---

## Architecture decisions (do not violate)

1. **No framework ownership.** reqm must never require `@hydra.main`,
   `hydra.initialize()`, or any context manager at the user's call site.
   reqm handles all Hydra plumbing internally.

2. **Fail fast.** `dummy_inputs` is called at build/get time, not at inference.
   Errors surface early and loudly, not silently in production.

3. **Minimal public API.** The surface users touch is:
   - `Quant` (base class to subclass)
   - `QuantManager(config_module)` (config management and object building)
   Keep everything else internal.

4. **Declarative over imperative.** Config files express what to build.
   Python code expresses the interface contract. Never mix them.

5. **Directory-based, not registry-based.** Config modules are importable
   Python packages containing YAMLs. No global registry, no eager imports.
   Every YAML must declare `# @package _global_` for explicit composition.

6. **Generic instantiation.** `QuantManager.build()` instantiates whatever
   `_target_` points to — it does not enforce that the result is a Quant.

---

## Code conventions

### Docstrings
Every public class, method, and function must have a Google-style docstring
with an `Examples:` section containing runnable code. Small LLMs helping users
will rely on these.

```python
def build(self, config_name: str, *, ...) -> object:
    """Build an object from a config via hydra.utils.instantiate.

    Loads the config, applies overrides, resolves interpolations, and
    passes the result to Hydra's recursive instantiation.

    Args:
        config_name: Config name (relative path, no .yaml extension).

    Returns:
        The instantiated object.

    Raises:
        FileNotFoundError: If config_name does not exist.
        hydra.errors.InstantiationException: If instantiation fails.

    Examples:
        >>> import my_configs
        >>> from reqm import QuantManager
        >>> QM = QuantManager(my_configs)
        >>> model = QM.build("summarizer/prod")
        >>> result = model(text="Hello world")
    """
```

### Type annotations
All public APIs must be fully type-annotated. Internal helpers should be
annotated where it aids clarity.

### Error messages
Errors must be actionable. Always tell the user what alias, config path, or
interface was involved and what to do next.

```python
# Good
raise FileNotFoundError(
    f"Config '{config_name}' not found in config module at {self._config_dir}. "
    f"Available configs: {self.list_configs()}"
)

# Bad
raise FileNotFoundError(f"Config not found: {config_name}")
```

### No magic
Avoid metaclass magic, import hooks, or decorators that alter behavior invisibly.
If something happens, it should be traceable by reading the call stack.

---

## File layout

```
src/reqm/
├── __init__.py          # public API exports: Quant, QuantManager
├── quant.py             # Quant ABC definition
├── quant_manager.py     # QuantManager, ConfigValidationError
└── overrides_ext.py     # @override / @allow_any_override support

examples/
└── estimators/          # end-to-end example project
    ├── __init__.py      # QM = QuantManager(configs) — single construction point
    ├── filters/         # non-Quant configurable dependencies
    │   ├── api.py       # Filter base class
    │   ├── no_filter.py, outlier.py, top_k.py
    ├── quants/          # Estimator Quant subclasses
    │   ├── api.py       # Estimator(Quant) base class
    │   ├── mean.py, median.py, trimmed_mean.py, ensemble.py
    ├── scripts/         # uniform call site demos (import QM from parent)
    │   ├── evaluate.py, inspect_config.py, compare.py
    │   ├── validate_configs.py, sweep.py
    └── configs/         # config module for QuantManager
        ├── filters/     # filter configs (non-Quant)
        ├── *.yaml       # estimator configs (compose filters via defaults)
        └── ensemble/    # ensemble configs (compose estimators via defaults)
└── torch_models/        # PyTorch integration example (requires torch)
    ├── __init__.py      # QM = QuantManager(configs)
    ├── torch_quant.py   # TorchQuant bridge (copy into your project)
    ├── models/          # Regressor(TorchQuant) subclasses
    ├── configs/         # model configs
    └── scripts/         # evaluate.py, audit.py
```

---

## What to build next

Completed:
1. ~~`quant.py` — `Quant` ABC with `dummy_inputs` abstract method~~
2. ~~`overrides_ext.py` — `@override` / `@allow_any_override` support~~
3. ~~`quant_manager.py` — `QuantManager` class + `ConfigValidationError`~~

4. ~~`__init__.py` — wire up public API exports (`Quant`, `QuantManager`)~~
5. ~~`examples/` — estimators example project with eval script~~

Remaining:
6. Integration tests with Quant + QuantManager together

---

## Testing

Run tests with:
```bash
uv run pytest
```

### Write tests abundantly

Tests are first-class documentation here. Write as many as are appropriate —
they double as concrete, runnable usage examples that LLMs and humans can learn from.

Rules:
- Every public API must have multiple tests covering: happy path, edge cases, error cases
- Test names must be descriptive sentences: `test_get_returns_correct_quant_instance`,
  not `test_get`
- Each test should be self-contained and readable in isolation — no shared mutable state
- Tests that demonstrate usage patterns are as valuable as tests that catch bugs
- When a new feature is added, write tests before or alongside (not after) the implementation

### Quant ABC signature override

`Quant.__call__` is defined as `**kwargs` and decorated with `@allow_any_override`.
This is intentional. Subclasses narrow the signature to their specific API.
The `@allow_any_override` marker tells type checkers and linters that the
signature change is deliberate, not a mistake.

```python
# Base — accepts anything
class Quant(EnforceOverrides):
    @abstractmethod
    @allow_any_override
    def __call__(self, **kwargs) -> Any: ...

# Subclass — narrows to specific API (correct and intended)
class Summarizer(Quant):
    @override
    def __call__(self, text: str, max_tokens: int = 512) -> str: ...
```

### Two-level signature narrowing (TorchQuant pattern)

`TorchQuant.forward` has `@allow_any_override` so domain base classes can
narrow it. But the domain base class must **not** use `@allow_any_override`
on its own `forward` — this locks the signature for all concrete models:

```
TorchQuant        → forward(**kwargs)           @allow_any_override (open)
  Regressor       → forward(x: Tensor)          NO @allow_any_override (locked)
    LinearModel   → forward(x: Tensor)          must match Regressor exactly
    BadModel      → forward(a, b)               REJECTED at class definition time
```

This pattern is critical for uniform call sites. Without the domain base
locking the signature, each concrete model could use a different `forward`
signature, breaking evaluation scripts at runtime instead of at definition time.

Always create a domain base class between TorchQuant and concrete models.
See `docs/torch_integration.md` for the full explanation.
