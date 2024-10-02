from datetime import datetime

import click
import pandas as pd
from sqlalchemy.exc import NoResultFound

import fire.cli
from fire.api.model import (
    Tidsserie,
    HøjdeTidsserie,
)
from fire.cli.ts import (
    _find_tidsserie,
    _udtræk_tidsserie,
)
from fire.cli.ts.statistik_ts import (
    StatistikHts,
    beregn_statistik_til_hts_rapport,
)
from fire.cli.ts.plot_ts import (
    plot_tidsserie,
    plot_data,
    plot_fit,
    plot_konfidensbånd,
)

from . import ts

HTS_PARAMETRE = {
    "t": "t",
    "decimalår": "decimalår",
    "kote":"kote",
    "sz": "sz",
}


@ts.command()
@click.argument("objekt", required=True, type=str)
@click.option(
    "--parametre",
    "-p",
    required=False,
    type=str,
    default="t,decimalår,kote,sz",
    help="""Vælg hvilke parametre i tidsserien der skal udtrækkes. Som standard
sat til 't,decimalår,kote,sz'. Bruges værdien 'alle' udtrækkes alle mulige parametre
i tidsserien.  Se ``fire ts hts --help`` for yderligere detaljer.""",
)
@click.option(
    "--fil",
    "-f",
    required=False,
    type=click.Path(writable=True),
    help="Skriv den udtrukne tidsserie til Excel fil.",
)
@fire.cli.default_options()
def hts(objekt: str, parametre: str, fil: click.Path, **kwargs) -> None:
    """
    Udtræk en Højdetidsserie.


    "OBJEKT" sættes til enten et punkt eller et specifik navngiven tidsserie.
    Hvis "OBJEKT" er et punkt udskrives en oversigt over de tilgængelige
    tidsserier til dette punkt. Hvis "OBJEKT" er en tidsserie udskrives
    tidsserien på skærmen. Hvilke parametre der udskrives kan specificeres
    i en kommasepareret liste med ``--parametre``. Følgende parametre kan vælges::

    \b
        t               Tidspunkt for koordinatobservation
        decimalår       Tidspunkt for koordinatobservation i decimalår
        kote            Koordinatens z-komponent
        sz              z-komponentens (kotens) spredning (i mm)

    Tidsserien kan skrives til en fil ved brug af ``--fil``, der resulterer i
    en csv-fil på den angivne placering. Denne fil kan efterfølgende åbnes
    i Excel, eller et andet passende program, til videre analyse.

    \b
    **EKSEMPLER**

    Vis alle tidsserier for punktet RDIO::

        fire ts hts RDIO

    Vis tidsserien "K-63-00909_HTS_81066" med standardparametre::

        fire ts hts K-63-00909_HTS_81066

    Vis tidsserie med brugerdefinerede parametre::

        fire ts hts K-63-00909_HTS_81066 --parametre decimalår,kote,sz

    Gem tidsserie med samtlige tilgængelige parametre::

        fire ts hts K-63-00909_HTS_81066 -p alle -f RDIO_HTS_81066.xlsx
    """
    _udtræk_tidsserie(objekt, HøjdeTidsserie, HTS_PARAMETRE, parametre, fil)

    return
