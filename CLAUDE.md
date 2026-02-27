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

`reqm` (Ridiculously Easy Quant Manager) is a config-based aliased object factory
with enforced interfaces, built on top of Hydra's `instantiate`. It eliminates
"Hydra ceremony" (context managers, `@hydra.main`, etc.) while keeping Hydra's
config power. The uniform call site — `reqm.get("alias")` — works identically in
notebooks, production services, tests, and scripts.

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

### Registry
Maps alias strings to `(config_path, interface_class)` pairs.
Registration happens at import time or explicitly. The registry is global per process.

### `reqm.get(alias)`
The uniform call site. Looks up the registry, instantiates via
`hydra.utils.instantiate`, validates interface, runs `dummy_inputs` sanity check.
Returns a ready-to-use Quant instance.

---

## Architecture decisions (do not violate)

1. **No framework ownership.** reqm must never require `@hydra.main`,
   `hydra.initialize()`, or any context manager at the user's call site.
   reqm handles all Hydra plumbing internally.

2. **Fail fast.** `dummy_inputs` is called at build/get time, not at inference.
   Errors surface early and loudly, not silently in production.

3. **Minimal public API.** The surface users touch is:
   - `Quant` (base class to subclass)
   - `reqm.register(alias, config_path, interface)` (registration)
   - `reqm.get(alias)` (retrieval)
   Keep everything else internal.

4. **Declarative over imperative.** Config files express what to build.
   Python code expresses the interface contract. Never mix them.

5. **Uniform call site is sacred.** `reqm.get("alias")` must never change
   signature regardless of what's behind the alias.

---

## Code conventions

### Docstrings
Every public class, method, and function must have a Google-style docstring
with an `Examples:` section containing runnable code. Small LLMs helping users
will rely on these.

```python
def get(alias: str) -> Quant:
    """Retrieve a built Quant instance by alias.

    Instantiates the Quant from its registered config, validates it against
    the registered interface, and runs dummy_inputs as a sanity check.

    Args:
        alias: The registered alias string, e.g. "summarizer/prod".

    Returns:
        A ready-to-use Quant instance.

    Raises:
        KeyError: If alias is not registered.
        TypeError: If the instantiated object does not implement the
            registered interface.
        RuntimeError: If dummy_inputs sanity check fails.

    Examples:
        >>> import reqm
        >>> model = reqm.get("summarizer/prod")
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
raise KeyError(
    f"Alias '{alias}' is not registered. "
    f"Call reqm.register('{alias}', config_path, interface) first."
)

# Bad
raise KeyError(f"Unknown alias: {alias}")
```

### No magic
Avoid metaclass magic, import hooks, or decorators that alter behavior invisibly.
If something happens, it should be traceable by reading the call stack.

---

## File layout

```
src/reqm/
├── __init__.py          # public API exports only: Quant, register, get
├── quant.py             # Quant ABC definition
├── registry.py          # Registry class and global instance
├── factory.py           # instantiate logic wrapping hydra
└── examples/
    ├── __init__.py
    ├── hello_world.py   # simplest end-to-end example
    └── r2p.py           # research-to-production swap pattern
```

---

## What to build next (current status: pre-implementation)

Implementation order:
1. `quant.py` — `Quant` ABC with `dummy_inputs` abstract method
2. `registry.py` — `Registry` class: register, lookup
3. `factory.py` — `build(alias)` wrapping `hydra.utils.instantiate`
4. `__init__.py` — wire up public API
5. `examples/` — working hello-world examples
6. `tests/` — one test per public API entry point

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
class Quant(ABC):
    @abstractmethod
    @allow_any_override
    def __call__(self, **kwargs) -> Any: ...

# Subclass — narrows to specific API (correct and intended)
class Summarizer(Quant):
    def __call__(self, text: str, max_tokens: int = 512) -> str: ...
```
