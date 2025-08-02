"""Workflow for fetching Codex task artefacts."""

from __future__ import annotations

import asyncio

import typer


async def _process_task(url: str) -> str:
    """Placeholder async workflow for processing a Codex task."""
    await asyncio.sleep(0)  # TODO: implement real logic
    return f"processed {url}"


def codex_task_command(url: str) -> None:
    """Entry point used by the Typer CLI."""
    typer.echo(f"Parsing Codex task page: {url}…")
    result = asyncio.run(_process_task(url))
    typer.echo(result)
