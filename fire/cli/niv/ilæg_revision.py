import sys
import getpass

import click
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire import uuid
from fire.api.model import (
    EventType,
    PunktInformation,
    PunktInformationTypeAnvendelse,
    Sag,
    Sagsevent,
    SagseventInfo,
)

from . import (
    ARKDEF_REVISION,
    bekræft,
    find_faneblad,
    find_sag,
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
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
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
    sag = find_sag(projektnavn)

    fire.cli.print("Lægger punktrevisionsarbejde i databasen")

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")
    alvor, test = bekræft("Skriv punktrevisionsdata til databasen", alvor, test)
    # Fortrød de?
    if alvor and test:
        return

    revision = find_faneblad(f"{projektnavn}-revision", "Revision", ARKDEF_REVISION)
    revision = revision.replace("nan", "")
    bemærkning = " ".join(bemærkning)

    # Udfyld udeladte identer
    punkter = list(revision["Punkt"])
    udfyldningsværdi = ""
    for i in range(len(punkter)):
        if punkter[i].strip() != "":
            udfyldningsværdi = punkter[i].strip()
            continue
        punkter[i] = udfyldningsværdi
    revision["Punkt"] = punkter

    # Find alle lokationskoordinater, der skal korrigeres
    lokation = revision.query(f"Attribut == 'OVERVEJ:lokation'")
    lokation = lokation.query(f"`Ny værdi` != ''")
    for row in lokation.to_dict("records"):
        fire.cli.print(
            f"IKKE IMPLEMENTERET - Korrigerer lokation for: {row['Punkt']}: {row['Ny værdi']}"
        )
        if alvor:
            pass  # refaktor af opret_punkt(row["Punkt"], row["Ny værdi"], sag)
    revision = revision.query(f"Attribut != 'OVERVEJ:lokation'")

    # Find identer for alle punkter, der indgår i revisionen
    identer = tuple(sorted(set(revision["Punkt"]) - set(["nan", ""])))
    fire.cli.print(f"Behandler {len(identer)} punkter")

    til_opret = []
    til_ret = []
    til_sluk = []
    punkter_med_oprettelse = set()
    punkter_med_rettelse = set()
    punkter_med_slukning = set()

    # Så itererer vi over alle punkter
    for ident in identer:
        fire.cli.print(ident, fg="yellow", bold=True)

        # Hent punkt og alle relevante punktinformationer i databasen
        # Håndter punkter der endnu ikke er persisterede under test.
        #
        # Ved opdatering af eksisterende punkter vil vi gerne checke
        # infonøglerne, så vi er nødt til at hente det faktiske punkt,
        # med tilørende infonøgler, fra databasen - alvor eller ej
        try:
            punkt = fire.cli.firedb.hent_punkt(ident)
            infonøgler = {
                info.objektid: i for i, info in enumerate(punkt.punktinformationer)
            }
        except NoResultFound as ex:
            if not alvor:
                punkt = fire.cli.firedb.hent_punkt("9-09-00009")
                infonøgler = dict()
            else:
                fire.cli.print(
                    f"FEJL: Kan ikke finde punkt {ident}!",
                    fg="yellow",
                    bg="red",
                    bold=True,
                )
                fire.cli.print(f"Mulig årsag: {ex}")
                sys.exit(1)

        # Hent alle revisionselementer for punktet fra revisionsarket
        rev = revision.query(f"Punkt == '{ident}' and Attribut != 'Opret'")

        for r in rev.to_dict("records"):
            if r["id"] == 999999:
                continue
            if r["id"] == -1:
                continue
            pitnavn = r["Attribut"]
            if pitnavn == "":
                continue
            if pitnavn.startswith("OVERVEJ:"):
                continue

            if r["Sluk"] and r["Ny værdi"]:
                fire.cli.print(
                    f"    * FEJL: 'Sluk' og 'Ny værdi' begge udfyldt: {r['Ny værdi']}",
                    fg="red",
                    bold=False,
                )
                continue

            if pitnavn is None:
                fire.cli.print(
                    "    * Ignorerer uanført punktinformationstype",
                    fg="red",
                    bold=False,
                )
                continue

            pit = fire.cli.firedb.hent_punktinformationtype(pitnavn)
            if pit is None:
                fire.cli.print(
                    f"    * Ignorerer ukendt punktinformationstype '{pitnavn}'",
                    fg="red",
                    bold=True,
                )
                continue

            # Nyt punktinfo-element?
            if pd.isna(r["id"]):
                fire.cli.print(f"    Opretter nyt punktinfo-element: {pitnavn}")
                if pit.anvendelse == PunktInformationTypeAnvendelse.FLAG:
                    if r["Ny værdi"]:
                        fire.cli.print(
                            f"    BEMÆRK: {pitnavn} er et flag. Ny værdi '{r['Ny værdi']}' ignoreres",
                            fg="yellow",
                            bold=True,
                        )
                    pi = PunktInformation(infotype=pit, punkt=punkt)
                elif pit.anvendelse == PunktInformationTypeAnvendelse.TEKST:
                    # Ingen definitiv test her: Tom tekst kan være gyldig.
                    # Men vi sørger for at den ikke er None
                    tekst = r["Ny værdi"]
                    if tekst is None or tekst == "":
                        fire.cli.print(
                            f"    ADVARSEL: Tom tekst anført for {pitnavn}.",
                            fg="yellow",
                            bold=True,
                        )
                        tekst = ""
                    pi = PunktInformation(infotype=pit, punkt=punkt, tekst=tekst)
                else:
                    try:
                        # Både punktum og komma er accepterede decimalseparatorer
                        tal = float(r["Ny værdi"].replace(",", "."))
                    except ValueError as ex:
                        fire.cli.print(
                            f"    FEJL: {pitnavn} forventer numerisk værdi [{ex}].",
                            fg="yellow",
                            bold=True,
                        )
                        tal = 0
                    pi = PunktInformation(infotype=pit, punkt=punkt, tal=tal)

                til_opret.append(pi)
                punkter_med_oprettelse.add(ident)
                if alvor:
                    fire.cli.firedb.indset_punktinformation(
                        opret(sag, punkt.ident, pitnavn), pi
                    )
                continue

            # Ingen ændringer? - så afslutter vi og går til næste element.
            if r["Sluk"] == r["Ny værdi"] == "":
                continue

            # Herfra håndterer vi kun punktinformationer med indførte ændringer

            # Nu kan vi bruge objektid som heltal (ovenfor havde vi brug for NaN-egenskaben)
            oid = int(r["id"])
            if r["Sluk"] == "x":
                try:
                    pi = punkt.punktinformationer[infonøgler[oid]]
                except KeyError:
                    if alvor:
                        fire.cli.print(
                            f"    * Ukendt id - ignorerer element '{oid}'",
                            fg="red",
                            bold=True,
                        )
                        continue
                fire.cli.print(f"    Slukker: {pitnavn}")
                til_sluk.append(pi)
                punkter_med_slukning.add(punkt.ident)
                if alvor:
                    fire.cli.firedb.luk_punktinfo(pi, sluk(sag, punkt.ident, pitnavn))
                continue

            fire.cli.print(f"    Retter punktinfo-element: {pitnavn}")
            if pit.anvendelse == PunktInformationTypeAnvendelse.FLAG:
                pi = PunktInformation(infotype=pit, punkt=punkt)
            elif pit.anvendelse == PunktInformationTypeAnvendelse.TEKST:
                pi = PunktInformation(infotype=pit, punkt=punkt, tekst=r["Ny værdi"])
            else:
                try:
                    tal = float(r["Ny værdi"])
                except ValueError as ex:
                    fire.cli.print(
                        f"    FEJL: {pitnavn} forventer numerisk værdi [{ex}].",
                        fg="yellow",
                        bold=True,
                    )
                    tal = 0
                pi = PunktInformation(infotype=pit, punkt=punkt, tal=tal)
            til_ret.append(pi)
            punkter_med_rettelse.add(punkt.ident)
            if alvor:
                fire.cli.firedb.indset_punktinformation(
                    ret(sag, punkt.ident, pitnavn), pi
                )
            continue
    opret_tekst = f"Opretter {len(til_opret)} attributter fordelt på {len(punkter_med_oprettelse)} punkter"
    sluk_tekst = f"Slukker for {len(til_sluk)} attributter fordelt på {len(punkter_med_slukning)} punkter"
    ret_tekst = f"Retter {len(til_ret)} attributter fordelt på {len(punkter_med_rettelse)} punkter"

    if test:
        fire.cli.print(
            f"TESTEDE punktrevision for '{projektnavn}':", fg="yellow", bold=True
        )
        fire.cli.print(f"    * {opret_tekst}")
        fire.cli.print(f"    * {sluk_tekst}")
        fire.cli.print(f"    * {ret_tekst}")
        fire.cli.print(f"Ingen data lagt i FIRE-databasen", fg="yellow")
        sys.exit(0)


# -----------------------------------------------------------------------------
def opret(sag: Sag, punktid: str, pitnavn: str) -> Sagsevent:
    """Konstruer en sagshændelse beregnet på registrering af ny punktinfo"""
    se = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKTINFO_TILFOEJET)
    tekst = f"{punktid}: Opret {pitnavn}"
    info = SagseventInfo(beskrivelse=tekst)
    se.sagseventinfos.append(info)
    return se


# -----------------------------------------------------------------------------
def ret(sag: Sag, punktid: str, pitnavn: str) -> Sagsevent:
    """Konstruer en sagshændelse beregnet på registrering af ny punktinfo"""
    se = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKTINFO_TILFOEJET)
    tekst = f"{punktid}: Ret {pitnavn}"
    info = SagseventInfo(beskrivelse=tekst)
    se.sagseventinfos.append(info)
    return se


# -----------------------------------------------------------------------------
def sluk(sag: Sag, punktid: str, pitnavn: str) -> Sagsevent:
    """Konstruer en sagshændelse beregnet på slukning af punktinfo"""
    se = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKTINFO_FJERNET)
    tekst = f"{punktid}: Sluk {pitnavn}"
    info = SagseventInfo(beskrivelse=tekst)
    se.sagseventinfos.append(info)
    return se
