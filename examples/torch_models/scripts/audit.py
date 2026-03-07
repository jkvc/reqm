"""
audit.py — Build every model and run dummy_inputs to verify they work.

This is the auditability pattern: reqm can verify every model actually
runs at build time, not silently at inference. This script exercises
that pattern for all configs.

Usage:
    uv run python -m examples.torch_models.scripts.audit
"""

from __future__ import annotations

import torch

from examples.torch_models import QM


def main() -> None:
    all_configs = QM.list_configs()
    print(f"Auditing {len(all_configs)} model configs...\n")

    for name in all_configs:
        model = QM.build(name)

        # Run every dummy input through the model
        with torch.no_grad():
            for i, inputs in enumerate(model.dummy_inputs()):
                model(**inputs)

        param_count = sum(p.numel() for p in model.parameters())
        print(
            f"  {name:<20s}  {model.__class__.__name__:<20s}  "
            f"{param_count:>6,} params  "
            f"{len(model.dummy_inputs())} dummy inputs OK"
        )

    print(f"\nAll {len(all_configs)} models passed audit.")


if __name__ == "__main__":
    main()
