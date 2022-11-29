"""Home to all functions that are useful throughout the whole package."""

from typing import Iterable


def escape_characters(text: str, escape_characters: Iterable) -> str:
    """Escapes specific characters in a given text.

    Args:
        text: The text to escape.
        escape_characters: An iterable containing the characters that
        have to be escaped.
    """
    escape_characters_set = set(escape_characters)
    return "".join((f"\\{c}" if c in escape_characters_set else c for c in text))
