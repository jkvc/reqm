"""
quant.py — The Quant abstract base class.

A Quant is the unit reqm builds and manages: a callable with constructor args
defined in config, and a dummy_inputs method that makes it auditable.
"""

from abc import abstractmethod
from typing import Any

from reqm.overrides_ext import EnforceOverrides, allow_any_override


class Quant(EnforceOverrides):
    """Abstract base class for all reqm Quants.

    A Quant is a callable unit managed by reqm. It is:

    - **Callable** — invoked directly with its inputs via ``__call__``
    - **Config-driven** — constructor arguments defined in YAML, not hardcoded
    - **Auditable** — ``dummy_inputs()`` provides example inputs that reqm uses
      to verify the Quant actually runs at build time, not silently at inference

    Subclasses must implement:

    - ``__call__(**kwargs)`` — narrowed to the specific input signature
    - ``dummy_inputs()`` — returns a list of input dicts, each ``**``-expandable
      into ``__call__``

    Examples:
        Define a Quant::

            from reqm import Quant
            from reqm.overrides_ext import override

            class Summarizer(Quant):
                def __init__(self, model_name: str, max_tokens: int):
                    self.model = load_model(model_name)
                    self.max_tokens = max_tokens

                @override
                def __call__(self, text: str) -> str:
                    return self.model.summarize(text, max_tokens=self.max_tokens)

                @override
                def dummy_inputs(self) -> list[dict[str, Any]]:
                    return [
                        {"text": "The quick brown fox."},
                        {"text": "Short."},
                    ]

        reqm calls ``dummy_inputs`` at build time::

            for inputs in quant.dummy_inputs():
                quant(**inputs)  # fails fast here if something is broken
    """

    @abstractmethod
    @allow_any_override
    def __call__(self, **kwargs) -> Any:
        """Call the Quant with the given inputs.

        Subclasses must override this with their specific input signature.
        The base signature is ``**kwargs`` to allow any narrowing — see
        ``allow_any_override`` for why this is intentional.

        Args:
            **kwargs: Inputs to the Quant. The actual parameters are defined
                by the subclass.

        Returns:
            The Quant's output. Type is defined by the subclass.

        Examples:
            Subclass narrowing the signature::

                class Greeter(Quant):
                    @override
                    def __call__(self, name: str) -> str:
                        return f"Hello, {name}!"

            Calling the Quant::

                greeter = reqm.get("greeter/friendly")
                result = greeter(name="world")
        """
        ...

    @abstractmethod
    def dummy_inputs(self) -> list[dict[str, Any]]:
        """Return a list of example input dicts for build-time sanity checking.

        Each dict maps argument names to example values. reqm ``**``-expands
        each dict into ``__call__`` when building the Quant. If any call fails,
        the error is raised immediately with context — fail fast, not in prod.

        Multiple dicts are encouraged: cover the happy path and edge cases.
        These also serve as living documentation of valid call signatures.

        Returns:
            A non-empty list of dicts, each ``**``-expandable into ``__call__``.

        Raises:
            NotImplementedError: If not implemented by the subclass.

        Examples:
            Single input set::

                def dummy_inputs(self) -> list[dict[str, Any]]:
                    return [{"text": "The quick brown fox."}]

            Multiple input sets (recommended — covers more call patterns)::

                def dummy_inputs(self) -> list[dict[str, Any]]:
                    return [
                        {"text": "Short text."},
                        {"text": "A longer piece of text to summarize properly."},
                        {"text": "Edge case: single word."},
                    ]
        """
        ...
