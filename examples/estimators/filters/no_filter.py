"""
no_filter.py — Passthrough filter that returns data unchanged.

Use this as the default when you want to see raw, unfiltered behavior.
Pairs with any Estimator to establish the unfiltered baseline.
"""

from __future__ import annotations

from examples.estimators.filters.api import Filter


class NoFilter(Filter):
    """Returns data exactly as received — no filtering applied.

    Examples:
        >>> NoFilter()([1.0, 100.0, 2.0])
        [1.0, 100.0, 2.0]
    """

    def __call__(self, data: list[float]) -> list[float]:
        return data
