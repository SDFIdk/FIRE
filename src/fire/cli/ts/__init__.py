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
    PunktSamling,
    Koordinat,
)


@click.group()
def ts():
    """
    Håndtering af koordinattidsserier.
    """
    pass


def _print_tidsserieoversigt(
    tidsserier: list[Tidsserie],
) -> None:
    """
    Print en oversigt over en liste af tidsserier

    raises:     SystemExit
    """

    def foretrukken_ident(ts: Tidsserie):
        if isinstance(ts, GNSSTidsserie):
            return ts.punkt.gnss_navn
        elif isinstance(ts, HøjdeTidsserie):
            return ts.punkt.ident

    tabel = Table("Ident", "Tidsserienavn", "Referenceramme", box=box.SIMPLE)

    # Sorter tidsserier efter punkt
    tidsserier.sort(key=lambda ts: (foretrukken_ident(ts)))

    for ts in tidsserier:
        tabel.add_row(foretrukken_ident(ts), ts.navn, ts.referenceramme)

    console = Console()
    console.print(tabel)

def _udtræk_tidsserie(
    objekt: str,
    tidsserieklasse: type[Tidsserie],
    srid: str,
    parametre_alle: dict[str, str],
    parametre: str,
    fil: click.Path,
):
    """
    Find tidsserier hvor `objekt` indgår i navnet eller i punktets ident.

    Hjælpefunktion til fire ts gnss/hts. Søger på tidsserienavnet ud fra `objekt` og
    filtrerer resultaterne efter `srid` og de valgte tidsserietyper (GNSS/HTS).
    Findes ingen resultater, søges der i stedet efter tidsserier hørende til et punkt med
    `objekt` som ident.
    """
    if srid is not None:
        try:
            srid = fire.cli.firedb.hent_srid(srid)
        except NoResultFound:
            raise SystemExit(f"Srid '{srid}' ikke fundet i databasen.")
        srid_filter = lambda ts: ts.srid == srid
    else:
        srid_filter = lambda ts: True

    # Prøv først at søge med objekt som søgestreng på tidsserienavn og filtrer på srid
    tidsserier = fire.cli.firedb.hent_tidsserier(objekt, tidsserieklasse=tidsserieklasse)
    tidsserier = [ts for ts in tidsserier if srid_filter(ts)]

    # Hvis ingen tidsserier, prøver vi med objekt som ident
    if not tidsserier:
        try:
            punkt = fire.cli.firedb.hent_punkt(objekt)
        except NoResultFound:
            raise SystemExit("Punkt eller tidsserie ikke fundet")
        else:
            # Udtræk punktets tidsserier og filtrer på ts-type og srid
            tidsserier=[ts for ts in punkt.tidsserier if isinstance(ts, tidsserieklasse) and srid_filter(ts)]

    if not tidsserier:
        raise SystemExit("Fandt ingen tidsserier")

    # Print oversigt over fundne tidsserier
    _print_tidsserieoversigt(tidsserier)

    # Hvis der kun blev fundet én tidsserie så printer vi den
    if len(tidsserier)==1:
        _print_tidsserie(tidsserier[0], parametre_alle, parametre, fil)


def _print_tidsserie(
    tidsserie: Tidsserie,
    parametre_alle: dict[str, str],
    parametre: str,
    fil: click.Path,
):
    """Print en tabel over en tidsserie med de givne parametre """
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


def skift_jessenpunkt(
    punktsamling: PunktSamling,
    gamle_tidsserier: list[HøjdeTidsserie],
    nyt_jessenpunkt: Punkt,
) -> tuple[PunktSamling, list[HøjdeTidsserie]]:
    """
    Skifter jessenpunket for en liste af højdetidsserier.

    Kræver at det nye jessenpunkt har en tidsserie i den gamle punktsamling. Beregnes
    derefter ved at trække det nye jessenpunkts tidsserie fra de andre tidsserier.

    Returnerer en ny instans af PunktSamling, der har referencekoten 0 til det nye
    jessenpunkt og som indeholder nye instanser af HøjdeTidsserier med de nye koter.

    Bemærk at de nye tidsserier kun kan beregnes til de tidspunkter hvor der er overlap
    med det nye jessenpunkts tidsserie. I særlige tilfælde, hvor et punkt aldrig er blevet
    målt samtidig med det nye jessenpunkt, kan der derfor returneres tidsserier som ikke
    indeholder nogen koter.
    """
    if punktsamling.jessenpunkt == nyt_jessenpunkt:
        fire.cli.print("Det valgte punkt er allerede jessenpunkt for punktsamlingen.")
        return punktsamling, gamle_tidsserier

    reference_ts = [ts for ts in punktsamling.tidsserier if nyt_jessenpunkt == ts.punkt]

    if not reference_ts:
        raise ValueError(
            f"Kan ikke bruge {nyt_jessenpunkt.ident} som nyt jessenpunkt. Har ikke en tidsserie."
        )

    reference_ts = reference_ts[0]

    ref_ts_df = pd.DataFrame(
        list(zip(reference_ts.t, reference_ts.kote, reference_ts.sz)),
        columns=("tid", "ref_kote", "ref_sz"),
    )

    ny_punktsamling = PunktSamling(
        navn=f"Midlertidigt jessenpunkt {nyt_jessenpunkt.ident}",
        jessenpunkt=nyt_jessenpunkt,
        jessenkoordinat=None,  # Ingen jessekote, hvilket skal tolkes som 0!
        formål=f"Ad hoc punktsamling for {nyt_jessenpunkt.ident}",
        punkter=punktsamling.punkter,
    )

    nye_tidsserier = []
    for ts in gamle_tidsserier:
        # springer det nye jessenpunkt over
        if ts.punkt == nyt_jessenpunkt:
            continue

        ny_ts = HøjdeTidsserie(
            navn=f"{ts.punkt.ident}_HTS_{nyt_jessenpunkt.ident}",
            punkt=ts.punkt,
            punktsamling=ny_punktsamling,
            formål=f"",
        )

        ts_df = pd.DataFrame(
            list(zip(ts.t, ts.kote, ts.sz)), columns=("tid", "kote", "sz")
        )

        # Inner join imellem reference_ts og ts for at finde de steder hvor punkterne er blevet målt samtidig
        merged = pd.merge(ref_ts_df, ts_df, left_on="tid", right_on="tid")

        # Beregn ny kote
        merged["ny_kote"] = merged["kote"] - merged["ref_kote"]

        # Opret nye koordinater
        nye_koordinater = []
        for i, row in merged.iterrows():
            nyt_koord = Koordinat(
                punkt=ts.punkt,
                t=row["tid"],
                z=row["ny_kote"],
                sz=row["sz"],
            )
            nye_koordinater.append(nyt_koord)

        # Tilføj de nye koordinater til den nye tidsserie
        ny_ts.koordinater = nye_koordinater

        nye_tidsserier.append(ny_ts)

    # Særbehandling for at oprette tidsserie og koter for gammel jessenpunkt
    ny_ts_for_gammelt_jessenpunkt = HøjdeTidsserie(
        navn=f"{punktsamling.jessenpunkt.ident}_HTS_{nyt_jessenpunkt.ident}",
        punkt=punktsamling.jessenpunkt,
        punktsamling=ny_punktsamling,
        formål=f"",
    )

    # Det gamle jessenpunkt havde i princippet en "konstant" tidsserie som altid var lig med referencekoten.
    nye_koordinater = []
    for i, row in ref_ts_df.iterrows():
        nyt_koord = Koordinat(
            punkt=punktsamling.jessenpunkt,
            t=row["tid"],
            z=punktsamling.jessenkote - row["ref_kote"],
            sz=row["ref_sz"],
        )
        nye_koordinater.append(nyt_koord)

    ny_ts_for_gammelt_jessenpunkt.koordinater = nye_koordinater

    # Tilføj tidsserien for det gamle jessenpunkt
    nye_tidsserier.append(ny_ts_for_gammelt_jessenpunkt)

    # Tilføj alle de nye tidsserier til punktsamlingen
    ny_punktsamling.tidsserier = nye_tidsserier

    return ny_punktsamling, nye_tidsserier


from fire.cli.ts.gnss import gnss
from fire.cli.ts.hts import hts
