"""
evaluate.py — Run an estimator over synthetic datasets and compute MSE.

This is the core demo of the reqm pattern: ONE script, ONE call site.
Swap the config name on the command line and get different experimental
results — no code changes, no if/else chains, no factory functions.

Usage:
    uv run python -m examples.estimators.scripts.evaluate <config_name>

Examples:
    uv run python -m examples.estimators.scripts.evaluate mean_simple
    uv run python -m examples.estimators.scripts.evaluate mean_outlier
    uv run python -m examples.estimators.scripts.evaluate median_simple
    uv run python -m examples.estimators.scripts.evaluate trimmed_mean
    uv run python -m examples.estimators.scripts.evaluate ensemble/mean_median
"""

from __future__ import annotations

import sys

import examples.estimators.configs as configs
from examples.estimators.datasets import DATASETS
from reqm import QuantManager


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m examples.estimators.scripts.evaluate <config_name>")
        print("\nAvailable configs:")
        QM = QuantManager(configs)
        for name in QM.list_configs():
            if not name.startswith("filters/"):
                print(f"  {name}")
        sys.exit(1)

    config_name = sys.argv[1]

    # --- The uniform call site: build any estimator from config ---
    QM = QuantManager(configs)
    estimator = QM.build(config_name)

    # --- Run over every dataset and collect errors ---
    print(f"\nConfig: {config_name}")
    print(f"{'truth':>8s}  {'pred':>8s}  {'error':>10s}")
    print("-" * 30)

    squared_errors: list[float] = []
    for sample in DATASETS:
        pred = estimator(data=sample["data"])
        err = (pred - sample["truth"]) ** 2
        squared_errors.append(err)
        print(f"{sample['truth']:8.2f}  {pred:8.2f}  {err:10.4f}")

    mse = sum(squared_errors) / len(squared_errors)
    print("-" * 30)
    print(f"{'MSE':>20s}: {mse:.4f}")


if __name__ == "__main__":
    main()
