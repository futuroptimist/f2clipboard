import subprocess

import pytest
from typer.testing import CliRunner

import f2clipboard


def test_merge_checks_runs_on_modified_files(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        if cmd[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=" M app.py\n?? new.txt\n",
                stderr="",
            )
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("f2clipboard.merge_checks.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["merge-checks", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert calls[0][:3] == ["pre-commit", "run", "--files"]
    assert calls[0][3:] == ["app.py", "new.txt"]
    assert calls[1] == ["pytest", "-q"]


def test_merge_checks_respects_explicit_files(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        if cmd[:2] == ["git", "status"]:
            pytest.fail("git status should not be called when files are provided")
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("f2clipboard.merge_checks.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app,
        ["merge-checks", "--repo", str(tmp_path), "--file", "a.py", "--file", "b.py"],
    )
    assert result.exit_code == 0
    assert calls[0][:3] == ["pre-commit", "run", "--files"]
    assert calls[0][3:] == ["a.py", "b.py"]
    assert calls[1] == ["pytest", "-q"]


def test_merge_checks_skips_pre_commit_without_files(monkeypatch, tmp_path):
    commands: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        if cmd[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("f2clipboard.merge_checks.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["merge-checks", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert commands == [["pytest", "-q"]]


def test_merge_checks_exits_on_pre_commit_failure(monkeypatch, tmp_path):
    commands: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        if cmd[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=" M main.py\n",
                stderr="",
            )
        if cmd[:2] == ["pre-commit", "run"]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 3)
        pytest.fail("pytest should not run when pre-commit fails")

    monkeypatch.setattr("f2clipboard.merge_checks.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["merge-checks", "--repo", str(tmp_path)])
    assert result.exit_code == 3
    assert commands[0][:3] == ["pre-commit", "run", "--files"]


def test_parse_git_status_handles_rename_and_deletion():
    from f2clipboard.merge_checks import _parse_git_status

    output = "R  old.py -> new.py\nD  removed.py\n?? added.py\n"
    assert _parse_git_status(output) == ["new.py", "added.py"]
