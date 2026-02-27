# reqm

**R**idiculously **E**asy **Q**uant **M**anager

Config-based aliased object factory with enforced interfaces. Built on [Hydra](https://hydra.cc).

---

## The problem

Hydra is excellent for experiment management. But using it as a general object factory requires ceremony:

```python
# You have to do all of this just to instantiate one object
with hydra.initialize(config_path="conf"):
    cfg = hydra.compose(config_name="my_model")
    model = hydra.utils.instantiate(cfg.model)
```

This ceremony means Hydra stays in the lab. It's awkward in a notebook, verbose in a service, and doesn't belong in production call sites.

`reqm` gives you Hydra's power — config-driven instantiation, composable overrides, alias-based lookup — with none of the ceremony.

```python
import reqm

model = reqm.get("prod_summarizer")
```

That's it. Same call in a notebook, a FastAPI endpoint, a test, or a batch job.

---

## Core concept: the Quant

A **Quant** is the unit reqm builds and manages. It is:

- **Callable** — invoked directly with its inputs
- **Config-driven** — constructor arguments defined in YAML, no hardcoding
- **Auditable** — must implement `dummy_inputs()`, a dict of example inputs the factory uses to verify it actually runs

```python
from reqm import Quant

class Summarizer(Quant):
    def __init__(self, model_name: str, max_tokens: int):
        self.model = load_model(model_name)
        self.max_tokens = max_tokens

    def dummy_inputs(self) -> dict:
        return {"text": "The quick brown fox jumps over the lazy dog."}

    def __call__(self, text: str) -> str:
        return self.model.summarize(text, max_tokens=self.max_tokens)
```

The `dummy_inputs` contract is what separates a Quant from a plain ABC. reqm calls each Quant with its own dummy inputs at build time — if it fails, it fails early and loudly, not silently in production.

---

## Handshake once, handoff

Register your interface once. After that, any conforming Quant can be swapped in via config — no call site changes, ever.

```yaml
# conf/summarizer/prod.yaml
_target_: myproject.models.Summarizer
model_name: gpt-4o
max_tokens: 512

# conf/summarizer/fast.yaml
_target_: myproject.models.Summarizer
model_name: gpt-4o-mini
max_tokens: 128

# conf/summarizer/experiment_v3.yaml
_target_: myproject.models.FinetunedSummarizer
checkpoint: runs/v3/best.ckpt
max_tokens: 256
```

```python
# This line never changes
model = reqm.get("summarizer/prod")
model = reqm.get("summarizer/fast")
model = reqm.get("summarizer/experiment_v3")
```

This is the R2P (research-to-production) pattern: iterate freely in config space, ship without touching call sites.

---

## Why not just Hydra?

Hydra is framework-first. It expects to own your program's entry point. `reqm` is library-first — it has no opinion about your application structure and works wherever Python runs.

| | Hydra | reqm |
|---|---|---|
| Object instantiation | ✅ | ✅ |
| Config composition | ✅ | ✅ (via Hydra) |
| Interface enforcement | ❌ | ✅ |
| Auditability (`dummy_inputs`) | ❌ | ✅ |
| Works in notebooks | ⚠️ | ✅ |
| CLI ceremony required | ✅ | ❌ |

---

## Name

`reqm` is also a nod to [Rue Esquermoise](https://en.wikipedia.org/wiki/Rue_Esquermoise), one of the oldest streets in Lille, France, dating to the 13th century. Its etymology traces to the Flemish *eskelm* — "frontier." A fitting name for a library that sits at the frontier between research and production.

---

## Status

Early development. API design in progress.
