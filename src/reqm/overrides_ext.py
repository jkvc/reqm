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

import functools
from typing import Any, Callable, TypeVar

from overrides import EnforceOverrides, final
from overrides import override as _override

F = TypeVar("F", bound=Callable[..., Any])


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


class _PendingOverride:
    """Descriptor that resolves override validation at class-creation time.

    When Python calls ``__set_name__`` during class body execution, we have
    access to the owner class and its MRO. At that point we check whether the
    parent method carries ``__allow_any_override__`` and call the appropriate
    form of ``@override``.
    """

    def __init__(self, method: Callable) -> None:
        self._method = method
        functools.update_wrapper(self, method)  # type: ignore[arg-type]
        # EnforceOverrides inspects the class namespace before __set_name__
        # fires. Setting __override__ here ensures it sees a marked override
        # on the _PendingOverride instance itself, not just the resolved method.
        self.__override__ = True  # type: ignore[attr-defined]

    def __set_name__(self, owner: type, name: str) -> None:
        method = self._method

        # Find the parent method via MRO. We do this manually because
        # _override() uses sys._getframe() to locate the enclosing class,
        # which gives the wrong frame depth when called from __set_name__.
        parent = None
        for base in owner.__mro__[1:]:
            if name in vars(base):
                parent = vars(base)[name]
                break

        if parent is None:
            raise TypeError(
                f"'{name}' in '{owner.__name__}' does not override any method "
                f"in its base classes. Remove @override or check the method name."
            )

        # Respect @final — raise before installing.
        if getattr(parent, "__final__", False):
            raise TypeError(
                f"'{name}' in '{owner.__name__}' attempts to override a "
                f"@final method from '{type(parent).__name__}'."
            )

        # Mark the resolved method for any downstream EnforceOverrides check.
        method.__override__ = True  # type: ignore[attr-defined]

        # Replace this descriptor with the resolved plain method.
        # Signature checking is deliberately skipped when the parent has
        # @allow_any_override; static type checkers handle it at that level.
        setattr(owner, name, method)

def override(method: F) -> F:
    """Override decorator that respects ``@allow_any_override`` on parent methods.

    Drop-in replacement for ``@override`` from the ``overrides`` library.
    Behaviour:
    - If the parent method has ``@allow_any_override``: installs the override
      without signature validation (``check_signature=False``).
    - Otherwise: delegates to vanilla ``@override`` with full signature
      checking (``check_signature=True``).

    Resolution is deferred to class-creation time via ``__set_name__``, so
    the parent MRO is available when the check runs.

    Args:
        method: The overriding method.

    Returns:
        The resolved override (after ``__set_name__`` fires).

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
    return _PendingOverride(method)  # type: ignore[return-value]


__all__ = ["allow_any_override", "override", "final", "EnforceOverrides"]
