"""
api.py — Regressor base class (the TorchQuant interface for this example).

All Regressors share the same call signature:
``forward(x: torch.Tensor) -> torch.Tensor`` where x is (batch, features)
and output is (batch, 1).

The ``dummy_inputs`` method is defined here so subclasses only need to
implement ``forward()``.
"""

from __future__ import annotations

import torch

from examples.torch_models.torch_quant import TorchQuant
from reqm.overrides_ext import override


class Regressor(TorchQuant):
    """Abstract base for regression models.

    Every Regressor takes a 2D tensor ``x`` of shape ``(batch, in_features)``
    and returns a tensor of shape ``(batch, 1)``.

    Subclasses implement ``forward()`` with their specific architecture.
    The shared ``dummy_inputs`` ensures every subclass is auditable at
    build time.

    Examples:
        Subclass only needs ``forward()``::

            class MyRegressor(Regressor):
                def __init__(self, in_features: int):
                    super().__init__()
                    self.linear = nn.Linear(in_features, 1)

                @override
                def forward(self, x: torch.Tensor) -> torch.Tensor:
                    return self.linear(x)
    """

    # Subclasses must set this so dummy_inputs knows the input dimension.
    in_features: int

    @override
    def dummy_inputs(self) -> list[dict[str, object]]:
        return [
            {"x": torch.randn(4, self.in_features)},
            {"x": torch.randn(1, self.in_features)},
        ]
