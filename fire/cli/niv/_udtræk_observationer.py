# CLI: fire niv udtræk-observationer

import json
import pathlib
import datetime as dt
from functools import partial
from typing import (
    List,
    Tuple,
)

import click

from fire.enumtools import (
    enum_names,
    selected_or_default,
)
from fire.api.model.punkttyper import (
    Punkt,
)
from fire.api.niv import (
    DVR90_navn,
    NivMetode,
    Nøjagtighed,
)
import fire.cli
from fire.cli.niv import (
    niv as niv_command_group,
    ARKDEF_OBSERVATIONER,
    ARKDEF_PUNKTOVERSIGT,
)
from fire.ident import klargør_identer_til_søgning
from fire.io.regneark import (
    observationsrække,
    punktrække,
    til_nyt_ark,
    skriv_data,
)
from fire.api.niv.udtræk_observationer import (
    filterkriterier,
    adskil_filnavne,
    adskil_identer,
    polygoner,
    klargør_geometrifiler,
    søgefunktioner_med_valgte_metoder,
    brug_alle_på_alle,
    observationer_inden_for_spredning,
    opstillingspunkter,
    timestamp,
    punkter_til_geojson,
    ResultatSæt,
)
from fire.cli.click_types import Datetime
from fire.cli.niv import er_projekt_okay


DATE_FORMAT = "%d-%m-%Y"
"Dato-format til kommandolinie-argument."


def valider_om_projekt_er_okay(ctx, param, value):
    """
    Kalder valideringslogikken i `er_projekt_okay()`,
    som stopper programmet, hvis det ikke er ok.

    """
    er_projekt_okay(value)
    return value


@niv_command_group.command()
# Following Click manual advice and not setting required=True on kriterier.
# Instead, we just exit the command, since no `kriterier` means search everywhere.
@click.argument("projektnavn", nargs=1, type=str, callback=valider_om_projekt_er_okay)
@click.argument("kriterier", nargs=-1, type=str)
@click.option(
    "-b",
    "--buffer",
    help="""Positiv afstand i meter fra geometri eller identer.

Et område på en bredde af bufferens størrelse føjes til identers placering
og geometrier, som søgningen skal medtage under udvælgelsen af observationer.

Søgefremgangsmåden styres af, om `buffer` = 0 og `buffer` > 0:

For identer sker det på følgende måde:

    `buffer` == 0: Fremsøg observationer med identen som opstillingspunkt.

    `buffer` >= 0: Fremsøg observationer inden for `buffer` meter af identens placering.

For geometrifiler sker det således:

    `buffer` == 0: Fremsøg observationer på eller inden for geometrien.

    `buffer` >= 0: Fremsøg observationer inden for `buffer` meter af geometriens omfang.
""",
    required=False,
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
)
@click.option(
    "-n",
    "--nøjagtighed",
    help="""Målenøjagtighed på observationer.

Vælg mellem [P]ræcision, [K]valitet eller [D]etail.

Er nøjagtighed ikke angivet, bliver det mildeste kriterium valgt (detail).
""",
    required=False,
    # Ville være rart, hvis click havde implementeret mulighed for at anvende Enum'er.
    # Mere info: https://github.com/pallets/click/issues/605
    type=click.Choice(enum_names(Nøjagtighed), case_sensitive=False),
    default=None,
    show_default=True,
)
@click.option(
    "-M",
    "--metode",
    help="""Målemetode.

Vælg mellem `MGL` (motoriseret geometrisk nivellement) eller `MTL` (motoriseret trigonometrisk nivellement).

Er metode ikke angivet, søger programmet blandt begge observationstyper.
""",
    required=False,
    # Ville være rart, hvis click havde implementeret mulighed for at anvende Enum'er.
    # Mere info: https://github.com/pallets/click/issues/605
    type=click.Choice(enum_names(NivMetode), case_sensitive=False),
    default=None,
    show_default=True,
)
@click.option(
    "-df",
    "--fra",
    help="Hent observationer fra og med denne dato.",
    required=False,
    type=Datetime(format=DATE_FORMAT),
)
@click.option(
    "-dt",
    "--til",
    help="Hent observationer til, men ikke med, denne dato.",
    required=False,
    type=Datetime(format=DATE_FORMAT),
)
@fire.cli.default_options()
def udtræk_observationer(
    projektnavn: str,
    kriterier: Tuple[str],
    buffer: int,
    nøjagtighed: str,
    metode: str,
    fra: dt.datetime,
    til: dt.datetime,
    # These `kwargs` can be ignored for now, since they refer to default
    # CLI options that are already in effect by use of call-back functions.
    **kwargs,
) -> None:
    """
    Udtræk nivellement-observationer for et eksisterende projekt ud fra søgekriterier.

    KRITERIER kan være både identer (landsnumre) og geometri-filer.
    
    Programmet skelner automatisk kriterierne fra hinanden. Kriterier, der ikke
    passer i disse kategorier, bliver vist i terminal-output og derefter ignoreret.

        BEMÆRK: Geometrifiler skal være i WGS84

    Eksempel:

        fire niv udtræk-observationer projekt_x 125-03-09003 rectangle.geojson

    Brugscenarium:

        En bruger, der har oprettet et projekt, kan fremsøge observationer
        inden for et givet tidsrum (fra og til), givet standard kvalitets-
        kriterier samt observationsmetode og afstand til identer/geometri.

        Det er kombinationen af valgt nøjagtighed og metode, der afgør valget
        af kriterium, hvormed fundne observationer skal filtreres fra.

        Resultatet af søgningen er samtlige, aktive observationer i databasen,
        der opfylder ovenstående.

        Resultatet skrives til det eksisterende projekt-regneark i fanerne
        `Observationer` og `Punktoversigt`.

            BEMÆRK: Eksisterende data i disse ark overskrives!

    Fremsøgningsproces:

        Kommandolinie-argumenterne afgør fremsøgningsprocessen.

        Se de enkelte kommando-linie-argumenters dokumentation for flere
        detaljer om deres betydning for fremsøgningsprocessen.

    """

    # Arrangér kommandolinie-inputtet
    # -------------------------------

    ofname = pathlib.Path(f"{projektnavn}.xlsx").absolute()
    metoder = selected_or_default(metode, NivMetode)
    nøjagtigheder = selected_or_default(nøjagtighed, Nøjagtighed)
    spredning = filterkriterier(nøjagtigheder)
    geometrifiler, kriterier = adskil_filnavne(kriterier)
    identer, ubrugelige = adskil_identer(kriterier)

    # Check resultaterne
    if len(ubrugelige) > 0:
        fire.cli.print("Fandt ugyldige ident-formater eller filnavne:", bold=True)
        fire.cli.print("* " + "\n* ".join(ubrugelige))

    # Søg i databasen
    # ---------------

    # Her gemmes alle observationer
    resultatsæt: ResultatSæt = set()

    # Genvej
    db = fire.cli.firedb

    # Søg baseret på identer
    if identer:

        fire.cli.print("Klargør identer", bold=True)
        identer_klargjort: List[str] = klargør_identer_til_søgning(identer)

        fire.cli.print("Søg i databasen efter punkter til hver ident", fg="yellow")
        punkter: List[Punkt] = db.hent_punkt_liste(identer_klargjort)

        if buffer == 0:
            # Vi søger kun observationer med identerne som opstillingspunkter.
            fire.cli.print("Søg med punkterne som opstillingspunkt", fg="yellow")
            objekter = punkter
            # Forbereder søgefunktion med argumenter fastsat.
            DVR90 = db.hent_srid(DVR90_navn)
            funktion = db.hent_observationer_fra_opstillingspunkt
            fastholdte_argumenter = dict(tid_fra=fra, tid_til=til, srid=DVR90, kun_aktive=True)
            forberedt_søgefunktion = partial(funktion, **fastholdte_argumenter)

        else:  # Buffer > 0
            # Vi søger observationer og punkter i nærheden af identernes placering.
            fire.cli.print(f"Søg inden for {buffer:d} m af punkterne.", fg="yellow")
            objekter = polygoner(punkter, buffer)
            # Forbereder søgefunktion med argumenter fastsat.
            funktion = db.hent_observationer_naer_geometri
            fastholdte_argumenter = dict(afstand=0, tid_fra=fra, tid_til=til)
            forberedt_søgefunktion = partial(funktion, **fastholdte_argumenter)

        # Byg søgefunktioner (én for hver valgt metode)
        søgefunktioner = søgefunktioner_med_valgte_metoder(forberedt_søgefunktion, metoder)

        # Hent observationerne
        resultatsæt |= set(brug_alle_på_alle(søgefunktioner, objekter))

    # Søg baseret på geometrifiler
    if geometrifiler:
        fire.cli.print("Klargør geometrifiler", bold=True)
        klargjorte_geometrier = klargør_geometrifiler(geometrifiler)

        # Hent observationer inden for geometrien og med den angivne buffer.
        fire.cli.print("Søg for hvert lag/hver feature i geometrifilerne", fg="yellow")
        # Forbereder søgefunktion med argumenter fastsat.
        funktion = db.hent_observationer_naer_geometri
        fastholdte_argumenter = dict(afstand=buffer, tid_fra=fra, tid_til=til)
        forberedt_søgefunktion = partial(funktion, **fastholdte_argumenter)
        søgefunktioner = søgefunktioner_med_valgte_metoder(forberedt_søgefunktion, metoder)
        resultatsæt |= set(brug_alle_på_alle(søgefunktioner, klargjorte_geometrier))

    # Anvend kvalitetskriterier
    # -------------------------

    fire.cli.print("Filtrér observationer")
    observationer = list(observationer_inden_for_spredning(resultatsæt, spredning))

    fire.cli.print("Indsaml opstillingspunkter fra observationer")
    punkter = opstillingspunkter(observationer)

    # Gem resultatet
    # --------------

    # Regneark
    fire.cli.print("Gem observationer og punkter i projekt-regnearket")
    ark_observationer = til_nyt_ark(
        observationer,
        ARKDEF_OBSERVATIONER,
        observationsrække,
        "Hvornår",
    )
    ark_punktoversigt = til_nyt_ark(
        punkter,
        ARKDEF_PUNKTOVERSIGT,
        punktrække,
        "Punkt",
    )

    # Kontrol
    fire.cli.print('Check: Punktoversigt har alle punkter i Observationer[Fra]: ', nl=False)
    if not all(ark_punktoversigt["Punkt"].isin(ark_observationer["Fra"])):
        fire.cli.print("Nej", fg='red')
    else:
        fire.cli.print("Ja", fg='green')

    # Forbered ark-skrivning
    faner = {
        "Observationer": ark_observationer,
        "Punktoversigt": ark_punktoversigt,
    }

    # Skriv til regneark
    fire.cli.print(f"Skriver til {ofname}...")
    read_and_update = "r+b"
    with open(ofname, read_and_update) as output:
        skriv_data(output, faner)

    # GeoJSON primært til hurtig kontrolcheck af resultaternes placering
    fire.cli.print(f"Gem punkter som .geojson-fil...")
    kolonner = ["Punkt", "Type", "Nord", "Øst"]
    flettet = ark_observationer.merge(
        ark_punktoversigt[["Punkt", "Nord", "Øst"]],
        left_on="Fra",
        right_on="Punkt",
    )[kolonner]
    ofname = f"{projektnavn}-{timestamp()}.geojson"
    fire.cli.print(f"Skriver punkter til {ofname} ...")
    with open(ofname, "w+") as f:
        json.dump(punkter_til_geojson(flettet), f, indent=2)
