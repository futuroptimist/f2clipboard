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
_plugin_versions: dict[str, str] = {}


@app.command("plugins")
def plugins_command(
    json_output: bool = typer.Option(
        False, "--json", help="Output plugin names as JSON."
    ),
    count: bool = typer.Option(
        False, "--count", help="Print the number of installed plugins."
    ),
    versions: bool = typer.Option(False, "--versions", help="Show plugin versions."),
    sort: bool = typer.Option(
        False, "--sort", help="Sort plugin names alphabetically."
    ),
    filter_: str | None = typer.Option(
        None, "--filter", help="Only include plugin names containing this substring."
    ),
    ignore_case: bool = typer.Option(
        False, "--ignore-case", help="Filter plugin names case-insensitively."
    ),
) -> None:
    """List registered plugin names, counts or versions."""

    # No plugins loaded at all: mirror existing behavior
    if not _loaded_plugins:
        count_value = 0
        if count and json_output:
            typer.echo(json.dumps({"count": count_value}))
        elif count:
            typer.echo("0")
        elif json_output:
            typer.echo("{}" if versions else "[]")
        else:
            typer.echo("No plugins installed")
        return

    # Start from loaded plugins, then apply filter & sort deterministically
    names = list(_loaded_plugins)
    if filter_:
        if ignore_case:
            needle = filter_.lower()
            names = [name for name in names if needle in name.lower()]
        else:
            names = [name for name in names if filter_ in name]

    # If filter removes everything, mirror empty behavior again
    if not names:
        if count and json_output:
            typer.echo(json.dumps({"count": 0}))
        elif count:
            typer.echo("0")
        elif json_output:
            typer.echo("{}" if versions else "[]")
        else:
            typer.echo("No plugins installed")
        return

    if sort:
        names = sorted(names)

    # Counts should reflect the (possibly filtered) list.
    if count and json_output:
        typer.echo(json.dumps({"count": len(names)}))
    elif count:
        typer.echo(str(len(names)))
    elif json_output:
        if versions:
            data = {name: _plugin_versions.get(name, "unknown") for name in names}
            typer.echo(json.dumps(data))
        else:
            typer.echo(json.dumps(names))
    elif versions:
        for name in names:
            typer.echo(f"{name} {_plugin_versions.get(name, 'unknown')}")
    else:
        for name in names:
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
            if ep.name in _loaded_plugins:
                # Skip already loaded plugins to avoid duplicate command registration
                continue
            plugin = ep.load()
            plugin(app)
            _loaded_plugins.append(ep.name)
            dist = getattr(ep, "dist", None)
            _plugin_versions[ep.name] = getattr(dist, "version", "unknown")
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
