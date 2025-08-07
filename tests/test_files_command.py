import subprocess
import sys


def test_files_command_missing_dir(tmp_path):
    missing = tmp_path / "missing"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "f2clipboard.cli",
            "files",
            "--dir",
            str(missing),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Directory not found" in result.stderr
