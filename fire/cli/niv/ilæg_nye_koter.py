import sys

import click
import pandas as pd
from sqlalchemy import func

import fire.cli
from fire import uuid
from fire.api.model import (
    EventType,
    Punkt,
    Koordinat,
    Sag,
    Sagsevent,
    SagseventInfo,
)


from . import (
    ARKDEF_PUNKTOVERSIGT,
    ARKDEF_OBSERVATIONER,
    anvendte,
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    gyldighedstidspunkt,
    niv,
    skriv_ark,
)


@niv.command()
@fire.cli.default_options()
@click.option(
    "-t",
    "--test",
    is_flag=True,
    default=True,
    help="Check inputfil, skriv intet til databasen",
)
@click.option(
    "-a",
    "--alvor",
    is_flag=True,
    default=False,
    help="Skriv aftestet materiale til databasen",
)
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
def ilæg_nye_koter(
    projektnavn: str, sagsbehandler: str, alvor: bool, test: bool, **kwargs
) -> None:
    """Registrer nyberegnede koter i databasen"""
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")
    alvor, test = bekræft("Læg nye koter i databasen", alvor, test)
    # Fortrød de?
    if alvor and test:
        return

    punktoversigt = find_faneblad(
        projektnavn, "Endelig beregning", ARKDEF_PUNKTOVERSIGT
    )
    punktoversigt = punktoversigt.replace("nan", "")
    ny_punktoversigt = punktoversigt[0:0]

    DVR90 = fire.cli.firedb.hent_srid("EPSG:5799")
    registreringstidspunkt = func.current_timestamp()
    tid = gyldighedstidspunkt(projektnavn)

    # Generer sagsevent
    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.KOORDINAT_BEREGNET)

    til_registrering = []
    opdaterede_punkter = []
    for punktdata in punktoversigt.to_dict(orient="records"):
        # Blanklinje, tilbageholdt, eller allerede registreret?
        if (
            pd.isna(punktdata["Ny kote"])
            or punktdata["uuid"] != ""
            or punktdata["Udelad publikation"] == "x"
        ):
            ny_punktoversigt = ny_punktoversigt.append(punktdata, ignore_index=True)
            continue

        punkt = fire.cli.firedb.hent_punkt(punktdata["Punkt"])
        opdaterede_punkter.append(punkt)
        punktdata["uuid"] = sagsevent.id

        kote = Koordinat(
            srid=DVR90,
            punkt=punkt,
            t=tid,
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
        punktnavne = punktnavne[0:10]
    sagseventtekst = f"Opdatering af DVR90 kote til {', '.join(punktnavne)}"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    # Generer dokumentation til fanebladet "Sagsgang"
    # Variablen "registreringstidspunkt" har værdien "CURRENT_TIMESTAMP"
    # som udvirker mikrosekundmagi når den bliver skrevet til databasen,
    # men ikke er meget informativ for en menneskelig læser her i regne-
    # arkenes prosaiske verden. Derfor benytter vi pd.Timestamp.now(),
    # som ikke har mikrosekundmagi over sig, men som kan læses og giver
    # mening, selv om den ikke bliver eksakt sammenfaldende med det
    # tidsstempel hændelsen får i databasen. Det lever vi med.
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "Koteberegning",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)

    # Persister koterne til databasen
    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    fire.cli.print(f"Ialt {n} koter")
    if test:
        fire.cli.print("Testkørsel. Intet skrevet til databasen")
        return

    sagsevent.koordinater = til_registrering
    fire.cli.firedb.indset_sagsevent(sagsevent)

    # Skriv resultater til resultatregneark
    ny_punktoversigt = ny_punktoversigt.replace("nan", "")
    resultater = {"Sagsgang": sagsgang, "Resultat": ny_punktoversigt}
    skriv_ark(projektnavn, resultater)

    fire.cli.print(
        f"Koter registreret. Flyt nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
    )
