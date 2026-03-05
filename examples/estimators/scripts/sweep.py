"""
sweep.py — Run ALL estimator configs and rank them by performance.

This is the ablation study workflow: add a new YAML config, re-run sweep,
see where it ranks. No code changes needed — just drop a new config file
into the configs/ directory and run this script again.

Usage:
    uv run python -m examples.estimators.scripts.sweep
"""

from __future__ import annotations

import examples.estimators.configs as configs
from examples.estimators.datasets import DATASETS
from reqm import QuantManager


def compute_mse(estimator: object, datasets: list[dict]) -> float:
    errors = []
    for sample in datasets:
        pred = estimator(data=sample["data"])
        errors.append((pred - sample["truth"]) ** 2)
    return sum(errors) / len(errors)


def main() -> None:
    QM = QuantManager(configs)

    # Auto-discover all estimator configs (exclude filter-only configs)
    estimator_configs = [
        name for name in QM.list_configs() if not name.startswith("filters/")
    ]

    print(f"Sweeping {len(estimator_configs)} estimator configs...\n")

    # --- Build and evaluate each config ---
    results: list[tuple[str, float]] = []
    for name in estimator_configs:
        estimator = QM.build(name)
        mse = compute_mse(estimator, DATASETS)
        results.append((name, mse))

    # --- Rank by MSE (best first) ---
    results.sort(key=lambda r: r[1])

    max_name_len = max(len(name) for name, _ in results)
    header = f"{'rank':>4s}  {'config':<{max_name_len}s}  {'MSE':>10s}"
    print(header)
    print("-" * len(header))
    for rank, (name, mse) in enumerate(results, 1):
        print(f"{rank:4d}  {name:<{max_name_len}s}  {mse:10.4f}")


if __name__ == "__main__":
    main()
