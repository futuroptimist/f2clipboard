import logging
from importlib.metadata import PackageNotFoundError, entry_points, version

import typer
from typer import Typer, rich_utils

from .chat2prompt import chat2prompt_command
from .codex_task import codex_task_command
from .files import files_command

try:
    __version__ = version("f2clipboard")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+dev"

# Ensure CLI help renders at a reasonable width even when the terminal reports
# a very small value (e.g. ``COLUMNS=1``).  Typer uses a global Rich console for
# formatting help text; overriding it with an explicit width avoids breaking
# option strings across lines, which caused tests looking for ``--clipboard``
# to fail when the environment specified an extremely narrow terminal.
# Typer uses ``MAX_WIDTH`` to determine help text width. Setting a reasonable
# default avoids issues when the environment reports an unworkably small number
# of columns (e.g. ``COLUMNS=1``), which previously split option names across
# lines and broke tests that inspected the help text.
rich_utils.MAX_WIDTH = 80

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
