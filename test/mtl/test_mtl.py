from shutil import copy
import os

import click
import pytest

from click.testing import CliRunner
from fire.cli.mtl import mtl


def test_cli():
    runner = CliRunner()

    title = "go"
    args = ["go", "bananas"]

    # Lidt bannerlarm
    click.echo("\nTest: " + title)
    click.echo(" Emulating: fire mtl " + " ".join(args))

    # Kildefilerne ligger samme sted som testkodefilen
    source_dir = os.path.dirname(os.path.abspath(__file__))

    # Kopier nødvendige filer til isoleret filsystem og kør så testen derfra
    with runner.isolated_filesystem():
        # Roden i det isolerede filsystem
        dest_dir = os.getcwd()
        for filename in ("bananas.xlsx", "bananas.obs", "resultat_canonical.xlsx"):
            copy(source_dir + "/" + filename, dest_dir)
        result = runner.invoke(mtl, args)

    # Lav lidt larm om hvorvidt resulatet var succesfuldt
    if result.exit_code != 0:
        click.echo(" Failed: " + str(args))
        click.echo(" Exception: " + str(result.exception))
        click.echo(" Output: " + str(result.output))
        return False
    else:
        click.echo(" Success: " + str(args))
        return True
