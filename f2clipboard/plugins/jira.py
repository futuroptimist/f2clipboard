"""Jira ticket summariser plugin."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import clipboard
import httpx
import typer

from ..config import Settings
from ..llm import summarise_log


async def _load_issue(source: str) -> dict[str, Any]:
    """Return Jira issue JSON from a local file or HTTP URL."""
    path = Path(source)
    if path.exists():
        return json.loads(path.read_text())
    async with httpx.AsyncClient() as client:
        resp = await client.get(source, headers={"Accept": "application/json"})
        resp.raise_for_status()
        return resp.json()


async def _summarise_issue(source: str, settings: Settings) -> str:
    """Fetch, summarise and return Jira issue text."""
    issue = await _load_issue(source)
    fields = issue.get("fields", {})
    summary = fields.get("summary") or ""
    description = fields.get("description") or ""
    text = f"{summary}\n\n{description}"
    return await summarise_log(text, settings)


def register(app: typer.Typer) -> None:
    """Register the Jira command with the main Typer application."""

    @app.command()
    def jira(
        source: str = typer.Argument(..., help="Jira issue URL or path to JSON file"),
    ) -> None:
        """Summarise a Jira ticket and copy result to the clipboard."""
        settings = Settings()
        result = asyncio.run(_summarise_issue(source, settings))
        clipboard.copy(result)
        typer.echo(result)
