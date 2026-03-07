# PyTorch Integration

reqm is a generic library — it does not depend on PyTorch. But its primary
use case is config-driven model experimentation with `nn.Module` subclasses.
This document explains the `__call__` conflict and provides a ready-to-use
bridge class.

---

## The problem: `__call__` ownership

`Quant` requires subclasses to override `__call__`. `nn.Module` requires
subclasses to override `forward()` and leave `__call__` alone, because
`nn.Module.__call__` runs forward/backward hooks, autograd profiling,
and then calls `self.forward()`.

If you override `__call__` on an `nn.Module`, you bypass all of PyTorch's
hook machinery. Gradients may not flow, hooks won't fire, and profiling
breaks silently.

---

## The solution: TorchQuant

`TorchQuant` is a bridge class that inherits from both `nn.Module` and
`Quant`. It:

1. Provides a concrete `__call__` that delegates to `nn.Module.__call__`
   (preserving hooks and autograd)
2. Makes `forward()` the abstract method with `@allow_any_override`, so
   subclasses narrow its signature freely

```python
class TorchQuant(nn.Module, Quant):
    @override
    def __call__(self, **kwargs):
        return nn.Module.__call__(self, **kwargs)

    @abstractmethod
    @allow_any_override
    def forward(self, **kwargs): ...
```

Subclasses override `forward()` (not `__call__`) and `dummy_inputs()`:

```python
class MyModel(TorchQuant):
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.linear = nn.Linear(hidden_dim, 1)

    @override
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)

    @override
    def dummy_inputs(self) -> list[dict[str, object]]:
        return [{"x": torch.randn(4, hidden_dim)}]
```

---

## Where TorchQuant lives

`TorchQuant` is **not** part of the `reqm` package — it lives in
`examples/torch_models/torch_quant.py`. Copy it into your own project:

```bash
cp examples/torch_models/torch_quant.py myproject/torch_quant.py
```

Then import from your copy:

```python
from myproject.torch_quant import TorchQuant
```

This keeps reqm dependency-free while giving you a tested, documented
bridge class.

---

## What still works

Everything from plain Quant carries over:

- **Config-driven instantiation** — constructor args in YAML, built with
  `QM.build("config_name")`
- **Auditability** — `dummy_inputs()` is called at build time to verify
  the model runs
- **Uniform call site** — `model(**inputs)` works identically whether
  the model is a plain Quant or a TorchQuant

Plus everything from nn.Module:

- **Hooks** — forward hooks, backward hooks all fire normally
- **Gradients** — autograd works because `__call__` goes through
  `nn.Module.__call__` → `forward()`
- **state_dict** — `model.state_dict()` and `load_state_dict()` work
- **Parameters** — `model.parameters()` returns all learnable parameters
- **Device management** — `model.to(device)`, `model.cuda()`, etc.

---

## What to watch for

### `super().__init__()` is required

`nn.Module.__init__()` must be called for parameter registration. Always
call `super().__init__()` in your constructor:

```python
class MyModel(TorchQuant):
    def __init__(self, hidden_dim: int):
        super().__init__()  # <-- required
        self.linear = nn.Linear(hidden_dim, 1)
```

### `@override` on `forward()`

`EnforceOverrides` requires the `@override` decorator on `forward()`.
This is intentional — it makes the override explicit.

### Don't override `__call__`

The whole point of TorchQuant is that `__call__` is handled for you.
Override `forward()` instead.

### Always create a domain base class that locks `forward`

`TorchQuant.forward` has `@allow_any_override`, meaning any direct subclass
can use whatever signature it wants. This is intentional — TorchQuant
doesn't know your domain. But if every concrete model subclasses TorchQuant
directly, there's no shared contract. Your evaluation scripts would break
at runtime when one model expects `forward(x)` and another expects
`forward(a, b, c)`.

The fix: create a **domain base class** between TorchQuant and your concrete
models. The domain base overrides `forward` with the narrowed signature and
does **not** apply `@allow_any_override`, locking it for all descendants:

```python
class Regressor(TorchQuant):
    """All regressors share: forward(self, x: Tensor) -> Tensor."""
    in_features: int

    @override
    @abc.abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor: ...
    # No @allow_any_override here — the signature is locked

    @override
    def dummy_inputs(self) -> list[dict[str, object]]:
        return [{"x": torch.randn(4, self.in_features)}]
```

Now `EnforceOverrides` rejects any subclass that tries a different signature:

```python
class LinearRegressor(Regressor):      # OK — matches forward(self, x)
    @override
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)

class BadRegressor(Regressor):          # TypeError at class definition time
    @override
    def forward(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return a + b
```

The three levels:

| Level | Class | `forward` | `@allow_any_override`? |
|-------|-------|-----------|----------------------|
| 1 | `TorchQuant` | `**kwargs` (open) | Yes |
| 2 | Domain base (e.g. `Regressor`) | Narrowed (e.g. `x: Tensor`) | **No** — locked |
| 3 | Concrete model (e.g. `LinearRegressor`) | Must match level 2 | N/A |

This is the "handshake once, handoff" pattern applied to PyTorch models:
define the interface once in the domain base, then iterate freely on
implementations knowing the contract is enforced at class definition time.

---

## Runnable example

The repo includes a complete torch example at `examples/torch_models/`:

```bash
# Evaluate a model
uv run python -m examples.torch_models.scripts.evaluate linear_simple
uv run python -m examples.torch_models.scripts.evaluate mlp_small
uv run python -m examples.torch_models.scripts.evaluate mlp_large

# Audit all models (build + run dummy_inputs)
uv run python -m examples.torch_models.scripts.audit
```

Structure:

```
examples/torch_models/
├── __init__.py          # QM = QuantManager(configs)
├── torch_quant.py       # TorchQuant bridge (copy this into your project)
├── models/
│   ├── api.py           # Regressor(TorchQuant) base class
│   ├── linear.py        # LinearRegressor
│   └── mlp.py           # MLPRegressor
├── configs/
│   ├── linear_simple.yaml
│   ├── mlp_small.yaml
│   └── mlp_large.yaml
└── scripts/
    ├── evaluate.py      # Run a model on synthetic data
    └── audit.py         # Build all models and verify with dummy_inputs
```
