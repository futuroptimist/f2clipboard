"""Automate merge conflict resolution attempts."""

from __future__ import annotations

import subprocess
from enum import Enum
from pathlib import Path

import typer

from .merge_checks import merge_checks_command


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


def merge_resolve_command(
    base: str = typer.Option(
        "origin/main", "--base", "-b", help="Base branch to merge from."
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
) -> None:
    """Attempt automatic merge conflict resolution strategies."""

    repo = repo.resolve()
    _ensure_clean_worktree(repo)

    strategies: list[MergeStrategy]
    if strategy is MergeStrategy.both:
        strategies = [MergeStrategy.ours, MergeStrategy.theirs]
    else:
        strategies = [strategy]

    succeeded: MergeStrategy | None = None
    for current in strategies:
        if _attempt_merge(repo, base, current):
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
