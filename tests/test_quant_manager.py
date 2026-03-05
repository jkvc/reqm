"""
Tests for reqm.quant_manager.QuantManager.

These tests use tests/test_config_module_one/ as a sample config module
containing YAML configs that exercise atomic configs, defaults-list
composition, chained defaults, multi-dependency defaults, subdirectory
configs, cross-directory references, interpolation, and validation.
"""

import pytest
import yaml
from omegaconf import DictConfig

import tests.test_config_module_one as config_module
from reqm.quant_manager import ConfigValidationError, QuantManager
from tests.dummy_objects import ComposedObject, MultiDepObject, SimpleObject

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def QM() -> QuantManager:
    """A QuantManager pointing at the test config module."""
    return QuantManager(config_module)


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_constructor_accepts_importable_module(self) -> None:
        QM = QuantManager(config_module)
        assert QM is not None

    def test_constructor_rejects_non_module(self) -> None:
        with pytest.raises(TypeError):
            QuantManager("not_a_module")  # type: ignore[arg-type]

    def test_constructor_rejects_none(self) -> None:
        with pytest.raises(TypeError):
            QuantManager(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# list_configs
# ---------------------------------------------------------------------------


class TestListConfigs:
    def test_list_configs_returns_all_yaml_files(self, QM: QuantManager) -> None:
        configs = QM.list_configs()
        assert "atomic_simple" in configs
        assert "atomic_no_target" in configs
        assert "depends_on_atomic" in configs

    def test_list_configs_includes_subdirectory_configs(self, QM: QuantManager) -> None:
        configs = QM.list_configs()
        assert "sub/nested" in configs
        assert "sub/deep/deeply_nested" in configs
        assert "sub/depends_on_root" in configs

    def test_list_configs_excludes_non_yaml_files(self, QM: QuantManager) -> None:
        configs = QM.list_configs()
        for name in configs:
            assert not name.endswith(".py"), f"Python file leaked into list: {name}"
            assert not name.endswith(".pyc"), f"Bytecode file leaked into list: {name}"

    def test_list_configs_returns_sorted_list(self, QM: QuantManager) -> None:
        configs = QM.list_configs()
        assert configs == sorted(configs)

    def test_list_configs_uses_forward_slash_separators(self, QM: QuantManager) -> None:
        configs = QM.list_configs()
        for name in configs:
            assert "\\" not in name, f"Backslash in config name: {name}"


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_validate_passes_for_valid_config(self, QM: QuantManager) -> None:
        QM.validate("atomic_simple")

    def test_validate_passes_for_subdirectory_config(self, QM: QuantManager) -> None:
        QM.validate("sub/nested")

    def test_validate_raises_config_validation_error_on_missing_package_global(
        self, QM: QuantManager
    ) -> None:
        with pytest.raises(ConfigValidationError):
            QM.validate("invalid_no_package_global")

    def test_validate_error_message_includes_config_name(
        self, QM: QuantManager
    ) -> None:
        with pytest.raises(ConfigValidationError, match="invalid_no_package_global"):
            QM.validate("invalid_no_package_global")

    def test_validate_all_finds_invalid_config(self, QM: QuantManager) -> None:
        with pytest.raises(ConfigValidationError):
            QM.validate()

    def test_validate_nonexistent_config_raises(self, QM: QuantManager) -> None:
        with pytest.raises(FileNotFoundError):
            QM.validate("this_config_does_not_exist")


# ---------------------------------------------------------------------------
# get_config — atomic configs
# ---------------------------------------------------------------------------


class TestGetConfigAtomic:
    def test_get_config_atomic_returns_dictconfig(self, QM: QuantManager) -> None:
        cfg = QM.get_config("atomic_simple")
        assert isinstance(cfg, DictConfig)

    def test_get_config_atomic_has_expected_keys(self, QM: QuantManager) -> None:
        cfg = QM.get_config("atomic_simple")
        assert cfg._target_ == "tests.dummy_objects.SimpleObject"
        assert cfg.value == 42
        assert cfg.label == "hello"

    def test_get_config_atomic_no_target(self, QM: QuantManager) -> None:
        cfg = QM.get_config("atomic_no_target")
        assert cfg.database_host == "localhost"
        assert cfg.database_port == 5432
        assert cfg.debug is True

    def test_get_config_nonexistent_raises(self, QM: QuantManager) -> None:
        with pytest.raises(Exception):
            QM.get_config("this_config_does_not_exist")


# ---------------------------------------------------------------------------
# get_config — defaults list composition
# ---------------------------------------------------------------------------


class TestGetConfigDefaults:
    def test_get_config_with_single_default(self, QM: QuantManager) -> None:
        cfg = QM.get_config("depends_on_atomic")
        assert cfg.name == "parent"
        assert cfg._target_ == "tests.dummy_objects.ComposedObject"
        assert cfg.child.value == 42
        assert cfg.child.label == "hello"
        assert cfg.child._target_ == "tests.dummy_objects.SimpleObject"

    def test_get_config_with_chained_defaults(self, QM: QuantManager) -> None:
        """chain_end -> chain_middle -> atomic_simple (depth 2)."""
        cfg = QM.get_config("chain_end")
        assert cfg.name == "end"
        assert cfg.child.name == "middle"
        assert cfg.child.child.value == 42
        assert cfg.child.child.label == "hello"

    def test_get_config_with_multiple_defaults(self, QM: QuantManager) -> None:
        cfg = QM.get_config("multi_dep")
        assert cfg.tag == "multi"
        assert cfg.first.value == 42
        assert cfg.first.label == "hello"
        assert cfg.second.database_host == "localhost"
        assert cfg.second.database_port == 5432

    def test_get_config_cross_directory_reference(self, QM: QuantManager) -> None:
        """Root config referencing a config in sub/."""
        cfg = QM.get_config("depends_on_nested")
        assert cfg.name == "depends_on_nested"
        assert cfg.nested_data.value == 99
        assert cfg.nested_data.label == "nested"

    def test_get_config_subdirectory_references_root(self, QM: QuantManager) -> None:
        """Config in sub/ referencing a config at the root."""
        cfg = QM.get_config("sub/depends_on_root")
        assert cfg.name == "sub_depends_on_root"
        assert cfg.root_data.value == 42
        assert cfg.root_data.label == "hello"

    def test_get_config_from_subdirectory(self, QM: QuantManager) -> None:
        cfg = QM.get_config("sub/nested")
        assert cfg.value == 99
        assert cfg.label == "nested"

    def test_get_config_from_deep_subdirectory(self, QM: QuantManager) -> None:
        cfg = QM.get_config("sub/deep/deeply_nested")
        assert cfg.value == 7
        assert cfg.label == "deep"


# ---------------------------------------------------------------------------
# get_config — interpolation
# ---------------------------------------------------------------------------


class TestGetConfigInterpolation:
    def test_get_config_resolves_interpolations(self, QM: QuantManager) -> None:
        cfg = QM.get_config("with_interpolation")
        assert cfg.base_value == 10
        assert cfg.doubled == 10
        assert cfg.label == "value is 10"

    def test_get_config_throws_on_missing_interpolation(self, QM: QuantManager) -> None:
        with pytest.raises(Exception):
            QM.get_config("with_missing_interpolation")


# ---------------------------------------------------------------------------
# get_config — overrides
# ---------------------------------------------------------------------------


class TestGetConfigOverrides:
    def test_get_config_with_config_overrides_dict(self, QM: QuantManager) -> None:
        cfg = QM.get_config(
            "atomic_simple", config_overrides={"value": 999, "label": "overridden"}
        )
        assert cfg.value == 999
        assert cfg.label == "overridden"

    def test_get_config_with_param_overrides(self, QM: QuantManager) -> None:
        cfg = QM.get_config("atomic_simple", param_overrides=["value=999"])
        assert cfg.value == 999

    def test_get_config_with_both_overrides(self, QM: QuantManager) -> None:
        cfg = QM.get_config(
            "atomic_simple",
            param_overrides=["value=100"],
            config_overrides={"label": "both"},
        )
        assert cfg.value == 100
        assert cfg.label == "both"

    def test_config_overrides_take_precedence_over_param_overrides(
        self, QM: QuantManager
    ) -> None:
        cfg = QM.get_config(
            "atomic_simple",
            param_overrides=["label=from_param"],
            config_overrides={"label": "from_config"},
        )
        assert cfg.label == "from_config"

    def test_get_config_with_config_overrides_adds_new_key(
        self, QM: QuantManager
    ) -> None:
        cfg = QM.get_config("atomic_simple", config_overrides={"new_key": "new_value"})
        assert cfg.new_key == "new_value"
        assert cfg.value == 42


# ---------------------------------------------------------------------------
# get_raw_config
# ---------------------------------------------------------------------------


class TestGetRawConfig:
    def test_get_raw_config_returns_string(self, QM: QuantManager) -> None:
        raw = QM.get_raw_config("atomic_simple")
        assert isinstance(raw, str)

    def test_get_raw_config_is_valid_yaml(self, QM: QuantManager) -> None:
        raw = QM.get_raw_config("atomic_simple")
        parsed = yaml.safe_load(raw)
        assert isinstance(parsed, dict)
        assert parsed["value"] == 42

    def test_get_raw_config_contains_resolved_values(self, QM: QuantManager) -> None:
        raw = QM.get_raw_config("with_interpolation")
        parsed = yaml.safe_load(raw)
        assert parsed["doubled"] == 10
        assert parsed["label"] == "value is 10"

    def test_get_raw_config_with_overrides(self, QM: QuantManager) -> None:
        raw = QM.get_raw_config("atomic_simple", config_overrides={"value": 123})
        parsed = yaml.safe_load(raw)
        assert parsed["value"] == 123


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------


class TestBuild:
    def test_build_instantiates_target_class(self, QM: QuantManager) -> None:
        obj = QM.build("atomic_simple")
        assert isinstance(obj, SimpleObject)

    def test_build_passes_constructor_args(self, QM: QuantManager) -> None:
        obj = QM.build("atomic_simple")
        assert isinstance(obj, SimpleObject)
        assert obj.value == 42
        assert obj.label == "hello"

    def test_build_with_config_overrides(self, QM: QuantManager) -> None:
        obj = QM.build("atomic_simple", config_overrides={"value": 999})
        assert isinstance(obj, SimpleObject)
        assert obj.value == 999

    def test_build_with_param_overrides(self, QM: QuantManager) -> None:
        obj = QM.build("atomic_simple", param_overrides=["value=999"])
        assert isinstance(obj, SimpleObject)
        assert obj.value == 999

    def test_build_recursive_instantiation(self, QM: QuantManager) -> None:
        """depends_on_atomic has a nested _target_ under `child`."""
        obj = QM.build("depends_on_atomic")
        assert isinstance(obj, ComposedObject)
        assert obj.name == "parent"
        assert isinstance(obj.child, SimpleObject)
        assert obj.child.value == 42

    def test_build_multi_dep_recursive(self, QM: QuantManager) -> None:
        obj = QM.build("multi_dep")
        assert isinstance(obj, MultiDepObject)
        assert obj.tag == "multi"
        assert isinstance(obj.first, SimpleObject)
        assert obj.first.value == 42

    def test_build_from_subdirectory(self, QM: QuantManager) -> None:
        obj = QM.build("sub/nested")
        assert isinstance(obj, SimpleObject)
        assert obj.value == 99
        assert obj.label == "nested"

    def test_build_chained_defaults(self, QM: QuantManager) -> None:
        """chain_end -> chain_middle -> atomic_simple (recursive instantiation)."""
        obj = QM.build("chain_end")
        assert isinstance(obj, ComposedObject)
        assert obj.name == "end"
        assert isinstance(obj.child, ComposedObject)
        assert obj.child.name == "middle"
        assert isinstance(obj.child.child, SimpleObject)
        assert obj.child.child.value == 42

    def test_build_nonexistent_config_raises(self, QM: QuantManager) -> None:
        with pytest.raises(Exception):
            QM.build("this_config_does_not_exist")
