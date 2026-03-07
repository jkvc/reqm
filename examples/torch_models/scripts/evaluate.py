"""
evaluate.py — Build a model from config and run it on synthetic data.

Demonstrates the uniform call site: swap the config name, get a different
model architecture. No code changes needed.

Usage:
    uv run python -m examples.torch_models.scripts.evaluate <config_name>

Examples:
    uv run python -m examples.torch_models.scripts.evaluate linear_simple
    uv run python -m examples.torch_models.scripts.evaluate mlp_small
    uv run python -m examples.torch_models.scripts.evaluate mlp_large
"""

from __future__ import annotations

import sys

import torch

from examples.torch_models import QM


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m examples.torch_models.scripts.evaluate <config_name>")
        print("\nAvailable configs:")
        for name in QM.list_configs():
            print(f"  {name}")
        sys.exit(1)

    config_name = sys.argv[1]

    # --- The uniform call site: build any model from config ---
    model = QM.build(config_name)

    # --- Run on synthetic data ---
    print(f"\nConfig: {config_name}")
    print(f"Model: {model.__class__.__name__}")
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")

    x = torch.randn(8, 4)
    with torch.no_grad():
        output = model(x=x)

    print(f"\nInput shape:  {list(x.shape)}")
    print(f"Output shape: {list(output.shape)}")
    print(f"Output mean:  {output.mean().item():.4f}")
    print(f"Output std:   {output.std().item():.4f}")


if __name__ == "__main__":
    main()
