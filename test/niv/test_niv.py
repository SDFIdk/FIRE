from pathlib import Path

import numpy as np
import pandas as pd
from click.testing import CliRunner

from fire.io.regneark import arkdef
from fire.cli.niv import (
    niv,
    find_faneblad,
    skriv_ark,
)


def test_revision(mocker):
    """Test fire niv kommandoer relateret til punktrevision"""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # fire niv opret-sag test
        mocker.patch("fire.cli.niv._opret_sag.bekræft", return_value=True)
        result = runner.invoke(niv, ["opret-sag", "testsag", "This is only a test"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv udtræk-revision test
        result = runner.invoke(niv, ["udtræk-revision", "testsag", "k-63", "SKEJ"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv ilæg-revision test
        mocker.patch("fire.cli.niv._ilæg_revision.bekræft", return_value=True)
        result = runner.invoke(niv, ["ilæg-revision", "testsag"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv ilæg-nye-punkter test
        nyetablerede = find_faneblad(
            "testsag", "Nyetablerede punkter", arkdef.NYETABLEREDE_PUNKTER
        )

        nyt_punkt = {
            "Foreløbigt navn": "Dokk1",
            "Nord": 56.176809,
            "Øst": 10.22475,
            "Fikspunktstype": "Højde",
            "Beskrivelse": "Testpunkt",
            "Afmærkning": "Bolt",
            "Højde_over_terræn": 1.32,
        }
        df_nyt_punkt = pd.DataFrame(data=[nyt_punkt.values()], columns=nyt_punkt.keys())
        nyetablerede = pd.concat([nyetablerede, df_nyt_punkt], ignore_index=True)
        skriv_ark("testsag", {"Nyetablerede punkter": nyetablerede})

        mocker.patch("fire.cli.niv._ilæg_nye_punkter.bekræft", return_value=True)
        result = runner.invoke(niv, ["ilæg-nye-punkter", "testsag"])
        print(result.output)
        print(result)
        assert result.exit_code == 0

        # fire niv luk-sag test
        mocker.patch("fire.cli.niv._luk_sag.bekræft", return_value=True)
        result = runner.invoke(niv, ["luk-sag", "testsag"])
        print(result.output)
        assert result.exit_code == 0


def test_observationer(mocker):
    """Test fire niv kommandoer relateret til punktrevision"""
    runner = CliRunner()

    used_files = ["obs_mgl"]
    files = []
    for filename in used_files:
        with open(Path(__file__).resolve().parent / filename) as f:
            files.append((filename, f.readlines()))

    with runner.isolated_filesystem():
        # kopier filer til isoleret filsystem
        for filename, data in files:
            with open(filename, "w") as f:
                f.writelines(data)

        # fire niv opret-sag test
        mocker.patch("fire.cli.niv._opret_sag.bekræft", return_value=True)
        result = runner.invoke(niv, ["opret-sag", "testsag", "This is only a test"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv læs-observationer test
        inputfiler = find_faneblad("testsag", "Filoversigt", arkdef.FILOVERSIGT)
        fil = {
            "Filnavn": "obs_mgl",
            "Type": "MGL",
            "σ": 0.7,
            "δ": 0.02,
        }
        df_fil = pd.DataFrame(data=[fil.values()], columns=fil.keys())
        inputfiler = pd.concat([inputfiler, df_fil], ignore_index=True)
        skriv_ark("testsag", {"Filoversigt": inputfiler})

        result = runner.invoke(niv, ["læs-observationer", "testsag"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv ilæg-observationer test
        mocker.patch("fire.cli.niv._ilæg_observationer.bekræft", return_value=True)
        result = runner.invoke(niv, ["ilæg-observationer", "testsag"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv luk-sag test
        mocker.patch("fire.cli.niv._luk_sag.bekræft", return_value=True)
        result = runner.invoke(niv, ["luk-sag", "testsag"])
        print(result)
        print(result.output)
        assert result.exit_code == 0


def _check_fastholdt(df, ark, punkt):
    return df[ark].loc[df[ark]["Punkt"] == punkt]["Fasthold"].values[0] != ""


def _check_tom_kote(df, ark, punkt):
    # pandas opfatter tomme celler som NaN når de tilgås via .values
    return np.isnan(df[ark].loc[df[ark]["Punkt"] == punkt]["Ny kote"].values[0])


def _sammenlign_kolonner(df, ark1, ark2, kolonnenavn):
    return df[ark1][kolonnenavn].equals(df[ark2][kolonnenavn])


def test_regn():
    """Test fire niv kommandoer relateret til punktrevision

    Sagen "test_regn" er på forhånd oprettet uden om databasen, hvilket gør det
    muligt at benytte udjævningsfunktionaliteten i `fire niv` uden sagsoprettelse
    m.m.
    """
    fastholdte_punkter = [
        "101-01-09014",
        "102-02-09004",
        "103-04-00815",
        "98-07-00010",
    ]
    runner = CliRunner()

    filename = "test_regn.xlsx"
    with open(Path(__file__).resolve().parent / filename, "rb") as f:
        filedata = f.read()

    with runner.isolated_filesystem():
        # kopier filer til isoleret filsystem
        with open(filename, "wb") as f:
            f.write(filedata)

        # kontrolberegning
        result = runner.invoke(niv, ["regn", "test_regn"])
        print(result.output)
        assert result.exit_code == 0

        regneark = pd.read_excel(filename, sheet_name=None)
        # Er de forventede faneblad oprettet?
        assert "Kontrolberegning" in regneark.keys()
        assert "Singulære" in regneark.keys()
        assert "Netgeometri" in regneark.keys()

        # Sanity check på tværs af faneblade
        assert _sammenlign_kolonner(
            regneark, "Punktoversigt", "Kontrolberegning", "Fasthold"
        )
        for punkt in fastholdte_punkter:
            assert _check_fastholdt(regneark, "Kontrolberegning", punkt)
            assert _check_tom_kote(regneark, "Kontrolberegning", punkt)

        regneark = None
        del regneark

        # endelig beregning
        fastholdte_punkter.extend(["101-02-09023", "102-03-09170"])
        faneblad = find_faneblad("test_regn", "Kontrolberegning", arkdef.PUNKTOVERSIGT)
        faneblad.loc[faneblad["Punkt"] == "101-02-09023", "Fasthold"] = "e"
        faneblad.loc[faneblad["Punkt"] == "102-03-09170", "Fasthold"] = "e"
        skriv_ark("test_regn", {"Kontrolberegning": faneblad})

        result = runner.invoke(niv, ["regn", "test_regn"])
        print(result.output)
        assert result.exit_code == 0

        regneark = pd.read_excel(filename, sheet_name=None)
        # Er de forventede faneblad oprettet?
        assert "Endelig beregning" in regneark.keys()
        assert "Kontrolberegning" in regneark.keys()
        assert "Singulære" in regneark.keys()
        assert "Netgeometri" in regneark.keys()

        for punkt in fastholdte_punkter:
            assert _check_fastholdt(regneark, "Endelig beregning", punkt)
            assert _check_tom_kote(regneark, "Endelig beregning", punkt)
