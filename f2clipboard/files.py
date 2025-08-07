"""Typer command wrapping the original local directory workflow."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import typer


def files_command(
    directory: str = typer.Option(
        ".", "--dir", help="Directory to search for files (default: current directory)"
    ),
    pattern: str = typer.Option(
        "*", "--pattern", help="File glob pattern to match (e.g. *.py)"
    ),
) -> None:
    """Invoke the legacy script to copy selected files to the clipboard."""
    script_path = Path(__file__).resolve().parent.parent / "f2clipboard.py"
    if not script_path.exists():
        typer.echo("Legacy script not found: f2clipboard.py", err=True)
        raise typer.Exit(code=1)

    dir_path = Path(directory)
    if not dir_path.exists():
        typer.echo(f"Directory not found: {directory}", err=True)
        raise typer.Exit(code=1)

    spec = spec_from_file_location("legacy_f2clipboard", script_path)
    if spec is None or spec.loader is None:  # pragma: no cover - importlib error
        typer.echo("Could not load legacy f2clipboard script", err=True)
        raise typer.Exit(code=1)

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(["--dir", directory, "--pattern", pattern])
