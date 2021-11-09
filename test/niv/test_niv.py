from pathlib import Path

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
        nyetablerede = nyetablerede.append(nyt_punkt, ignore_index=True)
        skriv_ark("testsag", {"Nyetablerede punkter": nyetablerede})

        mocker.patch("fire.cli.niv._ilæg_nye_punkter.bekræft", return_value=True)
        result = runner.invoke(niv, ["ilæg-nye-punkter", "testsag"])
        print(result.output)
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
        for (filename, data) in files:
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
        inputfiler = inputfiler.append(fil, ignore_index=True)
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
        print(result.output)
        assert result.exit_code == 0
