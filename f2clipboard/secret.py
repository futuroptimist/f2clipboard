"""Utilities for scanning and redacting secrets from text."""

from __future__ import annotations

import re
from typing import Pattern

SECRET_PATTERNS: list[Pattern[str]] = [
    # GitHub tokens: ghp_ (classic), gho_ (OAuth), ghu_ (user-to-server),
    # ghs_ (SAML), and ghr_ (refresh tokens)
    re.compile(r"gh[oprsu]_[A-Za-z0-9]{36}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{22,}"),
    # OpenAI, Slack, AWS and Bearer tokens
    re.compile(r"sk-[A-Za-z0-9]{32,}"),
    re.compile(r"xox[a-zA-Z]-[A-Za-z0-9-]{10,}"),
    re.compile(r"(?:ASIA|AKIA)[0-9A-Z]{16}"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._-]{8,}"),
    re.compile(
        r"(?i)(?P<key>[\w-]*(?:api|token|secret|password)[\w-]*)"
        r"(?P<pre>\s*)(?P<sep>[:=])(?P<post>\s*)"
        r"(?P<value>[A-Za-z0-9-_.]{8,})"
    ),
]


def redact_secrets(text: str) -> str:
    """Return *text* with known secret patterns replaced by placeholders.

    Whitespace around ``:`` or ``=`` in environment-style assignments is preserved
    to keep formatting intact.
    """

    def _repl(match: re.Match[str]) -> str:
        groups = match.groupdict()
        if "key" in groups:
            return (
                f"{groups['key']}{groups.get('pre', '')}{groups['sep']}"
                f"{groups.get('post', '')}***"
            )
        token = match.group(0)
        if (
            token.startswith("gh")
            and token[2] in {"p", "o", "u", "s", "r"}
            and token[3] == "_"
        ):
            return f"{token[:3]}_REDACTED"
        if token.startswith("github_pat_"):
            return "github_pat_REDACTED"
        if token.startswith("sk-"):
            return "sk-REDACTED"
        if token.startswith("xox"):
            prefix = token.split("-", 1)[0]
            return f"{prefix}-REDACTED"
        if token.startswith("AKIA") or token.startswith("ASIA"):
            return f"{token[:4]}_REDACTED"
        if token.lower().startswith("bearer "):
            return "Bearer ***"
        return "***"

    for pattern in SECRET_PATTERNS:
        text = pattern.sub(_repl, text)
    return text
