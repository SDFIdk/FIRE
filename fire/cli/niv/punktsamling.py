import getpass

import click
import pandas as pd
from sqlalchemy.exc import (
    NoResultFound,
)

from fire import uuid
from fire.api.model import (
    Punkt,
    PunktSamling,
    Koordinat,
    Tidsserie,
    HøjdeTidsserie,
    Srid,
)
import fire.cli
from fire.cli.niv import (
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    niv,
    skriv_ark,
    er_projekt_okay,
    udled_jessenpunkt_fra_punktoversigt,
    afbryd_hvis_ugyldigt_jessenpunkt,
)
import fire.io.dataframe as frame
from fire.io.regneark import arkdef


def find_eller_opret_jessenkote(
    jessenpunkt: Punkt, jessenkote: float, kotesystem: Srid
) -> Koordinat:
    """
    Finder et Koordinat-objekt i databasen med givet punkt, jessenkote, og kotesystem

    Hvis der findes mere end ét Koordinat så returneres det først fundne. Hvis der ikke
    eksisterer et sådant Koordinat, så oprettes og returneres et nyoprettet koordinat, som
    man sidenhen kan vælge at lægge i databasen.

    Bemærk at denne funktion er tiltænkt situationer hvor en punktsamling forsøges ilagt
    databasen med en jessenkote som ikke findes. Dog kan den også bruges til at finde
    eller oprette arbitrære Koordinater.
    """
    try:
        # Filterer med vilje ikke på RegistreringTil = None, idet jessenpunktet godt
        # kan have tidsserier i andre punktsamlinger, hvis tidsserie-koordinater også
        # har SRID'en TS:jessen.
        # RegistreringTil = None vil kun finde det nyeste koord. som altså kan ændre
        # kote.
        # Der forventes kun ét resultat, men søgningen kan i edge-cases returnere
        # flere koordinater med identisk z-værdi, hvorfor der bare tages den først
        # fundne, som også burde være den første i tid.
        jessenkoordinat = [
            k
            for k in jessenpunkt.koordinater
            if k.srid == kotesystem and k.z == jessenkote
        ][0]
    except IndexError:

        fire.cli.print(
            f"BEMÆRK: Jessenkote ikke fundet i databasen. \n"
            f"Opretter nyt Jessenkoordinat med koten {jessenkote} [m]",
            fg="black",
            bg="yellow",
        )

        jessenkoordinat = Koordinat(
            punkt=jessenpunkt,
            srid=kotesystem,
            # hvilket tidspunkt skal den nye jessenkote gælde fra?
            # default er "current_timestamp"
            # t=None,
            z=jessenkote,
            sz=0,
        )

    return jessenkoordinat


def find_punktsamling(
    jessenpunkt: Punkt,
    punktsamlingsnavn: str = "",
) -> PunktSamling:
    """Finder en punktsamling ud fra angivet navn og jessenpunkt."""

    punktsamling = fire.cli.firedb.hent_punktsamling(punktsamlingsnavn)

    # Sikr at den fundne Punktsamling også har korrekt Jessenpunkt
    if punktsamling.jessenpunkt != jessenpunkt:
        fire.cli.print(
            f"FEJL: Jessenpunktet '{punktsamling.jessenpunkt.ident}' for punktsamlingen '{punktsamlingsnavn}' "
            f"er ikke det samme som det angivne Jessenpunkt '{jessenpunkt.ident}'",
            fg="black",
            bg="yellow",
        )
        raise SystemExit(1)

    return punktsamling


def er_punktsamling_unik(
    punktsamling_A: PunktSamling, punktsamlinger: list[PunktSamling] = []
) -> tuple[set[str], set[str], set[str]]:
    """
    Undersøg om en Punktsamling A udgør en unik samling af punkter.

    Givet Punktsamling A (herved forstås mængden af punkter i punktsamlingen) undersøges
    der for alle andre Punktsamlinger B flg:
        1. Er A lig med B
        2. Er A en delmængde af B (Er A et "subset" af B)
        3. Er B en delmængde af A (Er A et "superset" af B)

    Returnerer for hvert af de ovenstående tilfælde, en mængde af navne på punktsamlinger
    der falder inden for de 3 kategorier.
    """
    if not isinstance(punktsamling_A, PunktSamling):
        raise TypeError("'punktsamling' er ikke en instans af PunktSamling")

    # Mængde af punkter i Punktsamling A
    punkter_A = {pkt.ident for pkt in punktsamling_A.punkter}

    if not punktsamlinger:
        punktsamlinger = fire.cli.firedb.hent_alle_punktsamlinger()

    # Initialiser lister
    ligmed, subset, superset = set(), set(), set()
    for punktsamling_B in punktsamlinger:

        # Lad være med at sammenligne Punktsamlingen med sig selv
        if punktsamling_A.navn == punktsamling_B.navn:
            continue

        # Mængde af punkter i Punktsamling B
        punkter_B = {pkt.ident for pkt in punktsamling_B.punkter}

        if punkter_A == punkter_B:
            ligmed.add(punktsamling_B.navn)
        elif punkter_A.issubset(punkter_B):
            subset.add(punktsamling_B.navn)
        elif punkter_A.issuperset(punkter_B):
            superset.add(punktsamling_B.navn)

    return ligmed, subset, superset


def opret_ny_tidsserie(
    punkt: Punkt, punktsamling: PunktSamling, tidsserienavn: str = None
) -> Tidsserie:
    """
    Opretter ny højdetidsserie

    Hvis intet tidsserienavn angives, så bruges default-navnet: [IDENT]_HTS_[JESSENNR]. Hvis der findes
    en tidsserie med samme navn i forvejen, vil funktionen fejle.
    """
    if not tidsserienavn:
        tidsserienavn = (
            f"{punkt.ident}_HTS_{punktsamling.jessenpunkt.jessennummer}"  # Default navn
        )

    try:
        tidsserie = fire.cli.firedb.hent_tidsserie(tidsserienavn)
    except NoResultFound:
        pass
    else:
        fire.cli.print(
            f"FEJL: Tidsserien '{tidsserienavn}' eksisterer allerede. ",
            fg="black",
            bg="yellow",
        )
        raise SystemExit

    if punkt not in punktsamling.punkter:
        punktsamling.tilføj_punkter([punkt])

    tidsserie = HøjdeTidsserie(
        punkt=punkt,
        punktsamling=punktsamling,
        navn=tidsserienavn,
        formål=f"",
    )

    return tidsserie


def opret_ny_punktsamling(
    jessenpunkt: Punkt, punkter: list[Punkt], punktsamlingsnavn: str = None
) -> PunktSamling:
    """
    Opretter ny punktsamling og tilhørende højdetidsserier

    Hvis intet punktsamlingsnavn angives, så bruges default-navnet PUNKTSAMLING_[JESSENNR].
    Hvis der findes en punktsamling med samme navn i forvejen, vil funktionen fejle.

    Punkter som skal indgå i punktsamling angives med "punkter". Der oprettes også
    højdetidsserier for alle disse punkter. Tidsserierne oprettes med default-navne.
    """
    if not punktsamlingsnavn:
        punktsamlingsnavn = f"PUNKTSAMLING_{jessenpunkt.jessennummer}"  # Default navn

    try:
        punktsamling = fire.cli.firedb.hent_punktsamling(punktsamlingsnavn)
    except NoResultFound:
        pass
    else:
        fire.cli.print(
            f"FEJL: Punktsamlingen '{punktsamlingsnavn}' eksisterer allerede. "
            f"Anvend 'fire niv udtræk-punktsamling' for at udtrække og redigere i eksisterende punktsamlinger.",
            fg="black",
            bg="yellow",
        )
        raise SystemExit

    # fjern dubletter med list(set( ... ))
    punkter = list(set([jessenpunkt] + punkter))
    punktsamling = PunktSamling(
        navn=punktsamlingsnavn,
        formål="",
        jessenpunkt=jessenpunkt,
        jessenkoordinat=None,  # Nye punktsamlinger får ikke nogen jessenkote
        punkter=punkter,
    )

    # Opret tidsserier for alle de nye punkter
    tidsserier = [opret_ny_tidsserie(punkt, punktsamling) for punkt in punkter]

    return punktsamling


def generer_arkdata(punktsamling: PunktSamling) -> tuple[list, list]:
    """Genererer data ud fra en Punktsamling, til indsættelse i punktsamlings- og højdetidsseriearkene"""
    ps_data = [
        (
            punktsamling.navn,
            punktsamling.jessenpunkt.ident,
            punktsamling.jessenpunkt.jessennummer,
            punktsamling.jessenkote,
            punktsamling.formål,
        )
    ]

    # Finder først punktsamlingens tidsserier
    hts_data = [
        (
            punktsamling.navn,
            hts.punkt.ident,
            ("x" if hts.punkt == punktsamling.jessenpunkt else ""),
            hts.navn,
            hts.formål,
            "Jessen",
        )
        for hts in punktsamling.tidsserier
        if hts.registreringtil is None
    ]

    # Dernæst finder vi punktsamlingens punkter, som ikke har nogen tidsserier
    hts_data += [
        (
            punktsamling.navn,
            punkt.ident,
            ("x" if punkt == punktsamling.jessenpunkt else ""),
            "Ingen tidsserie fundet",
            "Ingen tidsserie fundet",
            "Jessen",
        )
        for punkt in punktsamling.punkter
        if punkt
        not in [
            hts.punkt for hts in punktsamling.tidsserier if hts.registreringtil is None
        ]
    ]

    return ps_data, hts_data
