"""Tests for plugin interface."""

import importlib
from importlib.metadata import EntryPoint

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
