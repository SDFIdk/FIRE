import sys
from datetime import datetime
from typing import Tuple

import click
import pandas as pd

import fire.cli
from fire.cli import firedb
from fire import uuid

# Typingelementer fra databaseAPIet.
from fire.api.model import (
    EventType,
    GeometriObjekt,
    Point,
    Punkt,
    Koordinat,
    Observation,
    PunktInformation,
    PunktInformationType,
    PunktInformationTypeAnvendelse,
    Sag,
    Sagsevent,
    SagseventInfo,
    Sagsinfo,
)


from . import (
    ARKDEF_PUNKTOVERSIGT,
    anvendte,
    check_om_resultatregneark_er_lukket,
    find_sag,
    find_sagsgang,
    niv,
    skriv_ark
)


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.argument(
    "sagsbehandler",
    nargs=1,
    type=str,
)
def ilæg_nye_koter(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyberegnede koter i databasen"""
    check_om_resultatregneark_er_lukket(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print("Lægger nye koter i databasen")

    try:
        punktoversigt = pd.read_excel(
            f"{projektnavn}.xlsx",
            sheet_name="Punktoversigt",
            usecols=anvendte(ARKDEF_PUNKTOVERSIGT),
        )
    except Exception as ex:
        fire.cli.print(
            f"Kan ikke læse punktoversigt fra '{projektnavn}.xlsx'",
            fg="yellow",
            bold=True,
        )
        fire.cli.print(f"Mulig årsag: {ex}")
        sys.exit(1)

    ny_punktoversigt = punktoversigt[0:0]

    DVR90 = firedb.hent_srid("EPSG:5799")
    registreringstidspunkt = datetime.now()

    # Generer sagsevent
    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.KOORDINAT_BEREGNET)

    til_registrering = []
    opdaterede_punkter = []
    for punktdata in punktoversigt.to_dict(orient="records"):
        # Blanklinje, eller allerede registreret?
        if pd.isna(punktdata["Ny kote"]) or not pd.isna(punktdata["uuid"]):
            ny_punktoversigt = ny_punktoversigt.append(punktdata, ignore_index=True)
            continue

        punkt = firedb.hent_punkt(punktdata["Punkt"])
        opdaterede_punkter.append(punkt)
        punktdata["uuid"] = sagsevent.id

        kote = Koordinat(
            srid=DVR90,
            punkt=punkt,
            t=registreringstidspunkt,
            z=punktdata["Ny kote"],
            sz=punktdata["Ny σ"],
        )

        til_registrering.append(kote)
        ny_punktoversigt = ny_punktoversigt.append(punktdata, ignore_index=True)

    if 0 == len(til_registrering):
        fire.cli.print("Ingen koter at registrere!", fg="yellow", bold=True)
        return

    # Vi vil ikke have alt for lange sagseventtekster (bl.a. fordi Oracle ikke
    # kan lide lange tekststrenge), så vi indsætter udeladelsesprikker hvis vi
    # opdaterer mere end 10 punkter ad gangen
    n = len(opdaterede_punkter)
    punktnavne = [p.ident for p in opdaterede_punkter]
    if n > 10:
        punktnavne[9] = "..."
        punktnavne[10] = punktnavne[-1]
    sagseventtekst = f"Opdatering af DVR90 kote til {', '.join(punktnavne)}"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": registreringstidspunkt,
        "Hvem": sagsbehandler,
        "Hændelse": "Koteberegning",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)

    # Persister koterne til databasen
    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    if "ja" != input(
        f"-->  HELT sikker på at du vil skrive {n} koter til databasen (ja/nej)? "
    ):
        fire.cli.print("Dropper skrivning")
        return

    sagsevent.koordinater = til_registrering
    firedb.indset_sagsevent(sagsevent)

    # Skriv resultater til resultatregneark
    resultater = {"Sagsgang": sagsgang, "Punktoversigt": ny_punktoversigt}
    skriv_ark(projektnavn, resultater)

    fire.cli.print(
        f"Koter registreret. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
    )
