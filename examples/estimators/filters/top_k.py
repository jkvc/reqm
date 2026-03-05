"""
top_k.py — Top-K filter.

Keeps only the ``k`` largest values, discarding the rest. Useful when you
only care about the high end of a distribution. The ``k`` hyperparameter
controls how many values survive.
"""

from __future__ import annotations

from examples.estimators.filters.api import Filter


class TopKFilter(Filter):
    """Keeps the ``k`` largest values from the input data.

    Args:
        k: Number of top values to keep. Default 5.

    Examples:
        >>> f = TopKFilter(k=3)
        >>> f([1.0, 5.0, 3.0, 4.0, 2.0])
        [5.0, 4.0, 3.0]
    """

    def __init__(self, k: int = 5):
        self.k = k

    def __call__(self, data: list[float]) -> list[float]:
        return sorted(data, reverse=True)[: self.k]
