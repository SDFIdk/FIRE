import sys
from datetime import datetime
from math import trunc, isnan, radians
from time import sleep

import click
import pandas as pd
from pyproj import Proj
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire import uuid
from fire.api.model import (
    EventType,
    GeometriObjekt,
    Koordinat,
    Point,
    Punkt,
    PunktInformation,
    PunktInformationType,
    PunktInformationTypeAnvendelse,
    Sag,
    Sagsevent,
    SagseventInfo,
    Srid,
)

from . import (
    ARKDEF_REVISION,
    bekræft,
    find_faneblad,
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
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

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
    opdateret = pd.DataFrame(columns=list(ARKDEF_REVISION))

    # Udfyld udeladte identer
    punkter = list(revision["Punkt"])
    udfyldningsværdi = ""
    for i in range(len(punkter)):
        if punkter[i].strip() != "":
            udfyldningsværdi = punkter[i].strip()
            continue
        punkter[i] = udfyldningsværdi
    revision["Punkt"] = punkter

    # Find alle punkter, der skal nyoprettes
    oprettelse = revision.query(f"Attribut == 'Opret'")
    for row in oprettelse.to_dict("records"):
        if row["id"] == -1:
            continue
        fire.cli.print(f"Opretter nyt punkt: {row['Punkt']}")
        if alvor:
            opret_punkt(row["Punkt"], row["Ny værdi"], sag)
    revision = revision.query(f"Attribut != 'Opret'")

    # Find alle lokationskoordinater, der skal korrigeres
    lokation = revision.query(f"Attribut == 'Lokation'")
    lokation = lokation.query(f"`Ny værdi` != ''")
    for row in lokation.to_dict("records"):
        fire.cli.print(
            f"IKKE IMPLEMENTERET - Korrigerer lokation for: {row['Punkt']}: {row['Ny værdi']}"
        )
        if alvor:
            pass  # refaktor af opret_punkt(row["Punkt"], row["Ny værdi"], sag)
    revision = revision.query(f"Attribut != 'Lokation'")

    # Find alle koordinater, der skal oprettes

    # Først skal vi bruge alle gyldige koordinatsystemnavne
    srider = fire.cli.firedb.hent_srider()
    sridnavne = [srid.name.upper() for srid in srider]

    # Så itererer vi over hele rammen og ignorerer ikke-koordinaterne
    til_registrering = []
    opdaterede_punkter = []
    koordinatoprettelsestekst = str()
    for r in revision.to_dict("records"):
        sridnavn = r["Attribut"].upper()
        if sridnavn not in sridnavne:
            continue
        try:
            koord = [float(k.replace(",", ".")) for k in r["Ny værdi"].split()]
        except ValueError as ex:
            fire.cli.print(
                f"Slemt koordinatudtryk:\n{'    '.join(r['Ny værdi'])}\n{ex}"
            )
            sys.exit(1)

        # Oversæt NaN til None
        koord = [None if isnan(k) else k for k in koord]

        # Tæt-på-kopi af kode fra "niv/ilæg_nye_koter.py". Her bør mediteres og overvejes
        # hvordan denne opgave kan parametriseres på en rimeligt generel måde, så den kan
        # udstilles i et "højniveau-API"
        srid = fire.cli.firedb.hent_srid(sridnavn)
        registreringstidspunkt = func.current_timestamp()
        sagsevent = Sagsevent(
            sag=sag, id=uuid(), eventtype=EventType.KOORDINAT_BEREGNET
        )

        # Undgå forsøg på at læse punkter der endnu ikke er skrevet til databasen:
        # Ved testkørsler bruger vi dummypunkt 00009 fra det ikke-eksisterende
        # opmålingsdistrikt 9-09. Ved endelige kørsler har vi lige lagt punkterne
        # i databasen ovenfor, så her kan vi bruge de faktiske punktnavne.
        if not alvor:
            punkt = fire.cli.firedb.hent_punkt("9-09-00009")
        else:
            punkt = fire.cli.firedb.hent_punkt(r["Punkt"])
        opdaterede_punkter.append(r["Punkt"])

        # Det er ikke helt så nemt som i C at oversætte decimal-år til datetime
        if koord[3] is None:
            tid = None
        else:
            år = trunc(koord[3])
            rest = koord[3] - år
            startdato = datetime(år, 1, 1)
            årlængde = datetime(år + 1, 1, 1) - startdato
            tid = startdato + rest * årlængde

        koordinat = Koordinat(
            srid=srid,
            punkt=punkt,
            x=koord[0],
            y=koord[1],
            z=koord[2],
            t=tid,
            sx=koord[4],
            sy=koord[5],
            sz=koord[6],
        )
        til_registrering.append(koordinat)

        # I Grønland er vi nødt til at duplikere geografiske koordinater til UTM24,
        # da Oracles indbyggede UTM-rutine er for ringe til at vi kan generere
        # udstillingskoordinater on-the-fly.
        if sridnavn == "EPSG:4909" or sridnavn == "EPSG:4747":
            srid_utm24 = fire.cli.firedb.hent_srid("EPSG:3184")
            utm24 = Proj("proj=utm zone=24 ellps=GRS80", preserve_units=False)
            x, y = utm24(koord[0], koord[1])
            koordinat = Koordinat(
                srid=srid_utm24,
                punkt=punkt,
                x=x,
                y=y,
                z=None,
                t=tid,
                sx=koord[4],
                sy=koord[5],
                sz=None,
            )
            til_registrering.append(koordinat)

    n = len(opdaterede_punkter)
    if n > 0:
        punktnavne = sorted(list(set(opdaterede_punkter)))
        if len(punktnavne) > 10:
            punktnavne[9] = "..."
            punktnavne[10] = punktnavne[-1]
            punktnavne = punktnavne[0:10]
        koordinatoprettelsestekst = (
            f"Opdatering af {n} koordinater til {', '.join(punktnavne)}"
        )
        sagseventinfo = SagseventInfo(beskrivelse=koordinatoprettelsestekst)
        sagsevent.sagseventinfos.append(sagseventinfo)
        sagsevent.koordinater = til_registrering
        if alvor:
            fire.cli.firedb.indset_sagsevent(sagsevent)

    # Så tager vi fat på punktinformationerne

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
        # Her er det lidt sværere end for koordinaternes vedkommende:
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
            if r["Attribut"] in sridnavne:
                continue
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
                            f"    ADVARSEL: Tom tekst anført for {pitnavn} [{ex}].",
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
        if koordinatoprettelsestekst != "":
            fire.cli.print(f"    * {koordinatoprettelsestekst}")
        fire.cli.print(f"    * {opret_tekst}")
        fire.cli.print(f"    * {sluk_tekst}")
        fire.cli.print(f"    * {ret_tekst}")
        fire.cli.print(f"Ingen data lagt i FIRE-databasen", fg="yellow")
        sys.exit(0)


def opret_punkt(ident: str, lokation: str, sag: Sag):
    """Opret nyt punkt i databasen, ud fra minimumsinformationsmængder."""

    lok = lokation.split()
    assert len(lok) in (
        2,
        4,
    ), f"Lokation '{lokation}' matcher ikke format: 55.443322 [N] 12.345678 [Ø]."
    if len(lok) == 2:
        lok = [lok[0], "", lok[1], ""]
    try:
        e = float(lok[2])
        n = float(lok[0])
    except ValueError as ex:
        fire.cli.print(f"Ikke-numerisk lokationskoordinat anført: {lokation} ({ex})")
        sys.exit(1)

    # Håndter verdenshjørner Nn/ØøEe/VvWw/Ss
    if lok[1].upper() == "S":
        n = -n
    if lok[3].upper() in ("W", "V"):
        e = -e

    # Regionen kan detekteres alene ud fra længdegraden, hvis vi holder os til
    # {DK, EE, FO, GL}. EE er dog ikke understøttet her: Hvis man forsøger at
    # oprette nye estiske punkter vil de blive tildelt region DK
    if e > 0:
        region = "REGION:DK"
    elif e < -11:
        region = "REGION:GL"
    else:
        region = "REGION:FO"

    # Hvis ident har regionspræfiks, så skræller vi det af og håndterer det separat
    region_ident = ident.split()
    if len(region_ident) == 2:
        assert region_ident[0] in (
            "DK",
            "FO",
            "GL",
        ), f"Ukendt regionspræfiks: {region_ident[0]}"
        ident = region_ident[1]

    prefix = {"REGION:DK": "", "REGION:FO": "FO  ", "REGION:GL": "GL  "}

    if 3 == len(ident.split("-")):
        identtype = "IDENT:landsnr"
    elif 4 == len(ident) and not ident.isnumeric():
        identtype = "IDENT:GNSS"
    elif ident.startswith("G.M."):
        identtype = "IDENT:GI"
    elif ident.startswith("G.I."):
        identtype = "IDENT:GI"
    else:
        if ident.isnumeric():
            identtype = "IDENT:station"
        else:
            identtype = "IDENT:ekstern"

    p = Punkt(id=uuid())
    go = GeometriObjekt()
    go.geometri = Point([e, n])
    p.geometriobjekter.append(go)

    se = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKT_OPRETTET)
    si = SagseventInfo(beskrivelse=f"opret {ident}")
    se.sagseventinfos.append(si)
    se.punkter.append(p)
    fire.cli.firedb.indset_sagsevent(se)

    # indsæt ident
    pit = fire.cli.firedb.hent_punktinformationtype(identtype)
    if pit is None:
        fire.cli.print(f"Kan ikke finde identtype '{identtype}'")
        sys.exit(1)
    pi = PunktInformation(infotype=pit, punkt=p, tekst=f"{prefix[region]}{ident}")
    se = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKTINFO_TILFOEJET)
    si = SagseventInfo(beskrivelse=f"tilpas {ident}")
    se.sagseventinfos.append(si)
    fire.cli.firedb.indset_punktinformation(se, pi)

    # indsæt region
    pit = fire.cli.firedb.hent_punktinformationtype(region)
    if pit is None:
        fire.cli.print(f"Kan ikke finde region '{region}'")
        sys.exit(1)
    pi = PunktInformation(infotype=pit, punkt=p)
    se = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.PUNKTINFO_TILFOEJET)
    si = SagseventInfo(beskrivelse=f"tilpas {ident}")
    se.sagseventinfos.append(si)
    fire.cli.firedb.indset_punktinformation(se, pi)


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
