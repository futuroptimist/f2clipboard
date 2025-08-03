"""Workflow for fetching Codex task artefacts."""

from __future__ import annotations

import asyncio
import re

import httpx
import typer

from .config import Settings


async def _fetch_task_html(url: str) -> str:
    """Fetch raw HTML for a Codex task page."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def _extract_pr_url(html: str) -> str | None:
    """Return the first GitHub PR URL found in the given HTML."""
    match = re.search(r'href="(https://github.com/[^"]+/pull/\d+)"', html)
    return match.group(1) if match else None


async def _process_task(url: str) -> str:
    """Download the task page and extract the linked PR URL."""
    html = await _fetch_task_html(url)
    pr_url = _extract_pr_url(html)
    return pr_url or "PR URL not found"


def codex_task_command(
    url: str = typer.Argument(..., help="Codex task URL to process"),
) -> None:
    """Parse a Codex task page and print its GitHub PR URL."""
    typer.echo(f"Parsing Codex task page: {url}…")
    Settings()  # load environment (e.g. GITHUB_TOKEN) for future use
    result = asyncio.run(_process_task(url))
    typer.echo(result)
