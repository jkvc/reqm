"""
linear.py — Simple linear regression model.

Single linear layer, no activation. The simplest possible TorchQuant.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from examples.torch_models.models.api import Regressor
from reqm.overrides_ext import override


class LinearRegressor(Regressor):
    """Single-layer linear regression.

    Args:
        in_features: Number of input features.

    Examples:
        >>> model = LinearRegressor(in_features=3)
        >>> x = torch.randn(4, 3)
        >>> output = model(x=x)
        >>> output.shape
        torch.Size([4, 1])
    """

    def __init__(self, in_features: int):
        super().__init__()
        self.in_features = in_features
        self.linear = nn.Linear(in_features, 1)

    @override
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)
