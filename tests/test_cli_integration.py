import subprocess
import sys


def test_cli_basic(temp_directory, clipboard_env):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "f2clipboard",
            "--dir",
            temp_directory,
            "--pattern",
            "*.txt",
        ],
        input="1\ndone\n",
        text=True,
        capture_output=True,
        env=clipboard_env,
    )
    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "copied" in output
