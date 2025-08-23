"""Workflow for fetching Codex task artefacts."""

from __future__ import annotations

import asyncio
import gzip
import re
from typing import Annotated, Any

import httpx
import pyperclip
import typer

from .config import Settings
from .llm import summarise_log
from .secret import redact_secrets

try:  # optional dependency for authenticated Codex tasks
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover - Playwright may be missing
    async_playwright = None  # type: ignore[assignment]

GITHUB_API = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"

# GitHub check-run conclusions considered failing. Other states such as
# "success", "neutral" or "skipped" are ignored when gathering logs.
FAIL_CONCLUSIONS = {"failure", "timed_out", "cancelled", "action_required"}


async def _fetch_task_html(url: str, cookie: str | None = None) -> str:
    """Fetch raw HTML for a Codex task page.

    If ``cookie`` is provided, Playwright is used to inject the session cookie before
    navigating to the page. Otherwise, a simple HTTP request is performed.
    """
    if cookie:
        if async_playwright is None:  # pragma: no cover - import guard
            raise RuntimeError("playwright is required for authenticated Codex tasks")
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context()
            host = httpx.URL(url).host
            await context.add_cookies(
                [
                    {
                        "name": "codex_session",
                        "value": cookie,
                        "domain": host,
                        "path": "/",
                    }
                ]
            )
            page = await context.new_page()
            await page.goto(url)
            html = await page.content()
            await browser.close()
            return html
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def _extract_pr_url(html: str) -> str | None:
    """Return the first GitHub PR URL found in the given HTML.

    The Codex task page includes a "View PR" link pointing to the associated
    GitHub pull request. Codex's markup may use single or double quotes around
    attribute values, whitespace around the equals sign and different attribute
    casing. The regular expression accounts for these variants, ignoring case
    and normalising the extracted URL.
    """

    match = re.search(
        r"href\s*=\s*['\"](https://github.com/[^'\"?#]+/pull/\d+)(?:/)?(?:[?#][^'\"]*)?['\"]",
        html,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def _parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Extract owner, repo and pull number from a PR URL.

    Trailing slashes, query strings and fragments are tolerated and ignored.
    """
    pr_url = pr_url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    pattern = (
        r"https://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
    )
    match = re.match(pattern, pr_url)
    if not match:  # pragma: no cover - defensive programming
        raise ValueError("Invalid PR URL")
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def _decode_log(data: bytes) -> str:
    """Return log text, decompressing if the payload is gzipped.

    GitHub's log endpoint sometimes returns gzip-compressed bytes without a
    `Content-Encoding` header. Rather than relying on exception handling, we
    inspect the magic header to decide whether decompression is required.
    """

    if data[:2] == b"\x1f\x8b":  # gzip magic number
        return gzip.decompress(data).decode("utf-8", errors="replace")
    return data.decode("utf-8", errors="replace")


def _github_headers(token: str | None) -> dict[str, str]:
    """Return standard headers for GitHub API requests.

    The Authorization header is included when a token is supplied.
    Whitespace-only tokens are ignored.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "f2clipboard",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    token = token.strip() if token else None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _fetch_check_runs(pr_url: str, token: str | None) -> list[dict[str, Any]]:
    """Return check runs for the PR's head commit using the GitHub REST API."""
    owner, repo, number = _parse_pr_url(pr_url)
    async with httpx.AsyncClient(
        base_url=GITHUB_API, headers=_github_headers(token)
    ) as client:
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
    html = await _fetch_task_html(url, settings.codex_cookie)
    pr_url = _extract_pr_url(html)
    if not pr_url:
        return "PR URL not found"

    check_runs = await _fetch_check_runs(pr_url, settings.github_token)
    owner, repo, _ = _parse_pr_url(pr_url)
    sections: list[str] = []
    async with httpx.AsyncClient(
        base_url=GITHUB_API, headers=_github_headers(settings.github_token)
    ) as client:
        for run in check_runs:
            if run.get("conclusion") not in FAIL_CONCLUSIONS:
                continue
            log_text = await _download_log(client, owner, repo, run["id"])
            log_text = redact_secrets(log_text)
            if len(log_text.encode()) > settings.log_size_threshold:
                summary = await summarise_log(log_text, settings)
                snippet = "\n".join(log_text.splitlines()[:100])
                rendered = (
                    f"{summary}\n\n<details>\n<summary>First 100 lines</summary>\n\n"
                    f"```text\n{snippet}\n```\n</details>"
                )
            else:
                rendered = f"```text\n{log_text}\n```"
            sections.append(f"### {run['name']}\n\n{rendered}")

    return "\n\n".join(sections) or "No failing checks"


def codex_task_command(
    url: str = typer.Argument(..., help="Codex task URL to process"),
    copy_to_clipboard: bool = typer.Option(
        True,
        "--clipboard/--no-clipboard",
        help="Copy result to the system clipboard.",
    ),
    log_size_threshold: Annotated[
        int | None,
        typer.Option(
            "--log-size-threshold",
            help="Summarise logs larger than this many bytes.",
        ),
    ] = None,
    openai_model: Annotated[
        str | None,
        typer.Option("--openai-model", help="OpenAI model for summarising logs."),
    ] = None,
    anthropic_model: Annotated[
        str | None,
        typer.Option("--anthropic-model", help="Anthropic model for summarising logs."),
    ] = None,
) -> None:
    """Parse a Codex task page and print any failing GitHub checks.

    The generated Markdown is copied to the clipboard unless ``--no-clipboard`` is passed.
    Use ``--log-size-threshold`` to override the summarisation threshold.
    """
    typer.echo(f"Parsing Codex task page: {url}…")
    settings_kwargs = {}
    if log_size_threshold is not None:
        settings_kwargs["LOG_SIZE_THRESHOLD"] = log_size_threshold
    if openai_model is not None:
        settings_kwargs["OPENAI_MODEL"] = openai_model
    if anthropic_model is not None:
        settings_kwargs["ANTHROPIC_MODEL"] = anthropic_model
    settings = Settings(**settings_kwargs) if settings_kwargs else Settings()
    result = asyncio.run(_process_task(url, settings))
    if copy_to_clipboard:
        try:
            pyperclip.copy(result)
        except pyperclip.PyperclipException as exc:
            import warnings

            warnings.warn(f"Could not copy to clipboard: {exc}", RuntimeWarning)
    typer.echo(result)
