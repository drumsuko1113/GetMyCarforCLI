from __future__ import annotations

from click.testing import CliRunner

from getmycar import __version__
from getmycar.main import cli


def test_version_is_set() -> None:
    assert __version__


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "getmycar" in result.output.lower()
