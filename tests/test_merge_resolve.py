from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

import f2clipboard


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _prepare_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "file.txt").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "file.txt")
    _git(repo, "commit", "-m", "initial")
    _git(repo, "branch", "-M", "main")
    return repo


def _create_conflict_repo(tmp_path: Path) -> Path:
    repo = _prepare_repo(tmp_path)
    _git(repo, "checkout", "-b", "feature")
    (repo / "file.txt").write_text("feature\n", encoding="utf-8")
    _git(repo, "commit", "-am", "feature change")
    _git(repo, "checkout", "main")
    (repo / "file.txt").write_text("main\n", encoding="utf-8")
    _git(repo, "commit", "-am", "main change")
    _git(repo, "checkout", "feature")
    return repo


def test_merge_resolve_prefers_ours(tmp_path: Path) -> None:
    repo = _create_conflict_repo(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(repo),
            "--base",
            "main",
            "--strategy",
            "ours",
            "--no-run-checks",
        ],
    )
    assert result.exit_code == 0
    assert (repo / "file.txt").read_text(encoding="utf-8") == "feature\n"


def test_merge_resolve_prefers_theirs(tmp_path: Path) -> None:
    repo = _create_conflict_repo(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(repo),
            "--base",
            "main",
            "--strategy",
            "theirs",
            "--no-run-checks",
        ],
    )
    assert result.exit_code == 0
    assert (repo / "file.txt").read_text(encoding="utf-8") == "main\n"


def test_merge_resolve_requires_clean_worktree(tmp_path: Path) -> None:
    repo = _create_conflict_repo(tmp_path)
    (repo / "untracked.txt").write_text("dirty", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        ["merge-resolve", "--repo", str(repo), "--base", "main", "--strategy", "ours"],
    )
    assert result.exit_code != 0
    output = result.stdout + result.stderr
    assert "uncommitted changes" in output


def test_merge_resolve_attempts_both_strategies(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(cmd)
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:5] == ["git", "merge", "--no-commit", "-X", "ours"]:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="conflict")
        if cmd[:5] == ["git", "--no-pager", "diff", "--name-only", "--diff-filter=U"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="conflict.txt\n", stderr=""
            )
        if cmd[:4] == ["git", "--no-pager", "diff", "--diff-filter=U"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd == ["git", "merge", "--abort"]:
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[:5] == ["git", "merge", "--no-commit", "-X", "theirs"]:
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("f2clipboard.merge_resolve.subprocess.run", fake_run)

    runner = CliRunner()
    repo = tmp_path
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(repo),
            "--base",
            "main",
            "--strategy",
            "both",
            "--no-run-checks",
        ],
    )
    assert result.exit_code == 0
    assert any(
        call[:6] == ["git", "merge", "--no-commit", "-X", "ours", "main"]
        for call in calls
    )
    assert any(
        call[:6] == ["git", "merge", "--no-commit", "-X", "theirs", "main"]
        for call in calls
    )


def test_merge_resolve_runs_checks(monkeypatch, tmp_path: Path) -> None:
    repo = _create_conflict_repo(tmp_path)
    called: dict[str, Path] = {}

    def fake_merge_checks(*, files, repo: Path) -> None:
        called["repo"] = repo

    monkeypatch.setattr(
        "f2clipboard.merge_resolve.merge_checks_command", fake_merge_checks
    )

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        ["merge-resolve", "--repo", str(repo), "--base", "main", "--strategy", "ours"],
    )
    assert result.exit_code == 0
    assert called["repo"] == repo


def test_merge_resolve_outputs_conflict_prompt(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        commands.append(cmd)
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:5] == ["git", "merge", "--no-commit", "-X", "ours"]:
            return subprocess.CompletedProcess(
                cmd, 1, stdout="", stderr="conflict ours"
            )
        if cmd == ["git", "merge", "--abort"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:5] == ["git", "merge", "--no-commit", "-X", "theirs"]:
            return subprocess.CompletedProcess(
                cmd, 1, stdout="", stderr="conflict theirs"
            )
        if cmd[:5] == ["git", "--no-pager", "diff", "--name-only", "--diff-filter=U"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="foo.txt\nbar.txt\n", stderr=""
            )
        if cmd[:4] == ["git", "--no-pager", "diff", "--diff-filter=U"]:
            diff = (
                "diff --git a/foo.txt b/foo.txt\n"
                "<<<<<<< HEAD\nfoo\n=======\nbar\n>>>>>>> origin/main\n"
            )
            return subprocess.CompletedProcess(cmd, 0, stdout=diff, stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("f2clipboard.merge_resolve.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(tmp_path),
            "--base",
            "origin/main",
            "--strategy",
            "both",
            "--no-run-checks",
        ],
    )

    assert result.exit_code == 1
    stdout = result.stdout
    assert "Conflicting files:" in stdout
    assert "- foo.txt" in stdout
    assert "Codex merge-conflicts prompt" in stdout
    assert "SYSTEM:" in stdout
    assert "```diff" in stdout
    assert "<<<<<<< HEAD" in stdout
    # Ensure diff commands executed
    assert any(
        cmd[:5] == ["git", "--no-pager", "diff", "--name-only", "--diff-filter=U"]
        for cmd in commands
    )
