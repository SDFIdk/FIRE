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

@ts.command()
@click.argument("tidsserie", required=True, type=str)
@click.option(
    "--plottype",
    "-t",
    required=False,
    type=click.Choice(["rå", "fit", "konf"]),
    default="rå",
    help="Hvilken type plot vil man se?",
)
@click.option(
    "--parametre",
    "-p",
    required=False,
    type=str,
    default="kote",
    help="Hvilken parameter skal plottes?",
)
@fire.cli.default_options()
def plot_hts(tidsserie: str, plottype: str, parametre: str, **kwargs) -> None:
    """
    Plot en Højdetidsserie.

    Et simpelt plot der som standard viser kotens udvikling over tid.

    "TIDSSERIE" er et Højdetidsserienavn fra FIRE. Eksisterende Højdetidsserier kan
    fremsøges med kommandoen ``fire ts hts <punktnummer>``.
    Hvilke parametre der plottes kan specificeres i en kommasepareret liste med
    ``--parametre``. Højst 3 parametre plottes. Følgende parametre kan vælges::

    \b
        t               Tidspunkt for koordinatobservation
        kote            Koordinatens z-komponent
        sz              z-komponentens (kotens) spredning (i mm)
        decimalår       Tidspunkt for koordinatobservation i decimalår

    Typen af plot som vises kan vælges med ``--plottype``. Følgende plottyper kan vælges::

    \b
        rå              Plot rå data
        fit             Plot lineær regression oven på de rå data
        konf            Plot lineær regression med konfidensbånd

    \f
    **EKSEMPLER:**

    Plot af højdetidsserie for GED3::

        fire ts plot-hts 52-03-00846_HTS_81005

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_hts_GED3_HTS_81005.png
        :width: 800
        :alt: Eksempel på plot af højde-tidsserie for GED3.

    Plot af højdetidsserie for GED2::

        fire ts plot-hts 52-03-00845_HTS_81050 -t fit

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_hts_GED2_HTS_81050_fit.png
        :width: 800
        :alt: Eksempel på plot af højde-tidsserie for GED2.

    Plot af højdetidsserie for GED5::

        fire ts plot-hts 52-03-09089_HTS_81068 -t konf

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_hts_GED5_HTS_81068_konf.png
        :width: 800
        :alt: Eksempel på plot af højde-tidsserie for GED5.

    """
    plot_funktioner = {
        "rå": plot_data,
        "fit": plot_fit,
        "konf": plot_konfidensbånd,
    }

    try:
        tidsserie = _find_tidsserie(HøjdeTidsserie, tidsserie)
    except NoResultFound:
        raise SystemExit("Højdetidsserie ikke fundet")

    parametre = parametre.split(",")

    for parm in parametre:
        if parm not in HTS_PARAMETRE.keys():
            raise SystemExit(f"Ukendt tidsserieparameter '{parm}'")

    parametre = [HTS_PARAMETRE[parm] for parm in parametre]

    plot_tidsserie(tidsserie, plot_funktioner[plottype], parametre, y_enhed="mm")

