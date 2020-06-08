import traceback

import click
from click.testing import CliRunner
from pytest import approx

import fire
from fire.cli.gama import gama
from fire.api import FireDb
from fire.api.model import Sag


def _run_cli(runner, title, args):
    click.echo("\nTest: " + title)
    click.echo(" Emulating: python gama " + " ".join(args))

    result = runner.invoke(gama, args)

    if result.exit_code != 0:
        click.echo(" Failed: " + str(args))
        click.echo(" Exception: " + str(result.exception))
        click.echo(" Output: " + str(result.output))
        click.echo(" Traceback:")
        traceback.print_tb(result.exc_info[2])
        return False
    else:
        click.echo(" Success: " + str(args))
        return True


def test_cli(firedb: FireDb, sag: Sag):
    firedb.session.add(sag)
    firedb.session.commit()
    runner = CliRunner()

    title = "Read all points"
    args = [
        "read",
        "-i",
        "test/gama/input/near_geometry.xml",
        "-c",
        sag.id,
    ]

    assert _run_cli(runner, title, args)

    sag = firedb.hent_sag(sag.id)

    for koordinat in sag.sagsevents[-1].koordinater:
        if koordinat.punkt.ident == "SKEJ":
            assert koordinat.z == approx(72.0285)

        if koordinat.punkt.ident == "RDIO":
            assert koordinat.z == approx(85.1816)

        if koordinat.punkt.ident == "RDO1":
            assert koordinat.z == approx(86.1778)
