"""
hello_world.py — simplest possible reqm end-to-end example.

Demonstrates:
- Defining a Quant by subclassing reqm.Quant
- Writing a YAML config (inline here as a temp file for self-containment)
- Registering an alias
- Retrieving and calling the Quant via reqm.get()

Run with::

    python -m reqm.examples.hello_world
"""

import tempfile
import textwrap
import os
import reqm
from reqm import Quant


# ---------------------------------------------------------------------------
# 1. Define your Quant — subclass Quant and implement __call__ + dummy_inputs
# ---------------------------------------------------------------------------

class Greeter(Quant):
    """A simple Quant that greets a name.

    Args:
        greeting: The greeting word to use, e.g. "Hello" or "Hi".
        punctuation: Punctuation to append, e.g. "!" or ".".

    Examples:
        >>> g = Greeter(greeting="Hello", punctuation="!")
        >>> g(name="world")
        'Hello, world!'
    """

    def __init__(self, greeting: str, punctuation: str = "!"):
        self.greeting = greeting
        self.punctuation = punctuation

    def dummy_inputs(self) -> dict:
        """Return example inputs. reqm calls this at build time as a sanity check."""
        return {"name": "world"}

    def __call__(self, name: str) -> str:
        """Greet the given name.

        Args:
            name: The name to greet.

        Returns:
            A greeting string.
        """
        return f"{self.greeting}, {name}{self.punctuation}"


# ---------------------------------------------------------------------------
# 2. Write a config file
#    In a real project this lives at e.g. conf/greeter/friendly.yaml
#    Here we write it to a temp file so the example is self-contained.
# ---------------------------------------------------------------------------

CONFIG_YAML = textwrap.dedent("""\
    _target_: reqm.examples.hello_world.Greeter
    greeting: Hello
    punctuation: "!"
""")


# ---------------------------------------------------------------------------
# 3. Register + retrieve + call
# ---------------------------------------------------------------------------

def main():
    # Write config to a temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(CONFIG_YAML)
        config_path = f.name

    try:
        # Register the alias
        reqm.register("greeter/friendly", config_path, Greeter)

        # Retrieve — this instantiates, validates interface, runs dummy_inputs
        greeter = reqm.get("greeter/friendly")

        # Call it
        result = greeter(name="world")
        print(result)  # Hello, world!

    finally:
        os.unlink(config_path)


if __name__ == "__main__":
    main()
