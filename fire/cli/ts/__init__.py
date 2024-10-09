from datetime import datetime

import click
import pandas as pd
from rich.table import Table
from rich.console import Console
from rich import box
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound


import fire.cli
from fire.api.model import (
    Tidsserie,
    GNSSTidsserie,
    HøjdeTidsserie,
    Punkt,
)


@click.group()
def ts():
    """
    Håndtering af koordinattidsserier.
    """
    pass


def _print_tidsserieoversigt(tidsserieklasse: type[Tidsserie], punkt: Punkt = None) -> None:
    """
    Oversigt over tidsserier af en bestemt types

    raises:     SystemExit
    """

    def identgnss(punkt: Punkt):
        return punkt.gnss_navn

    def identident(punkt: Punkt):
        return punkt.ident

    if tidsserieklasse == GNSSTidsserie:
        foretrukken_ident = identgnss
    else:
        foretrukken_ident = identident

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

    tabel = Table("Ident", "Tidsserienavn", "Referenceramme", box=box.SIMPLE)

    # Sorter tidsserier efter punkt
    tidsserier.sort(key=lambda ts: (foretrukken_ident(ts.punkt)))

    for ts in tidsserier:
        tabel.add_row(foretrukken_ident(ts.punkt), ts.navn, ts.referenceramme)

    console = Console()
    console.print(tabel)


def _find_tidsserie(tidsserieklasse: type[Tidsserie], tidsserienavn: str) -> Tidsserie:
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


def _udtræk_tidsserie(
    objekt: str,
    tidsserieklasse: type[Tidsserie],
    parametre_alle: dict[str, str],
    parametre: str,
    fil: click.Path,
):
    if not objekt:
        _print_tidsserieoversigt(tidsserieklasse)
        raise SystemExit

    # Prøv først med at søg efter specifik tidsserie
    try:
        tidsserie = _find_tidsserie(tidsserieklasse, objekt)
    except NoResultFound:
        try:
            punkt = fire.cli.firedb.hent_punkt(objekt)
        except NoResultFound:
            raise SystemExit("Punkt eller tidsserie ikke fundet")

        _print_tidsserieoversigt(tidsserieklasse, punkt)
        raise SystemExit

    if parametre.lower() == "alle":
        parametre = ",".join(parametre_alle.keys())

    parametre = parametre.split(",")
    overskrifter = []
    kolonner = []
    for p in parametre:
        if p not in parametre_alle.keys():
            raise SystemExit(f"Ukendt tidsserieparameter '{p}'")

        overskrifter.append(p)
        kolonner.append(tidsserie.__getattribute__(parametre_alle[p]))

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


from .gnss import gnss
from .hts import hts
