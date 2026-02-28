"""
r2p.py — Research-to-Production (R2P) pattern with reqm.

Demonstrates:
- Registering multiple aliases for the same interface
- Swapping implementations by changing only the alias string
- The call site never changes across prod / fast / experiment variants

This is the core value proposition of reqm: iterate freely in config space,
ship without touching call sites.

Run with::

    python -m reqm.examples.r2p
"""

import tempfile
import textwrap
import os
import reqm
from reqm import Quant
from reqm.overrides_ext import override


# ---------------------------------------------------------------------------
# 1. Define the interface — one ABC, many implementations
# ---------------------------------------------------------------------------

class Summarizer(Quant):
    """Abstract summarizer interface. All variants must implement this.

    Examples:
        >>> # Don't instantiate Summarizer directly — use a concrete subclass
        >>> # or reqm.get("summarizer/prod")
    """

    @override
    def dummy_inputs(self) -> dict:
        return {"text": "The quick brown fox jumps over the lazy dog."}

    @override
    def __call__(self, text: str) -> str:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 2. Concrete implementations — in a real project these live in separate files
# ---------------------------------------------------------------------------

class VerboseSummarizer(Summarizer):
    """Summarizes by adding a verbose prefix. Stands in for a large model.

    Args:
        prefix: Text to prepend to the summary.

    Examples:
        >>> s = VerboseSummarizer(prefix="[VERBOSE]")
        >>> s(text="short text")
        '[VERBOSE] short text'
    """

    def __init__(self, prefix: str):
        self.prefix = prefix

    @override
    def __call__(self, text: str) -> str:
        return f"{self.prefix} {text}"


class FastSummarizer(Summarizer):
    """Summarizes by truncating. Stands in for a cheap/fast model.

    Args:
        max_words: Maximum number of words to keep.

    Examples:
        >>> s = FastSummarizer(max_words=3)
        >>> s(text="one two three four five")
        'one two three...'
    """

    def __init__(self, max_words: int):
        self.max_words = max_words

    @override
    def __call__(self, text: str) -> str:
        words = text.split()
        if len(words) <= self.max_words:
            return text
        return " ".join(words[: self.max_words]) + "..."


# ---------------------------------------------------------------------------
# 3. Configs — in a real project these are YAML files in conf/
# ---------------------------------------------------------------------------

CONFIGS = {
    "summarizer/prod": textwrap.dedent("""\
        _target_: reqm.examples.r2p.VerboseSummarizer
        prefix: "[PROD]"
    """),
    "summarizer/fast": textwrap.dedent("""\
        _target_: reqm.examples.r2p.FastSummarizer
        max_words: 5
    """),
    "summarizer/experiment_v3": textwrap.dedent("""\
        _target_: reqm.examples.r2p.VerboseSummarizer
        prefix: "[EXP-V3]"
    """),
}


# ---------------------------------------------------------------------------
# 4. Register all aliases, then swap freely — call site never changes
# ---------------------------------------------------------------------------

def main():
    tmp_files = []

    try:
        # Write configs to temp files and register
        for alias, yaml_content in CONFIGS.items():
            f = tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            )
            f.write(yaml_content)
            f.close()
            tmp_files.append(f.name)
            reqm.register(alias, f.name, Summarizer)

        text = "The quick brown fox jumps over the lazy dog."

        # --- This is the R2P pattern ---
        # The call site is identical. Only the alias string changes.
        for alias in ["summarizer/prod", "summarizer/fast", "summarizer/experiment_v3"]:
            model = reqm.get(alias)
            result = model(text=text)
            print(f"{alias:35s} → {result}")

    finally:
        for path in tmp_files:
            os.unlink(path)


if __name__ == "__main__":
    main()
