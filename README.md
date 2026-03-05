# reqm

**R**idiculously **E**asy **Q**uant **M**anager

Directory-based config management and object factory built on [Hydra](https://hydra.cc).

---

## The problem

Hydra is excellent for config-driven instantiation. But using it as a general object factory requires ceremony:

```python
# You have to do all of this just to instantiate one object
with hydra.initialize(config_path="conf"):
    cfg = hydra.compose(config_name="my_model")
    model = hydra.utils.instantiate(cfg.model)
```

This ceremony means Hydra stays in the lab. It's awkward in a notebook, verbose in a service, and doesn't belong in production call sites.

`reqm` gives you Hydra's power — config-driven instantiation, composable overrides, recursive object graphs — with none of the ceremony:

```python
from reqm import QuantManager
import my_configs

QM = QuantManager(my_configs)
model = QM.build("summarizer_prod")
```

Same call in a notebook, a FastAPI endpoint, a test, or a batch job.

---

## Core concept: the Quant

A **Quant** is the unit reqm builds and manages. It is:

- **Callable** — invoked directly with its inputs
- **Config-driven** — constructor arguments defined in YAML, no hardcoding
- **Auditable** — implements `dummy_inputs()`, example inputs the factory uses to verify it actually runs

```python
from reqm import Quant
from reqm.overrides_ext import override

class Summarizer(Quant):
    def __init__(self, model_name: str, max_tokens: int):
        self.model = load_model(model_name)
        self.max_tokens = max_tokens

    @override
    def dummy_inputs(self) -> list[dict]:
        return [{"text": "The quick brown fox jumps over the lazy dog."}]

    @override
    def __call__(self, text: str) -> str:
        return self.model.summarize(text, max_tokens=self.max_tokens)
```

The `dummy_inputs` contract is what separates a Quant from a plain ABC. reqm can call each Quant with its own dummy inputs at build time — if it fails, it fails early and loudly, not silently in production.

---

## Config modules and QuantManager

A **config module** is any importable Python package containing YAML files:

```
my_configs/
├── __init__.py
├── summarizer_prod.yaml
├── summarizer_fast.yaml
└── serving/
    └── prod.yaml
```

Each YAML config declares what to build:

```yaml
# @package _global_
_target_: myproject.models.Summarizer
model_name: gpt-4o
max_tokens: 512
```

`QuantManager` takes the config module and gives you a uniform API:

```python
import my_configs
from reqm import QuantManager

QM = QuantManager(my_configs)
QM.list_configs()          # ["serving/prod", "summarizer_fast", "summarizer_prod"]
QM.validate()              # check all configs have # @package _global_
cfg = QM.get_config("summarizer_prod")   # resolved OmegaConf DictConfig
obj = QM.build("summarizer_prod")        # instantiated object
```

Configs can compose other configs via Hydra defaults lists:

```yaml
# @package _global_
defaults:
  - /base_model@child
  - _self_
_target_: myproject.models.Ensemble
weight: 0.6
```

---

## The uniform call site

The core value proposition: ONE script, swap the config name, get different experimental results. No code changes, no if/else chains, no factory functions.

```python
import sys
import my_configs
from reqm import QuantManager

QM = QuantManager(my_configs)
model = QM.build(sys.argv[1])       # <-- only this string changes
result = model(text="Hello world")
```

```bash
python evaluate.py summarizer_prod
python evaluate.py summarizer_fast
python evaluate.py summarizer_experiment_v3
```

---

## Runnable example

The repo includes a complete example project at `examples/estimators/` that demonstrates Quant subclasses, non-Quant configurable dependencies (Filters), Hydra config composition, and multiple scripts sharing the same uniform call site:

```bash
# Evaluate a single estimator config
uv run python -m examples.estimators.scripts.evaluate mean_simple

# Inspect the fully resolved config YAML
uv run python -m examples.estimators.scripts.inspect_config ensemble/mean_median

# Compare multiple configs side by side
uv run python -m examples.estimators.scripts.compare mean_simple mean_outlier median_simple

# Validate all configs
uv run python -m examples.estimators.scripts.validate_configs

# Sweep all configs and rank by performance
uv run python -m examples.estimators.scripts.sweep
```

---

## Why not just Hydra?

Hydra is framework-first. It expects to own your program's entry point. `reqm` is library-first — it has no opinion about your application structure and works wherever Python runs.

| | Hydra | reqm |
|---|---|---|
| Object instantiation | yes | yes |
| Config composition | yes | yes (via Hydra) |
| Auditability (`dummy_inputs`) | no | yes |
| Works in notebooks | limited | yes |
| CLI ceremony required | yes | no |

---

## Name

`reqm` is also a nod to [Rue Esquermoise](https://en.wikipedia.org/wiki/Rue_Esquermoise), one of the oldest streets in Lille, France, dating to the 13th century. Its etymology traces to the Flemish *eskelm* — "frontier." A fitting name for a library that sits at the frontier between research and production.

---

## Status

Core API implemented: `Quant`, `QuantManager`, config composition, and override support all work. See `examples/estimators/` for a complete working project.
