"""Dummy objects for QuantManager build/instantiation tests.

These classes are referenced by ``_target_`` in the YAML configs under
``tests/test_config_module_one/``.
"""


class SimpleObject:
    """Trivial class instantiated by atomic configs."""

    def __init__(self, value: int, label: str = "default"):
        self.value = value
        self.label = label


class ComposedObject:
    """Class whose constructor takes a nested object built from another config."""

    def __init__(self, name: str, child: object):
        self.name = name
        self.child = child


class MultiDepObject:
    """Class whose constructor takes multiple nested objects."""

    def __init__(self, tag: str, first: object, second: object):
        self.tag = tag
        self.first = first
        self.second = second
