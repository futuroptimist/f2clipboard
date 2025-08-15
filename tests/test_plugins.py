"""Tests for plugin interface."""

import importlib
from importlib.metadata import EntryPoint

from typer.testing import CliRunner

import f2clipboard


def plugin(app):
    """Sample plugin to register a command."""

    @app.command("hello")
    def hello_cmd() -> None:  # pragma: no cover - invoked via Typer
        """Dummy plugin command."""
        pass


def test_plugin_loaded(monkeypatch):
    ep = EntryPoint(
        name="sample", value="tests.test_plugins:plugin", group="f2clipboard.plugins"
    )

    def fake_entry_points(*args, **kwargs):
        if kwargs.get("group") == "f2clipboard.plugins":
            return [ep]
        return []

    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", fake_entry_points)
    f2clipboard._load_plugins()
    names = [cmd.name for cmd in f2clipboard.app.registered_commands]
    assert "hello" in names


def test_plugins_command_lists_plugins(monkeypatch):
    ep = EntryPoint(
        name="sample", value="tests.test_plugins:plugin", group="f2clipboard.plugins"
    )

    def fake_entry_points(*args, **kwargs):
        if kwargs.get("group") == "f2clipboard.plugins":
            return [ep]
        return []

    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", fake_entry_points)
    f2clipboard._loaded_plugins = []
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins"])
    assert result.exit_code == 0
    assert "sample" in result.stdout


def test_plugins_command_json_lists_plugins(monkeypatch):
    ep = EntryPoint(
        name="sample", value="tests.test_plugins:plugin", group="f2clipboard.plugins"
    )

    def fake_entry_points(*args, **kwargs):
        if kwargs.get("group") == "f2clipboard.plugins":
            return [ep]
        return []

    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", fake_entry_points)
    f2clipboard._loaded_plugins = []
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip() == '["sample"]'


def test_plugins_command_json_no_plugins(monkeypatch):
    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", lambda *a, **k: [])
    f2clipboard._loaded_plugins = []
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "[]"


def test_plugins_command_count(monkeypatch):
    ep = EntryPoint(
        name="sample", value="tests.test_plugins:plugin", group="f2clipboard.plugins"
    )

    def fake_entry_points(*args, **kwargs):
        if kwargs.get("group") == "f2clipboard.plugins":
            return [ep]
        return []

    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", fake_entry_points)
    f2clipboard._loaded_plugins = []
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--count"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "1"


def test_plugins_command_count_no_plugins(monkeypatch):
    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", lambda *a, **k: [])
    f2clipboard._loaded_plugins = []
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--count"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0"
