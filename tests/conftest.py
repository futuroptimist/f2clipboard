import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def temp_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "src"))
        os.makedirs(os.path.join(tmpdir, "assets"))

        with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
            f.write("test content 1")
        with open(os.path.join(tmpdir, "src/file2.py"), "w") as f:
            f.write("test content 2")
        with open(os.path.join(tmpdir, "src/app.js"), "w") as f:
            f.write("test content 3")
        with open(os.path.join(tmpdir, "src/styles.css"), "w") as f:
            f.write("test content 4")

        with open(os.path.join(tmpdir, "assets/test.jpg"), "wb") as f:
            f.write(b"fake jpg content")
        with open(os.path.join(tmpdir, "assets/icon.png"), "wb") as f:
            f.write(b"fake png content")

        with open(os.path.join(tmpdir, ".gitignore"), "w") as f:
            f.write("*.log\nnode_modules/\n")

        yield tmpdir
