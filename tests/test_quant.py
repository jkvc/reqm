"""
Tests for reqm.quant — Quant ABC and allow_any_override.

Tests here also serve as usage examples: each test is a self-contained
demonstration of how Quant is defined and used.
"""

from typing import Any

import pytest

from reqm.overrides_ext import EnforceOverrides, allow_any_override, override
from reqm.quant import Quant

# ---------------------------------------------------------------------------
# Minimal concrete implementations used across tests
# ---------------------------------------------------------------------------


class EchoQuant(Quant):
    """Quant that echoes its input back. Simplest valid implementation."""

    @override
    def __call__(self, text: str) -> str:
        return text

    @override
    def dummy_inputs(self) -> list[dict[str, Any]]:
        return [{"text": "hello"}]


class MultiInputQuant(Quant):
    """Quant with multiple constructor args and multiple dummy input sets."""

    def __init__(self, prefix: str, suffix: str):
        self.prefix = prefix
        self.suffix = suffix

    @override
    def __call__(self, text: str) -> str:
        return f"{self.prefix}{text}{self.suffix}"

    @override
    def dummy_inputs(self) -> list[dict[str, Any]]:
        return [
            {"text": "hello"},
            {"text": "world"},
            {"text": ""},
        ]


class NoArgsCallQuant(Quant):
    """Quant whose __call__ takes no arguments beyond self."""

    @override
    def __call__(self) -> str:
        return "pong"

    @override
    def dummy_inputs(self) -> list[dict[str, Any]]:
        return [{}]


# ---------------------------------------------------------------------------
# Quant is abstract — cannot be instantiated directly
# ---------------------------------------------------------------------------


def test_quant_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Quant()


def test_quant_subclass_without_call_cannot_be_instantiated():
    class MissingCall(Quant):
        @override
        def dummy_inputs(self) -> list[dict[str, Any]]:
            return [{}]

    with pytest.raises(TypeError):
        MissingCall()


def test_quant_subclass_without_dummy_inputs_cannot_be_instantiated():
    class MissingDummyInputs(Quant):
        @override
        def __call__(self, **kwargs) -> Any:
            return None

    with pytest.raises(TypeError):
        MissingDummyInputs()


def test_quant_subclass_missing_both_methods_cannot_be_instantiated():
    class Empty(Quant):
        pass

    with pytest.raises(TypeError):
        Empty()


# ---------------------------------------------------------------------------
# Concrete subclasses instantiate and call correctly
# ---------------------------------------------------------------------------


def test_echo_quant_returns_input():
    q = EchoQuant()
    assert q(text="hello") == "hello"


def test_echo_quant_returns_empty_string():
    q = EchoQuant()
    assert q(text="") == ""


def test_multi_input_quant_wraps_text():
    q = MultiInputQuant(prefix="[", suffix="]")
    assert q(text="hello") == "[hello]"


def test_multi_input_quant_with_empty_affixes():
    q = MultiInputQuant(prefix="", suffix="")
    assert q(text="bare") == "bare"


def test_no_args_call_quant():
    q = NoArgsCallQuant()
    assert q() == "pong"


# ---------------------------------------------------------------------------
# dummy_inputs returns the right structure
# ---------------------------------------------------------------------------


def test_dummy_inputs_returns_a_list():
    q = EchoQuant()
    result = q.dummy_inputs()
    assert isinstance(result, list)


def test_dummy_inputs_returns_non_empty_list():
    q = EchoQuant()
    assert len(q.dummy_inputs()) > 0


def test_dummy_inputs_each_element_is_a_dict():
    q = MultiInputQuant(prefix=">>", suffix="<<")
    for item in q.dummy_inputs():
        assert isinstance(item, dict)


def test_dummy_inputs_dicts_have_string_keys():
    q = MultiInputQuant(prefix=">>", suffix="<<")
    for item in q.dummy_inputs():
        for key in item:
            assert isinstance(key, str)


def test_dummy_inputs_can_be_expanded_into_call():
    """Each dummy input dict must be **-expandable into __call__."""
    q = MultiInputQuant(prefix=">>", suffix="<<")
    for inputs in q.dummy_inputs():
        result = q(**inputs)
        assert isinstance(result, str)


def test_no_args_dummy_inputs_empty_dict_expands_into_call():
    q = NoArgsCallQuant()
    for inputs in q.dummy_inputs():
        result = q(**inputs)
        assert result == "pong"


def test_dummy_inputs_multiple_sets_all_runnable():
    """All dummy input sets must produce a result without raising."""
    q = MultiInputQuant(prefix="[", suffix="]")
    results = [q(**inputs) for inputs in q.dummy_inputs()]
    assert len(results) == len(q.dummy_inputs())


# ---------------------------------------------------------------------------
# Quant is recognized as ABC-derived and EnforceOverrides-derived
# ---------------------------------------------------------------------------


def test_quant_is_abstract():
    """Quant uses ABCMeta (via EnforceOverridesMeta) so abstractmethods work."""
    from abc import ABCMeta

    assert isinstance(Quant, ABCMeta)


def test_quant_inherits_enforce_overrides():
    assert issubclass(Quant, EnforceOverrides)


def test_concrete_quant_is_instance_of_quant():
    q = EchoQuant()
    assert isinstance(q, Quant)


def test_concrete_quant_is_callable():
    q = EchoQuant()
    assert callable(q)


# ---------------------------------------------------------------------------
# allow_any_override marker
# ---------------------------------------------------------------------------


def test_allow_any_override_sets_marker_attribute():
    def dummy_method():
        pass

    marked = allow_any_override(dummy_method)
    assert hasattr(marked, "__allow_any_override__")
    assert marked.__allow_any_override__ is True


def test_allow_any_override_returns_same_callable():
    def dummy_method():
        return 42

    marked = allow_any_override(dummy_method)
    assert marked() == 42


def test_quant_call_has_allow_any_override_marker():
    """Quant.__call__ must carry the allow_any_override marker."""
    assert getattr(Quant.__call__, "__allow_any_override__", False) is True


def test_subclass_call_does_not_require_marker():
    """Subclass __call__ does NOT need the marker — only the base does."""
    assert not getattr(EchoQuant.__call__, "__allow_any_override__", False)


# ---------------------------------------------------------------------------
# EnforceOverrides — subclass must use @override
# ---------------------------------------------------------------------------


def test_subclass_missing_override_decorator_raises():
    """Quant subclass overriding without @override raises TypeError."""
    with pytest.raises(TypeError):

        class BadQuant(Quant):
            def __call__(self, text: str) -> str:  # missing @override
                return text

            def dummy_inputs(self) -> list[dict[str, Any]]:
                return [{"text": "hello"}]


# ---------------------------------------------------------------------------
# Subclass signature narrowing — the core design intent
# ---------------------------------------------------------------------------


class NarrowedQuant(Quant):
    @override
    def __call__(self, x: int, y: int) -> int:
        return x + y

    @override
    def dummy_inputs(self) -> list[dict[str, Any]]:
        return [{"x": 1, "y": 2}]


def test_subclass_can_narrow_call_signature_to_positional_args():
    """Subclass may define __call__ with specific positional args, not **kwargs."""
    q = NarrowedQuant()
    assert q(x=3, y=4) == 7


class SingleArgQuant(Quant):
    @override
    def __call__(self, value: float) -> float:
        return value * 2.0

    @override
    def dummy_inputs(self) -> list[dict[str, Any]]:
        return [{"value": 1.0}]


def test_subclass_can_narrow_call_to_single_arg():
    q = SingleArgQuant()
    assert q(value=5.0) == 10.0


class TypedQuant(Quant):
    @override
    def __call__(self, numbers: list[int]) -> int:
        return sum(numbers)

    @override
    def dummy_inputs(self) -> list[dict[str, Any]]:
        return [
            {"numbers": [1, 2, 3]},
            {"numbers": []},
            {"numbers": [100]},
        ]


def test_subclass_dummy_inputs_match_narrowed_call_signature():
    """dummy_inputs must match the narrowed __call__ signature."""
    q = TypedQuant()
    for inputs in q.dummy_inputs():
        result = q(**inputs)
        assert isinstance(result, int)
