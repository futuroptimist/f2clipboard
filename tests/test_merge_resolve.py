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
        if cmd[:4] == ["git", "--no-pager", "diff", "--diff-filter=U"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="diff", stderr="")
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


def test_merge_resolve_fetches_pr_and_uses_base(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "worktree"
    repo.mkdir()
    (repo / ".git").mkdir()
    commands: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        commands.append(cmd)
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:4] == ["git", "config", "--get", "remote.origin.url"]:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="https://github.com/example/repo.git\n",
                stderr="",
            )
        if cmd[:4] == ["git", "fetch", "--force", "origin"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:2] == ["git", "checkout"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:4] == ["git", "--no-pager", "diff", "--diff-filter=U"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:6] == ["git", "merge", "--no-commit", "-X", "ours", "origin/develop"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:2] == ["git", "merge"] and cmd[1] == "--abort":
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("f2clipboard.merge_resolve.subprocess.run", fake_run)
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._fetch_pr_base",
        lambda owner, repo, number, token: "develop",
    )

    class DummySettings:
        github_token = "token"
        openai_api_key = None
        anthropic_api_key = None
        openai_model = "gpt-3.5-turbo"
        anthropic_model = "claude-3-haiku-20240307"

        def __init__(self) -> None:  # pragma: no cover - nothing to do
            return

    monkeypatch.setattr("f2clipboard.merge_resolve.Settings", DummySettings)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(repo),
            "--strategy",
            "ours",
            "--no-run-checks",
            "--pr",
            "https://github.com/example/repo/pull/123",
        ],
    )

    assert result.exit_code == 0
    assert ["git", "fetch", "--force", "origin", "pull/123/head:pr-123"] in commands
    assert ["git", "checkout", "pr-123"] in commands
    assert any(
        call[:6] == ["git", "merge", "--no-commit", "-X", "ours", "origin/develop"]
        for call in commands
    )


def test_merge_resolve_pr_respects_explicit_base(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "worktree"
    repo.mkdir()
    (repo / ".git").mkdir()
    commands: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        commands.append(cmd)
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:4] == ["git", "config", "--get", "remote.origin.url"]:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="https://github.com/example/repo.git\n",
                stderr="",
            )
        if cmd[:4] == ["git", "fetch", "--force", "origin"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:2] == ["git", "checkout"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:4] == ["git", "--no-pager", "diff", "--diff-filter=U"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:6] == ["git", "merge", "--no-commit", "-X", "ours", "feature-base"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:2] == ["git", "merge"] and cmd[1] == "--abort":
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("f2clipboard.merge_resolve.subprocess.run", fake_run)
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._fetch_pr_base",
        lambda owner, repo, number, token: "develop",
    )

    class DummySettings:
        github_token = "token"
        openai_api_key = None
        anthropic_api_key = None
        openai_model = "gpt-3.5-turbo"
        anthropic_model = "claude-3-haiku-20240307"

        def __init__(self) -> None:  # pragma: no cover - nothing to do
            return

    monkeypatch.setattr("f2clipboard.merge_resolve.Settings", DummySettings)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(repo),
            "--strategy",
            "ours",
            "--no-run-checks",
            "--pr",
            "123",
            "--base",
            "feature-base",
        ],
    )

    assert result.exit_code == 0
    assert ["git", "fetch", "--force", "origin", "pull/123/head:pr-123"] in commands
    assert ["git", "checkout", "pr-123"] in commands
    assert any(
        call[:6] == ["git", "merge", "--no-commit", "-X", "ours", "feature-base"]
        for call in commands
    )


def test_merge_resolve_posts_success_comment(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    monkeypatch.setattr(
        "f2clipboard.merge_resolve._ensure_clean_worktree", lambda repo: None
    )
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._fetch_pr_base",
        lambda owner, repo, number, token: "main",
    )
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._checkout_pr_branch",
        lambda repo, number: f"pr-{number}",
    )

    attempted: dict[str, object] = {}

    def fake_attempt(repo: Path, base: str, strategy):
        attempted["base"] = base
        attempted["strategy"] = strategy.value
        return True, None

    monkeypatch.setattr("f2clipboard.merge_resolve._attempt_merge", fake_attempt)

    checks: dict[str, Path] = {}

    def fake_merge_checks(*, files, repo: Path) -> None:
        checks["repo"] = repo

    monkeypatch.setattr(
        "f2clipboard.merge_resolve.merge_checks_command", fake_merge_checks
    )

    posted: dict[str, object] = {}

    def fake_post(
        owner: str, repo: str, number: int, token: str | None, body: str
    ) -> None:
        posted["owner"] = owner
        posted["repo"] = repo
        posted["number"] = number
        posted["token"] = token
        posted["body"] = body

    monkeypatch.setattr("f2clipboard.merge_resolve._post_pr_comment", fake_post)

    class DummySettings:
        github_token = "token"
        openai_api_key = None
        anthropic_api_key = None
        openai_model = "gpt-3.5-turbo"
        anthropic_model = "claude-3-haiku-20240307"

        def __init__(self) -> None:
            return

    monkeypatch.setattr("f2clipboard.merge_resolve.Settings", DummySettings)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(repo),
            "--pr",
            "https://github.com/example/repo/pull/42",
        ],
    )

    assert result.exit_code == 0
    assert attempted["base"] == "origin/main"
    assert attempted["strategy"] == "ours"
    assert checks["repo"] == repo.resolve()
    assert posted == {
        "owner": "example",
        "repo": "repo",
        "number": 42,
        "token": "token",
        "body": (
            "✅ `f2clipboard merge-resolve` completed automatically using the `ours` strategy. "
            "Merge checks were executed successfully."
        ),
    }


def test_merge_resolve_posts_failure_comment(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    monkeypatch.setattr(
        "f2clipboard.merge_resolve._ensure_clean_worktree", lambda repo: None
    )
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._fetch_pr_base",
        lambda owner, repo, number, token: "main",
    )
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._checkout_pr_branch",
        lambda repo, number: f"pr-{number}",
    )

    monkeypatch.setattr(
        "f2clipboard.merge_resolve._attempt_merge",
        lambda repo, base, strategy: (False, "conflict diff"),
    )

    posted: dict[str, object] = {}

    def fake_post(
        owner: str, repo: str, number: int, token: str | None, body: str
    ) -> None:
        posted["owner"] = owner
        posted["repo"] = repo
        posted["number"] = number
        posted["token"] = token
        posted["body"] = body

    monkeypatch.setattr("f2clipboard.merge_resolve._post_pr_comment", fake_post)

    class DummySettings:
        github_token = "token"
        openai_api_key = None
        anthropic_api_key = None
        openai_model = "gpt-3.5-turbo"
        anthropic_model = "claude-3-haiku-20240307"

        def __init__(self) -> None:
            return

    monkeypatch.setattr("f2clipboard.merge_resolve.Settings", DummySettings)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        [
            "merge-resolve",
            "--repo",
            str(repo),
            "--pr",
            "https://github.com/example/repo/pull/42",
        ],
    )

    assert result.exit_code != 0
    assert posted == {
        "owner": "example",
        "repo": "repo",
        "number": 42,
        "token": "token",
        "body": (
            "⚠️ `f2clipboard merge-resolve` could not resolve the merge automatically. "
            "Manual conflict resolution is required."
        ),
    }


def test_merge_resolve_generates_patch_suggestion(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    monkeypatch.setattr(
        "f2clipboard.merge_resolve._ensure_clean_worktree", lambda repo: None
    )
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._attempt_merge",
        lambda repo, base, strategy: (False, "conflict diff"),
    )

    recorded: dict[str, str] = {}

    def fake_suggestion(diff: str, settings) -> str:
        recorded["diff"] = diff
        return "PATCH"

    monkeypatch.setattr(
        "f2clipboard.merge_resolve._generate_patch_suggestion", fake_suggestion
    )

    class DummySettings:
        github_token = None
        openai_api_key = "key"
        anthropic_api_key = None
        openai_model = "gpt-4o-mini"
        anthropic_model = "claude-3-haiku-20240307"

        def __init__(self) -> None:
            return

    monkeypatch.setattr("f2clipboard.merge_resolve.Settings", DummySettings)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        ["merge-resolve", "--repo", str(repo), "--base", "main", "--strategy", "ours"],
    )

    assert result.exit_code == 1
    assert recorded["diff"] == "conflict diff"
    assert "Suggested patch (apply with `git apply`):" in result.stdout
    assert "PATCH" in result.stdout


def test_merge_resolve_warns_when_patch_generation_fails(
    monkeypatch, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    monkeypatch.setattr(
        "f2clipboard.merge_resolve._ensure_clean_worktree", lambda repo: None
    )
    monkeypatch.setattr(
        "f2clipboard.merge_resolve._attempt_merge",
        lambda repo, base, strategy: (False, "conflict diff"),
    )

    monkeypatch.setattr(
        "f2clipboard.merge_resolve._generate_patch_suggestion",
        lambda diff, settings: None,
    )

    class DummySettings:
        github_token = None
        openai_api_key = "key"
        anthropic_api_key = None
        openai_model = "gpt-4o-mini"
        anthropic_model = "claude-3-haiku-20240307"

        def __init__(self) -> None:
            return

    monkeypatch.setattr("f2clipboard.merge_resolve.Settings", DummySettings)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        ["merge-resolve", "--repo", str(repo), "--base", "main", "--strategy", "ours"],
    )

    assert result.exit_code == 1
    combined_output = result.stdout + result.stderr
    assert "Failed to generate a patch suggestion automatically." in combined_output


def test_post_pr_comment_requires_token(monkeypatch, capsys) -> None:
    called = False

    def fake_httpx_post(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("HTTP call should not be made without a token")

    monkeypatch.setattr("f2clipboard.merge_resolve.httpx.post", fake_httpx_post)

    f2clipboard.merge_resolve._post_pr_comment(
        "owner", "repo", 1, token="", body="hello"
    )

    captured = capsys.readouterr()
    assert "Skipping PR comment" in captured.err
    assert called is False
