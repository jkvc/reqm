"""
api.py — Filter base class (the non-Quant dependency interface).

A Filter takes a list of floats and returns a (possibly shorter) filtered
list. Estimators use a Filter to preprocess raw data before computing
their estimate.

This is intentionally NOT a Quant — it exists to show that reqm configs
can compose any object, not just Quants. Each concrete Filter is defined
in its own YAML config and injected into an Estimator config via a
Hydra defaults list.
"""

from __future__ import annotations


class Filter:
    """Base class for data filters.

    Subclasses implement ``__call__`` to transform a list of floats.
    Estimators receive a Filter via constructor injection — the specific
    Filter class and its hyperparameters are determined entirely by config.

    Examples:
        >>> from examples.estimators.filters import NoFilter
        >>> f = NoFilter()
        >>> f([1.0, 2.0, 3.0])
        [1.0, 2.0, 3.0]
    """

    def __call__(self, data: list[float]) -> list[float]:
        raise NotImplementedError
