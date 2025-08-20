"""Convert chat transcripts into prompts for coding assistants."""

from __future__ import annotations

import html
import re

import clipboard
import httpx
import typer


def _extract_text(html_text: str) -> str:
    """Return plain text from HTML, preserving line breaks and bullet points."""

    def _replace_ordered(match: re.Match[str]) -> str:
        outer = match.group(0)
        inner = match.group(1)
        start_match = re.search(r"start=['\"]?(\d+)['\"]?", outer, flags=re.IGNORECASE)
        start = int(start_match.group(1)) if start_match else 1
        items = re.findall(
            r"<li[^>]*>(.*?)</li[^>]*>", inner, flags=re.IGNORECASE | re.DOTALL
        )
        numbered = [f"{i}. {item}" for i, item in enumerate(items, start)]
        return "\n" + "\n".join(numbered) + "\n"

    html_text = re.sub(
        r"<ol[^>]*>(.*?)</ol>",
        _replace_ordered,
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html_text = re.sub(r"<li[^>]*>", "\n- ", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"</li[^>]*>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(
        r"</?(?:br|p|div|h[1-6])[^>]*>", "\n", html_text, flags=re.IGNORECASE
    )
    text = re.sub(r"<[^>]+>", "", html_text)
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(filter(None, lines))


def _fetch_transcript(url: str, timeout: float = 10.0) -> str:
    """Download transcript text from a shared chat URL."""
    response = httpx.get(url, follow_redirects=True, timeout=timeout)
    response.raise_for_status()
    return _extract_text(response.text)


def _build_prompt(transcript: str, platform: str) -> str:
    return (
        f"You are given the following {platform} chat transcript. "
        "Read it and fully implement any code or configuration changes discussed. "
        "Return the complete implementation.\n\n"
        f"{transcript}"
    )


def chat2prompt_command(
    url: str = typer.Argument(..., help="Chat transcript URL"),
    platform: str = typer.Option("codex", "--platform", "-p", help="Target platform"),
    copy_to_clipboard: bool = typer.Option(
        True, "--clipboard/--no-clipboard", help="Copy prompt to clipboard."
    ),
    timeout: float = typer.Option(
        10.0, "--timeout", help="HTTP request timeout in seconds"
    ),
) -> None:
    """Create a coding prompt from a chat transcript and copy it to the clipboard."""
    if timeout <= 0:
        raise typer.BadParameter("timeout must be greater than 0")
    transcript = _fetch_transcript(url, timeout=timeout)
    prompt = _build_prompt(transcript, platform)
    if copy_to_clipboard:
        clipboard.copy(prompt)
    typer.echo(prompt)
