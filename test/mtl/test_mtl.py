import click
import pytest

from click.testing import CliRunner
from fire.cli.mtl import mtl


def test_cli():
    runner = CliRunner()

    title = "go"
    args = ["go", "bananas"]

    click.echo("\nTest: " + title)
    click.echo(" Emulating: python mtl " + " ".join(args))
    result = runner.invoke(mtl, args)

    assert result.exit_code == 0
