"""
median.py — Median estimator.

Naturally robust to outliers even without aggressive filtering, making it
a good baseline to compare against MeanEstimator.
"""

from __future__ import annotations

import statistics

from examples.estimators.filters.api import Filter
from examples.estimators.quants.api import Estimator
from reqm.overrides_ext import override


class MedianEstimator(Estimator):
    """Computes the median after filtering.

    Args:
        filter: A Filter instance that preprocesses the data.
            Injected via Hydra config composition.

    Examples:
        >>> from examples.estimators.filters import NoFilter
        >>> est = MedianEstimator(filter=NoFilter())
        >>> est(data=[1.0, 2.0, 100.0])
        2.0
    """

    def __init__(self, filter: Filter):
        self.filter = filter

    @override
    def __call__(self, data: list[float]) -> float:
        filtered = self.filter(data)
        return statistics.median(filtered) if filtered else 0.0
