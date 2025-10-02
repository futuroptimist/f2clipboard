"""Utilities for running merge validation checks."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Iterable

import typer


def _parse_git_status(output: str) -> list[str]:
    """Return modified file paths parsed from ``git status --porcelain`` output."""

    files: list[str] = []

    if "\0" in output:
        entries = [entry for entry in output.split("\0") if entry]
        entry_iter = iter(entries)
        for entry in entry_iter:
            status = entry[:2]
            path = entry[3:]
            if status and status[0] in {"R", "C"}:
                # Renames/copies include the old path in the current entry and
                # the new path as the next NUL-delimited payload. Prefer the
                # new path.
                try:
                    path = next(entry_iter)
                except StopIteration:  # pragma: no cover - defensive guard
                    break
            if "D" in status or not path:
                continue
            files.append(path)
        return files

    for line in output.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:].strip()
        if not path:
            continue
        if path.startswith('"') and path.endswith('"'):
            try:
                path = ast.literal_eval(path)
            except (SyntaxError, ValueError):  # pragma: no cover - defensive guard
                path = path.strip('"')
        if "->" in path:
            path = path.split("->", 1)[1].strip()
        if "D" in status:
            continue
        files.append(path)
    return files


def _collect_modified_files(repo: Path) -> list[str]:
    """Return tracked files with modifications inside *repo*."""

    proc = subprocess.run(
        ["git", "status", "--porcelain", "-z"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or "git status failed"
        raise RuntimeError(message)
    return _parse_git_status(proc.stdout)


def _run_command(args: Iterable[str], cwd: Path) -> int:
    """Run a subprocess returning its exit code."""

    result = subprocess.run(list(args), cwd=cwd)
    return result.returncode


def merge_checks_command(
    files: list[Path] | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Explicit file paths to run pre-commit on.",
        show_default=False,
    ),
    repo: Path = typer.Option(
        Path("."),
        "--repo",
        help="Repository root containing the merge worktree.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Run ``pre-commit`` and ``pytest`` to validate a merge."""

    repo = repo.resolve()
    target_files: list[str]
    if files:
        target_files = []
        for path in files:
            resolved = path if path.is_absolute() else (repo / path)
            resolved = resolved.resolve()
            try:
                target_files.append(str(resolved.relative_to(repo)))
            except ValueError:
                target_files.append(str(resolved))
    else:
        try:
            target_files = _collect_modified_files(repo)
        except RuntimeError as exc:
            typer.echo(f"Failed to determine modified files: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    if target_files:
        typer.echo(
            f"Running pre-commit on {len(target_files)} file(s)…",
        )
        exit_code = _run_command(["pre-commit", "run", "--files", *target_files], repo)
        if exit_code != 0:
            raise typer.Exit(code=exit_code)
    else:
        typer.echo("No modified files detected; skipping pre-commit.")

    typer.echo("Running pytest -q…")
    exit_code = _run_command(["pytest", "-q"], repo)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)

    typer.echo("Checks completed successfully.")
