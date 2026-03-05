"""
datasets.py — Synthetic evaluation datasets for estimator experiments.

Each dataset is a dict with:
- ``data``: a list of floats (the raw observations, possibly with outliers)
- ``truth``: the known ground truth center value

Scripts import DATASETS from here so the evaluation data is defined once
and shared across evaluate, compare, and sweep.
"""

from __future__ import annotations

DATASETS: list[dict] = [
    # Clean data, no outliers — every estimator should do well here
    {"data": [10.0, 10.1, 9.9, 10.2, 9.8], "truth": 10.0},
    # Two extreme outliers contaminating otherwise clean data around 5.0
    {"data": [5.0, 5.1, 4.9, 5.2, 4.8, 100.0, -80.0], "truth": 5.0},
    # One-sided outlier pulling the mean upward from the true center of 3.0
    {"data": [3.0, 3.1, 2.9, 3.2, 2.8, 50.0], "truth": 3.0},
    # Symmetric outliers on both sides of the true center of 20.0
    {"data": [20.0, 19.5, 20.5, 19.8, 20.2, -100.0, 150.0], "truth": 20.0},
    # Perfectly uniform data — all estimators should return exactly 1.0
    {"data": [1.0, 1.0, 1.0, 1.0, 1.0], "truth": 1.0},
]
