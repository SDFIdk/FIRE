import sys
from datetime import datetime

import click
import pandas as pd

import fire.cli
from fire.cli import firedb
from fire import uuid

# Typingelementer fra databaseAPIet.
from fire.api.model import (
    EventType,
    Punkt,
    PunktInformation,
    PunktInformationType,
    PunktInformationTypeAnvendelse,
    Sag,
    Sagsevent,
    SagseventInfo,
)


from . import (
    ARKDEF_REVISION,
    anvendte,
    check_om_resultatregneark_er_lukket,
    find_sag,
    find_sagsgang,
    niv,
)


# ------------------------------------------------------------------------------
# Her starter revisionsilæggelsesprogrammet
# ------------------------------------------------------------------------------
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
@click.argument(
    "bemærkning",
    nargs=-1,
    type=str,
)
def ilæg_revision(
    alvor: bool,
    test: bool,
    projektnavn: str,
    sagsbehandler: str,
    bemærkning: str,
    **kwargs,
) -> None:
    """Læg reviderede punktdata i databasen"""
    check_om_resultatregneark_er_lukket(projektnavn)
    if alvor:
        sag = find_sag(projektnavn)
    else:
        sag = Sag()

    sagsgang = find_sagsgang(projektnavn)

    # Vi skal bruge uuider for sagsevents undervejs, så vi genererer dem her men
    # Færdiggør dem først når vi er klar til registrering
    se_tilføj = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKTINFO_TILFOEJET)
    se_slet = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKTINFO_FJERNET)

    fire.cli.print("Lægger punktrevisionsarbejde i databasen")

    # For tiden kan vi kun teste, så vi påtvinger midlertidigt flagene værdier, der afspejler dette
    test = True
    alvor = False

    # Påtving konsistens mellem alvor/test flag
    if alvor:
        test = False
        fire.cli.print(
            " BEKRÆFT: Skriver reviderede punktdata til FIRE-databasen!!! ",
            bg="red",
            fg="white",
        )
        fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag['uuid']})")
        fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")
        if "ja" != input("OK (ja/nej)? "):
            fire.cli.print("Dropper skrivning til FIRE-databasen")
            return

    if test:
        fire.cli.print(
            f" TESTER punktrevision for {projektnavn} ", bg="red", fg="white"
        )

    try:
        revision = pd.read_excel(
            f"{projektnavn}-revision.xlsx",
            sheet_name="Revision",
            usecols=anvendte(ARKDEF_REVISION),
        )
    except Exception as ex:
        fire.cli.print(
            f"Kan ikke læse revisionsblad fra '{projektnavn}-revision.xlsx'",
            fg="yellow",
            bold=True,
        )
        fire.cli.print(f"Mulig årsag: {ex}")
        sys.exit(1)
    bemærkning = " ".join(bemærkning)

    opdateret = pd.DataFrame(columns=list(ARKDEF_REVISION))
    print(opdateret)

    # Disse navne er lange at sejle rundt med, så vi laver en kort form
    TEKST = PunktInformationTypeAnvendelse.TEKST
    FLAG = PunktInformationTypeAnvendelse.FLAG
    TAL = PunktInformationTypeAnvendelse.TAL

    # Find identer for alle punkter, der indgår i revisionen
    identer = tuple(sorted(set(revision["Punkt"].dropna().astype(str))))
    fire.cli.print(f"Behandler {len(identer)} punkter")

    # Så itererer vi over alle punkter
    for ident in identer:
        fire.cli.print(ident, fg="yellow", bold=True)

        # Hent punkt og alle relevante punktinformationer i databasen
        punkt = firedb.hent_punkt(ident)
        infotypenavne = [i.infotype.name for i in punkt.punktinformationer]
        infonøgler = {
            info.objektid: i for i, info in enumerate(punkt.punktinformationer)
        }

        # Hent alle revisionselementer for punktet fra revisionsarket
        rev = revision[revision["Punkt"] == ident]

        for r in rev.to_dict("records"):
            if r["Attribut"].startswith("OVERVEJ:"):
                fire.cli.print(
                    f"    * Overvejelser endnu ikke implementeret",
                    fg="red",
                    bold=False,
                )
                continue
            pitnavn = r["Attribut"]
            if pitnavn is None:
                fire.cli.print(
                    f"    * Ignorerer uanført punktinformationstype",
                    fg="red",
                    bold=False,
                )
                continue

            # Nyt punktinfo-element?
            if pd.isna(r["id"]):
                pit = firedb.hent_punktinformationtype(pitnavn)
                if pit is None:
                    fire.cli.print(
                        f"    * Ignorerer ukendt punktinformationstype '{pitnavn}'",
                        fg="red",
                        bold=True,
                    )
                    continue
                fire.cli.print(f"    Opretter nyt punktinfo-element: {pitnavn}")

            # Ingen ændringer? - så afslutter vi og går til næste element.
            if pd.isna(r["Sluk"]) and pd.isna(r["Ret tal"]) and pd.isna(r["Ret tekst"]):
                continue

            # Herfra håndterer vi kun punktinformationer med indførte ændringer

            # Nu kan vi bruge objektid som heltal (ovenfor havde vi brug for NaN-egenskaben)
            oid = int(r["id"])

            # Find det tilsvarende persisterede element
            try:
                pinfo = punkt.punktinformationer[infonøgler[oid]]
            except KeyError:
                fire.cli.print(
                    f"    * Ukendt id - ignorerer element '{r}'", fg="red", bold=True
                )
                continue
            anvendelse = pinfo.infotype.anvendelse
            # print(f"anvendelse={anvendelse}, tekst={r['Ret tekst']}")

            if r["Sluk"] == "x":
                fire.cli.print(f"    Slukker: {pitnavn}")
                # ...
                continue

    # Drop sagsevents etc.
    if test:
        fire.cli.print(
            f" TESTEDE punktrevision for {projektnavn} ", bg="red", fg="white"
        )
        fire.cli.print(f"Ingen data lagt i FIRE-databasen", fg="yellow")
        firedb.session.rollback()
        sys.exit(0)

    # Ad disse veje videre
    sagseventtekst = "bla bla bla"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    se_tilføj.sagseventinfos.append(sagseventinfo)
    registreringstidspunkt = datetime.now()

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": registreringstidspunkt,
        "Hvem": sagsbehandler,
        "Hændelse": "Koteberegning",
        "Tekst": sagseventtekst,
        "uuid": se_tilføj.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)
