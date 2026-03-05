# Estimator example project.
#
# Demonstrates:
# - Defining a Quant interface (Estimator) with multiple implementations
# - Non-Quant configurable dependencies (Filter) composed via Hydra defaults
# - A uniform call site pattern where only the config name changes
#
# Structure:
#   filters/    — Filter base class + implementations (non-Quant dependencies)
#   quants/     — Estimator base class + implementations (Quant subclasses)
#   configs/    — YAML config module for QuantManager
#   scripts/    — Runnable scripts demonstrating the uniform call site pattern
#
# Run any script with:
#     uv run python -m examples.estimators.scripts.evaluate mean_simple
#     uv run python -m examples.estimators.scripts.inspect_config ensemble/mean_median
#     uv run python -m examples.estimators.scripts.compare \
#         mean_simple mean_outlier median_simple
#     uv run python -m examples.estimators.scripts.validate_configs
#     uv run python -m examples.estimators.scripts.sweep
