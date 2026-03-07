"""
compare.py — Run multiple estimator configs side by side on the same datasets.

Prints a comparison table so you can see at a glance how different configs
perform. This is the ablation study pattern: same data, different algorithms.

Usage:
    uv run python -m examples.estimators.scripts.compare \\
        <config1> <config2> [config3 ...]

Examples:
    uv run python -m examples.estimators.scripts.compare \\
        mean_simple mean_outlier median_simple
    uv run python -m examples.estimators.scripts.compare \\
        mean_simple trimmed_mean ensemble/mean_median
"""

from __future__ import annotations

import sys

from examples.estimators import QM
from examples.estimators.datasets import DATASETS


def compute_mse(estimator: object, datasets: list[dict]) -> float:
    errors = []
    for sample in datasets:
        pred = estimator(data=sample["data"])
        errors.append((pred - sample["truth"]) ** 2)
    return sum(errors) / len(errors)


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: python -m examples.estimators.scripts.compare"
            " <config1> <config2> [...]"
        )
        print("\nAvailable configs:")
        for name in QM.list_configs():
            if not name.startswith("filters/"):
                print(f"  {name}")
        sys.exit(1)

    config_names = sys.argv[1:]

    # --- Build all estimators from their configs ---
    results: list[tuple[str, float]] = []
    for name in config_names:
        estimator = QM.build(name)
        mse = compute_mse(estimator, DATASETS)
        results.append((name, mse))

    # --- Print comparison table, sorted by MSE (best first) ---
    results.sort(key=lambda r: r[1])

    max_name_len = max(len(name) for name, _ in results)
    header = f"{'config':<{max_name_len}s}  {'MSE':>10s}"
    print(f"\n{header}")
    print("-" * len(header))
    for name, mse in results:
        print(f"{name:<{max_name_len}s}  {mse:10.4f}")


if __name__ == "__main__":
    main()
