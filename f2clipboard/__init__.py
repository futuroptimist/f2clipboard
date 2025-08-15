import json
import logging
from importlib.metadata import PackageNotFoundError, entry_points, version

import typer
from typer import Typer

from .chat2prompt import chat2prompt_command
from .codex_task import codex_task_command
from .files import files_command

try:
    __version__ = version("f2clipboard")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+dev"

app = Typer(add_completion=False, help="Flows \u2192 clipboard automation CLI")
app.command("codex-task")(codex_task_command)
app.command("chat2prompt")(chat2prompt_command)
app.command("files")(files_command)

_loaded_plugins: list[str] = []


@app.command("plugins")
def plugins_command(
    json_output: bool = typer.Option(
        False, "--json", help="Output plugin names as JSON."
    ),
    count: bool = typer.Option(
        False, "--count", help="Print the number of installed plugins."
    ),
) -> None:
    """List registered plugin names or counts."""
    if not _loaded_plugins:
        if count:
            typer.echo("0")
        elif json_output:
            typer.echo("[]")
        else:
            typer.echo("No plugins installed")
        return
    if count:
        typer.echo(str(len(_loaded_plugins)))
    elif json_output:
        typer.echo(json.dumps(_loaded_plugins))
    else:
        for name in _loaded_plugins:
            typer.echo(name)


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
            if ep.name not in _loaded_plugins:
                _loaded_plugins.append(ep.name)
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
