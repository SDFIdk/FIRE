from shutil import copy
import os

import click
import pytest

from click.testing import CliRunner
import fire.cli.niv
from fire.cli.niv import (
    niv,
    find_faneblad,
    skriv_ark,
    ARKDEF_NYETABLEREDE_PUNKTER,
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
        result = runner.invoke(niv, ["udtræk-revision", "testsag", "K-63"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv ilæg-revision test
        mocker.patch("fire.cli.niv._ilæg_revision.bekræft", return_value=True)
        result = runner.invoke(niv, ["ilæg-revision", "testsag"])
        print(result.output)
        assert result.exit_code == 0

        # fire niv ilæg-nye-punkter test
        nyetablerede = find_faneblad(
            "testsag", "Nyetablerede punkter", ARKDEF_NYETABLEREDE_PUNKTER
        )

        nyt_punkt = {
            "Foreløbigt navn": "Dokk1",
            "Nord": 56.176809,
            "Øst": 10.22475,
            # "Etablereret dato": "2021-02-21",
            "Hvem": "Karl Smart",
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
