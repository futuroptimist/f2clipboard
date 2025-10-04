"""Automate merge conflict resolution attempts."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

import typer

from .merge_checks import merge_checks_command


class MergeStrategy(str, Enum):
    """Supported automatic merge strategies."""

    ours = "ours"
    theirs = "theirs"
    both = "both"


@dataclass
class ConflictDetails:
    """Captured information about unresolved merge conflicts."""

    files: list[str]
    diff: str


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


def _attempt_merge(
    repo: Path,
    base: str,
    strategy: MergeStrategy,
    on_failure: Optional[Callable[[Path], None]] = None,
) -> bool:
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
    if on_failure is not None:
        on_failure(repo)
    abort = subprocess.run(["git", "merge", "--abort"], cwd=repo)
    if abort.returncode != 0:
        typer.echo(
            "Failed to abort merge automatically; resolve the repository state manually.",
            err=True,
        )
        raise typer.Exit(code=abort.returncode or 1)
    return False


def _collect_conflict_details(repo: Path) -> ConflictDetails:
    """Return conflicting file names and diff hunks for the current merge state."""

    files_proc = subprocess.run(
        [
            "git",
            "--no-pager",
            "diff",
            "--name-only",
            "--diff-filter=U",
        ],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    files: list[str] = []
    if files_proc.returncode == 0:
        files = [
            line.strip() for line in files_proc.stdout.splitlines() if line.strip()
        ]
    else:
        message = files_proc.stderr.strip() or "unable to list conflicting files"
        typer.echo(f"Warning: {message}", err=True)

    diff_proc = subprocess.run(
        ["git", "--no-pager", "diff", "--diff-filter=U"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    diff = ""
    if diff_proc.returncode == 0:
        diff = diff_proc.stdout.strip()
    else:
        message = diff_proc.stderr.strip() or "unable to capture conflict diff"
        typer.echo(f"Warning: {message}", err=True)

    return ConflictDetails(files=files, diff=diff)


def _render_conflict_prompt(conflicts: ConflictDetails, base: str) -> None:
    """Display guidance and a Codex-ready prompt for manual conflict resolution."""

    if conflicts.files:
        typer.echo("Conflicting files:")
        for path in conflicts.files:
            typer.echo(f"- {path}")
    else:
        typer.echo("Conflicting files could not be determined.")

    typer.echo("")
    typer.echo("Codex merge-conflicts prompt:")
    typer.echo("")
    lines = [
        "SYSTEM:",
        "You are an automated assistant that resolves Git merge conflicts for the f2clipboard project.",
        "",
        "USER:",
        (
            "The merge of "
            f"{base} "
            "into the current branch produced conflicts. Resolve them and return a patch that applies cleanly."
        ),
        "Keep unrelated files unchanged.",
    ]
    if conflicts.files:
        lines.append("")
        lines.append("Conflicting files:")
        lines.extend(f"- {name}" for name in conflicts.files)
    lines.extend(
        [
            "",
            "CONTEXT:",
        ]
    )
    if conflicts.diff:
        lines.append("```diff")
        lines.append(conflicts.diff)
        lines.append("```")
    else:
        lines.append("(Conflict diff unavailable)")
    lines.extend(
        [
            "",
            "After applying the generated patch, run `f2clipboard merge-checks` to verify the result.",
        ]
    )
    typer.echo("\n".join(lines))


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

    conflict_details: Optional[ConflictDetails] = None

    def _capture_conflicts(_: Path) -> None:
        nonlocal conflict_details
        conflict_details = _collect_conflict_details(repo)

    succeeded: Optional[MergeStrategy] = None
    for current in strategies:
        if _attempt_merge(repo, base, current, on_failure=_capture_conflicts):
            conflict_details = None
            succeeded = current
            break

    if succeeded is None:
        typer.echo(
            "Automatic merge strategies failed. Manual intervention required.", err=True
        )
        typer.echo("")
        if conflict_details is not None:
            _render_conflict_prompt(conflict_details, base)
        else:
            typer.echo(
                "No conflict details were captured. Retry the merge manually for more context."
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
