"""Automate merge conflict resolution attempts."""

from __future__ import annotations

import re
import subprocess
from enum import Enum
from pathlib import Path

import click
import httpx
import typer
from click.core import ParameterSource

from .config import Settings
from .merge_checks import merge_checks_command

GITHUB_API = "https://api.github.com"
PR_BRANCH_PREFIX = "pr-"


class MergeStrategy(str, Enum):
    """Supported automatic merge strategies."""

    ours = "ours"
    theirs = "theirs"
    both = "both"


def _git_status(repo: Path) -> subprocess.CompletedProcess[str]:
    """Return ``git status --porcelain`` output for *repo*."""

    return subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _ensure_clean_worktree(repo: Path) -> None:
    """Abort if the repository has uncommitted changes or an active merge."""

    merge_head = repo / ".git" / "MERGE_HEAD"
    if merge_head.exists():
        typer.echo(
            "A merge is already in progress. Complete or abort it before rerunning.",
            err=True,
        )
        raise typer.Exit(code=1)

    status = _git_status(repo)
    if status.returncode != 0:
        message = status.stderr.strip() or "git status failed"
        typer.echo(message, err=True)
        raise typer.Exit(code=status.returncode or 1)
    if status.stdout.strip():
        typer.echo(
            "Repository has uncommitted changes. Commit or stash them before running merge-resolve.",
            err=True,
        )
        raise typer.Exit(code=1)


def _attempt_merge(repo: Path, base: str, strategy: MergeStrategy) -> bool:
    """Try merging *base* into *repo* using *strategy*."""

    typer.echo(f"Attempting merge with strategy '{strategy.value}' from {base}…")
    result = subprocess.run(
        ["git", "merge", "--no-commit", "-X", strategy.value, base],
        cwd=repo,
    )
    if result.returncode == 0:
        return True

    typer.echo(
        f"Merge with strategy '{strategy.value}' failed (exit code {result.returncode}).",
        err=True,
    )
    abort = subprocess.run(["git", "merge", "--abort"], cwd=repo)
    if abort.returncode != 0:
        typer.echo(
            "Failed to abort merge automatically; resolve the repository state manually.",
            err=True,
        )
        raise typer.Exit(code=abort.returncode or 1)
    return False


def _parse_pr_identifier(pr_value: str) -> tuple[int, str | None, str | None]:
    """Return PR number and optional owner/repo parsed from *pr_value*."""

    pr_value = pr_value.strip()
    if pr_value.isdigit():
        return int(pr_value), None, None

    match = re.match(
        r"https?://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
        pr_value,
    )
    if match:
        return (
            int(match.group("number")),
            match.group("owner"),
            match.group("repo"),
        )

    raise ValueError("Provide a PR number or GitHub pull request URL")


def _get_remote_slug(repo: Path) -> tuple[str, str]:
    """Return ``(owner, repo)`` derived from the origin remote URL."""

    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "Could not read origin remote URL"
        raise RuntimeError(message)

    url = result.stdout.strip()
    if not url:
        raise RuntimeError("origin remote URL is empty")

    if url.startswith("git@"):
        path = url.split(":", 1)[-1]
    elif "github.com/" in url:
        path = url.split("github.com/", 1)[-1]
    else:
        raise RuntimeError("Unsupported origin remote URL format")

    if path.endswith(".git"):
        path = path[:-4]

    owner, _, repo_name = path.partition("/")
    if not owner or not repo_name:
        raise RuntimeError("Could not parse origin remote into owner/repo")

    return owner, repo_name


def _fetch_pr_base(owner: str, repo: str, number: int, token: str | None) -> str | None:
    """Return the base branch for the PR or ``None`` when unavailable."""

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "f2clipboard",
    }
    token = token.strip() if token else None
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = httpx.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}",
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        typer.echo(f"Warning: Failed to fetch PR metadata: {exc}", err=True)
        return None

    data = response.json()
    base = data.get("base", {})
    ref = base.get("ref")
    return ref or None


def _checkout_pr_branch(repo: Path, number: int) -> str:
    """Fetch the PR head into a local branch and check it out."""

    branch = f"{PR_BRANCH_PREFIX}{number}"
    fetch = subprocess.run(
        ["git", "fetch", "--force", "origin", f"pull/{number}/head:{branch}"],
        cwd=repo,
    )
    if fetch.returncode != 0:
        typer.echo(
            f"Failed to fetch PR #{number} from origin (exit code {fetch.returncode}).",
            err=True,
        )
        raise typer.Exit(code=fetch.returncode or 1)

    checkout = subprocess.run(["git", "checkout", branch], cwd=repo)
    if checkout.returncode != 0:
        typer.echo(
            f"Failed to check out fetched branch '{branch}' (exit code {checkout.returncode}).",
            err=True,
        )
        raise typer.Exit(code=checkout.returncode or 1)

    return branch


def merge_resolve_command(
    base: str | None = typer.Option(
        None,
        "--base",
        "-b",
        help="Base branch to merge from (defaults to PR base or origin/main).",
    ),
    strategy: MergeStrategy = typer.Option(
        MergeStrategy.ours,
        "--strategy",
        "-s",
        help="Merge strategy to attempt (ours, theirs or both).",
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository containing the PR branch.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    run_checks: bool = typer.Option(
        True,
        "--run-checks/--no-run-checks",
        help="Run `f2clipboard merge-checks` after a successful merge.",
    ),
    pr: str | None = typer.Option(
        None,
        "--pr",
        help="PR number or GitHub pull request URL to fetch and check out before merging.",
    ),
) -> None:
    """Attempt automatic merge conflict resolution strategies."""

    repo = repo.resolve()
    _ensure_clean_worktree(repo)

    ctx = click.get_current_context(silent=True)
    base_provided = False
    if ctx is not None:
        base_source = ctx.get_parameter_source("base")
        base_provided = base_source not in (None, ParameterSource.DEFAULT)

    merge_base = base if base is not None else None

    if pr:
        try:
            pr_number, owner, repo_name = _parse_pr_identifier(pr)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

        if owner is None or repo_name is None:
            try:
                owner, repo_name = _get_remote_slug(repo)
            except RuntimeError as exc:
                typer.echo(str(exc), err=True)
                raise typer.Exit(code=1) from exc

        settings = Settings()
        base_ref = _fetch_pr_base(owner, repo_name, pr_number, settings.github_token)
        branch = _checkout_pr_branch(repo, pr_number)
        typer.echo(f"Checked out PR #{pr_number} into '{branch}'.")
        if base_ref and not base_provided:
            merge_base = f"origin/{base_ref}"
            typer.echo(f"Using base branch '{merge_base}' from PR metadata.")

    if merge_base is None:
        merge_base = "origin/main"

    strategies: list[MergeStrategy]
    if strategy is MergeStrategy.both:
        strategies = [MergeStrategy.ours, MergeStrategy.theirs]
    else:
        strategies = [strategy]

    succeeded: MergeStrategy | None = None
    for current in strategies:
        if _attempt_merge(repo, merge_base, current):
            succeeded = current
            break

    if succeeded is None:
        typer.echo(
            "Automatic merge strategies failed. Manual intervention required.", err=True
        )
        raise typer.Exit(code=1)

    typer.echo(f"Merge completed using strategy '{succeeded.value}'.")
    typer.echo(
        "Review the changes, resolve any remaining issues and commit when ready."
    )

    if run_checks:
        merge_checks_command(files=None, repo=repo)
    else:
        typer.echo(
            "Run `f2clipboard merge-checks` to validate the merge when convenient."
        )
