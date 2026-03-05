"""
ensemble.py — Weighted ensemble of two Estimators.

Demonstrates Quant-depends-on-Quant composition: both ``primary`` and
``secondary`` are themselves Estimators built from their own configs.
The ensemble blends their outputs with a configurable weight ``alpha``.

Composed entirely in YAML via Hydra defaults lists — no Python wiring needed.
"""

from __future__ import annotations

from examples.estimators.quants.api import Estimator
from reqm.overrides_ext import override


class EnsembleEstimator(Estimator):
    """Weighted blend of two child Estimators.

    Prediction: ``alpha * primary(data) + (1 - alpha) * secondary(data)``

    Args:
        primary: The first Estimator (built from its own config).
        secondary: The second Estimator (built from its own config).
        alpha: Weight for the primary estimator. Default 0.5.

    Examples:
        >>> from examples.estimators.filters import NoFilter
        >>> from examples.estimators.quants.mean import MeanEstimator
        >>> from examples.estimators.quants.median import MedianEstimator
        >>> primary = MeanEstimator(filter=NoFilter())
        >>> secondary = MedianEstimator(filter=NoFilter())
        >>> ens = EnsembleEstimator(primary=primary, secondary=secondary, alpha=0.6)
        >>> ens(data=[1.0, 2.0, 3.0])
        2.0
    """

    def __init__(self, primary: Estimator, secondary: Estimator, alpha: float = 0.5):
        self.primary = primary
        self.secondary = secondary
        self.alpha = alpha

    @override
    def __call__(self, data: list[float]) -> float:
        p = self.primary(data=data)
        s = self.secondary(data=data)
        return self.alpha * p + (1 - self.alpha) * s
