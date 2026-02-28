"""
Tests for reqm.overrides_ext — allow_any_override, override, final, EnforceOverrides.

Tests also serve as usage examples for each exported symbol.
"""

import abc
import typing as ty

import pytest

from reqm.overrides_ext import (
    EnforceOverrides,
    allow_any_override,
    final,
    override,
)

# ---------------------------------------------------------------------------
# allow_any_override
# ---------------------------------------------------------------------------


def test_allow_any_override_sets_attribute():
    def method():
        pass

    marked = allow_any_override(method)
    assert marked.__allow_any_override__ is True


def test_allow_any_override_returns_same_function():
    def method():
        return 42

    marked = allow_any_override(method)
    assert marked() == 42


def test_allow_any_override_preserves_function_name():
    def my_method():
        pass

    marked = allow_any_override(my_method)
    assert marked.__name__ == "my_method"


def test_allow_any_override_on_method_without_attribute_initially():
    def method():
        pass

    assert not hasattr(method, "__allow_any_override__")
    allow_any_override(method)
    assert method.__allow_any_override__ is True


# ---------------------------------------------------------------------------
# override — allows signature narrowing when parent has @allow_any_override
# ---------------------------------------------------------------------------


class _NarrowCallBase(EnforceOverrides):
    @abc.abstractmethod
    @allow_any_override
    def __call__(self, **kwargs) -> ty.Any: ...


class _NarrowCallChild(_NarrowCallBase):
    @override
    def __call__(self, text: str) -> str:
        return text.upper()


def test_override_allows_signature_narrowing_on_allow_any_override_method():
    """Subclass can narrow __call__ signature when parent has @allow_any_override."""
    child = _NarrowCallChild()
    assert child(text="hello") == "HELLO"


class _MultiArgBase(EnforceOverrides):
    @abc.abstractmethod
    @allow_any_override
    def __call__(self, **kwargs) -> ty.Any: ...


class _MultiArgChild(_MultiArgBase):
    @override
    def __call__(self, x: int, y: int) -> int:
        return x + y


def test_override_allows_multiple_specific_args_when_parent_has_allow_any_override():
    child = _MultiArgChild()
    assert child(x=3, y=4) == 7


class _NoArgBase(EnforceOverrides):
    @abc.abstractmethod
    @allow_any_override
    def compute(self, **kwargs) -> ty.Any: ...


class _NoArgChild(_NoArgBase):
    @override
    def compute(self) -> str:
        return "done"


def test_override_allows_no_args_when_parent_has_allow_any_override():
    child = _NoArgChild()
    assert child.compute() == "done"


def test_override_enforces_method_exists_in_parent():
    """@override on a method that doesn't exist in any parent raises TypeError."""
    with pytest.raises(TypeError, match="does not override"):

        class _NonexistentChild(EnforceOverrides):
            @override
            def nonexistent_method(self) -> None: ...


class _GreetBase(EnforceOverrides):
    def greet(self) -> str:
        return "hello"


class _GreetChild(_GreetBase):
    @override
    def greet(self) -> str:
        return "hi"


def test_override_works_on_normal_method_without_allow_any_override():
    """@override on a normal (non-allow_any_override) parent method works."""
    child = _GreetChild()
    assert child.greet() == "hi"


class _AbstractNameBase(EnforceOverrides):
    @abc.abstractmethod
    def name(self) -> str: ...


class _AbstractNameChild(_AbstractNameBase):
    @override
    def name(self) -> str:
        return "child"


def test_override_on_abstract_method_without_allow_any_override():
    """@override on a plain abc.abstractmethod (no allow_any_override) works."""
    child = _AbstractNameChild()
    assert child.name() == "child"


# ---------------------------------------------------------------------------
# EnforceOverrides — subclass must mark all overrides with @override
# ---------------------------------------------------------------------------


class _EnforceBase(EnforceOverrides):
    def greet(self) -> str:
        return "hello"


def test_enforce_overrides_requires_override_decorator():
    """EnforceOverrides raises if a method is overridden without @override."""
    with pytest.raises(TypeError):

        class Child(_EnforceBase):
            def greet(self) -> str:  # missing @override
                return "hi"


class _ValueBase(EnforceOverrides):
    def value(self) -> int:
        return 1


class _ValueChild(_ValueBase):
    @override
    def value(self) -> int:
        return 2


def test_enforce_overrides_passes_when_override_used():
    assert _ValueChild().value() == 2


class _ComboBase(EnforceOverrides):
    @abc.abstractmethod
    @allow_any_override
    def __call__(self, **kwargs) -> ty.Any: ...

    @abc.abstractmethod
    def label(self) -> str: ...


class _ComboChild(_ComboBase):
    @override
    def __call__(self, text: str) -> str:  # narrowed
        return text

    @override
    def label(self) -> str:
        return "child"


def test_enforce_overrides_with_allow_any_override_combo():
    """Full pattern: EnforceOverrides + allow_any_override + override."""
    c = _ComboChild()
    assert c(text="hello") == "hello"
    assert c.label() == "child"


# ---------------------------------------------------------------------------
# final — re-exported from overrides library
# ---------------------------------------------------------------------------


class _FinalBase(EnforceOverrides):
    @final
    def locked(self) -> str:
        return "locked"


def test_final_prevents_overriding():
    with pytest.raises(TypeError):

        class Child(_FinalBase):
            @override
            def locked(self) -> str:
                return "unlocked"


class _FinalCallableBase:
    @final
    def value(self) -> int:
        return 99


def test_final_method_is_callable():
    assert _FinalCallableBase().value() == 99


# ---------------------------------------------------------------------------
# __all__ exports
# ---------------------------------------------------------------------------


def test_all_exports_are_present():
    from reqm import overrides_ext

    for name in ["allow_any_override", "override", "final", "EnforceOverrides"]:
        assert hasattr(overrides_ext, name), f"Missing export: {name}"
