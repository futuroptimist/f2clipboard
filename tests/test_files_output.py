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


def test_files_command_forwards_output(monkeypatch, tmp_path):
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
    out_file = tmp_path / "out.md"
    result = runner.invoke(
        app, ["files", "--dir", str(tmp_path), "--output", str(out_file)]
    )
    assert result.exit_code == 0
    assert called["argv"] == [
        "--dir",
        str(tmp_path),
        "--pattern",
        "*",
        "--output",
        str(out_file),
    ]


def test_legacy_main_writes_output(monkeypatch, tmp_path):
    (tmp_path / "a.py").write_text("a")
    legacy = _load_legacy_module()

    monkeypatch.setattr(legacy, "select_files", lambda files: list(files))

    copied: dict[str, str] = {}
    monkeypatch.setattr(
        legacy.clipboard, "copy", lambda content: copied.setdefault("data", content)
    )

    out_file = tmp_path / "snippet.md"
    legacy.main(
        [
            "--dir",
            str(tmp_path),
            "--pattern",
            "*.py",
            "--output",
            str(out_file),
        ]
    )

    assert out_file.read_text() == copied["data"]
