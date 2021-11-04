# CLI: fire niv udtræk-observationer

import json
import pathlib
import datetime as dt
from typing import (
    Any,
    Callable,
    List,
    Tuple,
)
from functools import partial

import click
import fiona
from shapely import geometry
import pandas as pd

from fire.ident import kan_være_ident
from fire.enumtools import (
    enum_names,
    selected_or_default,
)
from fire.api.model import Geometry
from fire.api.model.punkttyper import (
    Punkt,
    ObservationsTypeID,
    Observation,
    GeometriskKoteforskel,
    TrigonometriskKoteforskel,
)
from fire.api.niv import (
    DVR90_navn,
    NivMetode,
    Nøjagtighed,
)
from fire.api.niv.kriterier import (
    EMPIRISK_SPREDNING,
    mildeste_kvalitetskrav,
)
import fire.cli
from fire.cli.niv import (
    er_projekt_okay,
    niv as niv_command_group,
    ARKDEF_OBSERVATIONER,
    ARKDEF_PUNKTOVERSIGT,
)
from fire.cli.click_types import Datetime
from fire.ident import klargør_ident_til_søgning
from fire.io.regneark import (
    observationsrække,
    punktrække,
    til_nyt_ark,
    skriv_data,
)


DATE_FORMAT = "%d-%m-%Y"
"Dato-format til kommandolinie-argument."


def adskil_kriterier(kriterier: List[str]) -> Tuple[str]:
    kriterier = set(kriterier)
    geometrifiler = [
        kriterium for kriterium in kriterier if pathlib.Path(kriterium).is_file()
    ]
    kriterier -= set(geometrifiler)
    identer = [kriterium for kriterium in kriterier if kan_være_ident(kriterium)]
    ubrugelige = kriterier - set(identer)
    return identer, geometrifiler, ubrugelige


def klargør_geometrifiler(geometrifiler: List[str]) -> List[Geometry]:
    """
    Åbn og konvertér indhold af geometrifiler.

    """
    klargjorte_geometrier: List[Geometry] = []
    for filnavn in geometrifiler:
        geometri_data = fiona.open(filnavn)

        try:
            # Validér
            crs = geometri_data.crs.get("init")
            assert (
                crs.lower() == "epsg:4326"
            ), f"Kan indtil videre kun læse geometrifiler, der anvender EPSG:4326. Modtog {crs!r} fra {filnavn!r}."

            # Konvertér indhold til shapely-objekter
            delgeometrier = [
                geometry.shape(delgeometri.get("geometry"))
                for delgeometri in geometri_data
            ]
            # Opret Geometry-instanser
            klargjorte_geometrier.extend([Geometry(dgb.wkt) for dgb in delgeometrier])
        finally:
            geometri_data.close()

    return klargjorte_geometrier


def opstillingspunkter(observationer: List[Observation]) -> List[Punkt]:
    """Returnerer unikke opstillingspunkter for observationerne."""
    return list(set(o.opstillingspunkt for o in observationer))


def punkter_til_geojson(data: pd.DataFrame) -> dict:
    """Konvertér punkter til geojson-tekststreng."""
    return {
        "type": "FeatureCollection",
        "Features": [
            {
                "type": "Feature",
                "properties": {k: v for k, v in row.iteritems()},
                "geometry": {
                    "type": "Point",
                    "coordinates": row[["Øst", "Nord"]].tolist(),
                },
            }
            for _, row in data.iterrows()
        ],
    }


def timestamp():
    return dt.datetime.now().isoformat()[:19].replace(":", "")


@niv_command_group.command()
# Following Click manual advice and not setting required=True on kriterier.
# Instead, we just exit the command, since no `kriterier` means search everywhere.
@click.argument("projektnavn", nargs=1, type=str)
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
    type=int,
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

    # Validering
    # ----------

    er_projekt_okay(projektnavn)

    ofname = pathlib.Path(f"{projektnavn}.xlsx").absolute()
    assert ofname.is_file(), f"{ofname!r} eksisterer ikke."

    # Buffer
    if buffer < 0:
        fire.cli.print(f"Buffer kan ikke være mindre end nul. Fik {buffer!r} .", fg='red')
        raise SystemExit

    metoder = selected_or_default(metode, NivMetode)
    nøjagtigheder = selected_or_default(nøjagtighed, Nøjagtighed)

    # Hent filterkriterier
    filterkriterium = partial(
        mildeste_kvalitetskrav, nøjagtigheder=nøjagtigheder, mapping=EMPIRISK_SPREDNING
    )
    SPREDNING = {
        ObservationsTypeID.geometrisk_koteforskel: filterkriterium(
            metoder=[NivMetode.MGL]
        ),
        ObservationsTypeID.trigonometrisk_koteforskel: filterkriterium(
            metoder=[NivMetode.MTL]
        ),
    }

    # Tag brugbare kriterier og advar eventuelt om ubrugelige.
    identer, geometrifiler, ubrugelige = adskil_kriterier(kriterier)

    # Check resultaterne
    if len(geometrifiler) > 1:
        fire.cli.print("Det er indtil videre forventet, at der kun bliver oplyst én geometrifil ad gangen.", fg='red')
        raise SystemExit
    if len(ubrugelige) > 0:
        fire.cli.print(f"Følgende kriterier er hverken en korrekt-formuleret ident eller geometrifil: {ubrugelige!r}", bold=True)

    # Klargør søgninger
    # -----------------

    DVR90 = fire.cli.firedb.hent_srid(DVR90_navn)
    OBSKLASSE = {
        NivMetode.MGL: GeometriskKoteforskel,
        NivMetode.MTL: TrigonometriskKoteforskel,
    }

    # Her gemmes alle observationer
    resultatsæt = set()

    # Genvejsvariabel
    db = fire.cli.firedb

    fire.cli.print("Klargør identer", bold=True)
    identer_klargjort: List[str] = [klargør_ident_til_søgning(ident) for ident in identer]

    fire.cli.print("Søg i databasen efter punkter til hver ident", fg="yellow")
    punkter: List[Punkt] = db.hent_punkt_liste(identer_klargjort)

    # Punkt-scenarium 1 - Buffer == 0
    # Vi søger kun observationer med identerne som opstillingspunkter.
    if buffer == 0:

        fire.cli.print("Hent observationer for identerne", fg="yellow")
        hent_observationer = partial(
            db.hent_observationer_fra_opstillingspunkt,
            tid_fra=fra,
            tid_til=til,
            srid=DVR90,
            kun_aktive=True,
        )
        hentere = [
            partial(hent_observationer, observationsklasse=OBSKLASSE[metode])
            for metode in metoder
        ]
        resultatsæt |= set(brug_alle_på_alle(hentere, punkter))

    # / Punkt-scenarium 1

    # Punkt-scenarium 2: Buffer er angivet
    # Vi søger observationer og punkter i nærheden af identernes placering.

    else:

        # Hent punkternes WGS84-koordinater:
        # Geometri-koordinaterne er altid i WGS84.
        koordinatsæt = [punkt.geometri.koordinater for punkt in punkter]

        # Opbyg geometri for punkt-koordinater til søgning.
        shapely_punkter = [geometry.Point(*koordinater) for koordinater in koordinatsæt]

        # Lav den endelige søge-geometri ved at bruge den angivne buffer som
        # radius i en forsimplet cirkel (polygon) omkring koordinaterne.
        shapely_polygoner = [punkt.buffer(buffer) for punkt in shapely_punkter]

        # Tilføj polygonerne for de enkelte identer til geometrier, der skal søges i nærheden af.
        # Opret samtidig et geometri-objekt med hver søge-geometris Well-Known Text (WKT).
        søge_geometrier = [Geometry(polygon.wkt) for polygon in shapely_polygoner]

        fire.cli.print(
            f"Hent observationer inden for {buffer:d} m af identerne.", fg="yellow"
        )
        hent_observationer = partial(
            db.hent_observationer_naer_geometri,
            afstand=0,
            tid_fra=fra,
            tid_til=til,
        )
        hentere = [
            partial(hent_observationer, observationsklasse=OBSKLASSE[metode])
            for metode in metoder
        ]
        resultatsæt |= set(brug_alle_på_alle(hentere, søge_geometrier))

    # / Punkt-scenarium 2

    if geometrifiler:
        fire.cli.print("Klargør geometrifiler", bold=True)
        # Hver geometrifil kan have flere features eller lag
        # Foretag søgning for hvert lag i hver fil:

        klargjorte_geometrier = klargør_geometrifiler(geometrifiler)

        # Hent observationer inden for geometrien og med den angivne buffer.
        fire.cli.print(
            "Hent observationer for hvert lag/hver feature i geometrifilerne",
            fg="yellow",
        )
        hent_observationer = partial(
            db.hent_observationer_naer_geometri,
            afstand=buffer,
            tid_fra=fra,
            tid_til=til,
        )
        hentere = [
            partial(hent_observationer, observationsklasse=OBSKLASSE[metode])
            for metode in metoder
        ]
        resultatsæt |= set(brug_alle_på_alle(hentere, klargjorte_geometrier))

    fire.cli.print("Filtrér observationer")
    observationer = [
        observation
        for observation in list(resultatsæt)
        if observation.spredning_afstand <= SPREDNING[observation.observationstypeid]
    ]

    fire.cli.print("Indsaml opstillingspunkter fra observationer")
    punkter = opstillingspunkter(observationer)

    fire.cli.print("Gem observationer og punkter i projekt-regnearket")
    ark_observationer = til_nyt_ark(
        observationer, ARKDEF_OBSERVATIONER, observationsrække, "Hvornår"
    )
    ark_punktoversigt = til_nyt_ark(punkter, ARKDEF_PUNKTOVERSIGT, punktrække, "Punkt")
    fire.cli.print('Check: Alle punkter i regnearket Punktoversigt findes i Observationer[Fra]: ', nl=False)
    if not all(ark_punktoversigt["Punkt"].isin(ark_observationer["Fra"])):
        fire.cli.print("Nej", fg='red')
    else:
        fire.cli.print("Ja", fg='green')

    # Forbered ark-skrivning
    faner = {
        "Observationer": ark_observationer,
        "Punktoversigt": ark_punktoversigt,
    }

    fire.cli.print(f"Skriver til {ofname}...")
    read_and_update = "r+b"
    with open(ofname, read_and_update) as output:
        skriv_data(output, faner)

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


def brug_alle_på_alle(operationer: List[Callable], objekter: List[Any]):
    """
    For hver henter og hvert søgeobjekt hentes resultater.
    """
    return (
        operation(objekt)
        for operation in operationer
        for objekt in objekter
    )
