"""
Tests for TorchQuant — the nn.Module + Quant bridge.

All tests in this file require PyTorch. They are skipped automatically
if torch is not installed (reqm does not depend on torch).
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
nn = torch.nn

# Import TorchQuant from examples (it's a recipe, not part of the package)
from examples.torch_models.torch_quant import TorchQuant  # noqa: E402

from reqm.overrides_ext import override  # noqa: E402
from reqm.quant import Quant  # noqa: E402

# ---------------------------------------------------------------------------
# TorchQuant is abstract — cannot be instantiated directly
# ---------------------------------------------------------------------------


def test_torch_quant_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        TorchQuant()


def test_torch_quant_subclass_without_forward_cannot_be_instantiated():
    class MissingForward(TorchQuant):
        @override
        def dummy_inputs(self) -> list[dict[str, object]]:
            return [{}]

    with pytest.raises(TypeError):
        MissingForward()


def test_torch_quant_subclass_without_dummy_inputs_cannot_be_instantiated():
    class MissingDummy(TorchQuant):
        @override
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x

    with pytest.raises(TypeError):
        MissingDummy()


# ---------------------------------------------------------------------------
# Minimal concrete TorchQuant for testing
# ---------------------------------------------------------------------------


class SimpleTorchQuant(TorchQuant):
    """Minimal TorchQuant: identity function."""

    def __init__(self):
        super().__init__()

    @override
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x

    @override
    def dummy_inputs(self) -> list[dict[str, object]]:
        return [{"x": torch.randn(2, 3)}]


class LinearTorchQuant(TorchQuant):
    """TorchQuant with a real nn.Linear layer."""

    def __init__(self, in_features: int):
        super().__init__()
        self.in_features = in_features
        self.linear = nn.Linear(in_features, 1)

    @override
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)

    @override
    def dummy_inputs(self) -> list[dict[str, object]]:
        return [
            {"x": torch.randn(4, self.in_features)},
            {"x": torch.randn(1, self.in_features)},
        ]


# ---------------------------------------------------------------------------
# Inheritance checks
# ---------------------------------------------------------------------------


def test_torch_quant_is_subclass_of_quant():
    assert issubclass(TorchQuant, Quant)


def test_torch_quant_is_subclass_of_nn_module():
    assert issubclass(TorchQuant, nn.Module)


def test_concrete_torch_quant_is_instance_of_quant():
    model = SimpleTorchQuant()
    assert isinstance(model, Quant)


def test_concrete_torch_quant_is_instance_of_nn_module():
    model = SimpleTorchQuant()
    assert isinstance(model, nn.Module)


def test_concrete_torch_quant_is_callable():
    model = SimpleTorchQuant()
    assert callable(model)


# ---------------------------------------------------------------------------
# __call__ delegates to nn.Module.__call__ (which calls forward)
# ---------------------------------------------------------------------------


def test_call_returns_forward_result():
    model = SimpleTorchQuant()
    x = torch.randn(2, 3)
    result = model(x=x)
    assert torch.equal(result, x)


def test_call_invokes_forward_not_direct_call():
    """Verify that __call__ goes through nn.Module's machinery (forward)."""
    forward_called = []

    class TrackingQuant(TorchQuant):
        def __init__(self):
            super().__init__()

        @override
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            forward_called.append(True)
            return x

        @override
        def dummy_inputs(self) -> list[dict[str, object]]:
            return [{"x": torch.randn(1)}]

    model = TrackingQuant()
    model(x=torch.randn(1))
    assert len(forward_called) == 1, "forward() should have been called once"


def test_nn_module_hooks_are_invoked():
    """Verify that nn.Module forward hooks run (not bypassed)."""
    hook_called = []

    def hook(module, input, output):
        hook_called.append(True)

    model = SimpleTorchQuant()
    model.register_forward_hook(hook)
    model(x=torch.randn(2, 3))
    assert len(hook_called) == 1, "Forward hook should have been called"


# ---------------------------------------------------------------------------
# Linear model with real parameters
# ---------------------------------------------------------------------------


def test_linear_torch_quant_has_parameters():
    model = LinearTorchQuant(in_features=4)
    params = list(model.parameters())
    assert len(params) > 0


def test_linear_torch_quant_output_shape():
    model = LinearTorchQuant(in_features=4)
    x = torch.randn(8, 4)
    output = model(x=x)
    assert output.shape == (8, 1)


def test_linear_torch_quant_gradients_flow():
    model = LinearTorchQuant(in_features=4)
    x = torch.randn(8, 4)
    output = model(x=x)
    loss = output.sum()
    loss.backward()
    for p in model.parameters():
        assert p.grad is not None, "Gradients should flow through the model"


# ---------------------------------------------------------------------------
# dummy_inputs contract
# ---------------------------------------------------------------------------


def test_dummy_inputs_returns_list_of_dicts():
    model = LinearTorchQuant(in_features=3)
    inputs = model.dummy_inputs()
    assert isinstance(inputs, list)
    for item in inputs:
        assert isinstance(item, dict)


def test_dummy_inputs_expandable_into_call():
    """Each dummy input must be **-expandable into __call__."""
    model = LinearTorchQuant(in_features=3)
    for inputs in model.dummy_inputs():
        result = model(**inputs)
        assert isinstance(result, torch.Tensor)


def test_dummy_inputs_produce_correct_output_shape():
    model = LinearTorchQuant(in_features=5)
    for inputs in model.dummy_inputs():
        result = model(**inputs)
        assert result.shape[-1] == 1


# ---------------------------------------------------------------------------
# MRO: nn.Module.__call__ satisfies Quant's abstract __call__
# but forward() is still required
# ---------------------------------------------------------------------------


def test_mro_requires_forward_even_though_call_is_satisfied():
    """nn.Module.__call__ satisfies the ABC, but forward() is still abstract."""
    with pytest.raises(TypeError):
        # This should fail because forward is abstract on TorchQuant
        class NoForward(TorchQuant):
            @override
            def dummy_inputs(self) -> list[dict[str, object]]:
                return [{}]

        NoForward()


# ---------------------------------------------------------------------------
# state_dict / load_state_dict (nn.Module integration)
# ---------------------------------------------------------------------------


def test_state_dict_round_trip():
    model = LinearTorchQuant(in_features=4)
    state = model.state_dict()
    assert "linear.weight" in state
    assert "linear.bias" in state

    # Load into a new model
    model2 = LinearTorchQuant(in_features=4)
    model2.load_state_dict(state)

    x = torch.randn(2, 4)
    with torch.no_grad():
        assert torch.equal(model(x=x), model2(x=x))


# ---------------------------------------------------------------------------
# QuantManager integration (build from config)
# ---------------------------------------------------------------------------


def test_build_linear_from_config():
    from examples.torch_models import QM

    model = QM.build("linear_simple")
    assert isinstance(model, nn.Module)
    assert isinstance(model, Quant)

    x = torch.randn(4, 4)
    with torch.no_grad():
        output = model(x=x)
    assert output.shape == (4, 1)


def test_build_mlp_from_config():
    from examples.torch_models import QM

    model = QM.build("mlp_small")
    assert isinstance(model, nn.Module)

    x = torch.randn(4, 4)
    with torch.no_grad():
        output = model(x=x)
    assert output.shape == (4, 1)


def test_build_all_configs_and_audit():
    """Build every config, run dummy_inputs — the full audit pattern."""
    from examples.torch_models import QM

    for name in QM.list_configs():
        model = QM.build(name)
        with torch.no_grad():
            for inputs in model.dummy_inputs():
                output = model(**inputs)
                assert isinstance(output, torch.Tensor)
