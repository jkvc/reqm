"""
outlier.py — Z-score outlier filter.

Removes values more than ``std_threshold`` standard deviations from the mean.
This is the classic z-score outlier removal. The ``std_threshold`` hyperparameter
controls how aggressive the filtering is: lower values remove more points.
"""

from __future__ import annotations

import statistics

from examples.estimators.filters.api import Filter


class OutlierFilter(Filter):
    """Drops data points beyond ``std_threshold`` standard deviations from the mean.

    Args:
        std_threshold: Number of standard deviations beyond which a data
            point is considered an outlier. Default 2.0.

    Examples:
        >>> f = OutlierFilter(std_threshold=2.0)
        >>> f([1.0, 2.0, 3.0, 100.0])  # 100.0 is removed
        [1.0, 2.0, 3.0]
    """

    def __init__(self, std_threshold: float = 2.0):
        self.std_threshold = std_threshold

    def __call__(self, data: list[float]) -> list[float]:
        if len(data) < 2:
            return data
        mean = statistics.mean(data)
        stdev = statistics.pstdev(data)
        if stdev == 0:
            return data
        return [x for x in data if abs(x - mean) <= self.std_threshold * stdev]
