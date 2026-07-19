"""ThingFlash CLI entry point."""

from __future__ import annotations

import typer

from thingflash import __version__

app = typer.Typer(
    name="thingflash",
    help="Production-ready AWS IoT infrastructure from a declarative YAML manifest.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"thingflash {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the ThingFlash version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """ThingFlash command-line interface."""


if __name__ == "__main__":
    app()
