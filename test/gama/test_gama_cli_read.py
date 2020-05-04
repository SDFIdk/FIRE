import click
import pytest

from click.testing import CliRunner
from fire.cli.gama import gama


@pytest.mark.skip("Undlades indtil et bedre test datasæt er indlæst i databasen")
def test_cli():
    runner = CliRunner()

    title = "Read all points"
    args = [
        "read",
        "-i",
        "input/near_geometry.xml",
        "-c",
        "4f8f29c8-c38f-4c69-ae28-c7737178de1f",
    ]

    click.echo("\nTest: " + title)
    click.echo(" Emulating: python gama " + " ".join(args))
    result = runner.invoke(gama, args)

    assert result.exit_code
