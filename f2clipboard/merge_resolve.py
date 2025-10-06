"""Automate merge conflict resolution attempts."""

from __future__ import annotations

import asyncio
import re
import subprocess
from enum import Enum
from pathlib import Path

import click
import httpx
import typer
from click.core import ParameterSource

from .config import Settings
from .llm import generate_conflict_patch
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


def _collect_conflict_diff(repo: Path) -> str | None:
    """Return the conflicted diff after a failed merge attempt."""

    diff = subprocess.run(
        ["git", "--no-pager", "diff", "--diff-filter=U"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if diff.returncode != 0:
        message = diff.stderr.strip() or "git diff failed"
        typer.echo(f"Warning: {message}", err=True)
        return None
    output = diff.stdout.strip()
    return output or None


def _attempt_merge(
    repo: Path, base: str, strategy: MergeStrategy
) -> tuple[bool, str | None]:
    """Try merging *base* into *repo* using *strategy* and capture conflicts."""

    typer.echo(f"Attempting merge with strategy '{strategy.value}' from {base}…")
    result = subprocess.run(
        ["git", "merge", "--no-commit", "-X", strategy.value, base],
        cwd=repo,
    )
    if result.returncode == 0:
        return True, None

    typer.echo(
        f"Merge with strategy '{strategy.value}' failed (exit code {result.returncode}).",
        err=True,
    )
    conflict_diff = _collect_conflict_diff(repo)
    abort = subprocess.run(["git", "merge", "--abort"], cwd=repo)
    if abort.returncode != 0:
        typer.echo(
            "Failed to abort merge automatically; resolve the repository state manually.",
            err=True,
        )
        raise typer.Exit(code=abort.returncode or 1)
    return False, conflict_diff


def _generate_patch_suggestion(diff: str, settings: Settings) -> str | None:
    """Return an LLM-generated patch suggestion for merge conflicts."""

    if not diff.strip():
        return None

    if not (settings.openai_api_key or settings.anthropic_api_key):
        return None

    try:
        return asyncio.run(generate_conflict_patch(diff, settings))
    except RuntimeError as exc:
        # ``asyncio.run`` raises RuntimeError when nested inside a loop
        typer.echo(f"Warning: Could not generate patch suggestion: {exc}", err=True)
    except Exception as exc:  # pragma: no cover - defensive guard
        typer.echo(f"Warning: Patch suggestion failed: {exc}", err=True)
    return None


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


def _post_pr_comment(
    owner: str,
    repo: str,
    number: int,
    token: str | None,
    body: str,
) -> None:
    """Post a summarising PR comment when authentication is available."""

    token = token.strip() if token else None
    if not token:
        typer.echo(
            "Skipping PR comment because GITHUB_TOKEN is not configured.",
            err=True,
        )
        return

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "f2clipboard",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = httpx.post(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments",
            headers=headers,
            json={"body": body},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        typer.echo(f"Warning: Failed to post PR comment: {exc}", err=True)
        return

    typer.echo("Posted merge summary comment to the PR.")


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
        help=(
            "PR number or URL to fetch, check out and comment on before merging when authenticated."
        ),
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

    pr_number: int | None = None
    owner: str | None = None
    repo_name: str | None = None
    settings = Settings()

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

    conflict_diffs: list[str] = []
    succeeded: MergeStrategy | None = None
    for current in strategies:
        success, diff_text = _attempt_merge(repo, merge_base, current)
        if success:
            succeeded = current
            break
        if diff_text:
            conflict_diffs.append(diff_text)

    if succeeded is None:
        typer.echo(
            "Automatic merge strategies failed. Manual intervention required.", err=True
        )
        combined_diff = "\n\n".join(conflict_diffs)
        if combined_diff:
            typer.echo(
                "Attempting to generate a patch suggestion using the configured LLM…"
            )
            patch = _generate_patch_suggestion(combined_diff, settings)
            if patch:
                typer.echo("Suggested patch (apply with `git apply`):")
                typer.echo(patch)
            else:
                if settings.openai_api_key or settings.anthropic_api_key:
                    typer.echo(
                        "Failed to generate a patch suggestion automatically.",
                        err=True,
                    )
                else:
                    typer.echo(
                        "Configure OPENAI_API_KEY or ANTHROPIC_API_KEY to enable "
                        "automatic patch suggestions.",
                        err=True,
                    )
        if pr_number is not None and owner and repo_name:
            _post_pr_comment(
                owner,
                repo_name,
                pr_number,
                settings.github_token,
                "⚠️ `f2clipboard merge-resolve` could not resolve the merge automatically. "
                "Manual conflict resolution is required.",
            )
        raise typer.Exit(code=1)

    typer.echo(f"Merge completed using strategy '{succeeded.value}'.")
    typer.echo(
        "Review the changes, resolve any remaining issues and commit when ready."
    )

    if run_checks:
        try:
            merge_checks_command(files=None, repo=repo)
        except typer.Exit as exc:
            if pr_number is not None and owner and repo_name:
                exit_code = exc.exit_code if exc.exit_code is not None else 1
                summary = (
                    "❌ `f2clipboard merge-resolve` completed automatically using the "
                    f"`{succeeded.value}` strategy, but merge checks failed with exit code "
                    f"{exit_code}. Please review the check output and address any issues."
                )
                _post_pr_comment(
                    owner,
                    repo_name,
                    pr_number,
                    settings.github_token,
                    summary,
                )
            raise
        else:
            if pr_number is not None and owner and repo_name:
                summary = (
                    "✅ `f2clipboard merge-resolve` completed automatically using the "
                    f"`{succeeded.value}` strategy. Merge checks were executed successfully."
                )
                _post_pr_comment(
                    owner,
                    repo_name,
                    pr_number,
                    settings.github_token,
                    summary,
                )
    else:
        typer.echo(
            "Run `f2clipboard merge-checks` to validate the merge when convenient."
        )
        if pr_number is not None and owner and repo_name:
            summary = (
                "✅ `f2clipboard merge-resolve` completed automatically using the "
                f"`{succeeded.value}` strategy. Remember to run validation checks before pushing."
            )
            _post_pr_comment(
                owner,
                repo_name,
                pr_number,
                settings.github_token,
                summary,
            )
