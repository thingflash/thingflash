import enum
from dataclasses import dataclass
from pathlib import Path

import typer


class ExitCode(enum.IntEnum):
    OK = 0
    ERROR = 1
    VALIDATION_FAILED = 2
    APPROVAL_REQUIRED = 3
    PARTIAL_FAILURE = 4


class OutputFormat(enum.StrEnum):
    table = "table"
    json = "json"


@dataclass
class GlobalOpts:
    output: OutputFormat
    yes: bool
    manifest_path: Path


OutputOption = typer.Option(
    OutputFormat.table, "--output", "-o", help="Output format. Default: table."
)
YesOption = typer.Option(False, "--yes", "-y", help="Answer yes to all prompts. Default: false.")
ManifestOption = typer.Option(Path("thingflash.yaml"), "--manifest", "-f")
