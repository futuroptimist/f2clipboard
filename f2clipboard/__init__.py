import logging
import shutil
from importlib.metadata import PackageNotFoundError, entry_points, version

import typer
from rich.console import Console
from typer import Typer, rich_utils

from .chat2prompt import chat2prompt_command
from .codex_task import codex_task_command
from .files import files_command

try:
    __version__ = version("f2clipboard")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+dev"

# Ensure CLI help renders at a reasonable width even when the terminal reports
# an extremely small value (e.g. ``COLUMNS=1``). Typer uses a global Rich
# console for formatting help text, and Rich clamps the width to the detected
# terminal size. Calculate a safe minimum width and replace the default console
# so option strings like ``--clipboard`` are not split across lines.
_MIN_WIDTH = 80
_width = max(shutil.get_terminal_size(fallback=(_MIN_WIDTH, 24)).columns, _MIN_WIDTH)
rich_utils.console = Console(width=_width)
rich_utils.MAX_WIDTH = _width

app = Typer(add_completion=False, help="Flows \u2192 clipboard automation CLI")
app.command("codex-task")(codex_task_command)
app.command("chat2prompt")(chat2prompt_command)
app.command("files")(files_command)


def _version_callback(value: bool) -> None:
    """Print the package version and exit."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Main entry point handling global options."""
    return


def _load_plugins() -> None:
    """Load registered entry-point plugins."""
    for ep in entry_points(group="f2clipboard.plugins"):
        try:
            plugin = ep.load()
            plugin(app)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).warning(
                "Failed to load plugin %s: %s", ep.name, exc
            )


_load_plugins()


def main(argv: list[str] | None = None) -> None:
    """Entry point for f2clipboard CLI."""
    app(prog_name="f2clipboard", args=argv)


if __name__ == "__main__":  # python -m f2clipboard …
    main()
