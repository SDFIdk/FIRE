import click
from click.testing import CliRunner

from fire.cli.info import srid


def test_info_srid_alle():
    runner = CliRunner()

    args = ["--monokrom"]  # fjern formatering af output
    result = runner.invoke(srid, args)

    assert result.exit_code == 0

    forventet_output = """DK:TEST             SRID til brug i test-suite
EPSG:5799           Kotesystem: Dansk Vertikal Reference 1990\n"""

    assert result.output == forventet_output

    args = ["-T", "--monokrom"]  # fjern formatering af output
    result = runner.invoke(srid, args)

    assert result.exit_code == 0
    # samme output forventes, da der ikke er TS: srid'er i testdatasættet
    assert result.output == forventet_output


def test_info_srid():
    runner = CliRunner()

    args = ["DK:TEST", "--monokrom"]  # fjern formatering af output
    result = runner.invoke(srid, args)

    assert result.exit_code == 0

    forventet_output = """--- SRID ---
 Name:       :  DK:TEST
 Description :  SRID til brug i test-suite\n"""

    assert result.output == forventet_output
