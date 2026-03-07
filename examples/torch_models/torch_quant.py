"""
torch_quant.py — TorchQuant bridge between nn.Module and Quant.

This module solves the __call__ ownership conflict:
- nn.Module.__call__ runs hooks, autograd profiling, then calls forward()
- Quant.__call__ is the abstract method subclasses must implement

TorchQuant bridges the two: it satisfies Quant's __call__ contract by
delegating to nn.Module.__call__ (which calls forward()), and makes
forward() the abstract method subclasses override instead.

Copy this into your own project — reqm intentionally does not depend on
PyTorch, so TorchQuant lives in examples, not in the reqm package.
"""

from __future__ import annotations

import abc

import torch.nn as nn

from reqm import Quant
from reqm.overrides_ext import allow_any_override, override


class TorchQuant(nn.Module, Quant):
    """Base class for Quants that are also PyTorch modules.

    Inherits from both ``nn.Module`` and ``Quant``. Subclasses override
    ``forward()`` (not ``__call__``) to define their computation, just
    like any nn.Module. The ``dummy_inputs()`` contract from Quant still
    applies — implement it so reqm can verify the model runs at build time.

    Why this class exists:
        ``nn.Module.__call__`` is a concrete method that runs forward/backward
        hooks, autograd profiling, and then calls ``self.forward()``. If you
        override ``__call__`` directly (as plain Quant requires), you bypass
        all of that machinery. TorchQuant resolves this by:

        1. Providing a concrete ``__call__`` that delegates to
           ``nn.Module.__call__`` (preserving hooks)
        2. Making ``forward()`` the abstract method with ``@allow_any_override``
           so subclasses can narrow its signature freely

    Usage:
        Subclass TorchQuant, implement ``forward()`` and ``dummy_inputs()``::

            class MyModel(TorchQuant):
                def __init__(self, hidden_dim: int):
                    super().__init__()
                    self.linear = nn.Linear(hidden_dim, 1)

                @override
                def forward(self, x: torch.Tensor) -> torch.Tensor:
                    return self.linear(x)

                @override
                def dummy_inputs(self) -> list[dict[str, object]]:
                    return [{"x": torch.randn(4, hidden_dim)}]

    Examples:
        Build a TorchQuant from config::

            from examples.torch_models import QM
            model = QM.build("linear_simple")
            for inputs in model.dummy_inputs():
                output = model(**inputs)
    """

    @override
    def __call__(self, **kwargs: object) -> object:
        """Delegate to nn.Module.__call__, which runs hooks then forward().

        This satisfies Quant's abstract __call__ contract while preserving
        PyTorch's hook machinery. Users should NOT override this — override
        forward() instead.
        """
        return nn.Module.__call__(self, **kwargs)

    @override
    @abc.abstractmethod
    @allow_any_override
    def forward(self, **kwargs: object) -> object:
        """Define the model's computation.

        Subclasses override this with their specific input signature,
        just like any nn.Module. The ``@allow_any_override`` marker
        permits signature narrowing (e.g. ``forward(self, x: Tensor)``).

        Args:
            **kwargs: Model inputs. Subclasses narrow this signature.

        Returns:
            Model output. Type defined by the subclass.
        """
        ...
