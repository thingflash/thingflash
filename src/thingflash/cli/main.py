from __future__ import annotations

import typer

from thingflash import __version__
from thingflash.cli.commands import certificates, mqtt, project, shadow, things
from thingflash.cli.common import ExitCode
from thingflash.cli.output import econsole
from thingflash.core.errors import ManifestValidationError, ThingFlashError

app = typer.Typer(
    name="thingflash",
    help="Production-ready AWS IoT infrastructure from a declarative YAML manifest.",
    no_args_is_help=True,
    add_completion=True,
    pretty_exceptions_show_locals=False,
)

project.register(app)
app.add_typer(things.app, name="things", help="Manage AWS IoT Things (your devices).")
app.add_typer(
    certificates.app,
    name="certificates",
    help="Manage AWS IoT certificates (your device certificates).",
)
app.add_typer(shadow.app, name="shadow", help="Manage AWS IoT Device Shadows.")
app.add_typer(mqtt.app, name="mqtt", help="Publish to and test AWS IoT MQTT topics.")


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


def entrypoint() -> None:
    """Console-script entry point: run the app and translate ThingFlash errors."""
    try:
        app()
    except ThingFlashError as e:
        econsole.print(f"[red]Error: [{e.code}] {e.message}[/red]")
        if e.hint:
            econsole.print(f"[yellow]Hint: {e.hint}[/yellow]")
        code = (
            ExitCode.VALIDATION_FAILED if isinstance(e, ManifestValidationError) else ExitCode.ERROR
        )
        raise SystemExit(code) from e


if __name__ == "__main__":
    entrypoint()
