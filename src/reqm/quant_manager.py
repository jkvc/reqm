"""
quant_manager.py — Directory-based config management for reqm.

QuantManager takes an importable Python module (a directory with ``__init__.py``
and YAML config files) and treats its filesystem root as a Hydra config search
path. It provides methods to list, validate, load, and instantiate configs.
"""

from __future__ import annotations

import types
from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf


class ConfigValidationError(Exception):
    """Raised when a config file fails validation.

    Includes the config path and a description of what failed, so the user
    knows exactly which file to fix and what to change.

    Args:
        message: Human-readable description of the validation failure.

    Examples:
        Raised when ``# @package _global_`` is missing::

            raise ConfigValidationError(
                "Config 'model_a' at /path/to/model_a.yaml is missing the "
                "required '# @package _global_' header. Add it as the first "
                "line of the file."
            )
    """


class QuantManager:
    """Directory-based config manager built on Hydra.

    Takes an importable Python config module and uses its directory as the
    Hydra config root. Provides a uniform API to list, validate, load, and
    build objects from YAML configs.

    Args:
        config_module: An imported Python module whose directory contains
            YAML config files. Must be a real module with a ``__path__``
            or ``__file__`` attribute.

    Raises:
        TypeError: If *config_module* is not a Python module.

    Examples:
        Create a QuantManager from a config module::

            import my_configs
            from reqm import QuantManager

            QM = QuantManager(my_configs)
            QM.list_configs()        # ["model_a", "sub/model_b"]
            cfg = QM.get_config("model_a")
            obj = QM.build("model_a")
    """

    def __init__(self, config_module: types.ModuleType) -> None:
        if not isinstance(config_module, types.ModuleType):
            raise TypeError(
                f"Expected an imported Python module, got "
                f"{type(config_module).__name__}. Pass the module object "
                f"itself (e.g. `import my_configs; QuantManager(my_configs)`)."
            )

        if hasattr(config_module, "__path__"):
            self._config_dir = Path(config_module.__path__[0]).resolve()
        elif hasattr(config_module, "__file__") and config_module.__file__ is not None:
            self._config_dir = Path(config_module.__file__).resolve().parent
        else:
            raise TypeError(
                f"Module {config_module.__name__!r} has no __path__ or __file__ "
                f"attribute. Cannot determine config directory."
            )

    def _resolve_config_path(self, config_name: str) -> Path:
        """Return the absolute path to a config's YAML file, or raise."""
        yaml_path = self._config_dir / f"{config_name}.yaml"
        if not yaml_path.is_file():
            raise FileNotFoundError(
                f"Config '{config_name}' not found in config module "
                f"at {self._config_dir}. "
                f"Available configs: {self.list_configs()}"
            )
        return yaml_path

    def list_configs(self) -> list[str]:
        """List all YAML config names in the config module.

        Recursively walks the config module directory and returns config
        names (relative paths without the ``.yaml`` extension), sorted
        alphabetically.

        Returns:
            Sorted list of config name strings.

        Examples:
            >>> QM = QuantManager(my_configs)
            >>> QM.list_configs()
            ['model_a', 'model_b', 'serving/prod', 'serving/staging']
        """
        return sorted(
            str(p.relative_to(self._config_dir).with_suffix("")).replace("\\", "/")
            for p in self._config_dir.rglob("*.yaml")
        )

    def validate(self, config_name: str | None = None) -> None:
        """Validate that configs have the required ``# @package _global_`` header.

        If *config_name* is provided, validates only that config. If ``None``,
        validates every YAML file in the config module.

        Args:
            config_name: Optional config name to validate. If ``None``,
                validates all configs.

        Raises:
            ConfigValidationError: If a config is missing
                ``# @package _global_``.
            FileNotFoundError: If *config_name* does not correspond to a
                YAML file in the config module.

        Examples:
            Validate a single config::

                QM.validate("model_a")  # raises if invalid

            Validate all configs at once::

                QM.validate()  # checks every YAML in the module
        """
        names = [config_name] if config_name is not None else self.list_configs()
        for name in names:
            yaml_path = self._resolve_config_path(name)
            content = yaml_path.read_text(encoding="utf-8")
            if "# @package _global_" not in content:
                raise ConfigValidationError(
                    f"Config '{name}' at {yaml_path} is missing the required "
                    f"'# @package _global_' header. Add it as the first line "
                    f"of the file."
                )

    def get_config(
        self,
        config_name: str,
        *,
        config_overrides: dict | DictConfig | None = None,
        param_overrides: list[str] | None = None,
    ) -> DictConfig:
        """Load and fully resolve a config by name.

        Composes the config via Hydra, applies overrides, resolves all
        interpolations, and returns the result as an OmegaConf ``DictConfig``.

        Args:
            config_name: Config name (relative path, no ``.yaml`` extension).
            config_overrides: Optional dict or ``DictConfig`` merged on top
                of the composed config.
            param_overrides: Optional list of Hydra CLI-style override strings
                (e.g. ``["key=val", "nested.key=123"]``).

        Returns:
            Fully resolved ``DictConfig``.

        Raises:
            FileNotFoundError: If *config_name* does not exist.
            omegaconf.errors.MissingMandatoryValue: If an interpolation
                cannot be resolved.

        Examples:
            >>> cfg = QM.get_config("model_a")
            >>> cfg = QM.get_config("model_a", param_overrides=["lr=0.01"])
            >>> cfg = QM.get_config("model_a", config_overrides={"lr": 0.01})
        """
        self._resolve_config_path(config_name)

        GlobalHydra.instance().clear()
        with initialize_config_dir(config_dir=str(self._config_dir), version_base=None):
            cfg = compose(config_name=config_name, overrides=param_overrides or [])
        if config_overrides is not None:
            OmegaConf.set_struct(cfg, False)
            cfg = OmegaConf.merge(cfg, config_overrides)
        OmegaConf.resolve(cfg)
        return cfg

    def get_raw_config(
        self,
        config_name: str,
        *,
        config_overrides: dict | DictConfig | None = None,
        param_overrides: list[str] | None = None,
    ) -> str:
        """Load, resolve, and return a config as a YAML string.

        Equivalent to calling :meth:`get_config` and serializing the result
        via ``OmegaConf.to_yaml``.

        Args:
            config_name: Config name (relative path, no ``.yaml`` extension).
            config_overrides: Optional dict or ``DictConfig`` merged on top.
            param_overrides: Optional Hydra CLI-style override strings.

        Returns:
            The resolved config serialized as a YAML string.

        Examples:
            >>> yaml_str = QM.get_raw_config("model_a")
            >>> print(yaml_str)
            _target_: my_module.ModelA
            lr: 0.001
        """
        cfg = self.get_config(
            config_name,
            config_overrides=config_overrides,
            param_overrides=param_overrides,
        )
        return OmegaConf.to_yaml(cfg)

    def build(
        self,
        config_name: str,
        *,
        config_overrides: dict | DictConfig | None = None,
        param_overrides: list[str] | None = None,
    ) -> object:
        """Build an object from a config via ``hydra.utils.instantiate``.

        Loads the config with :meth:`get_config`, then passes it to Hydra's
        recursive instantiation. Returns whatever ``_target_`` points to.

        This is a generic instantiator — it does **not** require the result
        to be a :class:`~reqm.quant.Quant` subclass.

        Args:
            config_name: Config name (relative path, no ``.yaml`` extension).
            config_overrides: Optional dict or ``DictConfig`` merged on top.
            param_overrides: Optional Hydra CLI-style override strings.

        Returns:
            The instantiated object.

        Raises:
            FileNotFoundError: If *config_name* does not exist.
            hydra.errors.InstantiationException: If instantiation fails.

        Examples:
            >>> obj = QM.build("model_a")
            >>> obj = QM.build("model_a", param_overrides=["lr=0.01"])
        """
        cfg = self.get_config(
            config_name,
            config_overrides=config_overrides,
            param_overrides=param_overrides,
        )
        return instantiate(cfg)
