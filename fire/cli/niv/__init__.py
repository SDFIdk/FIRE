# Python infrastrukturelementer
import json
import os
import os.path
import subprocess
import sys
import webbrowser

from datetime import datetime
from enum import IntEnum
from itertools import chain
from math import hypot, sqrt
from typing import Dict, List, Set, Tuple
from fire import uuid

# Tredjepartsafhængigheder
import click
import pandas as pd
import xmltodict

from pyproj import Proj
from sqlalchemy.orm.exc import NoResultFound

# FIRE herself
import fire.cli
from fire.cli import firedb

# Typingelementer fra databaseAPIet.
from fire.api.model import (
    EventType,
    GeometriObjekt,
    Point,
    Punkt,
    Koordinat,
    Observation,
    PunktInformation,
    PunktInformationType,
    PunktInformationTypeAnvendelse,
    Sag,
    Sagsevent,
    SagseventInfo,
    Sagsinfo,
)




# ------------------------------------------------------------------------------
@click.group()
def niv():
    """Nivellement: Arbejdsflow, beregning og analyse

    Underkommandoerne:

        opret-sag

        udtræk-revision

        ilæg-revision

        ilæg-nye-punkter

        læs-observationer

        beregn-nye-koter

        ilæg-observationer

        ilæg-koter

        luk-sag

    definerer, i den anførte rækkefølge, nogenlunde arbejdsskridtene i et
    almindeligt opmålingsprojekt.

    OPRET-SAG registrerer sagen (projektet) i databasen og skriver det regneark,
    som bruges til at holde styr på arbejdet.

    UDTRÆK-REVISION udtrækker oversigt over eksisterende punkter i et område,
    til brug for punktrevision (herunder registrering af tabtgåede punkter).

    ILÆG-REVISION lægger opdaterede og nye punktattributter i databasen efter revision.

    ILÆG-NYE-PUNKTER lægger oplysninger om nyoprettede punkter i databasen, og tildeler
    bl.a. landsnumre til punkterne.

    LÆS-OBSERVATIONER læser råfilerne og skriver observationerne til regnearket så de
    er klar til brug i beregninger.

    BEREGN-NYE-KOTER beregner nye koter til alle punkter, og genererer rapporter og
    visualiseringsmateriale.

    ADJ er et synonym for BEREGN-NYE-KOTER, tilegnet nostalgikere og feinschmeckere.

    ILÆG-OBSERVATIONER lægger nye observationer i databasen.

    ILÆG-NYE-KOTER lægger nyberegnede koter i databasen.

    LUK-SAG arkiverer det afsluttende regneark og sætter sagens status til inaktiv.

    (i skrivende stund er ILÆG-REVISION og LUK-SAG endnu ikke implementeret, og
    ILÆG-NYE-PUNKTER står for en større overhaling)

    Eksempel:

    fire niv opret-sag andeby_2020 "Thomas Knudsen" "Testsag: Nyopmåling af Andeby"

    fire niv læs-observationer andeby_2020

    fire niv beregn-nye-koter andeby_2020

    fire niv ilæg-observationer andeby_2020

    fire niv ilæg-koter andeby_2020

    """
    pass


from .opret_sag import opret_sag




# ------------------------------------------------------------------------------
# Regnearksdefinitioner (søjlenavne og -typer)
# ------------------------------------------------------------------------------

ARKDEF_FILOVERSIGT = {"Filnavn": str, "Type": str, "σ": float, "δ": float}

ARKDEF_NYETABLEREDE_PUNKTER = {
    "Foreløbigt navn": str,
    "Landsnummer": str,
    "Nord": float,
    "Øst": float,
    "Etableret dato": "datetime64[ns]",
    "Hvem": str,
    "Beskrivelse": str,
    "Afmærkning": str,
    "Højde over terræn": float,
    "uuid": str,
}

ARKDEF_OBSERVATIONER = {
    "Journal": str,
    "Sluk": str,
    "Fra": str,
    "Til": str,
    "ΔH": float,
    "L": float,
    "Opst": int,
    "σ": float,
    "δ": float,
    "Kommentar": str,
    "Hvornår": "datetime64[ns]",
    "T": float,
    "Sky": int,
    "Sol": int,
    "Vind": int,
    "Sigt": int,
    "Kilde": str,
    "Type": str,
    "uuid": str,
}

ARKDEF_PUNKTOVERSIGT = {
    "Punkt": str,
    "Fasthold": str,
    "År": int,
    "Kote": float,
    "σ": float,
    "Ny kote": float,
    "Ny σ": float,
    "Δ-kote [mm]": float,
    "Opløft [mm/år]": float,
    "System": str,
    "Nord": float,
    "Øst": float,
    "uuid": str,
    "Udelad publikation": str,
}

ARKDEF_REVISION = {
    "Punkt": str,
    "Attribut": str,
    "Talværdi": float,
    "Tekstværdi": str,
    "Sluk": str,
    "Ret tal": float,
    "Ret tekst": str,
    "id": int,
    "Ikke besøgt": str,
}

ARKDEF_SAG = {
    "Dato": "datetime64[ns]",
    "Hvem": str,
    "Hændelse": str,
    "Tekst": str,
    "uuid": str,
}


# ------------------------------------------------------------------------------
# Hjælpefunktioner
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def anvendte(arkdef: Dict) -> str:
    """Anvendte søjler for given arkdef"""
    n = len(arkdef)
    if (n < 1) or (n > 26):
        return ""
    return "A:" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[n - 1]


# ------------------------------------------------------------------------------
def normaliser_placeringskoordinat(λ: float, φ: float) -> Tuple[float, float]:
    """Check op på placeringskoordinaterne.
    Hvis nogle ligner UTM, så regner vi om til geografiske koordinater.
    NaN og 0 flyttes ud i Kattegat, så man kan få øje på dem
    """

    if pd.isna(λ) or pd.isna(φ) or 0 == λ or 0 == φ:
        return (11.0, 56.0)

    # Heuristik til at skelne mellem UTM og geografiske koordinater.
    # Heuristikken fejler kun for UTM-koordinater fra et lille
    # område på 4 hektar ca. 500 km syd for Ghanas hovedstad, Accra.
    # Det er langt ude i Atlanterhavet, så det lever vi med.
    if abs(λ) < 100 and abs(φ) < 100:
        return (λ, φ)

    utm32 = Proj("proj=utm zone=32 ellps=GRS80", preserve_units=False)
    assert utm32 is not None, "Kan ikke initialisere projektionselelement utm32"
    return utm32(λ, φ, inverse=True)


# ------------------------------------------------------------------------------
def spredning(
    observationstype: str,
    afstand_i_m: float,
    antal_opstillinger: float,
    afstandsafhængig_spredning_i_mm: float,
    centreringsspredning_i_mm: float,
) -> float:
    """Apriorispredning for nivellementsobservation

    Fx.  MTL: spredning("mtl", 500, 3, 2, 0.5) = 1.25
         MGL: spredning("MGL", 500, 3, 0.6, 0.01) = 0.4243
         NUL: spredning("NUL", .....) = 0

    Rejser ValueError ved ukendt observationstype eller
    (via math.sqrt) ved negativ afstand_i_m.

    Negativ afstandsafhængig- eller centreringsspredning
    behandles som positive.

    Observationstypen NUL benyttes til at sammenbinde disjunkte
    undernet - det er en observation med forsvindende apriorifejl,
    der eksakt reproducerer koteforskellen mellem to fastholdte
    punkter
    """

    if "NUL" == observationstype.upper():
        return 0

    opstillingsafhængig = antal_opstillinger * (centreringsspredning_i_mm ** 2)

    if "MTL" == observationstype.upper():
        afstandsafhængig = afstandsafhængig_spredning_i_mm * afstand_i_m / 1000
        return hypot(afstandsafhængig, opstillingsafhængig)

    if "MGL" == observationstype.upper():
        afstandsafhængig = afstandsafhængig_spredning_i_mm * sqrt(afstand_i_m / 1000)
        return hypot(afstandsafhængig, opstillingsafhængig)

    raise ValueError(f"Ukendt observationstype: {observationstype}")




# -----------------------------------------------------------------------------
def skriv_ark(
    projektnavn: str, resultater: Dict[str, pd.DataFrame], suffix: str = "-resultat"
) -> None:
    """Skriv resultater til excel-fil"""
    if suffix == "-resultater":
        fire.cli.print(f"Skriver: {tuple(resultater)}")
        fire.cli.print(f"Til filen '{projektnavn}{suffix}.xlsx'")
    writer = pd.ExcelWriter(f"{projektnavn}{suffix}.xlsx", engine="xlsxwriter")
    for r in resultater:
        resultater[r].to_excel(writer, sheet_name=r, encoding="utf-8", index=False)
    writer.save()


# -----------------------------------------------------------------------------
def check_om_resultatregneark_er_lukket(navn: str) -> None:
    """Lam check for om resultatregneark stadig er åbent"""
    rf = f"{navn}-resultat.xlsx"
    if os.path.isfile(rf):
        try:
            os.rename(rf, "tempfile" + rf)
            os.rename("tempfile" + rf, rf)
        except OSError:
            fire.cli.print(f"Luk {rf} og prøv igen")
            sys.exit(1)


# -----------------------------------------------------------------------------
def find_sag(projektnavn: str) -> Sag:
    """Bomb hvis sag for projektnavn ikke er oprettet. Ellers returnér sagen"""
    sagsgang = find_sagsgang(projektnavn)
    sagsid = find_sagsid(sagsgang)
    try:
        sag = firedb.hent_sag(sagsid)
    except:
        fire.cli.print(
            f" Sag for {projektnavn} er endnu ikke oprettet - brug fire niv opret-sag! ",
            bold=True,
            bg="red",
        )
        sys.exit(1)
    if not sag.aktiv:
        fire.cli.print(
            f"Sag {sagsid} for {projektnavn} er markeret inaktiv. Genåbn for at gå videre."
        )
        sys.exit(1)

    return sag


# ------------------------------------------------------------------------------
def find_sagsgang(projektnavn: str) -> pd.DataFrame:
    """Udtræk sagsgangsregneark fra Excelmappe"""
    return pd.read_excel(f"{projektnavn}.xlsx", sheet_name="Sagsgang")


# ------------------------------------------------------------------------------
def find_sagsid(sagsgang: pd.DataFrame) -> str:
    sag = sagsgang.index[sagsgang["Hændelse"] == "sagsoprettelse"].tolist()
    assert (
        len(sag) == 1
    ), "Der skal være præcis 1 hændelse af type sagsoprettelse i arket"
    i = sag[0]
    if not pd.isna(sagsgang.uuid[i]):
        return str(sagsgang.uuid[i])
    return ""


# ------------------------------------------------------------------------------
# path_to_origin - eksempel:
#
# graph = {
#     'A': {'B', 'C'},
#     'B': {'C', 'D'},
#     'C': {'D'},
#     'D': {'C'},
#     'E': {'F'},
#     'F': {'C'},
#     'G': {}
# }
#
# print (path_to_origin (graph, 'A', 'C'))
# print (path_to_origin (graph, 'A', 'G'))
# ------------------------------------------------------------------------------
def path_to_origin(
    graph: Dict[str, Set[str]], start: str, origin: str, path: List[str] = []
):
    """
    Mikroskopisk backtracking netkonnektivitetstest. Baseret på et
    essay af Pythonstifteren Guido van Rossum, publiceret 1998 på
    https://www.python.org/doc/essays/graphs/. Koden er her
    moderniseret fra Python 1.5 til 3.7 og modificeret til at
    arbejde på dict-over-set (originalen brugte dict-over-list)
    """
    path = path + [start]
    if start == origin:
        return path
    if start not in graph:
        return None
    for node in graph[start]:
        if node not in path:
            newpath = path_to_origin(graph, node, origin, path)
            if newpath:
                return newpath
    return None
