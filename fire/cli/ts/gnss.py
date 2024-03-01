from typing import Type
from datetime import datetime

import click
import pandas as pd
from rich.table import Table
from rich.console import Console
from rich import box
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound

import fire.cli
from fire.api.model import Tidsserie, HøjdeTidsserie, GNSSTidsserie, Punkt
from fire.cli.ts._plot_gnss import (
    plot_gnss_ts,
    plot_gnss_analyse,
    plot_data,
    plot_fit,
    plot_konfidensbånd,
    GNSS_TS_PLOTTING_LABELS,
)

from . import ts


def _print_tidsserieoversigt(tidsserieklasse: Type, punkt: Punkt = None):
    """
    Oversigt over tidsserier af en bestemt types

    raises:     SystemExit
    """
    if punkt:
        tidsserier = [ts for ts in punkt.tidsserier if isinstance(ts, tidsserieklasse)]
    else:
        tidsserier = (
            fire.cli.firedb.session.query(tidsserieklasse)
            .filter(tidsserieklasse._registreringtil == None)
            .all()
        )  # NOQA

    if not tidsserier:
        raise SystemExit("Fandt ingen tidsserier")

    tabel = Table("Ident", "Tidsserie ID", "Referenceramme", box=box.SIMPLE)

    for ts in tidsserier:
        tabel.add_row(ts.punkt.gnss_navn, ts.navn, ts.referenceramme)

    console = Console()
    console.print(tabel)


def _find_tidsserie(tidsserieklasse: Type, tidsserienavn: str) -> Tidsserie:
    """
    Find en navngiven tidsserie

    raises:     NoResultFound
    """
    tidsserie = (
        fire.cli.firedb.session.query(tidsserieklasse)
        .filter(
            tidsserieklasse._registreringtil == None,
            func.lower(tidsserieklasse.navn) == func.lower(tidsserienavn),
        )
        .one()
    )  # NOQA

    return tidsserie


GNSS_TS_PARAMETRE = {
    "t": "t",
    "x": "x",
    "sx": "sx",
    "y": "y",
    "sy": "sy",
    "z": "z",
    "sz": "sz",
    "X": "X",
    "Y": "Y",
    "Z": "Z",
    "n": "n",
    "e": "e",
    "u": "u",
    "decimalår": "decimalår",
    "obslængde": "obslængde",
    "kkxx": "koordinatkovarians_xx",
    "kkxy": "koordinatkovarians_xy",
    "kkxz": "koordinatkovarians_xz",
    "kkyy": "koordinatkovarians_yy",
    "kkyz": "koordinatkovarians_yz",
    "kkzz": "koordinatkovarians_zz",
    "rkxx": "residualkovarians_xx",
    "rkxy": "residualkovarians_xy",
    "rkxz": "residualkovarians_xz",
    "rkyy": "residualkovarians_yy",
    "rkyz": "residualkovarians_yz",
    "rkzz": "residualkovarians_zz",
}


@ts.command()
@click.argument("objekt", required=False, type=str)
@click.option(
    "--parametre",
    "-p",
    required=False,
    type=str,
    default="t,x,sx,y,sy,z,sz",
    help="""Vælg hvilke parametre i tidsserien der skal udtrækkes. Som standard
sat til 't,x,sx,y,sy,z,sz'. Bruges værdien 'alle' udtrækkes alle mulige parametre
i tidsserien.  Se ``fire ts gnss --help`` for yderligere detaljer.""",
)
@click.option(
    "--fil",
    "-f",
    required=False,
    type=click.Path(writable=True),
    help="Skriv den udtrukne tidsserie til Excel fil.",
)
@fire.cli.default_options()
def gnss(objekt: str, parametre: str, fil: click.Path, **kwargs) -> None:
    """
    Udtræk en GNSS tidsserie.


    "OBJEKT" sættes til enten et punkt eller et specifik navngiven tidsserie.
    Hvis "OBJEKT" er et punkt udskrives en oversigt over de tilgængelige
    tidsserier til dette punkt. Hvis 'OBJEKT' er en tidsserie udskrives
    tidsserien på skærmen. Hvilke parametre der udskrives kan specificeres
    i en kommasepareret liste med ``--parametre``. Følgende parametre kan vælges::

    \b
        t               Tidspunkt for koordinatobservation
        x               Koordinatens x-komponent (geocentrisk)
        sx              x-komponentens spredning (i mm)
        y               Koordinatens y-komponent (geocentrisk)
        sy              y-komponentens spredning (i mm)
        z               Koordinatens z-komponent (geocentrisk)
        sz              z-komponentens spredning (i mm)
        X               Koordinatens x-komponent (geocentrisk, normaliseret)
        Y               Koordinatens y-komponent (geocentrisk, normaliseret)
        Z               Koordinatens z-komponent (geocentrisk, normaliseret)
        n               Normaliseret nordlig komponent (topocentrisk)
        e               Normaliseret østlig komponent (topocentrisk)
        u               Normaliseret vertikal komponent (topocentrisk)
        decimalår       Tidspunkt for koordinatobservation i decimalår
        obslængde       Observationslængde givet i timer
        kkxx            Koordinatkovariansmatricens XX-komponent
        kkxy            Koordinatkovariansmatricens XY-komponent
        kkxz            Koordinatkovariansmatricens XZ-komponent
        kkyy            Koordinatkovariansmatricens YY-komponent
        kkyz            Koordinatkovariansmatricens YZ-komponent
        kkzz            Koordinatkovariansmatricens ZZ-komponent
        rkxx            Residualkovariansmatricens XX-komponent
        rkxy            Residualkovariansmatricens XY-komponent
        rkxz            Residualkovariansmatricens XZ-komponent
        rkyy            Residualkovariansmatricens YY-komponent
        rkyz            Residualkovariansmatricens YZ-komponent
        rkzz            Residualkovariansmatricens ZZ-komponent

    Tidsserien kan skrives til en fil ved brug af ``--fil``, der resulterer i
    en csv-fil på den angivne placering. Denne fil kan efterfølgende åbnes
    i Excel, eller et andet passende program, til videre analyse.


    \b
    **EKSEMPLER**

    Vis alle tidsserier for punktet RDIO::

        fire ts gnss RDIO

    Vis tidsserien 'RDIO_5D_IGb08' med standardparametre::

        fire ts gnss RDIO_5D_IGb08

    Vis tidsserie med brugerdefinerede parametre::

        fire ts gnss RDIO_5D_IGb08 --parametre decimalår,n,e,u,sx,sy,sz

    Gem tidsserie med samtlige tilgængelige parametre::

        fire ts gnss RDIO_5D_IGb08 -p alle -f RDIO_5D_IGb08.xlsx
    """
    if not objekt:
        _print_tidsserieoversigt(GNSSTidsserie)
        raise SystemExit

    # Prøv først med at søg efter specifik tidsserie
    try:
        tidsserie = _find_tidsserie(GNSSTidsserie, objekt)
    except NoResultFound:
        try:
            punkt = fire.cli.firedb.hent_punkt(objekt)
        except NoResultFound:
            raise SystemExit("Punkt eller tidsserie ikke fundet")

        _print_tidsserieoversigt(GNSSTidsserie, punkt)
        raise SystemExit

    if parametre.lower() == "alle":
        parametre = ",".join(GNSS_TS_PARAMETRE.keys())

    parametre = parametre.split(",")
    overskrifter = []
    kolonner = []
    for p in parametre:
        if p not in GNSS_TS_PARAMETRE.keys():
            raise SystemExit(f"Ukendt tidsserieparameter '{p}'")

        overskrifter.append(p)
        kolonner.append(tidsserie.__getattribute__(GNSS_TS_PARAMETRE[p]))

    tabel = Table(*overskrifter, box=box.SIMPLE)
    data = list(zip(*kolonner))

    def klargør_celle(input):
        if isinstance(input, datetime):
            return str(input)
        if isinstance(input, float):
            return f"{input:.4f}"
        if not input:
            return ""

    for række in data:
        tabel.add_row(
            *[klargør_celle(celle) if celle is not None else "" for celle in række]
        )

    console = Console()
    console.print(tabel)

    if not fil:
        raise SystemExit

    data = {
        overskrift: kolonne for (overskrift, kolonne) in zip(overskrifter, kolonner)
    }
    df = pd.DataFrame(data)
    df.to_excel(fil, index=False)


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
    default=None,
    help="Hvilken parameter skal plottes? Vælges flere plottes max de tre første.",
)
@fire.cli.default_options()
def plot_gnss(tidsserie: str, plottype: str, parametre: str, **kwargs) -> None:
    """
    Plot en GNSS tidsserie.

    Et simpelt plot der som standard viser udviklingen i nord, øst og op retningerne over tid.
    Vælges plottypen ``konf`` vises som standard kun Op-retningen.
    Plottes kun én enkelt tidsserieparameter vises for plottyperne ``fit`` og ``konf`` også
    værdien af fittets hældning.

    "TIDSSERIE" er et GNSS-tidsserie ID fra FIRE. Eksisterende GNSS-tidsserier kan
    fremsøges med kommandoen ``fire ts gnss <punktnummer>``.
    Hvilke parametre der plottes kan specificeres i en kommasepareret liste med ``--parametre``.
    Højst 3 parametre plottes. Følgende parametre kan vælges::

    \b
        t               Tidspunkt for koordinatobservation
        x               Koordinatens x-komponent (geocentrisk)
        y               Koordinatens y-komponent (geocentrisk)
        z               Koordinatens z-komponent (geocentrisk)
        X               Koordinatens x-komponent (geocentrisk, normaliseret)
        Y               Koordinatens y-komponent (geocentrisk, normaliseret)
        Z               Koordinatens z-komponent (geocentrisk, normaliseret)
        n               Normaliseret nordlig komponent (topocentrisk)
        e               Normaliseret østlig komponent (topocentrisk)
        u               Normaliseret vertikal komponent (topocentrisk)
        decimalår       Tidspunkt for koordinatobservation i decimalår

    Typen af plot som vises kan vælges med ``--plottype``. Følgende plottyper kan vælges::

    \b
        rå              Plot rå data
        fit             Plot lineær regression oven på de rå data
        konf            Plot lineær regression med konfidensbånd

    \f
    **EKSEMPLER**

    Plot af 5D-tidsserie for BUDP::

        fire ts plot-gnss BUDP_5D_IGb08

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_gnss_BUDP_5D_IGb08.png
        :width: 800
        :alt: Eksempel på plot af 5D-tidsserie for BUDP.

    Plot af 5D-tidsserie for SMID::

        fire ts plot-gnss SMID_5D_IGb08 -p X,Y -t fit

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_gnss_SMID_5D_IGb08_XY_fit.png
        :width: 800
        :alt: Eksempel på plot af 5D-tidsserie for SMID.

    Plot af 5D-tidsserie for TEJH::

        fire ts plot-gnss TEJH_5D_IGb08 -t konf

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_gnss_TEJH_5D_IGb08_konf.png
        :width: 800
        :alt: Eksempel på plot af 5D-tidsserie for TEJH.

    """
    # Dynamisk default værdi baseret på plottype.
    # Se https://stackoverflow.com/questions/51846634/click-dynamic-defaults-for-prompts-based-on-other-options for andre muligheder
    if parametre is None:
        if plottype == "konf":
            parametre = "u"
        else:
            parametre = "n,e,u"

    plot_funktioner = {
        "rå": plot_data,
        "fit": plot_fit,
        "konf": plot_konfidensbånd,
    }

    try:
        tidsserie = _find_tidsserie(GNSSTidsserie, tidsserie)
    except NoResultFound:
        raise SystemExit("Tidsserie ikke fundet")

    parametre = parametre.split(",")

    for parm in parametre:
        if parm not in GNSS_TS_ANALYSERBARE_PARAMETRE.keys():
            raise SystemExit(f"Ukendt tidsserieparameter '{parm}'")

    parametre = [GNSS_TS_ANALYSERBARE_PARAMETRE[parm] for parm in parametre]

    plot_gnss_ts(tidsserie, plot_funktioner[plottype], parametre)


