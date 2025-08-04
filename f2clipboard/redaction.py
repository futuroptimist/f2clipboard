"""Utilities for scanning and redacting secrets from text."""

from __future__ import annotations

import re

# Regular expressions for common secret formats
_PATTERNS: list[re.Pattern[str]] = [
    # GitHub personal access tokens, e.g. ghp_xxx...
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36}"),
    # AWS access key IDs
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


def redact_secrets(text: str) -> str:
    """Replace known secret patterns with ``[REDACTED]``.

    The function performs simple pattern matching to remove credentials from
    logs before they are printed or sent to an LLM.
    """

    for pattern in _PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text
