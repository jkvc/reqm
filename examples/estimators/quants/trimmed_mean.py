"""
trimmed_mean.py — Trimmed mean estimator.

Drops the top and bottom ``trim_pct`` fraction of values, then averages
what remains. A middle ground between mean (outlier-sensitive) and median
(ignores magnitude). The ``trim_pct`` hyperparameter controls how much of
each tail is discarded.
"""

from __future__ import annotations

import statistics

from examples.estimators.filters.api import Filter
from examples.estimators.quants.api import Estimator
from reqm.overrides_ext import override


class TrimmedMeanEstimator(Estimator):
    """Computes a trimmed mean after filtering.

    Args:
        filter: A Filter instance that preprocesses the data.
        trim_pct: Fraction of values to trim from each end.
            0.2 means drop the bottom 20% and top 20%. Default 0.1.

    Examples:
        >>> from examples.estimators.filters import NoFilter
        >>> est = TrimmedMeanEstimator(filter=NoFilter(), trim_pct=0.2)
        >>> est(data=[1.0, 2.0, 3.0, 4.0, 100.0])
        3.0
    """

    def __init__(self, filter: Filter, trim_pct: float = 0.1):
        self.filter = filter
        self.trim_pct = trim_pct

    @override
    def __call__(self, data: list[float]) -> float:
        filtered = self.filter(data)
        if not filtered:
            return 0.0
        sorted_data = sorted(filtered)
        n = len(sorted_data)
        trim_count = int(n * self.trim_pct)
        if trim_count > 0:
            trimmed = sorted_data[trim_count : n - trim_count]
        else:
            trimmed = sorted_data
        return statistics.mean(trimmed) if trimmed else statistics.mean(sorted_data)
