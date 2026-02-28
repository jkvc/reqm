"""
overrides_ext.py — Extended override utilities for reqm.

A thin extension of the `overrides` library that adds `allow_any_override`,
a marker for abstract methods whose signature subclasses are permitted to narrow.

The problem this solves:
    Quant defines ``__call__(self, **kwargs)`` as abstract so subclasses can
    narrow it to any specific signature (e.g. ``__call__(self, text: str)``).
    The vanilla ``@override`` would reject this as a signature mismatch.
    ``@allow_any_override`` on the base method tells our ``@override`` to skip
    signature checking for that particular method — while keeping it enforced
    for all other overrides.

Public API:
    allow_any_override  — marker decorator for base methods
    override            — drop-in for @override, respects @allow_any_override
    final               — re-export from overrides library (unchanged)
    EnforceOverrides    — re-export from overrides library (unchanged)

Usage::

    from reqm.overrides_ext import allow_any_override, override, EnforceOverrides

    class Base(EnforceOverrides):
        @abstractmethod
        @allow_any_override
        def __call__(self, **kwargs) -> Any: ...       # any signature OK

        @abstractmethod
        def name(self) -> str: ...                     # signature enforced

    class Child(Base):
        @override
        def __call__(self, text: str) -> str: ...      # different sig — allowed

        @override
        def name(self) -> str: ...                     # same sig — required
"""

import sys
import typing as ty

from overrides import EnforceOverrides, final
from overrides.overrides import _get_base_classes, _overrides

F = ty.TypeVar("F", bound=ty.Callable[..., ty.Any])


def _should_enforce_signature(method: ty.Callable) -> bool:
    """Decide whether signature checking applies for this override.

    Returns False if the method itself carries ``@allow_any_override``, or if
    every parent definition of the same method carries it.  Returns True as
    soon as any parent definition is found *without* the marker.

    Raises:
        TypeError: If no parent class defines a method with the same name.
    """
    if getattr(method, "__allow_any_override__", False):
        return False

    global_vars = getattr(method, "__globals__", None)
    if global_vars is None:
        global_vars = vars(sys.modules[method.__module__])

    found = False
    for super_class in _get_base_classes(sys._getframe(3), global_vars):
        parent_method = getattr(super_class, method.__name__, None)
        if parent_method is None:
            continue
        found = True
        if not getattr(parent_method, "__allow_any_override__", False):
            return True

    if not found:
        raise TypeError(
            f"'{method.__qualname__}' does not override any method in its "
            f"base classes. Remove @override or check the method name."
        )

    return False


def allow_any_override(method: F) -> F:
    """Mark an abstract method as permitting override with any signature.

    Place this on base class methods where subclasses are expected to narrow
    the signature (e.g. ``**kwargs`` → specific parameters). Without this
    marker, ``@override`` would reject the signature change as an LSP
    violation.

    This is a marker only — it sets ``__allow_any_override__ = True`` on the
    method. The check is performed by the ``@override`` decorator in this
    module at class-creation time.

    Args:
        method: The abstract method to mark.

    Returns:
        The same method, with ``__allow_any_override__ = True`` set.

    Examples:
        Mark a base method::

            class Base(EnforceOverrides):
                @abstractmethod
                @allow_any_override
                def __call__(self, **kwargs) -> Any: ...

        Subclass freely narrows the signature::

            class Child(Base):
                @override
                def __call__(self, text: str, max_tokens: int = 512) -> str:
                    ...
    """
    method.__allow_any_override__ = True  # type: ignore[attr-defined]
    return method


def override(method: F) -> F:
    """Override decorator that respects ``@allow_any_override`` on parent methods.

    Drop-in replacement for ``@override`` from the ``overrides`` library.
    Behaviour:
    - If the parent method has ``@allow_any_override``: installs the override
      without signature validation.
    - Otherwise: delegates to vanilla ``_overrides`` with full signature
      checking.

    Resolution happens at class-body execution time via the ``overrides``
    library's ``_get_base_classes`` frame introspection.

    Args:
        method: The overriding method.

    Returns:
        The method, marked with ``__override__ = True``.

    Raises:
        TypeError: If ``method`` does not override any parent method.

    Examples:
        Narrowing a signature (allowed because parent has @allow_any_override)::

            class Summarizer(Quant):
                @override
                def __call__(self, text: str, max_tokens: int = 512) -> str:
                    ...

        Normal override with signature enforcement::

            class Summarizer(Quant):
                @override
                def dummy_inputs(self) -> list[dict[str, Any]]:
                    return [{"text": "hello"}]
    """
    method.__override__ = True  # type: ignore[attr-defined]
    if _should_enforce_signature(method):
        _overrides(method, check_signature=True, check_at_runtime=False)
    return method


__all__ = ["allow_any_override", "override", "final", "EnforceOverrides"]
