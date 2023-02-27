"""
Funktionalitet til `fire niv udtræk-observationer`

"""

import pathlib
import datetime as dt
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Mapping,
    Set,
    Tuple,
    Union,
)
from functools import partial

import fiona
from shapely import geometry
import pandas as pd

from fire.srid import SRID
from fire.api.model import (
    Punkt,
    ObservationstypeID,
    Observation,
    GeometriskKoteforskel,
    TrigonometriskKoteforskel,
    Geometry,
)
from fire.api.niv.enums import (
    NivMetode,
    Nøjagtighed,
)
from fire.api.niv.kriterier import (
    EMPIRISK_SPREDNING,
    mildeste_kvalitetskrav,
)


# Typer til annotation
NivellementObservation = Union[GeometriskKoteforskel, TrigonometriskKoteforskel]
ResultatSæt = Set[NivellementObservation]
ObservationstypeIDType = int
Spredning = float
Spredninger = Mapping[ObservationstypeIDType, Spredning]

OBSKLASSE = {
    NivMetode.MGL: GeometriskKoteforskel,
    NivMetode.MTL: TrigonometriskKoteforskel,
}
"Oversætter mellem nivellementsmetode og observationsklasse."


def timestamp() -> str:
    return dt.datetime.now().isoformat()[:19].replace(":", "")


def brug_alle_på_alle(
    operationer: Iterable[Callable], objekter: Iterable[Any]
) -> Iterator[Any]:
    """
    Udfør hver operation på hvert objekt og returnér resultaterne.

    """
    return (
        resultat
        for operation in operationer
        for objekt in objekter
        for resultat in operation(objekt)
    )


def filterkriterier(nøjagtigheder: Iterable[Nøjagtighed]) -> Spredninger:
    """
    Returnerer en dictionary med en spredning for hver
    kombination af nivellementsmetode og valgte nøjagtigheder.

    """
    krav = partial(
        mildeste_kvalitetskrav,
        nøjagtigheder=nøjagtigheder,
        mapping=EMPIRISK_SPREDNING,
    )
    return {
        ObservationstypeID.geometrisk_koteforskel: krav(metoder=[NivMetode.MGL]),
        ObservationstypeID.trigonometrisk_koteforskel: krav(metoder=[NivMetode.MTL]),
    }


def klargør_geometrifiler(geometrifiler: Iterable[str]) -> List[Geometry]:
    """
    Returnerer samlet liste med hvert lag i hver fil.

    Hver geometrifil kan have flere features eller lag.

    Åbn og konvertér indhold af geometrifiler.

    """
    klargjorte_geometrier: List[Geometry] = []
    for filnavn in geometrifiler:
        geometri_data = fiona.open(filnavn)

        # Validér
        crs = geometri_data.crs.get("init")
        if crs.upper() != SRID.WGS84:
            continue

        # Konvertér indhold til shapely-objekter
        delgeometrier = [
            geometry.shape(delgeometri.get("geometry")) for delgeometri in geometri_data
        ]
        # Opret Geometry-instanser
        klargjorte_geometrier.extend([Geometry(dgb.wkt) for dgb in delgeometrier])
        geometri_data.close()

    return klargjorte_geometrier


def opstillingspunkter(observationer: Iterable[Observation]) -> List[Punkt]:
    """Returnerer unikke opstillingspunkter for observationerne."""
    return list(set(o.opstillingspunkt for o in observationer))


def punkter_til_geojson(data: pd.DataFrame) -> dict:
    """Konvertér punkter til geojson-tekststreng."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {k: v for k, v in row.items()},
                "geometry": {
                    "type": "Point",
                    "coordinates": row[["Øst", "Nord"]].tolist(),
                },
            }
            for _, row in data.iterrows()
        ],
    }


def søgefunktioner_med_valgte_metoder(
    forberedt_søgefunktion: Callable, metoder: List[NivMetode]
) -> Iterator[Callable]:
    """Returnerer en søgefunktion med fastsatte argumenter for hver metode."""
    return (
        partial(forberedt_søgefunktion, observationsklasse=OBSKLASSE[metode])
        for metode in metoder
    )


def polygoner(punkter: Iterable[Punkt], buffer: int) -> Iterator[Geometry]:
    """Returnerer en søgeklar liste med Geometry-instanser til søgning i databasen."""
    # Hent punkternes WGS84-koordinater:
    # Geometri-koordinaterne er altid i WGS84.
    koordinatsæt = (punkt.geometri.koordinater for punkt in punkter)

    # Opbyg geometri for punkt-koordinater til søgning.
    shapely_punkter = (geometry.Point(*koordinater) for koordinater in koordinatsæt)

    # Lav den endelige søge-geometri ved at bruge den angivne buffer som
    # radius i en forsimplet cirkel (polygon) omkring koordinaterne.
    shapely_polygoner = (punkt.buffer(buffer) for punkt in shapely_punkter)

    # Tilføj polygonerne for de enkelte identer til geometrier, der skal søges i nærheden af.
    # Opret samtidig et geometri-objekt med hver søge-geometris Well-Known Text (WKT).
    return (Geometry(polygon.wkt) for polygon in shapely_polygoner)


def observationer_inden_for_spredning(
    resultatsæt: ResultatSæt, spredninger: Spredninger
) -> Iterator[NivellementObservation]:
    return (
        observation
        for observation in list(resultatsæt)
        if observation.spredning_afstand <= spredninger[observation.observationstypeid]
    )
