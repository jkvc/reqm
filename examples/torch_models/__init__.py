# Torch models example project.
#
# Demonstrates:
# - TorchQuant: bridging nn.Module and Quant (override forward, not __call__)
# - Config-driven model instantiation via QuantManager
# - The same uniform call site pattern as the estimators example
#
# Structure:
#   torch_quant.py — TorchQuant base class (copy this into your own project)
#   models/        — Regressor base class + implementations (TorchQuant subclasses)
#   configs/       — YAML config module for QuantManager
#   scripts/       — Runnable scripts demonstrating the uniform call site pattern
#
# Requires: torch (not a reqm dependency — install it yourself)
#
# Run any script with:
#     uv run python -m examples.torch_models.scripts.evaluate linear_simple
#     uv run python -m examples.torch_models.scripts.evaluate mlp_small
#     uv run python -m examples.torch_models.scripts.evaluate mlp_large
#     uv run python -m examples.torch_models.scripts.audit

import examples.torch_models.configs as configs
from reqm import QuantManager

QM = QuantManager(configs)
