"""
mean.py — Arithmetic mean estimator.

The simplest estimator. Sensitive to outliers unless paired with an
OutlierFilter or similar. Compare mean_simple vs mean_outlier configs
to see how the same class behaves differently with different Filters.
"""

from __future__ import annotations

import statistics

from examples.estimators.filters.api import Filter
from examples.estimators.quants.api import Estimator
from reqm.overrides_ext import override


class MeanEstimator(Estimator):
    """Computes the arithmetic mean after filtering.

    Args:
        filter: A Filter instance that preprocesses the data.
            Injected via Hydra config composition.

    Examples:
        >>> from examples.estimators.filters import NoFilter
        >>> est = MeanEstimator(filter=NoFilter())
        >>> est(data=[1.0, 2.0, 3.0])
        2.0
    """

    def __init__(self, filter: Filter):
        self.filter = filter

    @override
    def __call__(self, data: list[float]) -> float:
        filtered = self.filter(data)
        return statistics.mean(filtered) if filtered else 0.0
