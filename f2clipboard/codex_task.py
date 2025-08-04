"""Workflow for fetching Codex task artefacts."""

from __future__ import annotations

import asyncio
import gzip
import re
from typing import Any

import httpx
import pyperclip
import typer

from .config import Settings

GITHUB_API = "https://api.github.com"


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


def _parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Extract owner, repo and pull number from a PR URL."""
    pattern = (
        r"https://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
    )
    match = re.match(pattern, pr_url)
    if not match:  # pragma: no cover - defensive programming
        raise ValueError("Invalid PR URL")
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def _decode_log(data: bytes) -> str:
    """Return log text, decompressing if content is gzipped."""
    try:
        return gzip.decompress(data).decode()
    except OSError:
        return data.decode()


async def _fetch_check_runs(pr_url: str, token: str | None) -> list[dict[str, Any]]:
    """Return check runs for the PR's head commit using the GitHub REST API."""
    owner, repo, number = _parse_pr_url(pr_url)
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(base_url=GITHUB_API, headers=headers) as client:
        pr_resp = await client.get(f"/repos/{owner}/{repo}/pulls/{number}")
        pr_resp.raise_for_status()
        sha = pr_resp.json()["head"]["sha"]
        runs_resp = await client.get(f"/repos/{owner}/{repo}/commits/{sha}/check-runs")
        runs_resp.raise_for_status()
        return runs_resp.json().get("check_runs", [])


async def _download_log(
    client: httpx.AsyncClient, owner: str, repo: str, run_id: int
) -> str:
    """Fetch and decode a check-run log."""
    resp = await client.get(f"/repos/{owner}/{repo}/check-runs/{run_id}/logs")
    resp.raise_for_status()
    return _decode_log(resp.content)


async def _process_task(url: str, settings: Settings) -> str:
    """Download the task page, fetch failing check logs and return Markdown."""
    html = await _fetch_task_html(url)
    pr_url = _extract_pr_url(html)
    if not pr_url:
        return "PR URL not found"

    check_runs = await _fetch_check_runs(pr_url, settings.github_token)
    owner, repo, _ = _parse_pr_url(pr_url)
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    sections: list[str] = []
    async with httpx.AsyncClient(base_url=GITHUB_API, headers=headers) as client:
        for run in check_runs:
            if run.get("conclusion") == "success":
                continue
            log_text = await _download_log(client, owner, repo, run["id"])
            if len(log_text.encode()) > settings.log_size_threshold:
                log_text = log_text[:100] + "\n…\n"  # TODO: summarise via LLM
            sections.append(f"### {run['name']}\n\n```text\n{log_text}\n```")

    return "\n\n".join(sections) or "No failing checks"


def codex_task_command(
    url: str = typer.Argument(..., help="Codex task URL to process"),
) -> None:
    """Parse a Codex task page and print any failing GitHub checks."""
    typer.echo(f"Parsing Codex task page: {url}…")
    settings = Settings()  # load environment (e.g. GITHUB_TOKEN)
    result = asyncio.run(_process_task(url, settings))
    typer.echo(result)
    try:
        pyperclip.copy(result)
    except pyperclip.PyperclipException:
        typer.secho("Warning: could not copy to clipboard", err=True)
