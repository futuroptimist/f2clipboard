"""Convert chat transcripts into prompts for coding assistants."""

from __future__ import annotations

import html
import re

import clipboard
import httpx
import typer


def _extract_text(html_text: str) -> str:
    """Return plain text from HTML."""
    text = re.sub(r"<[^>]+>", "", html_text)
    return html.unescape(text).strip()


def _fetch_transcript(url: str) -> str:
    """Download transcript text from a shared chat URL."""
    response = httpx.get(url, follow_redirects=True)
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
) -> None:
    """Create a coding prompt from a chat transcript and copy it to the clipboard."""
    transcript = _fetch_transcript(url)
    prompt = _build_prompt(transcript, platform)
    if copy_to_clipboard:
        clipboard.copy(prompt)
    typer.echo(prompt)
