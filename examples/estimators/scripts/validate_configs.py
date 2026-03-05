"""
validate_configs.py — Validate all configs and list available estimators.

Run this in CI or before experiments to catch config errors early:
missing ``# @package _global_`` headers, broken references, etc.

Usage:
    uv run python -m examples.estimators.scripts.validate_configs
"""

from __future__ import annotations

import examples.estimators.configs as configs
from reqm import QuantManager
from reqm.quant_manager import ConfigValidationError


def main() -> None:
    QM = QuantManager(configs)

    all_configs = QM.list_configs()
    print(f"Found {len(all_configs)} configs:\n")
    for name in all_configs:
        print(f"  {name}")

    # --- Validate every config has # @package _global_ ---
    print("\nValidating...")
    try:
        QM.validate()
        print(f"All {len(all_configs)} configs passed validation.")
    except ConfigValidationError as e:
        print(f"VALIDATION FAILED: {e}")
        raise SystemExit(1) from None

    # --- List estimator configs (exclude filter-only configs) ---
    estimator_configs = [n for n in all_configs if not n.startswith("filters/")]
    print(f"\nEstimator configs ({len(estimator_configs)}):")
    for name in estimator_configs:
        print(f"  {name}")

    filter_configs = [n for n in all_configs if n.startswith("filters/")]
    print(f"\nFilter configs ({len(filter_configs)}):")
    for name in filter_configs:
        print(f"  {name}")


if __name__ == "__main__":
    main()
