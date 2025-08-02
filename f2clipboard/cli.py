"""Command line entrypoint for f2clipboard."""

from . import app


def main() -> None:
    """Run the Typer application."""
    app()


if __name__ == "__main__":
    main()
