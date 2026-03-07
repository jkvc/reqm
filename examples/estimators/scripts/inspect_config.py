"""
inspect_config.py — Print the fully resolved config YAML for a given config name.

Useful for debugging and understanding what Hydra actually composes: see the
final resolved config with all defaults merged and interpolations resolved.

Usage:
    uv run python -m examples.estimators.scripts.inspect_config <config_name>

Examples:
    uv run python -m examples.estimators.scripts.inspect_config mean_simple
    uv run python -m examples.estimators.scripts.inspect_config ensemble/mean_median
"""

from __future__ import annotations

import sys

from examples.estimators import QM


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python -m examples.estimators.scripts.inspect_config <config_name>"
        )
        print("\nAvailable configs:")
        for name in QM.list_configs():
            print(f"  {name}")
        sys.exit(1)

    config_name = sys.argv[1]

    # --- Same QuantManager, different method: get_raw_config ---
    yaml_str = QM.get_raw_config(config_name)

    print(f"\n--- {config_name} (resolved) ---")
    print(yaml_str)


if __name__ == "__main__":
    main()
