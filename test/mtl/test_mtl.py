import os

import click
import pytest

from click.testing import CliRunner
from fire.cli.mtl import mtl


@pytest.mark.filterwarnings("ignore:kurtosistest only valid for n>=20")
def test_cli():
    runner = CliRunner()

    title = "go"
    args = ["go", "bananas"]

    click.echo("\nTest: " + title)
    click.echo(" Emulating: fire mtl " + " ".join(args))

    cwd = os.getcwd()
    # As os.chdir(os.path.dirname(__file__)), but using the absolute path
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    result = runner.invoke(mtl, args)
    os.remove("resultat.xlsx")
    os.chdir(cwd)

    assert result.exit_code == 0
