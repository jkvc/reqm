"""
api.py — Estimator base class (the Quant interface for this example).

All Estimators share the same call signature: ``__call__(data: list[float]) -> float``.
This uniformity is the whole point — any Estimator can be swapped for any other
by changing the config name, and every script that calls an Estimator works
unchanged.

The ``dummy_inputs`` method is defined here so subclasses only need to
implement ``__call__``.
"""

from __future__ import annotations

from reqm import Quant
from reqm.overrides_ext import override


class Estimator(Quant):
    """Abstract base for numerical estimators.

    Every Estimator takes ``data: list[float]`` and returns a single ``float``.
    Subclasses implement ``__call__`` with their specific estimation logic.

    The shared ``dummy_inputs`` ensures every subclass is auditable at build
    time — reqm can call it to verify the Estimator actually runs.

    Examples:
        Subclass only needs ``__call__``::

            class MyEstimator(Estimator):
                @override
                def __call__(self, data: list[float]) -> float:
                    return sum(data) / len(data)
    """

    @override
    def dummy_inputs(self) -> list[dict[str, object]]:
        return [
            {"data": [1.0, 2.0, 3.0, 4.0, 5.0]},
            {"data": [10.0, 20.0, 100.0, 15.0, 12.0]},
        ]
