# Config Management Design

## Overview

reqm uses **directory-based config management** built on Hydra's config
composition. There is no global registry. Instead, a "config module" is any
Python-importable package (a directory with `__init__.py`) that contains YAML
config files. `QuantManager` takes such a module and uses its filesystem root
as the Hydra config search path.

This replaces the previously planned `reqm.register()` / `reqm.get()` registry
pattern. The registry approach required eager imports of every config at startup,
which scales poorly and couples code to import order. Directory-based management
is lazy — configs are loaded on demand from the filesystem.

---

## QuantManager API

```python
from types import ModuleType
from omegaconf import DictConfig

class QuantManager:
    def __init__(self, config_module: ModuleType) -> None: ...
    def list_configs(self) -> list[str]: ...
    def validate(self, config_name: str | None = None) -> None: ...
    def get_config(
        self,
        config_name: str,
        *,
        config_overrides: dict | DictConfig | None = None,
        param_overrides: list[str] | None = None,
    ) -> DictConfig: ...
    def get_raw_config(
        self,
        config_name: str,
        *,
        config_overrides: dict | DictConfig | None = None,
        param_overrides: list[str] | None = None,
    ) -> str: ...
    def build(
        self,
        config_name: str,
        *,
        config_overrides: dict | DictConfig | None = None,
        param_overrides: list[str] | None = None,
    ) -> object: ...
```

### Constructor

`QuantManager(config_module)` accepts an imported Python module. It resolves
the module's `__path__` (or `__file__` parent) to an absolute directory, which
becomes the Hydra config root. Raises `TypeError` if the argument is not a
module.

### config_name convention

All methods that accept a `config_name` use the **relative path without the
`.yaml` extension**, matching Hydra convention:

- `"greeter"` → `greeter.yaml` at the config root
- `"sub/model"` → `sub/model.yaml` relative to the config root

### list_configs

Returns a sorted list of all `.yaml` file paths (relative to the config root,
without extension) found recursively in the config module directory.

### validate

Checks that config files contain the required `# @package _global_` header.

- `validate()` — validates every YAML in the config module
- `validate("some_config")` — validates only the named config

Raises `ConfigValidationError` (a custom exception) with an actionable message
when validation fails. Raises `FileNotFoundError` for nonexistent config names.

### get_config

Loads and fully resolves a config:

1. Initialize Hydra with the config module directory via `initialize_config_dir`
2. Call `hydra.compose(config_name, overrides=param_overrides)`
3. Merge `config_overrides` dict on top (if provided) via `OmegaConf.merge`
4. Resolve all interpolations with `OmegaConf.resolve` / `throw_on_missing=True`

Returns a fully resolved `DictConfig`.

### get_raw_config

Same as `get_config`, but serializes the resolved `DictConfig` to a YAML string
via `OmegaConf.to_yaml` and returns that string.

### build

Calls `get_config` to obtain the resolved config, then passes it to
`hydra.utils.instantiate`. Returns whatever object `_target_` points to.
This is a **generic** instantiator — it does not enforce that the result is a
`Quant` subclass.

---

## Override Pipeline

Two override mechanisms are supported, applied in order:

1. **`param_overrides`** (`list[str] | None`) — Hydra CLI-style overrides
   passed directly to `hydra.compose`. Examples: `["greeting=Hi",
   "nested.key=123"]`.

2. **`config_overrides`** (`dict | DictConfig | None`) — A dict merged on
   top of the composed config via `OmegaConf.merge`. Useful for programmatic
   overrides.

Resolution order: Hydra compose → merge config_overrides → OmegaConf.resolve.

---

## The `@package _global_` Requirement

Every YAML config managed by `QuantManager` **must** include this header as
its first directive:

```yaml
# @package _global_
```

### Why

Hydra's default behavior places a config's keys under a namespace derived from
its filesystem path. A config at `db/mysql.yaml` would nest its keys under
`db.mysql` by default. This implicit nesting makes cross-config interpolation
confusing and path-dependent.

`@package _global_` forces every config to declare its keys at the **root
level**. When composing configs via the defaults list, the placement is made
**explicit** with the `@` operator:

```yaml
# pipeline.yaml
# @package _global_
defaults:
  - /db/mysql@database

pipeline_name: my_pipeline
```

This places the contents of `db/mysql.yaml` under the `database` key — the
location is stated right there in the defaults list, not implied by the
filesystem path. This is maximally explicit and avoids surprises when configs
move between directories.

### Enforcement

`QuantManager.validate()` checks for this header and raises
`ConfigValidationError` if missing. Users are encouraged to call `validate()`
early (e.g., in tests or CI) to catch violations before they cause confusing
Hydra errors downstream.

---

## Config Module Structure

A config module is any importable Python package containing YAML files:

```
my_configs/
├── __init__.py          # makes it importable
├── model_a.yaml
├── model_b.yaml
└── serving/
    ├── prod.yaml
    └── staging.yaml
```

Usage:

```python
import my_configs
from reqm import QuantManager

QM = QuantManager(my_configs)

# List available configs
QM.list_configs()   # ["model_a", "model_b", "serving/prod", "serving/staging"]

# Load a config
cfg = QM.get_config("model_a")

# Build an object
model = QM.build("model_a")

# Validate all configs
QM.validate()
```

---

## Custom Exceptions

```python
class ConfigValidationError(Exception):
    """Raised when a config file fails validation.

    Includes the config path and a description of what failed, so the user
    knows exactly which file to fix and what to change.
    """
```

---

## Hydra Session Management

`QuantManager` manages Hydra's global state internally. Each call to
`get_config` / `get_raw_config` / `build` clears and reinitializes the Hydra
global singleton via `GlobalHydra.instance().clear()` before composing. This
ensures:

- Multiple `QuantManager` instances (pointing to different config modules) can
  coexist in the same process
- Repeated calls do not conflict with stale global state

This is an internal implementation detail — users never interact with Hydra
directly.
