"""
mlp.py — Multi-layer perceptron regression model.

Demonstrates a TorchQuant with configurable architecture: hidden dimension
and number of layers are constructor args defined in YAML config.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from examples.torch_models.models.api import Regressor
from reqm.overrides_ext import override


class MLPRegressor(Regressor):
    """Multi-layer perceptron for regression.

    Args:
        in_features: Number of input features.
        hidden_dim: Width of hidden layers.
        num_layers: Number of hidden layers (must be >= 1).

    Examples:
        >>> model = MLPRegressor(in_features=3, hidden_dim=16, num_layers=2)
        >>> x = torch.randn(4, 3)
        >>> output = model(x=x)
        >>> output.shape
        torch.Size([4, 1])
    """

    def __init__(self, in_features: int, hidden_dim: int, num_layers: int = 1):
        super().__init__()
        self.in_features = in_features

        layers: list[nn.Module] = []
        prev_dim = in_features
        for _ in range(num_layers):
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))

        self.net = nn.Sequential(*layers)

    @override
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
