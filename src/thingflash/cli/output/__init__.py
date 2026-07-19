import json
import sys
from collections.abc import Sequence
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from thingflash.cli.common import ExitCode, OutputFormat

console = Console()
econsole = Console(stderr=True)


def render(data: Any, fmt: OutputFormat, table_columns: Sequence[str] | None = None) -> None:
    if fmt == OutputFormat.json:
        print(json.dumps(_to_dict(data), indent=2, default=str))
        return

    if isinstance(data, list) and table_columns:
        table = Table(*[c.replace("_", " ").title() for c in table_columns])
        for item in data:
            table.add_row(*[str(getattr(item, c, "")) for c in table_columns])
        console.print(table)
    else:
        console.print(data)


def render_things(
    things: Any, fmt: OutputFormat, table_columns: Sequence[str] | None = None
) -> None:
    """Render a list of Things as JSON or a table."""
    render(things, fmt, table_columns=table_columns)


def success(message: str) -> None:
    """Emit a success message to stderr so JSON stdout stays pure."""
    econsole.print(f"[green]{message}[/green]")


def render_init_result(result: Any, fmt: OutputFormat) -> None:
    """Render the outcome of `thingflash init`."""
    if fmt == OutputFormat.json:
        render(result, fmt)
        return

    console.print(f"[bold green]Initialized ThingFlash project '{result.project}'[/bold green]")
    for path in result.created:
        console.print(f"  [green]create[/green]  {path}")
    for path in result.updated:
        console.print(f"  [yellow]update[/yellow]  {path}")
    for path in result.skipped:
        console.print(f"  [dim]skip  [/dim]  {path}")
    console.print(
        "\nNext: [cyan]thingflash doctor[/cyan] -> "
        "[cyan]thingflash validate[/cyan] -> "
        "[cyan]thingflash plan[/cyan] -> [cyan]thingflash apply[/cyan]"
    )


def error(err: Any) -> None:
    """Render a ThingFlashError to stderr (code + message + optional hint)."""
    econsole.print(f"[red]Error: [{err.code}] {err.message}[/red]")
    if getattr(err, "hint", None):
        econsole.print(f"[yellow]Hint: {err.hint}[/yellow]")


def render_validate(manifest: Any, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        render({"valid": True, "project": manifest.metadata.name}, fmt)
        return
    name = manifest.metadata.name
    console.print(f"[green]Manifest is valid[/green] (project: [bold]{name}[/bold])")


def render_doctor(checks: Any, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        render(checks, fmt)
        return
    table = Table("Check", "Status", "Detail")
    styles = {"ok": "green", "warn": "yellow", "fail": "red"}
    for check in checks:
        style = styles.get(check.status, "white")
        detail = check.detail + (f" — {check.hint}" if check.hint else "")
        table.add_row(check.name, f"[{style}]{check.status.upper()}[/{style}]", detail)
    console.print(table)


def render_plan(plan: Any, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        render(plan, fmt)
        return
    styles = {"+": "green", "~": "yellow", "-": "red", " ": "dim"}
    for action in plan.actions:
        style = styles.get(action.prefix, "white")
        console.print(f"  [{style}]{action.prefix}[/{style}] {action.resource_type}  {action.name}")
    for warning in plan.warnings:
        econsole.print(f"[yellow]! {warning}[/yellow]")
    if not plan.has_changes:
        console.print("[dim]No changes. Infrastructure is up to date.[/dim]")
    else:
        console.print(f"\nPlan: [bold]{len(plan.changes)}[/bold] change(s).")


def render_apply(result: Any, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        render({"applied": result.applied, "changes": result.plan.changes}, fmt)
        return
    # The plan was already rendered before confirmation; only summarize here.
    if result.plan.has_changes:
        console.print(
            f"\n[bold green]Apply complete.[/bold green] {len(result.plan.changes)} change(s)."
        )


def render_destroy_preview(applied: Any, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json or not applied:
        return
    console.print("[bold]The following resources will be destroyed:[/bold]")
    for resource in applied:
        console.print(f"  [red]-[/red] {resource.type}  {resource.name}")


def render_status(applied: Any, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        render(applied, fmt)
        return
    if not applied:
        console.print("[dim]Nothing deployed yet. Run `thingflash apply`.[/dim]")
        return
    table = Table("Resource Type", "Name")
    for resource in applied:
        table.add_row(resource.type, resource.name)
    console.print(table)


def render_destroy(removed: Any, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        render({"removed": removed}, fmt)
        return
    if not removed:
        console.print("[dim]Nothing to destroy.[/dim]")
        return
    console.print(f"[bold]Destroyed[/bold] {len(removed)} resource(s).")


def confirm_or_exit(question: str, *, yes: bool) -> None:
    if yes:
        return
    if not sys.stdin.isatty():
        econsole.print("[red]Confirmation required but no TTY. Use --yes.[/red]")
        raise typer.Exit(ExitCode.APPROVAL_REQUIRED)
    if not typer.confirm(question):
        raise typer.Exit(ExitCode.APPROVAL_REQUIRED)


def _to_dict(data: Any) -> Any:
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if isinstance(data, dict):
        return {key: _to_dict(value) for key, value in data.items()}
    if isinstance(data, list):
        return [_to_dict(x) for x in data]
    if hasattr(data, "__dataclass_fields__"):
        import dataclasses

        return dataclasses.asdict(data)
    return data
