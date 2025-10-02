import inspect
import json
import logging
from importlib.metadata import PackageNotFoundError, entry_points, version

import typer
import yaml
from typer import Typer

from .chat2prompt import chat2prompt_command
from .codex_task import codex_task_command
from .files import files_command
from .merge_checks import merge_checks_command

try:
    __version__ = version("f2clipboard")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+dev"

app = Typer(add_completion=False, help="Flows \u2192 clipboard automation CLI")
app.command("codex-task")(codex_task_command)
app.command("chat2prompt")(chat2prompt_command)
app.command("files")(files_command)
app.command("merge-checks")(merge_checks_command)

_loaded_plugins: list[str] = []
_plugin_versions: dict[str, str] = {}
_plugin_paths: dict[str, str] = {}


@app.command("plugins")
def plugins_command(
    json_output: bool = typer.Option(
        False, "--json", help="Output plugin names as JSON."
    ),
    yaml_output: bool = typer.Option(
        False, "--yaml", help="Output plugin names as YAML."
    ),
    count: bool = typer.Option(
        False, "--count", help="Print the number of installed plugins."
    ),
    versions: bool = typer.Option(False, "--versions", help="Show plugin versions."),
    paths: bool = typer.Option(False, "--paths", help="Show plugin source file paths."),
    sort: bool = typer.Option(
        False, "--sort", help="Sort plugin names alphabetically."
    ),
    reverse: bool = typer.Option(False, "--reverse", help="Reverse plugin order."),
    filter_: str | None = typer.Option(
        None, "--filter", help="Only include plugin names containing this substring."
    ),
    ignore_case: bool = typer.Option(
        False, "--ignore-case", help="Filter plugin names case-insensitively."
    ),
) -> None:
    """List registered plugin names, counts, versions or paths."""

    if json_output and yaml_output:
        typer.echo("--json and --yaml cannot be used together", err=True)
        raise typer.Exit(code=1)

    serializer = None
    if json_output:
        serializer = json.dumps
    elif yaml_output:

        def serializer(obj: object) -> str:  # type: ignore[redefined-outer-name]
            return yaml.safe_dump(obj, sort_keys=False)

    def _echo_serialized(obj: object) -> None:
        if serializer:
            typer.echo(serializer(obj))

    if not _loaded_plugins:
        if count and serializer:
            payload = {"count": 0, "plugins": {} if versions or paths else []}
            _echo_serialized(payload)
        elif count:
            typer.echo("0")
        elif serializer:
            empty = {} if (versions or paths) else []
            _echo_serialized(empty)
        else:
            typer.echo("No plugins installed")
        return

    names = list(_loaded_plugins)
    if filter_:
        if ignore_case:
            needle = filter_.lower()
            names = [name for name in names if needle in name.lower()]
        else:
            names = [name for name in names if filter_ in name]

    if not names:
        if count and serializer:
            payload = {"count": 0, "plugins": {} if versions or paths else []}
            _echo_serialized(payload)
        elif count:
            typer.echo("0")
        elif serializer:
            empty = {} if (versions or paths) else []
            _echo_serialized(empty)
        else:
            typer.echo("No plugins installed")
        return

    if sort:
        names = sorted(names)
    if reverse:
        names = list(reversed(names))

    def _build_data() -> object:
        if versions and paths:
            return {
                name: {
                    "version": _plugin_versions.get(name, "unknown"),
                    "path": _plugin_paths.get(name, "unknown"),
                }
                for name in names
            }
        if versions:
            return {name: _plugin_versions.get(name, "unknown") for name in names}
        if paths:
            return {name: _plugin_paths.get(name, "unknown") for name in names}
        return names

    if count and serializer:
        payload = {"count": len(names), "plugins": _build_data()}
        _echo_serialized(payload)
    elif count:
        typer.echo(str(len(names)))
    elif serializer:
        _echo_serialized(_build_data())
    elif versions and paths:
        for name in names:
            typer.echo(
                f"{name} {_plugin_versions.get(name, 'unknown')} {_plugin_paths.get(name, 'unknown')}"
            )
    elif versions:
        for name in names:
            typer.echo(f"{name} {_plugin_versions.get(name, 'unknown')}")
    elif paths:
        for name in names:
            typer.echo(f"{name} {_plugin_paths.get(name, 'unknown')}")
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
            try:
                _plugin_paths[ep.name] = inspect.getfile(plugin)
            except TypeError:  # pragma: no cover - built-in or C extension
                _plugin_paths[ep.name] = "unknown"
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
