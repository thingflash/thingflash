from __future__ import annotations

from typer.testing import CliRunner

from thingflash import __version__
from thingflash.cli.main import app

runner = CliRunner()


def test_version_flag_reports_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_shows_program_name() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "thingflash" in result.stdout.lower()


def test_no_args_is_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Usage" in result.stdout
