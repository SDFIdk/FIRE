import sys
import getpass

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
    SagseventInfoHtml,
)


from . import (
    ARKDEF_PUNKTOVERSIGT,
    ARKDEF_OBSERVATIONER,
    anvendte,
    bekræft2,
    find_faneblad,
    find_sag,
    find_sagsgang,
    gyldighedstidspunkt,
    niv,
    skriv_ark,
)


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
def ilæg_nye_koter(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyberegnede koter i databasen"""
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")

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
    with open(f"{projektnavn}-resultat-endelig.html") as html:
        clob = "".join(html.readlines())
    sagseventinfo = SagseventInfo(
        beskrivelse=sagseventtekst,
        htmler=[SagseventInfoHtml(html=clob)],
    )
    sagsevent.sagseventinfos.append(sagseventinfo)
    sagsevent.koordinater = til_registrering
    fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)

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

    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    fire.cli.print(f"Ialt {n} koter")

    try:
        fire.cli.firedb.session.flush()
    except Exception as ex:
        # rul tilbage hvis databasen smider en exception
        fire.cli.firedb.session.rollback()
        fire.cli.print(f"Der opstod en fejl - koter for '{projektnavn}' IKKE indlæst!")
        fire.cli.print(f"Mulig årsag: {ex}")
    else:
        spørgsmål = click.style("Du indsætter nu ", fg="white", bg="red")
        spørgsmål += click.style(
            f"{len(til_registrering)} kote(r) ", fg="white", bg="red", bold=True
        )
        spørgsmål += click.style(f"i ", fg="white", bg="red")
        spørgsmål += click.style(
            f"{fire.cli.firedb.db}", fg="white", bg="red", bold=True
        )
        spørgsmål += click.style("-databasen - er du sikker?", fg="white", bg="red")

        if bekræft2(spørgsmål):
            fire.cli.firedb.session.commit()

            # Skriv resultater til resultatregneark
            ny_punktoversigt = ny_punktoversigt.replace("nan", "")
            resultater = {"Sagsgang": sagsgang, "Resultat": ny_punktoversigt}
            skriv_ark(projektnavn, resultater)

            fire.cli.print(
                f"Koter registreret. Flyt nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
            )
