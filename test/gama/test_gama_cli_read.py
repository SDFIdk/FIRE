import click
from click.testing import CliRunner

from fire.cli.gama import gama
from fire.api.model import Sag


def test_cli(sag: Sag):
    runner = CliRunner()

    title = "Read all points"
    args = [
        "read",
        "-i",
        "input/near_geometry.xml",
        "-c",
        sag.id,
    ]

    click.echo("\nTest: " + title)
    click.echo(" Emulating: python gama " + " ".join(args))
    result = runner.invoke(gama, args)

    assert result.exit_code
