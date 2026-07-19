import typer

from thingflash.cli import output
from thingflash.cli.common import OutputFormat, OutputOption, YesOption
from thingflash.core import registry

app = typer.Typer(no_args_is_help=True)


@app.command("list", help="List all things.")
def list_things(out: OutputFormat = OutputOption) -> None:
    """List all Things managed by this project."""
    things = registry.list_things()
    output.render_things(things, out, table_columns=["name", "thing_type", "cert_expiry"])


@app.command("create", help="Create a new thing.")
def create_thing(
    name: str = typer.Argument(..., help="The name of the thing to create."),
    out: OutputFormat = OutputOption,
) -> None:
    """Create a new Thing."""
    thing = registry.create_thing(name)
    output.render(thing, out)


@app.command("delete", help="Delete a thing.")
def delete_thing(
    name: str = typer.Argument(..., help="The name of the thing to delete."),
    yes: bool = YesOption,
    out: OutputFormat = OutputOption,
) -> None:
    """Delete a Thing."""
    output.confirm_or_exit(f"Delete Thing '{name}' and detach its certificates?", yes=yes)
    registry.delete_thing(name)
    output.success(f"Thing '{name}' deleted.")
