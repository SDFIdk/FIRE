"""
Implementerer kommandoen `fire niv udtræk-observationer`

"""

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
from fire.ident import klargør_identer_til_søgning
from fire.io.regneark import (
    til_nyt_ark_observationer,
    til_nyt_ark_punktoversigt,
    skriv_data,
)
from fire.srid import SRID
from fire.api.model.punkttyper import (
    Punkt,
)
from fire.api.niv.datatyper import (
    NivMetode,
    Nøjagtighed,
)
from fire.api.niv.udtræk_observationer import (
    filterkriterier,
    polygoner,
    klargør_geometrifiler,
    søgefunktioner_med_valgte_metoder,
    brug_alle_på_alle,
    observationer_inden_for_spredning,
    filtrer_præcisionsnivellement,
    timestamp,
    ResultatSæt,
)
import fire.cli
from fire.cli.niv import (
    niv as niv_command_group,
    er_projekt_okay,
    KOTESYSTEMER,
)
from fire.io.geojson import (
    skriv_punkter_geojson,
    skriv_observationer_geojson,
)

from fire.typologi import (
    adskil_filnavne,
    adskil_identer,
)
from fire.cli.click_types import Datetime


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

Vælg mellem [P]ræcision, [K]valitet, [D]etail eller [U]kendt.

Er nøjagtighed ukendt, bliver observationerne ikke filtreret på nøjagtighed.
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
    help=f"Hent observationer fra og med denne dato. Angives på formen {DATE_FORMAT}.",
    required=False,
    type=Datetime(format=DATE_FORMAT),
)
@click.option(
    "-dt",
    "--til",
    help=f"Hent observationer til, men ikke med, denne dato. Angives på formen {DATE_FORMAT}.",
    required=False,
    type=Datetime(format=DATE_FORMAT),
)
@click.option(
    "-ao",
    "--alle-obs",
    help="Hent alle observationer til de adspurgte punkter.",
    required=False,
    is_flag=True,
)
@click.option(
    "--kotesystem",
    help="Angiv andet kotesystem end DVR90",
    required=False,
    type=click.Choice(KOTESYSTEMER.keys()),
    default="DVR90",
)
@click.option(
    "--præc",
    "-P",
    help="""Hent observationer fra valgt præcisionsnivellement.

Vælges `0` udtrækkes kun observationer som ikke indgik i nogen af de 3 præcisionsnivellementer.
""",
    required=False,
    type=click.IntRange(0, 3),
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
    alle_obs: bool,
    kotesystem: str,
    præc: int,
    # These `kwargs` can be ignored for now, since they refer to default
    # CLI options that are already in effect by use of call-back functions.
    **kwargs,
) -> None:
    """
    Udtræk nivellement-observationer for et eksisterende projekt ud fra søgekriterier.

    Kriterierne kan være både identer (landsnumre) og geometri-filer. Programmet skelner
    automatisk kriterierne fra hinanden. Kriterier, der ikke passer i disse kategorier,
    bliver vist i terminal-output og derefter ignoreret. Bemærk at data i geometrifiler skal
    være refereret til WGS84.

    **Eksempel**::

        fire niv udtræk-observationer SAG 125-03-09003 rectangle.geojson

    I et allerede oprettet et projekt, kan man fremsøge observationer inden for et givet
    tidsrum (fra og til), givet standard kvalitetskriterier samt observationsmetode og
    afstand til identer/geometri.

    Det er kombinationen af valgt nøjagtighed og metode, der afgør valget af kriterium,
    hvormed fundne observationer skal filtreres fra. Derudover kan man vælge om
    observationerne skal have indgået i et af de 3 landsdækkende præcisionsnivellementer.
    Resultatet af søgningen er samtlige, aktive observationer i databasen, der opfylder
    ovenstående.

    Resultatet skrives til det eksisterende projekt-regneark i fanerne
    "Observationer" og "Punktoversigt".

    \f
    .. warning:: Eksisterende data i disse ark overskrives!

    **Fremsøgningsproces**

    Kommandolinje-argumenterne afgør fremsøgningsprocessen. Se de enkelte
    kommandolinje-argumenters dokumentation herunder for flere detaljer om deres
    betydning for fremsøgningsprocessen.

    Ved angivelse af identer i KRITERIER fremsøges kun observationer mellem de adspurgte
    punkter. Ønskes alle observationer til de adspurgte punkter kan ``--alle-obs``
    tilføjes kaldet.

    **Geometrifiler**

    Det er muligt at søge inden for en vilkårlig polygon, i punkter og langs linjer.
    Sidstnævnte kan eksempelvis bruges sammen med en bufferafstand til at søge langs
    en vej, hvis forløb er angivet linjestykker i geometrifilen. Man kan altså søge
    langs vilkårlige vejsegmenter eller hvad som helst andet, man ønsker.
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
            funktion = db.hent_observationer_fra_opstillingspunkt
            fastholdte_argumenter = dict(
                tid_fra=fra,
                tid_til=til,
                kun_aktive=True,
                sigtepunkter=punkter,
            )

            if alle_obs:
                # Når ingen sigtepunkter angives hentes alle observationer til opstillingspunktet
                fastholdte_argumenter.pop("sigtepunkter")

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
        søgefunktioner = søgefunktioner_med_valgte_metoder(
            forberedt_søgefunktion, metoder
        )

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
        søgefunktioner = søgefunktioner_med_valgte_metoder(
            forberedt_søgefunktion, metoder
        )
        resultatsæt |= set(brug_alle_på_alle(søgefunktioner, klargjorte_geometrier))

    if not resultatsæt:
        raise SystemExit("Ingen observationer fundet")

    # Anvend kvalitetskriterier
    # -------------------------

    fire.cli.print("Filtrér observationer")
    observationer = list(observationer_inden_for_spredning(resultatsæt, spredning))

    if præc:
        observationer = filtrer_præcisionsnivellement(observationer, præc)

    fire.cli.print("Indsaml opstillings- og sigtepunkter fra observationer")
    opstillings_punkter = db.hent_punkter_fra_uuid_liste(
        o.opstillingspunktid for o in observationer
    )
    sigte_punkter = db.hent_punkter_fra_uuid_liste(
        o.sigtepunktid for o in observationer
    )
    punkter = list(set(opstillings_punkter) | set(sigte_punkter))
    # Gem resultatet
    # --------------

    # Regneark
    srid = fire.cli.firedb.hent_srid(kotesystem)
    fire.cli.print("Gem observationer og punkter i projekt-regnearket")
    ark_observationer = til_nyt_ark_observationer(observationer)
    ark_punktoversigt = til_nyt_ark_punktoversigt(punkter, srid=srid)
    ark_punktoversigt["System"] = (srid.kortnavn or srid.name)

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
    fire.cli.print(f"Gem punkter og observationer som .geojson-fil...")
    skriv_punkter_geojson(projektnavn, ark_punktoversigt, infiks=f"-{timestamp()}")
    skriv_observationer_geojson(
        projektnavn,
        ark_punktoversigt.set_index("Punkt"),
        ark_observationer,
        infiks=f"-{timestamp()}",
    )
