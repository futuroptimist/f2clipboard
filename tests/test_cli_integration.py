from unittest.mock import patch

import sys


def test_cli_yes(temp_directory):
    argv = ["-d", temp_directory, "-p", "*.txt", "--yes"]
    with patch("clipboard.copy") as mock_copy:
        from f2clipboard import main

        main(argv)
        assert mock_copy.called
