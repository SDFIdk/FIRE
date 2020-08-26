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


# ------------------------------------------------------------------------------
def læs_observationsstrenge(
    filinfo: pd.DataFrame, verbose: bool = False
) -> pd.DataFrame:
    """Pil observationsstrengene ud fra en række råfiler"""
    observationer = pd.DataFrame(columns=list(ARKDEF_OBSERVATIONER))
    for fil in filinfo.itertuples(index=False):
        if fil.Type.upper() not in ["MGL", "MTL", "NUL"]:
            continue
        if verbose:
            fire.cli.print(f"Læser {fil.Filnavn} med σ={fil.σ} og δ={fil.δ}")
        try:
            with open(fil.Filnavn, "rt", encoding="utf-8") as obsfil:
                for line in obsfil:
                    if "#" != line[0]:
                        continue
                    line = line.lstrip("#").strip()

                    # Check at observationen er i et af de kendte formater
                    tokens = line.split(" ", 13)
                    assert len(tokens) in (
                        9,
                        13,
                        14,
                    ), f"Deform input linje: {line} i fil: {fil.Filnavn}"

                    # Bring observationen på kanonisk 14-feltform.
                    for i in range(len(tokens), 13):
                        tokens.append(0)
                    # Tilføj tom kommentar hvis der ikke er nogen med indhold
                    if len(tokens) < 14:
                        tokens.append('""')
                    # Befri kommentar for anførelsestegn og overflødige mellemrum
                    tokens[13] = tokens[13].lstrip('"').strip().rstrip('"')

                    # Korriger de rædsomme dato/tidsformater
                    tid = " ".join((tokens[2], tokens[3]))
                    try:
                        isotid = datetime.strptime(tid, "%d.%m.%Y %H.%M")
                    except ValueError:
                        sys.exit(
                            f"Argh - ikke-understøttet datoformat: '{tid}' i fil: '{fil.Filnavn}'"
                        )

                    # Opbyg række-som-dict: Omsæt numeriske data fra strengrepræsentation til tal
                    obs = {
                        "Fra": tokens[0],
                        "Til": tokens[1],
                        "L": float(tokens[4]),
                        "ΔH": float(tokens[5]),
                        # Undgå journalside fortolkes som tal: Erstat decimalseparator
                        "Journal": tokens[6].replace(".", ":"),
                        "T": float(tokens[7]),
                        "Opst": int(tokens[8]),
                        "Sky": int(tokens[9]),
                        "Sol": int(tokens[10]),
                        "Vind": int(tokens[11]),
                        "Sigt": int(tokens[12]),
                        "σ": fil.σ,
                        "δ": fil.δ,
                        "Kommentar": tokens[13],
                        "Sluk": "",
                        "Hvornår": isotid,
                        "Kilde": fil.Filnavn,
                        "Type": fil.Type.upper(),
                        "uuid": "",
                    }
                    observationer = observationer.append(obs, ignore_index=True)
        except FileNotFoundError:
            fire.cli.print(f"Kunne ikke læse filen '{fil.Filnavn}'")
    return observationer


# ------------------------------------------------------------------------------
def find_nyetablerede(projektnavn: str) -> pd.DataFrame:
    """Opbyg oversigt over nyetablerede punkter"""
    fire.cli.print("Finder nyetablerede punkter")
    nyetablerede = pd.read_excel(
        f"{projektnavn}.xlsx",
        sheet_name="Nyetablerede punkter",
        usecols=anvendte(ARKDEF_NYETABLEREDE_PUNKTER),
    )

    # Sæt 'Foreløbigt navn'-søjlen som index, så vi kan adressere
    # som nyetablerede.at[punktnavn, elementnavn]
    return nyetablerede.set_index("Foreløbigt navn")


# ------------------------------------------------------------------------------
def find_inputfiler(navn: str) -> List[Tuple[str, float]]:
    """Opbyg oversigt over alle input-filnavne og deres tilhørende spredning og centreringsfejl"""
    try:
        inputfiler = pd.read_excel(
            f"{navn}.xlsx",
            sheet_name="Filoversigt",
            usecols=anvendte(ARKDEF_FILOVERSIGT),
        )
    except:
        sys.exit("Kan ikke finde filoversigt i projektfil")
    return inputfiler[inputfiler["Filnavn"].notnull()]  # Fjern blanklinjer


# ------------------------------------------------------------------------------
def importer_observationer(projektnavn: str) -> pd.DataFrame:
    """Opbyg dataframe med observationer importeret fra rådatafil"""
    fire.cli.print("Importerer observationer")
    observationer = læs_observationsstrenge(find_inputfiler(projektnavn))

    # Sorter efter journalside, så frem- og tilbageobservationer følges ad.
    # Den sære index-gymnastik sikrer at vi har fortløbende nummerering
    # også efter sorteringen.
    observationer.sort_values(by="Journal", inplace=True)
    observationer.reset_index(drop=True, inplace=True)

    # Oversæt alle anvendte identer til kanonisk form
    fra = tuple(observationer["Fra"])
    til = tuple(observationer["Til"])
    observerede_punkter = tuple(set(fra + til))
    kanonisk_ident = {}

    for punktnavn in observerede_punkter:
        try:
            punkt = firedb.hent_punkt(punktnavn)
            ident = punkt.ident
            fire.cli.print(f"Fandt {ident}", fg="green")
        except NoResultFound:
            fire.cli.print(f"Ukendt punkt: '{punktnavn}'", fg="red", bg="white")
            sys.exit(1)
        kanonisk_ident[punktnavn] = ident

    fra = tuple(kanonisk_ident[ident] for ident in fra)
    til = tuple(kanonisk_ident[ident] for ident in til)

    observationer["Fra"] = fra
    observationer["Til"] = til
    return observationer


# ------------------------------------------------------------------------------
def obs_feature(punkter: pd.DataFrame, observationer: pd.DataFrame) -> Dict[str, str]:
    """Omsæt observationsinformationer til JSON-egnet dict"""
    for i in range(observationer.shape[0]):
        fra = observationer.at[i, "Fra"]
        til = observationer.at[i, "Til"]
        feature = {
            "type": "Feature",
            "properties": {
                "Fra": fra,
                "Til": til,
                "Afstand": observationer.at[i, "L"],
                "ΔH": observationer.at[i, "ΔH"],
                # konvertering, da json.dump ikke uderstøtter int64
                "Opstillinger": int(observationer.at[i, "Opst"]),
                "Journal": observationer.at[i, "Journal"],
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [punkter.at[fra, "Øst"], punkter.at[fra, "Nord"]],
                    [punkter.at[til, "Øst"], punkter.at[til, "Nord"]],
                ],
            },
        }
        yield feature


# ------------------------------------------------------------------------------
def observationer_geojson(
    projektnavn: str, punkter: pd.DataFrame, observationer: pd.DataFrame,
) -> None:
    """Skriv observationer til geojson-fil"""

    with open(f"{projektnavn}-observationer.geojson", "wt") as obsfil:
        til_json = {
            "type": "FeatureCollection",
            "Features": list(obs_feature(punkter, observationer)),
        }
        json.dump(til_json, obsfil, indent=4)


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


# ------------------------------------------------------------------------------
def punkter_geojson(projektnavn: str, punkter: pd.DataFrame,) -> None:
    """Skriv punkter/koordinater i geojson-format"""
    with open(f"{projektnavn}-punkter.geojson", "wt") as punktfil:
        til_json = {
            "type": "FeatureCollection",
            "Features": list(punkt_feature(punkter)),
        }
        json.dump(til_json, punktfil, indent=4)


# ------------------------------------------------------------------------------
def opbyg_punktoversigt(
    navn: str, nyetablerede: pd.DataFrame, alle_punkter: Tuple[str, ...],
) -> pd.DataFrame:
    punktoversigt = pd.DataFrame(columns=list(ARKDEF_PUNKTOVERSIGT))
    fire.cli.print("Opbygger punktoversigt")

    # Forlæng punktoversigt, så der er plads til alle punkter
    punktoversigt = punktoversigt.reindex(range(len(alle_punkter)))
    punktoversigt["Punkt"] = alle_punkter
    # Geninstaller 'punkt'-søjlen som indexsøjle
    punktoversigt = punktoversigt.set_index("Punkt")

    nye_punkter = tuple(sorted(set(nyetablerede.index)))

    try:
        DVR90 = firedb.hent_srid("EPSG:5799")
    except KeyError:
        fire.cli.print(
            "DVR90 (EPSG:5799) ikke fundet i srid-tabel", bg="red", fg="white", err=True
        )
        sys.exit(1)

    for punkt in alle_punkter:
        if not pd.isna(punktoversigt.at[punkt, "Kote"]):
            continue
        if punkt in nye_punkter:
            continue

        fire.cli.print(f"Finder kote for {punkt}", fg="green")
        pkt = firedb.hent_punkt(punkt)

        # Grav aktuel kote frem
        kote = None
        for koord in pkt.koordinater:
            if koord.srid != DVR90:
                continue
            if koord.registreringtil is None:
                kote = koord
                break
        if kote is None:
            fire.cli.print(
                f"Ingen aktuel DVR90-kote fundet for {punkt}",
                bg="red",
                fg="white",
                err=True,
            )
            punktoversigt.at[punkt, "Kote"] = 0
            punktoversigt.at[punkt, "σ"] = 1e6
            punktoversigt.at[punkt, "År"] = 1800
            punktoversigt.at[punkt, "System"] = "DVR90"
            punktoversigt.at[punkt, "uuid"] = ""
        else:
            punktoversigt.at[punkt, "Kote"] = kote.z
            punktoversigt.at[punkt, "σ"] = kote.sz
            punktoversigt.at[punkt, "År"] = kote.registreringfra.year
            punktoversigt.at[punkt, "System"] = "DVR90"
            punktoversigt.at[punkt, "uuid"] = ""

        if pd.isna(punktoversigt.at[punkt, "Nord"]):
            punktoversigt.at[punkt, "Nord"] = pkt.geometri.koordinater[1]
            punktoversigt.at[punkt, "Øst"] = pkt.geometri.koordinater[0]

    # Nyetablerede punkter er ikke i databasen, så hent eventuelle manglende
    # koter og placeringskoordinater i fanebladet 'Nyetablerede punkter'
    for punkt in nye_punkter:
        if pd.isna(punktoversigt.at[punkt, "Kote"]):
            punktoversigt.at[punkt, "Kote"] = 0
        if pd.isna(punktoversigt.at[punkt, "Nord"]):
            punktoversigt.at[punkt, "Nord"] = nyetablerede.at[punkt, "Nord"]
        if pd.isna(punktoversigt.at[punkt, "Øst"]):
            punktoversigt.at[punkt, "Øst"] = nyetablerede.at[punkt, "Øst"]

    # Check op på placeringskoordinaterne
    for punkt in alle_punkter:
        (λ, φ) = normaliser_placeringskoordinat(
            punktoversigt.at[punkt, "Øst"], punktoversigt.at[punkt, "Nord"]
        )
        punktoversigt.at[punkt, "Nord"] = φ
        punktoversigt.at[punkt, "Øst"] = λ

    # Reformater datarammen så den egner sig til output
    return punktoversigt.reset_index()


# ------------------------------------------------------------------------------
def netanalyse(
    observationer: pd.DataFrame,
    alle_punkter: Tuple[str, ...],
    fastholdte_punkter: Tuple[str, ...],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    fire.cli.print("Analyserer net")
    assert len(fastholdte_punkter) > 0, "Netanalyse kræver mindst et fastholdt punkt"
    # Initialiser
    net = {}
    for punkt in alle_punkter:
        net[punkt] = set()

    # Tilføj forbindelser alle steder hvor der er observationer
    for fra, til in zip(observationer["Fra"], observationer["Til"]):
        net[fra].add(til)
        net[til].add(fra)

    # Tilføj forbindelser fra alle fastholdte punkter til det første fastholdte punkt
    udgangspunkt = fastholdte_punkter[0]
    for punkt in fastholdte_punkter:
        if punkt != udgangspunkt:
            net[udgangspunkt].add(punkt)
            net[punkt].add(udgangspunkt)

    # Analysér netgraf
    forbundne_punkter = set()
    ensomme_punkter = set()
    for punkt in alle_punkter:
        if path_to_origin(net, udgangspunkt, punkt) is None:
            ensomme_punkter.add(punkt)
        else:
            forbundne_punkter.add(punkt)

    # Vi vil ikke have de kunstige forbindelser mellem fastholdte punkter med
    # i output, så nu genopbygger vi nettet uden dem
    net = {}
    for punkt in alle_punkter:
        net[punkt] = set()
    for fra, til in zip(observationer["Fra"], observationer["Til"]):
        net[fra].add(til)
        net[til].add(fra)

    # De ensomme punkter skal heller ikke med i netgrafen
    for punkt in ensomme_punkter:
        net.pop(punkt, None)

    # Nu kommer der noget grimt...
    # Tving alle rækker til at være lige lange, så vi kan lave en dataframe af dem
    max_antal_naboer = max([len(net[e]) for e in net])
    nyt = {}
    for punkt in net:
        naboer = list(sorted(net[punkt])) + max_antal_naboer * [""]
        nyt[punkt] = tuple(naboer[0:max_antal_naboer])

    # Ombyg og omdøb søjler med smart "add_prefix"-trick fra
    # @piRSquared, https://stackoverflow.com/users/2336654/pirsquared
    # Se https://stackoverflow.com/questions/46078034/python-dict-with-values-as-tuples-to-pandas-dataframe
    netf = pd.DataFrame(nyt).T.rename_axis("Punkt").add_prefix("Nabo ").reset_index()
    netf.sort_values(by="Punkt", inplace=True)
    netf.reset_index(drop=True, inplace=True)

    ensomme = pd.DataFrame(sorted(ensomme_punkter), columns=["Punkt"])
    return netf, ensomme


# ------------------------------------------------------------------------------
def find_fastholdte(punktoversigt: pd.DataFrame) -> Dict[str, float]:
    relevante = punktoversigt[punktoversigt["Fasthold"] == "x"]
    fastholdte_punkter = tuple(relevante["Punkt"])
    fastholdteKoter = tuple(relevante["Kote"])
    return dict(zip(fastholdte_punkter, fastholdteKoter))


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


# ------------------------------------------------------------------------------
def gama_beregning(
    projektnavn: str,
    observationer: pd.DataFrame,
    punktoversigt: pd.DataFrame,
    estimerede_punkter: Tuple[str, ...],
) -> pd.DataFrame:
    fastholdte = find_fastholdte(punktoversigt)

    # Skriv Gama-inputfil i XML-format
    with open(f"{projektnavn}.xml", "wt") as gamafil:
        # Preambel
        gamafil.write(
            f"<?xml version='1.0' ?><gama-local>\n"
            f"<network angles='left-handed' axes-xy='en' epoch='0.0'>\n"
            f"<parameters\n"
            f"    algorithm='gso' angles='400' conf-pr='0.95'\n"
            f"    cov-band='0' ellipsoid='grs80' latitude='55.7' sigma-act='apriori'\n"
            f"    sigma-apr='1.0' tol-abs='1000.0'\n"
            f"    update-constrained-coordinates='no'\n"
            f"/>\n\n"
            f"<description>\n"
            f"    Nivellementsprojekt {ascii(projektnavn)}\n"  # Gama kaster op over Windows-1252 tegn > 127
            f"</description>\n"
            f"<points-observations>\n\n"
        )

        # Fastholdte punkter
        gamafil.write("\n\n<!-- Fixed -->\n\n")
        for punkt, kote in fastholdte.items():
            gamafil.write(f"<point fix='Z' id='{punkt}' z='{kote}'/>\n")

        # Punkter til udjævning
        gamafil.write("\n\n<!-- Adjusted -->\n\n")
        for punkt in estimerede_punkter:
            gamafil.write(f"<point adj='z' id='{punkt}'/>\n")

        # Observationer
        gamafil.write("<height-differences>\n")
        for obs in observationer.itertuples(index=False):
            if not pd.isna(obs.Sluk):
                fire.cli.print(f"Slukket {obs}")
                continue
            gamafil.write(
                f"<dh from='{obs.Fra}' to='{obs.Til}' "
                f"val='{obs.ΔH:+.6f}' "
                f"dist='{obs.L:.5f}' stdev='{spredning(obs.Type, obs.L, obs.Opst, obs.σ, obs.δ):.5f}' "
                f"extern='{obs.Journal}'/>\n"
            )

        # Postambel
        gamafil.write(
            "</height-differences>\n"
            "</points-observations>\n"
            "</network>\n"
            "</gama-local>\n"
        )

    # Lad GNU Gama om at køre udjævningen
    ret = subprocess.run(
        [
            "gama-local",
            f"{projektnavn}.xml",
            "--xml",
            f"{projektnavn}-resultat.xml",
            "--html",
            f"{projektnavn}-resultat.html",
        ]
    )
    if ret.returncode:
        fire.cli.print(f"Check {projektnavn}-resultat.html", bg="red", fg="white")
    webbrowser.open_new_tab(f"{projektnavn}-resultat.html")

    # Grav resultater frem fra GNU Gamas outputfil
    with open(f"{projektnavn}-resultat.xml") as resultat:
        doc = xmltodict.parse(resultat.read())

    # Sammenhængen mellem rækkefølgen af elementer i Gamas punktliste (koteliste
    # herunder) og varianserne i covariansmatricens diagonal er uklart beskrevet:
    # I Gamas xml-resultatfil antydes at der skal foretages en ombytning.
    # Men rækkefølgen anvendt her passer sammen med det Gama præsenterer i
    # html-rapportudgaven af beregningsresultatet.
    koteliste = doc["gama-local-adjustment"]["coordinates"]["adjusted"]["point"]
    punkter = [punkt["id"] for punkt in koteliste]
    koter = [float(punkt["z"]) for punkt in koteliste]
    varliste = doc["gama-local-adjustment"]["coordinates"]["cov-mat"]["flt"]
    varianser = [float(var) for var in varliste]
    assert len(koter) == len(varianser), "Mismatch mellem antal koter og varianser"

    # Skriv resultaterne til punktoversigten
    punktoversigt = punktoversigt.set_index("Punkt")
    for index in range(len(punkter)):
        punktoversigt.at[punkter[index], "Ny kote"] = koter[index]
        punktoversigt.at[punkter[index], "Ny σ"] = sqrt(varianser[index])
    punktoversigt = punktoversigt.reset_index()

    # Ændring i millimeter...
    d = list(abs(punktoversigt["Kote"] - punktoversigt["Ny kote"]) * 1000)
    # ...men vi ignorerer ændringer under mikrometerniveau
    dd = [e if e > 0.001 else None for e in d]
    punktoversigt["Δ-kote [mm]"] = dd
    return punktoversigt


# ------------------------------------------------------------------------------
# Her starter observationsregistreringsprogrammet...
# ------------------------------------------------------------------------------
@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn", nargs=1, type=str,
)
@click.argument(
    "sagsbehandler", nargs=1, type=str,
)
def ilæg_observationer(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyoprettede punkter i databasen"""
    check_om_resultatregneark_er_lukket(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print("Lægger nye observationer i databasen")
    obstype_trig = firedb.hent_observationstype("trigonometrisk_koteforskel")
    obstype_geom = firedb.hent_observationstype("geometrisk_koteforskel")

    til_registrering = []
    observationer = pd.read_excel(
        f"{projektnavn}.xlsx",
        sheet_name="Observationer",
        usecols=anvendte(ARKDEF_OBSERVATIONER),
    )
    # Fjern blanklinjer
    observationer = observationer[observationer["Fra"] == observationer["Fra"]]
    # Fjern allerede gemte
    observationer = observationer[observationer["uuid"] != observationer["uuid"]]
    observationer = observationer.reset_index(drop=True)

    alle_kilder = ", ".join(sorted(list(set(observationer.Kilde))))
    alle_uuider = observationer.uuid.astype(str)

    # Generer sagsevent
    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.OBSERVATION_INDSAT)
    sagseventtekst = f"Ilægning af observationer fra {alle_kilder}"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "observationsilægning",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)

    for i, obs in enumerate(observationer.itertuples(index=False)):
        # Ignorer allerede registrerede observationer
        if str(obs.uuid) not in ["", "None", "nan"]:
            continue

        # Vi skal bruge fra- og til-punkterne for at kunne oprette et
        # objekt af typen Observation
        try:
            punktnavn = obs.Fra
            punkt_fra = firedb.hent_punkt(punktnavn)
            punktnavn = obs.Til
            punkt_til = firedb.hent_punkt(punktnavn)
        except NoResultFound:
            fire.cli.print(f"Ukendt punkt: '{punktnavn}'", fg="red", bg="white")
            sys.exit(1)

        # For nivellementsobservationer er gruppeidentifikatoren identisk
        # med journalsidenummeret
        side = obs.Journal.split(":")[0]
        if side.isnumeric():
            gruppe = int(side)
        else:
            gruppe = None

        if obs.Type.upper() == "MTL":
            observation = Observation(
                antal=1,
                observationstype=obstype_trig,
                observationstidspunkt=obs.Hvornår,
                opstillingspunkt=punkt_fra,
                sigtepunkt=punkt_til,
                gruppe=gruppe,
                id=uuid(),
                value1=obs.ΔH,
                value2=obs.L,
                value3=obs.Opst,
                value4=obs.σ,
                value5=obs.δ,
            )
            observation.sagsevent = sagsevent

        elif obs.Type.upper() == "MGL":
            observation = Observation(
                antal=1,
                observationstype=obstype_geom,
                observationstidspunkt=obs.Hvornår,
                opstillingspunkt=punkt_fra,
                sigtepunkt=punkt_til,
                gruppe=gruppe,
                id=uuid(),
                value1=obs.ΔH,
                value2=obs.L,
                value3=obs.Opst,
                # value4=Refraktion, eta_1, sættes her til None
                value5=obs.σ,
                value6=obs.δ,
            )
        else:
            fire.cli.print(
                f"Ukendt observationstype: '{obs.Type}'", fg="red", bg="white"
            )
            sys.exit(1)
        alle_uuider[i] = observation.id
        til_registrering.append(observation)

    # Gør klar til at persistere
    observationer["uuid"] = alle_uuider

    # En lidt omstændelig dialog, for at fortælle at dette er en alvorlig ting.
    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    print(observationer[["Journal", "Fra", "Til", "uuid"]])
    fire.cli.print(f"Skriver {len(til_registrering)} observationer")
    fire.cli.print(
        "-->  HELT sikker på at du vil skrive observationerne til databasen (ja/nej)? ",
        bg="red",
        fg="white",
        bold=True,
        nl=False,
    )
    if input() != "ja":
        fire.cli.print("Dropper skrivning til database")
        return

    # Persister observationerne til databasen
    try:
        firedb.indset_flere_observationer(sagsevent, til_registrering)
    except Exception as ex:
        fire.cli.print(
            "Skrivning til databasen slog fejl", bg="red", fg="white", bold=True
        )
        fire.cli.print(f"Mulig årsag: {ex}")
        sys.exit(1)

    # Skriv resultater til resultatregneark
    resultater = {"Sagsgang": sagsgang, "Observationer": observationer}
    skriv_ark(projektnavn, resultater)
    fire.cli.print(
        f"Observationer registreret. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
    )


# ------------------------------------------------------------------------------
# Her starter indlæsningsprogrammet...
# ------------------------------------------------------------------------------
@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn", nargs=1, type=str,
)
def læs_observationer(projektnavn: str, **kwargs) -> None:
    """Importer data fra observationsfiler og opbyg punktoversigt"""
    check_om_resultatregneark_er_lukket(projektnavn)
    fire.cli.print("Så kører vi")
    resultater = {}

    # Opbyg oversigt over nyetablerede punkter
    nyetablerede = find_nyetablerede(projektnavn)
    nye_punkter = set(nyetablerede.index)

    # Opbyg oversigt over alle observationer
    observationer = importer_observationer(projektnavn)
    resultater["Observationer"] = observationer
    observerede_punkter = set(list(observationer["Fra"]) + list(observationer["Til"]))
    alle_gamle_punkter = observerede_punkter - nye_punkter

    # Vi vil gerne have de nye punkter først i punktoversigten,
    # så vi sorterer gamle og nye hver for sig
    nye_punkter = tuple(sorted(nye_punkter))
    alle_punkter = nye_punkter + tuple(sorted(alle_gamle_punkter))

    # Opbyg oversigt over alle punkter m. kote og placering
    punktoversigt = opbyg_punktoversigt(projektnavn, nyetablerede, alle_punkter)
    resultater["Punktoversigt"] = punktoversigt
    skriv_ark(projektnavn, resultater)
    fire.cli.print(
        f"Dataindlæsning afsluttet. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx'"
    )
    fire.cli.print(
        f"til '{projektnavn}.xlsx', og vælg fastholdte punkter i punktoversigten."
    )

    punkter_geojson(projektnavn, punktoversigt)
    observationer_geojson(projektnavn, punktoversigt.set_index("Punkt"), observationer)


# ------------------------------------------------------------------------------
# Her starter regneprogrammet...
# ------------------------------------------------------------------------------
# Aliaserne 'adj'/'beregn_nye_koter' er synonymer for 'udfør_beregn_nye_koter',
# som klarer det egentlige hårde arbejde.
# ------------------------------------------------------------------------------


@niv.command()
@fire.cli.default_options()
@click.argument("projektnavn", nargs=1, type=str)
def adj(projektnavn: str, **kwargs) -> None:
    """Udfør netanalyse og beregn nye koter"""
    udfør_beregn_nye_koter(projektnavn)


@niv.command()
@fire.cli.default_options()
@click.argument("projektnavn", nargs=1, type=str)
def beregn_nye_koter(projektnavn: str, **kwargs) -> None:
    """Udfør netanalyse og beregn nye koter"""
    udfør_beregn_nye_koter(projektnavn)


def udfør_beregn_nye_koter(projektnavn: str) -> None:
    check_om_resultatregneark_er_lukket(projektnavn)
    fire.cli.print("Så regner vi")

    # Opbyg oversigt over nyetablerede punkter
    nyetablerede = find_nyetablerede(projektnavn)
    nye_punkter = set(nyetablerede.index)

    # Opbyg oversigt over alle observationer
    try:
        observationer = pd.read_excel(
            f"{projektnavn}.xlsx",
            sheet_name="Observationer",
            usecols=anvendte(ARKDEF_OBSERVATIONER),
        )
    except:
        fire.cli.print(f"Der er ingen observationsoversigt i '{projektnavn}.xlsx'")
        fire.cli.print(
            f"- har du glemt at kopiere den fra '{projektnavn}-resultat.xlsx'?"
        )
        sys.exit(1)

    observerede_punkter = set(list(observationer["Fra"]) + list(observationer["Til"]))
    alle_gamle_punkter = observerede_punkter - nye_punkter

    # Vi vil gerne have de nye punkter først i listen, så vi sorterer gamle
    # og nye hver for sig
    nye_punkter = tuple(sorted(nye_punkter))
    alle_punkter = nye_punkter + tuple(sorted(alle_gamle_punkter))
    observerede_punkter = tuple(sorted(observerede_punkter))

    # Opbyg oversigt over alle punkter m. kote og placering
    try:
        punktoversigt = pd.read_excel(
            f"{projektnavn}.xlsx",
            sheet_name="Punktoversigt",
            usecols=anvendte(ARKDEF_PUNKTOVERSIGT),
        )
    except:
        fire.cli.print(f"Der er ingen punktoversigt i '{projektnavn}.xlsx'")
        fire.cli.print(
            f"- har du glemt at kopiere den fra '{projektnavn}-resultat.xlsx'?"
        )
        sys.exit(1)
    punktoversigt["uuid"] = ""

    # Har vi alle punkter med i punktoversigten?
    punkter_i_oversigt = set(punktoversigt["Punkt"])
    manglende_punkter_i_oversigt = set(alle_punkter) - punkter_i_oversigt
    if len(manglende_punkter_i_oversigt) > 0:
        fire.cli.print(f"Punktoversigten i '{projektnavn}.xlsx' mangler punkterne:")
        fire.cli.print(f"{manglende_punkter_i_oversigt}")
        fire.cli.print(
            f"- har du glemt at kopiere den fra '{projektnavn}-resultat.xlsx'?"
        )
        sys.exit(1)

    # Find fastholdte
    fastholdte = find_fastholdte(punktoversigt)
    if len(fastholdte) == 0:
        fire.cli.print("Vælger arbitrært punkt til fastholdelse")
        fastholdte = {observerede_punkter[0]: 0}
    fire.cli.print(f"Fastholdte: {tuple(fastholdte)}")

    # Udfør netanalyse
    (net, ensomme) = netanalyse(observationer, alle_punkter, tuple(fastholdte))
    resultater = {"Netgeometri": net, "Ensomme": ensomme}

    forbundne_punkter = tuple(sorted(net["Punkt"]))
    ensomme_punkter = tuple(sorted(ensomme["Punkt"]))
    estimerede_punkter = tuple(sorted(set(forbundne_punkter) - set(fastholdte)))
    fire.cli.print(f"Fandt {len(ensomme_punkter)} ensomme punkter: {ensomme_punkter}")
    fire.cli.print(f"Beregner nye koter for {len(estimerede_punkter)} punkter")

    # Udfør beregning
    resultater["Punktoversigt"] = gama_beregning(
        projektnavn, observationer, punktoversigt, estimerede_punkter
    )

    punkter_geojson(projektnavn, resultater["Punktoversigt"])
    skriv_ark(projektnavn, resultater)


def find_alle_løbenumre_i_distrikt(distrikt: str) -> List[str]:
    pit = firedb.hent_punktinformationtype("IDENT:landsnr")
    landsnumre = (
        firedb.session.query(PunktInformation)
        .filter(
            PunktInformation.infotypeid == pit.infotypeid,
            PunktInformation.tekst.startswith(distrikt),
        )
        .all()
    )
    løbenumre = [n.tekst.split("-")[-1] for n in landsnumre if "-" in n.tekst]
    # Ikke-numeriske løbenumre (fx vandstandsbrædder) forbliver som tekst,
    # men numeriske vil vi gerne have gjort til tal
    numre = [int(n) if str(n).isnumeric() else n for n in løbenumre]
    return set(numre)


# ------------------------------------------------------------------------------
# Her starter punktregistreringsprogrammet...
# ------------------------------------------------------------------------------
@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn", nargs=1, type=str,
)
@click.argument(
    "sagsbehandler", nargs=1, type=str,
)
def ilæg_nye_punkter(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyoprettede punkter i databasen"""
    check_om_resultatregneark_er_lukket(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print("Lægger nye punkter i databasen")

    # Opbyg oversigt over nyetablerede punkter
    nyetablerede = find_nyetablerede(projektnavn)
    nyetablerede = nyetablerede.reset_index()
    n = nyetablerede.shape[0]

    if n == 0:
        fire.cli.print("Ingen nyetablerede punkter at registrere")
        return

    landsnummer_pit = firedb.hent_punktinformationtype("IDENT:landsnr")
    beskrivelse_pit = firedb.hent_punktinformationtype("ATTR:beskrivelse")
    h_over_terræn_pit = firedb.hent_punktinformationtype("AFM:højde_over_terræn")
    assert landsnummer_pit is not None, "Rådden landsnummer_pit"
    assert beskrivelse_pit is not None, "Rådden beskrivelse_pit"
    assert h_over_terræn_pit is not None, "Rådden h_over_terræn_pit"

    # Vi samler de genererede punkter i en dict, så de kan persisteres samlet
    # under et enkelt sagsevent
    genererede_punkter = {}
    genererede_landsnumre = []
    anvendte_løbenumre = {}

    for i in range(n):
        # Et tomt tekstfelt kan repræsenteres på en del forskellige måder...
        # Punkter udstyret med uuid er allerede registrerede
        # if not (nyetablerede["uuid"][i] in ["", None] or pd.isna(nyetablerede["uuid"][i])):
        if str(nyetablerede.uuid[i]) not in ["", "None", "nan"]:
            continue
        print(f"Behandler punkt {nyetablerede['Foreløbigt navn'][i]}")

        lokation = normaliser_placeringskoordinat(
            nyetablerede["Øst"][i], nyetablerede["Nord"][i]
        )
        distrikt = nyetablerede["Landsnummer"][i]

        # Gør klar til at finde et ledigt landsnummer, hvis vi ikke allerede har et
        if 2 == len(distrikt.split("-")):
            if distrikt in anvendte_løbenumre:
                numre = anvendte_løbenumre[distrikt]
            else:
                numre = find_alle_løbenumre_i_distrikt(distrikt)
                anvendte_løbenumre[distrikt] = numre
                print(f"Fandt {len(numre)} punkter i distrikt {distrikt}")
        # Hvis der er anført et fuldt landsnummer må det hellere se ud som et
        elif 3 != len(distrikt.split("-")):
            fire.cli.print(f"Usselt landsnummer: {distrikt}")
            continue
        # Ellers har vi et komplet landsnummer, så punktet er allerede registreret
        else:
            continue

        # Hjælpepunkter har egen nummerserie
        if "ingen" == str(nyetablerede["Afmærkning"][i]).lower():
            nummerserie = range(90001, 100000)
        else:
            nummerserie = chain(range(9001, 10000), range(19001, 20000))

        # Så leder vi...
        for løbenummer in nummerserie:
            if løbenummer not in numre:
                # Lige nu laver vi kun numeriske løbenumre, men fx vandstandsbrædder
                # og punkter fra de gamle hovedstadsregistre har tekstuelle løbe"numre"
                if str(løbenummer).isnumeric():
                    landsnummer = f"{distrikt}-{løbenummer:05}"
                else:
                    landsnummer = f"{distrikt}-{løbenummer}"
                genererede_landsnumre.append(landsnummer)
                fire.cli.print(f"Anvender landsnummer {landsnummer}")
                numre.add(løbenummer)
                break
        # Hvis for-løkken løber til ende er vi løbet tør for løbenumre
        else:
            fire.cli.print(
                f"Løbet tør for landsnumre i distrikt {distrikt}", fg="red", bg="white"
            )
            continue

        # Skab nyt punktobjekt
        nyt_punkt = Punkt()
        nyt_punkt.id = uuid()

        # Tilføj punktets lokation som geometriobjekt
        geo = GeometriObjekt()
        geo.geometri = Point(lokation)
        nyt_punkt.geometriobjekter.append(geo)
        # Hvis lokationen i regnearket var UTM32, så bliver den nu længde/bredde
        nyetablerede.at[i, "Øst"] = lokation[0]
        nyetablerede.at[i, "Nord"] = lokation[1]

        # Tilføj punktets landsnummer som punktinformation
        pi_l = PunktInformation(
            infotype=landsnummer_pit, punkt=nyt_punkt, tekst=landsnummer
        )
        nyt_punkt.punktinformationer.append(pi_l)
        nyetablerede.at[i, "Landsnummer"] = landsnummer

        # Tilføj punktets højde over terræn som punktinformation, hvis anført
        try:
            ΔH = float(nyetablerede["Højde over terræn"][i])
        except (TypeError, ValueError):
            ΔH = 0
        if ΔH != ΔH:
            ΔH = 0.0
        if not pd.isna(nyetablerede["Højde over terræn"][i]):
            pi_h = PunktInformation(
                infotype=h_over_terræn_pit, punkt=nyt_punkt, tal=ΔH,
            )
            nyt_punkt.punktinformationer.append(pi_h)

        # Tilføj punktets afmærkning som punktinformation, selv hvis ikke anført
        afm_id = 4999  # AFM:4999 = "ukendt"
        afm_ids = {
            "ukendt": 4999,
            "bolt": 2700,
            "lodret bolt": 2701,
            "skruepløk": 2950,
            "ingen": 5998,
        }

        if not pd.isna(nyetablerede["Afmærkning"][i]):
            # Afmærkningsbeskrivelse
            afm = str(nyetablerede["Afmærkning"][i]).lower()
            # Første ord i afmærkningsbeskrivelsen
            afm_første = afm.split()[0].rstrip(":;,.- ").lstrip("afm:")

            if afm_første.isnumeric():
                afm_id = int(afm_første)
            else:
                afm_id = afm_ids.get(afm, 4999)

            afmærkning_pit = firedb.hent_punktinformationtype(f"AFM:{afm_id}")
            if afmærkning_pit is None:
                afm_id = 4999
                afmærkning_pit = firedb.hent_punktinformationtype("AFM:4999")
            beskrivelse = (
                afmærkning_pit.beskrivelse.replace("-\n", "")
                .replace("\n", " ")
                .rstrip(".")
                .strip()
            )
            nyetablerede.at[i, "Afmærkning"] = f"AFM:{afm_id} - {beskrivelse}"

        if afm_id == 4999:
            fire.cli.print(
                f"ADVARSEL: Nyoprettet punkt index {i} har ingen gyldig afmærkning anført",
                fg="red",
                bg="white",
                bold=True,
            )
        pi_a = PunktInformation(infotype=afmærkning_pit, punkt=nyt_punkt)
        nyt_punkt.punktinformationer.append(pi_a)

        # Tilføj punktbeskrivelsen som punktinformation, hvis anført
        if not pd.isna(nyetablerede["Beskrivelse"][i]):
            pi_b = PunktInformation(
                infotype=beskrivelse_pit,
                punkt=nyt_punkt,
                tekst=nyetablerede["Beskrivelse"][i],
            )
            nyt_punkt.punktinformationer.append(pi_b)

        genererede_punkter[i] = nyt_punkt

    if len(genererede_punkter) == 0:
        fire.cli.print("Ingen nyetablerede punkter at registrere")
        return

    # Gør klar til at persistere

    # Generer sagsevent
    sagsevent = Sagsevent(sag=sag)
    sagsevent.id = uuid()
    er = "er" if len(genererede_landsnumre) > 1 else ""
    sagseventtekst = f"Oprettelse af punkt{er} {', '.join(genererede_landsnumre)}"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "punktoprettelse",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)

    # Persister punkterne til databasen
    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    if "ja" != input(
        "-->  HELT sikker på at du vil skrive punkterne til databasen (ja/nej)? "
    ):
        fire.cli.print("Dropper skrivning")
        return
    firedb.indset_flere_punkter(sagsevent, list(genererede_punkter.values()))

    # ... og marker i regnearket at det er sket
    for k in genererede_punkter:
        nyetablerede.at[k, "uuid"] = genererede_punkter[k].id
    # Drop numerisk index
    nyetablerede = nyetablerede.reset_index(drop=True)

    # Skriv resultater til resultatregneark
    resultater = {"Sagsgang": sagsgang, "Nyetablerede punkter": nyetablerede}
    skriv_ark(projektnavn, resultater)
    fire.cli.print(
        f"Punkter oprettet. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
    )


# ------------------------------------------------------------------------------
# Her starter koteregistreringsprogrammet...
# ------------------------------------------------------------------------------
@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn", nargs=1, type=str,
)
@click.argument(
    "sagsbehandler", nargs=1, type=str,
)
def ilæg_nye_koter(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyberegnede koter i databasen"""
    check_om_resultatregneark_er_lukket(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print("Lægger nye koter i databasen")

    try:
        punktoversigt = pd.read_excel(
            f"{projektnavn}.xlsx",
            sheet_name="Punktoversigt",
            usecols=anvendte(ARKDEF_PUNKTOVERSIGT),
        )
    except Exception as ex:
        fire.cli.print(
            f"Kan ikke læse punktoversigt fra '{projektnavn}.xlsx'",
            fg="yellow",
            bold=True,
        )
        fire.cli.print(f"Mulig årsag: {ex}")
        sys.exit(1)

    ny_punktoversigt = punktoversigt[0:0]

    DVR90 = firedb.hent_srid("EPSG:5799")
    registreringstidspunkt = datetime.now()

    # Generer sagsevent
    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.KOORDINAT_BEREGNET)

    til_registrering = []
    opdaterede_punkter = []
    for punktdata in punktoversigt.to_dict(orient="records"):
        # Blanklinje, eller allerede registreret?
        if pd.isna(punktdata["Ny kote"]) or not pd.isna(punktdata["uuid"]):
            ny_punktoversigt = ny_punktoversigt.append(punktdata, ignore_index=True)
            continue

        punkt = firedb.hent_punkt(punktdata["Punkt"])
        opdaterede_punkter.append(punkt)
        punktdata["uuid"] = sagsevent.id

        kote = Koordinat(
            srid=DVR90,
            punkt=punkt,
            t=registreringstidspunkt,
            z=punktdata["Ny kote"],
            sz=punktdata["Ny σ"],
        )

        til_registrering.append(kote)
        ny_punktoversigt = ny_punktoversigt.append(punktdata, ignore_index=True)

    if 0 == len(til_registrering):
        fire.cli.print("Ingen koter at registrere!", fg="yellow", bold=True)
        return

    # Vi vil ikke have alt for lange sagseventtekster (bl.a. fordi Oracle ikke
    # kan lide lange tekststrenge), så vi indsætter udeladelsesprikker hvis vi
    # opdaterer mere end 10 punkter ad gangen
    n = len(opdaterede_punkter)
    punktnavne = [p.ident for p in opdaterede_punkter]
    if n > 10:
        punktnavne[9] = "..."
        punktnavne[10] = punktnavne[-1]
    sagseventtekst = f"Opdatering af DVR90 kote til {', '.join(punktnavne)}"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": registreringstidspunkt,
        "Hvem": sagsbehandler,
        "Hændelse": "Koteberegning",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)

    # Persister koterne til databasen
    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    if "ja" != input(
        f"-->  HELT sikker på at du vil skrive {n} koter til databasen (ja/nej)? "
    ):
        fire.cli.print("Dropper skrivning")
        return

    sagsevent.koordinater = til_registrering
    firedb.indset_sagsevent(sagsevent)

    # Skriv resultater til resultatregneark
    resultater = {"Sagsgang": sagsgang, "Punktoversigt": ny_punktoversigt}
    skriv_ark(projektnavn, resultater)

    fire.cli.print(
        f"Koter registreret. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
    )


# ------------------------------------------------------------------------------
# Her starter punktrevisionsprogrammet
# ------------------------------------------------------------------------------
@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn", nargs=1, type=str,
)
@click.argument("opmålingsdistrikter", nargs=-1)
def udtræk_revision(
    projektnavn: str, opmålingsdistrikter: Tuple[str], **kwargs
) -> None:
    """Gør klar til punktrevision: Udtræk eksisterende information.

        fire niv udtræk-revision projektnavn distrikts-eller-punktnavn(e)
    """

    revision = pd.DataFrame(columns=tuple(ARKDEF_REVISION)).astype(ARKDEF_REVISION)

    # Punkter med bare EN af disse attributter ignoreres
    uønskede_punkter = {
        "ATTR:hjælpepunkt",
        "ATTR:tabtgået",
        "ATTR:teknikpunkt",
        "AFM:naturlig",
        "ATTR:MV_punkt",
    }

    # Disse attributter indgår ikke i punktrevisionen
    # (men det diskvalificerer ikke et punkt at have dem)
    ignorerede_attributter = {
        "REGION:DK",
        "IDENT:refgeo_id",
        "IDENT:station",
        "NET:10KM",
        "SKITSE:md5",
        "ATTR:fundamentalpunkt",
        "ATTR:tinglysningsnr",
    }

    fire.cli.print("Udtrækker punktinformation til revision")
    for distrikt in opmålingsdistrikter:
        fire.cli.print(f"Behandler distrikt {distrikt}")
        try:
            punkter = firedb.soeg_punkter(f"{distrikt}%")
        except NoResultFound:
            punkter = []
        fire.cli.print(f"Der er {len(punkter)} punkter i distrikt {distrikt}")

        for punkt in punkter:
            ident = punkt.ident
            infotypenavne = [i.infotype.name for i in punkt.punktinformationer]
            if not uønskede_punkter.isdisjoint(infotypenavne):
                continue

            # Hvis punktet har et landsnummer kan vi bruge det til at frasortere irrelevante punkter
            if "IDENT:landsnr" in infotypenavne:
                landsnrinfo = punkt.punktinformationer[
                    infotypenavne.index("IDENT:landsnr")
                ]
                landsnr = landsnrinfo.tekst
                løbenr = landsnr.split("-")[-1]

                # Frasorter numeriske løbenumre udenfor 1-10, 801-999, 9001-19999
                if løbenr.isnumeric():
                    i = int(løbenr)
                    if 10 < i < 801:
                        continue
                    if 1000 < i < 9001:
                        continue
                    if i > 20000:
                        continue

            fire.cli.print(f"Punkt: {ident}")

            # Find index for aktuelle punktbeskrivelse, for at kunne vise den først
            beskrivelse = 0
            for i, info in enumerate(punkt.punktinformationer):
                if info.registreringtil is not None:
                    continue
                if info.infotype.name != "ATTR:beskrivelse":
                    continue
                beskrivelse = i
                break
            indices = list(range(len(punkt.punktinformationer)))
            indices[0] = beskrivelse
            indices[beskrivelse] = 0

            anvendte_attributter = []

            # Så itererer vi, med aktuelle beskrivelse først
            for i in indices:
                info = punkt.punktinformationer[i]
                if info.registreringtil is not None:
                    continue

                attributnavn = info.infotype.name
                if attributnavn in ignorerede_attributter:
                    continue

                # Vis kun landsnr for punkter med GM/GI/GNSS-primærident
                if attributnavn == "IDENT:landsnr" and info.tekst == ident:
                    continue

                tekst = info.tekst
                if tekst:
                    tekst = tekst.strip()
                tal = info.tal
                revision = revision.append(
                    {
                        "Punkt": ident,
                        "Sluk": "",
                        "Attribut": attributnavn,
                        "Talværdi": tal,
                        "Tekstværdi": tekst,
                        "id": info.objektid,
                        "Ikke besøgt": "x" if i == beskrivelse else None,
                    },
                    ignore_index=True,
                )
                anvendte_attributter.append(attributnavn)

            # Revisionsovervejelser: p.t. geometri og datumstabilitet
            if "ATTR:muligt_datumstabil" not in anvendte_attributter:
                revision = revision.append(
                    {
                        "Punkt": ident,
                        "Attribut": "OVERVEJ:muligt_datumstabil",
                        "Tekstværdi": "ukendt",
                        "Ret tekst": "ja/nej",
                    },
                    ignore_index=True,
                )
            lokation = punkt.geometri.koordinater
            revision = revision.append(
                {
                    "Punkt": ident,
                    "Attribut": "OVERVEJ:lokation",
                    # Centimeterafrunding for lokationskoordinaten er rigeligt
                    "Tekstværdi": f"{lokation[1]:.7f} N   {lokation[0]:.7f} Ø",
                },
                ignore_index=True,
            )

            # To blanklinjer efter hvert punktoversigt
            revision = revision.append({}, ignore_index=True)
            revision = revision.append({}, ignore_index=True)

    resultater = {"Revision": revision}
    skriv_ark(projektnavn, resultater, "-revision")
    fire.cli.print("Færdig!")


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
    "projektnavn", nargs=1, type=str,
)
@click.argument(
    "sagsbehandler", nargs=1, type=str,
)
@click.argument(
    "bemærkning", nargs=-1, type=str,
)
def ilæg_revision(
    alvor: bool,
    test: bool,
    projektnavn: str,
    sagsbehandler: str,
    bemærkning: str,
    **kwargs,
) -> None:
    """Ilæg reviderede punktdata"""
    check_om_resultatregneark_er_lukket(projektnavn)
    sag = find_sag(projektnavn)
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
        svar = input("OK (ja/nej)? ")
        if svar != "ja":
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
            pitnavn = r["Attribut"]
            if pitnavn is None:
                fire.cli.print(
                    f"    * Ignorerer uanført punktinformationstype",
                    fg="red",
                    bold=True,
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

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": registreringstidspunkt,
        "Hvem": sagsbehandler,
        "Hændelse": "Koteberegning",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)


# ------------------------------------------------------------------------------
# Her starter sagsoprettelsesprogrammet
# ------------------------------------------------------------------------------
@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn", nargs=1, type=str,
)
@click.argument(
    "sagsbehandler", nargs=1, type=str,
)
@click.argument(
    "beskrivelse", nargs=-1, type=str,
)
def opret_sag(projektnavn: str, sagsbehandler: str, beskrivelse: str, **kwargs) -> None:
    """Registrer ny sag i databasen - husk anførelsestegn om sagsbehandlernavn"""

    if os.path.isfile(f"{projektnavn}.xlsx"):
        fire.cli.print(
            f"Filen '{projektnavn}.xlsx' eksisterer - sagen er allerede oprettet"
        )
        sys.exit(1)

    beskrivelse = " ".join(beskrivelse)

    sag = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "sagsoprettelse",
        "Tekst": f"{projektnavn}: {beskrivelse}",
        "uuid": uuid(),
    }
    sagsgang = pd.DataFrame([sag], columns=tuple(ARKDEF_SAG))

    fire.cli.print(
        " BEKRÆFT: Opretter ny sag i FIRE databasen!!! ", bg="red", fg="white"
    )
    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag['uuid']})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")
    fire.cli.print(f"Beskrivelse:       {beskrivelse}")
    svar = input("OK (ja/nej)? ")
    if svar == "ja":
        sagsinfo = Sagsinfo(
            aktiv="true", behandler=sagsbehandler, beskrivelse=beskrivelse
        )
        firedb.indset_sag(Sag(id=sag["uuid"], sagsinfos=[sagsinfo]))
        fire.cli.print(f"Sag '{projektnavn}' oprettet")
    else:
        fire.cli.print("Opretter IKKE sag")
        # Ved demonstration af systemet er det nyttigt at kunne oprette
        # et sagsregneark, uden at oprette en tilhørende sag
        svar = input("Opret sagsregneark alligevel (ja/nej)? ")
        if svar != "ja":
            return

    fire.cli.print(f"Skriver sagsregneark '{projektnavn}.xlsx'")

    # Dummyopsætninger til sagsregnearkets sider
    forside = pd.DataFrame()
    nyetablerede = pd.DataFrame(columns=tuple(ARKDEF_NYETABLEREDE_PUNKTER)).astype(
        ARKDEF_NYETABLEREDE_PUNKTER
    )
    notater = pd.DataFrame([{"Dato": pd.Timestamp.now(), "Hvem": "", "Tekst": ""}])
    filoversigt = pd.DataFrame(columns=tuple(ARKDEF_FILOVERSIGT))
    param = pd.DataFrame({"Navn": ["Major", "Minor", "Revision"], "Værdi": [0, 0, 0]})

    resultater = {
        "Projektforside": forside,
        "Sagsgang": sagsgang,
        "Nyetablerede punkter": nyetablerede,
        "Notater": notater,
        "Filoversigt": filoversigt,
        "Parametre": param,
    }

    skriv_ark(projektnavn, resultater, "")
    fire.cli.print("Færdig!")
