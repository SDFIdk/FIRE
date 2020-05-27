from click.testing import CliRunner

from fire.cli.info import srid, obstype


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


def test_info_obstype():
    runner = CliRunner()

    args = ["geometrisk_koteforskel", "--monokrom"]  # fjern formatering af output
    result = runner.invoke(obstype, args)

    forventet_output = """--- OBSERVATIONSTYPE ---
  Navn        :  geometrisk_koteforskel
  Beskrivelse :  Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt geometrisk
  Værdi1      :  Koteforskel [m]
  Værdi2      :  Nivellementslængde [m]
  Værdi3      :  Antal opstillinger
  Værdi4      :  Variabel vedr. eta_1 (refraktion) [m^3]
  Værdi5      :  Afstandsafhængig varians koteforskel pr. målt koteforskel [m^2/m]
  Værdi6      :  Afstandsuafhængig varians koteforskel pr. målt koteforskel [m^2]
  Værdi7      :  Præcisionsnivellement [0,1,2,3]
  Sigtepunkt? :  True
"""
    assert result.output == forventet_output
    assert result.exit_code == 0

    args = ["findes_ikke", "--monokrom"]  # fjern formatering af output
    result = runner.invoke(obstype, args)

    assert result.exit_code == 1


def test_info_obstype_alle():
    runner = CliRunner()

    args = ["--monokrom"]  # fjern formatering af output
    result = runner.invoke(obstype, args)

    forventet_output = """geometrisk_koteforskel        Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt geometrisk
trigonometrisk_koteforskel    Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt...
retning                       Horisontal retning med uret fra opstilling til sigtepunkt...
horisontalafstand             Horisontal afstand mellem opstilling og sigtepunkt (reduceret til...
skråafstand                   Skråafstand mellem opstilling og sigtepunkt
zenitvinkel                   Zenitvinkel mellem opstilling og sigtepunkt
vektor                        Vektor der beskriver koordinatforskellen fra punkt 1 til punkt 2...
nulobservation                observation nummer nul, indlagt fra start i observationstabellen,...
"""
    assert result.output == forventet_output
