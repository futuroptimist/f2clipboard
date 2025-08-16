"""Tests for plugin interface."""

import importlib
import sys
from importlib.metadata import EntryPoint
from types import ModuleType

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


def test_load_plugins_idempotent(monkeypatch):
    mod = ModuleType("sample_plugin_mod")

    def sample_plugin(app):
        @app.command("hello")
        def hello_cmd() -> None:  # pragma: no cover - invoked via Typer
            pass

    mod.plugin = sample_plugin
    monkeypatch.setitem(sys.modules, mod.__name__, mod)

    ep = EntryPoint(
        name="sample", value=f"{mod.__name__}:plugin", group="f2clipboard.plugins"
    )

    def fake_entry_points(*args, **kwargs):
        if kwargs.get("group") == "f2clipboard.plugins":
            return [ep]
        return []

    monkeypatch.setattr("importlib.metadata.entry_points", lambda *a, **k: [])
    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", fake_entry_points)
    f2clipboard._loaded_plugins = []
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    f2clipboard._load_plugins()
    assert f2clipboard._loaded_plugins == ["sample"]


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
    f2clipboard._plugin_versions = {}
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
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip() == '["sample"]'


def test_plugins_command_json_no_plugins(monkeypatch):
    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", lambda *a, **k: [])
    f2clipboard._loaded_plugins = []
    f2clipboard._plugin_versions = {}
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
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--count"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "1"


def test_plugins_command_count_no_plugins(monkeypatch):
    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", lambda *a, **k: [])
    f2clipboard._loaded_plugins = []
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--count"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0"


def test_plugins_command_versions(monkeypatch):
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
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--versions"])
    assert result.exit_code == 0
    assert "sample unknown" in result.stdout


def test_plugins_command_json_versions(monkeypatch):
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
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--versions", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip() == '{"sample": "unknown"}'


def test_plugins_command_versions_no_plugins(monkeypatch):
    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", lambda *a, **k: [])
    f2clipboard._loaded_plugins = []
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--versions"])
    assert result.exit_code == 0
    assert "No plugins installed" in result.stdout


def test_plugins_command_json_versions_no_plugins(monkeypatch):
    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", lambda *a, **k: [])
    f2clipboard._loaded_plugins = []
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--versions", "--json"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "{}"


def _setup_two_plugins(monkeypatch):
    ep1 = EntryPoint(
        name="zeta", value="tests.test_plugins:plugin", group="f2clipboard.plugins"
    )
    ep2 = EntryPoint(
        name="alpha", value="tests.test_plugins:plugin", group="f2clipboard.plugins"
    )

    def fake_entry_points(*args, **kwargs):
        if kwargs.get("group") == "f2clipboard.plugins":
            return [ep1, ep2]
        return []

    importlib.reload(f2clipboard)
    monkeypatch.setattr(f2clipboard, "entry_points", fake_entry_points)
    f2clipboard._loaded_plugins = []
    f2clipboard._plugin_versions = {}
    f2clipboard._load_plugins()


def test_plugins_command_sort(monkeypatch):
    _setup_two_plugins(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--sort"])
    assert result.exit_code == 0
    assert result.stdout.strip().splitlines() == ["alpha", "zeta"]


def test_plugins_command_json_sort(monkeypatch):
    _setup_two_plugins(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--json", "--sort"])
    assert result.exit_code == 0
    assert result.stdout.strip() == '["alpha", "zeta"]'


def test_plugins_command_versions_sort(monkeypatch):
    _setup_two_plugins(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(f2clipboard.app, ["plugins", "--versions", "--sort"])
    assert result.exit_code == 0
    assert result.stdout.strip().splitlines() == ["alpha unknown", "zeta unknown"]


def test_plugins_command_versions_json_sort(monkeypatch):
    _setup_two_plugins(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(
        f2clipboard.app, ["plugins", "--versions", "--json", "--sort"]
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == '{"alpha": "unknown", "zeta": "unknown"}'
