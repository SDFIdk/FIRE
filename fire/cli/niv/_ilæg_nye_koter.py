import pathlib
from functools import partial
import getpass

import click
import pandas as pd

import fire.cli
from fire import uuid
from fire.api.model import (
    EventType,
    Koordinat,
)
from fire.io.regneark import arkdef
from fire.io.formattering import forkort
import fire.io.dataframe as frame

from . import (
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    gyldighedstidspunkt,
    niv,
    skriv_ark,
    er_projekt_okay,
)


def punktdata_ikke_skal_opdateres(punktdata: dict) -> bool:
    """
    Returnerer sand, hvis ingen koteopdatering er nødvendig.
    """
    return (
        # Blank linje (feltet er tomt)
        pd.isna(punktdata["Ny kote"])
        # Allerede registreret (eksisterer i databasen)
        or punktdata["uuid"] != ""
        # Tilbageholdt og skal derfor ikke gemmes, uanset hvad.
        or punktdata["Udelad publikation"] == "x"
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
    er_projekt_okay(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")

    filnavn_gama_output = pathlib.Path(f"{projektnavn}-resultat-endelig.html")
    if not filnavn_gama_output.is_file():
        fire.cli.print(
            f"Sagsopdateringen kræver en outputfil fra GNU Gama {str(filnavn_gama_output)}"
        )
        raise SystemExit(1)

    # Indlæs regnearket
    punktoversigt = find_faneblad(
        projektnavn, "Endelig beregning", arkdef.PUNKTOVERSIGT
    )
    # Lav en kopi med de endelige resultater
    ny_punktoversigt = punktoversigt.copy()

    # Forbered data til kote-oprettelse
    DVR90 = fire.cli.firedb.hent_srid("EPSG:5799")
    tid = gyldighedstidspunkt(projektnavn)
    ny_kote = partial(Koordinat, srid=DVR90, t=tid)

    event_id = uuid()
    til_registrering = []
    opdaterede_punkter = []
    for index, punktdata in punktoversigt.iterrows():
        if punktdata_ikke_skal_opdateres(punktdata):
            continue

        punkt = fire.cli.firedb.hent_punkt(punktdata["Punkt"])
        opdaterede_punkter.append(punkt)
        punktdata["uuid"] = event_id

        z = punktdata["Ny kote"]
        sz = punktdata["Ny σ"]
        kote = ny_kote(punkt=punkt, z=z, sz=sz)
        til_registrering.append(kote)
        ny_punktoversigt = frame.insert(ny_punktoversigt, index, punktdata)

    if 0 == len(til_registrering):
        fire.cli.print("Ingen koter at registrere!", fg="yellow", bold=True)
        return

    # Vi vil ikke have alt for lange sagseventtekster (bl.a. fordi Oracle ikke
    # kan lide lange tekststrenge), så vi indsætter udeladelsesprikker hvis vi
    # opdaterer mere end 10 punkter ad gangen
    n = len(opdaterede_punkter)
    punktnavne = [p.ident for p in opdaterede_punkter]
    punktnavne = forkort(punktnavne)
    sagseventtekst = f"Opdatering af DVR90 kote til {', '.join(punktnavne)}"
    clob_html = filnavn_gama_output.read_text()

    sagsevent = sag.ny_sagsevent(
        id=event_id,
        beskrivelse=sagseventtekst,
        eventtype=EventType.KOORDINAT_BEREGNET,
        htmler=[clob_html],
        koordinater=til_registrering,
    )
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
    sagsgang = frame.append(sagsgang, sagsgangslinje)

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

        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()

            # Skriv resultater til resultatregneark
            resultater = {"Sagsgang": sagsgang, "Resultat": ny_punktoversigt}
            if skriv_ark(projektnavn, resultater):
                fire.cli.print(
                    f"Koter registreret. Resultater skrevet til '{projektnavn}.xlsx'"
                )
