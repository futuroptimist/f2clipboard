import importlib.util
import types
from pathlib import Path

from typer.testing import CliRunner

from f2clipboard import app
from f2clipboard import files as files_module


def _load_legacy_module():
    spec = importlib.util.spec_from_file_location(
        "legacy_f2clipboard", Path(__file__).resolve().parents[1] / "f2clipboard.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_list_files_respects_exclude(tmp_path):
    (tmp_path / "a.py").write_text("a")
    (tmp_path / "b.py").write_text("b")
    legacy = _load_legacy_module()
    files = list(
        legacy.list_files(str(tmp_path), pattern="*.py", ignore_patterns=["b.py"])
    )
    assert str(tmp_path / "a.py") in files
    assert str(tmp_path / "b.py") not in files


def test_list_files_skips_directory_with_trailing_slash(tmp_path):
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "file.txt").write_text("data")
    legacy = _load_legacy_module()
    files = list(legacy.list_files(str(tmp_path), ignore_patterns=["ignored/"]))
    assert files == []


def test_files_command_forwards_exclude(monkeypatch, tmp_path):
    called = {}

    def fake_main(argv):
        called["argv"] = argv

    class FakeLoader:
        def exec_module(self, module):
            module.main = fake_main

    class FakeSpec:
        loader = FakeLoader()

    monkeypatch.setattr(
        files_module, "spec_from_file_location", lambda name, path: FakeSpec()
    )
    monkeypatch.setattr(
        files_module, "module_from_spec", lambda spec: types.SimpleNamespace()
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "files",
            "--dir",
            str(tmp_path),
            "--pattern",
            "*.py",
            "--exclude",
            "x",
            "--exclude",
            "y",
        ],
    )
    assert result.exit_code == 0
    assert called["argv"] == [
        "--dir",
        str(tmp_path),
        "--pattern",
        "*.py",
        "--exclude",
        "x",
        "--exclude",
        "y",
    ]


def test_legacy_main_uses_exclude(monkeypatch, tmp_path):
    (tmp_path / "a.py").write_text("a")
    (tmp_path / "b.py").write_text("b")
    legacy = _load_legacy_module()

    monkeypatch.setattr(legacy, "select_files", lambda files: list(files))

    copied: dict[str, str] = {}
    monkeypatch.setattr(
        legacy.clipboard, "copy", lambda content: copied.setdefault("data", content)
    )

    legacy.main(["--dir", str(tmp_path), "--pattern", "*.py", "--exclude", "b.py"])

    assert "b.py" not in copied["data"]
    assert "a.py" in copied["data"]
