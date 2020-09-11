import json
import os
import os.path
import sys
from typing import Dict, Tuple

import click
import pandas as pd
from pyproj import Proj

import fire.cli
from fire.cli import firedb
from fire.api.model import (
    Point,
    Punkt,
    Sag,
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


# -----------------------------------------------------------------------------
def skriv_ark(
    projektnavn: str, resultater: Dict[str, pd.DataFrame], suffix: str = "-resultat"
) -> None:
    """Skriv resultater til excel-fil"""
    if suffix != "":
        fire.cli.print(f"Skriver: {tuple(resultater)}")
        fire.cli.print(f"Til filen '{projektnavn}{suffix}.xlsx'")
    writer = pd.ExcelWriter(f"{projektnavn}{suffix}.xlsx", engine="xlsxwriter")
    for r in resultater:
        resultater[r].to_excel(writer, sheet_name=r, encoding="utf-8", index=False)
    writer.save()


# -----------------------------------------------------------------------------
def check_om_regneark_er_lukket(projektnavn: str, suffix: str = "-resultat") -> None:
    """Lam check for om resultatregneark stadig er åbent"""
    navn = f"{projektnavn}-{suffix}.xlsx"
    if os.path.isfile(navn):
        try:
            os.rename(navn, "tempfile" + navn)
            os.rename("tempfile" + navn, navn)
        except OSError:
            fire.cli.print(f"Luk {navn} og prøv igen")
            sys.exit(1)


# -----------------------------------------------------------------------------
def check_om_resultatregneark_er_lukket(navn: str) -> None:
    check_om_regneark_er_lukket(navn)


# ------------------------------------------------------------------------------
def find_faneblad(
    projektnavn: str, faneblad: str, arkdef: Dict, ignore_failure: bool = False
) -> pd.DataFrame:
    try:
        return pd.read_excel(
            f"{projektnavn}.xlsx",
            sheet_name=faneblad,
            usecols=anvendte(arkdef),
        )
    except:
        if ignore_failure:
            return None
        fire.cli.print(f"Der er ingen {faneblad} i '{projektnavn}.xlsx'")
        fire.cli.print(
            f"- har du glemt at kopiere den fra '{projektnavn}-resultat.xlsx'?"
        )
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
def punkter_geojson(
    projektnavn: str,
    punkter: pd.DataFrame,
) -> None:
    """Skriv punkter/koordinater i geojson-format"""
    with open(f"{projektnavn}-punkter.geojson", "wt") as punktfil:
        til_json = {
            "type": "FeatureCollection",
            "Features": list(punkt_feature(punkter)),
        }
        json.dump(til_json, punktfil, indent=4)


# ------------------------------------------------------------------------------
def punkt_feature(punkter: pd.DataFrame) -> Dict[str, str]:
    """Omsæt punktinformationer til JSON-egnet dict"""
    for i in range(punkter.shape[0]):
        punkt = punkter.at[i, "Punkt"]

        # Fastholdte punkter har ingen ny kote, så vi viser den gamle
        if punkter.at[i, "Fasthold"] == "x":
            fastholdt = True
            delta = 0.0
            kote = float(punkter.at[i, "Kote"])
            sigma = float(punkter.at[i, "σ"])
        else:
            fastholdt = False
            delta = float(punkter.at[i, "Δ-kote [mm]"])
            kote = float(punkter.at[i, "Ny kote"])
            sigma = float(punkter.at[i, "Ny σ"])

        # Endnu uberegnede punkter
        if kote is None:
            kote = 0.0
            delta = 0.0
            sigma = 0.0

        # Ignorerede ændringer (under 1 um)
        if delta is None:
            delta = 0.0

        feature = {
            "type": "Feature",
            "properties": {
                "id": punkt,
                "H": kote,
                "sH": sigma,
                "Δ": delta,
                "fastholdt": fastholdt,
            },
            "geometry": {
                "type": "Point",
                "coordinates": [punkter.at[i, "Øst"], punkter.at[i, "Nord"]],
            },
        }
        yield feature


from .opret_sag import opret_sag
from .læs_observationer import læs_observationer
from .udtræk_revision import udtræk_revision
from .ilæg_revision import ilæg_revision
from .regn import adj, beregn_nye_koter
from .ilæg_nye_koter import ilæg_nye_koter
from .ilæg_nye_punkter import ilæg_nye_punkter
from .netoversigt import netoversigt
