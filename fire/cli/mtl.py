# Python infrastrukturelementer
import sys
from typing import Dict, List, Set, Tuple, IO
from enum import IntEnum

# Kommandolinje- og databasehåndtering
import click
import fire.cli
from fire.cli import firedb
from fire.api.model import (
    # Typingelementer fra databaseAPIet:
    Koordinat,
    Punkt,
    PunktInformation,
    PunktInformationType,
    Sag,
    Sagsevent,
    Sagsinfo,
    Srid,
)
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound

# Beregning
import numpy as np
import statsmodels.api as sm
from math import sqrt
from pyproj import Proj
from scipy import stats

# Datahåndtering
import pandas as pd
import xlsxwriter
from datetime import date, time

# ------------------------------------------------------------------------------

@click.group()
def mtl():
    """Motoriseret trigonometrisk nivellement: Arbejdsflow, beregning og analyse"""
    pass

# ------------------------------------------------------------------------------

def get_observation_strings(
    filinfo: List[Tuple[str, float]], verbose: bool = False
) -> List[str]:
    """Pil observationsstrengene ud fra en række råfiler"""
    kol = IntEnum(
        "kol",
        "fra til dato tid L dH journal T setups sky sol vind sigt kommentar",
        start=0,
    )
    observationer = list()
    for fil in filinfo:
        filnavn = fil[0]
        spredning = fil[1]
        if verbose:
            print("Læser " + filnavn + " med spredning ", spredning)
        with open(filnavn, "rt") as obsfil:
            for line in obsfil:
                if "#" != line[0]:
                    continue
                line = line.lstrip("#").strip()

                # Check at observationen er i et af de kendte formater
                tokens = line.split(" ", 12)
                assert len(tokens) in (9, 13, 14), (
                    "Malform input line: " + line + " i fil: " + filnavn
                )

                # Bring observationen på kanonisk 14-feltform.
                for i in range(len(tokens), 13):
                    tokens.append(0)
                if len(tokens) < 14:
                    tokens.append('""')
                tokens[13] = tokens[13].lstrip('"').strip().rstrip('"')

                # Korriger de rædsomme dato/tidsformater
                dato = tokens[kol.dato].split(".")
                assert len(dato) == 3, (
                    "Forkert datoformat i "
                    + filnavn
                    + ",  linje "
                    + line
                    + ": ["
                    + tokens[kol.dato]
                    + "]"
                )
                dato = date(int(dato[2]), int(dato[1]), int(dato[0]))
                tid = tokens[kol.tid].split(".")
                assert len(tid) == 2, (
                    "Forkert tidsformat i "
                    + filnavn
                    + ",  linje "
                    + line
                    + ": ["
                    + tokens[kol.tid]
                    + "]"
                )
                tid = time(int(tid[0]), int(tid[1]))

                # Reorganiser søjler og omsæt numeriske data fra strengrepræsentation til tal
                reordered = [
                    tokens[kol.journal],
                    tokens[kol.fra],
                    tokens[kol.til],
                    float(tokens[kol.dH]),
                    float(tokens[kol.L]),
                    int(tokens[kol.setups]),
                    spredning,
                    tokens[kol.kommentar],
                    dato,
                    tid,
                    float(tokens[kol.T]),
                    int(tokens[kol.sky]),
                    int(tokens[kol.sol]),
                    int(tokens[kol.vind]),
                    int(tokens[kol.sigt]),
                    filnavn,
                ]

                observationer.append(reordered)
    return observationer

# ------------------------------------------------------------------------------

def punkt_information(ident: str) -> PunktInformation:
    """Find alle informationer for et fikspunkt"""
    pi = aliased(PunktInformation)
    pit = aliased(PunktInformationType)
    try:
        punktinfo = (
            firedb.session.query(pi)
            .filter(pit.name.startswith("IDENT:"), pi.tekst == ident)
            .first()
        )
    except NoResultFound:
        firecli.print(f"Error! {ident} not found!", fg="red", err=True)
        sys.exit(1)
    if punktinfo is not None:
        firecli.print(f"Fandt {ident}", fg="green", err=False)
    else:
        firecli.print(f"Fandt ikke {ident}", fg="cyan", err=False)
    return punktinfo

# ------------------------------------------------------------------------------

def punkt_kote(punktinfo: PunktInformation, koteid: int) -> Koordinat:
    """Find aktuelle koordinatværdi for koordinattypen koteid"""
    if punktinfo is None:
        return None
    for koord in punktinfo.punkt.koordinater:
        if koord.sridid != koteid:
            continue
        if koord.registreringtil is None:
            return koord
    return None

# ------------------------------------------------------------------------------

def punkt_geometri(punktinfo: PunktInformation, ident: str) -> Tuple[float, float]:
    """Find placeringskoordinat for punkt"""
    if punktinfo is None:
        return (11, 56)
    try:
        geom = firedb.hent_geometri_objekt(punktinfo.punktid)
        # Turn the string "POINT (lon lat)" into the tuple "(lon, lat)"
        geo = eval(str(geom.geometri).lstrip("POINT").strip().replace(" ", ","))
        assert len(geo) == 2, "Bad geometry format: " + str(geom.geometri)
    except NoResultFound:
        firecli.print(f"Error! Geometry for {ident} not found!", fg="red", err=True)
        sys.exit(1)
    return geo

# ------------------------------------------------------------------------------

# Bør nok være en del af API
def hent_sridid(db, srid: str) -> int:
    srider = db.hent_srider()
    for s in srider:
        if s.name == srid:
            return s.sridid
    return 0

# ------------------------------------------------------------------------------

def find_path(graph, start, end, path=[]):
    """
    Mikroskopisk backtracking netkonnektivitetstest. Baseret på et
    essay af GvR fra https://www.python.org/doc/essays/graphs/, men
    her moderniseret fra Python 1.8(?) til 3.6 og modificeret til
    at arbejde på dict-over-set (originalen brugte dict-over-list)
    """
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    for node in graph[start]:
        if node not in path:
            newpath = find_path(graph, node, end, path)
            if newpath:
                return newpath
    return None

# ------------------------------------------------------------------------------
# Eksempel:
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
# print (find_path (graph, 'A', 'C'))
# print (find_path (graph, 'A', 'G'))
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------

def find_nyetablerede():
    """Opbyg oversigt over nyetablerede punkter"""
    print("Finder nyetablerede punkter")
    try:
        nyetablerede = pd.read_excel(
            "projekt.xlsx",
            sheet_name="Nyetablerede punkter",
            usecols="A:E",
            dtype={
                "Foreløbigt navn": np.object,
                "Endeligt navn": np.object,
                "φ": np.float64,
                "λ": np.float64,
                "Foreløbig kote": np.float64,
            },
        )
    except:
        nyetablerede = pd.DataFrame(
            columns={"Foreløbigt navn", "Endeligt navn", "φ", "λ", "Foreløbig kote"},
        )
        assert nyetablerede.shape[0] == 0, "Forventede tom dataframe"

    # Sæt 'Foreløbigt navn'-søjlen som index, så vi kan adressere
    # som nyetablerede.at[punktnavn, elementnavn]
    return nyetablerede.set_index("Foreløbigt navn")

# ------------------------------------------------------------------------------

def find_inputfiler():
    """Opbyg oversigt over alle input-filnavne og deres tilhørende spredning"""
    try:
        inputfiler = pd.read_excel(
            "projekt.xlsx", sheet_name="Filoversigt", usecols="C:D"
        )
    except:
        sys.exit("Kan ikke finde filoversigt i projektfil")
    inputfiler = inputfiler[inputfiler["Filnavn"].notnull()]  # Fjern blanklinjer
    filnavne = inputfiler["Filnavn"]
    spredning = inputfiler["σ"]
    assert len(filnavne) > 0, "Ingen inputfiler anført"
    return list(zip(filnavne, spredning))

# ------------------------------------------------------------------------------

def find_observationer(importér):
    """Opbyg dataframe med alle observationer"""
    # Hvis importér ikke er sat: Læs observationer direkte i projektregnearket
    if not importér:
        print("Læser observationer")
        try:
            observationer = pd.read_excel(
                "projekt.xlsx", sheet_name="Observationer", usecols="A:P"
            )
        except:
            sys.exit('Kan ikke finde fanebladet "Observationer" i projektfil')
        # Opbyg liste over alle punkter (set(...) eliminerer dubletter)
        return observationer

    # Hvis importér er sat: Opbyg dataframe med alle observationer
    print("Importerer observationer")
    observationer = pd.DataFrame(
        get_observation_strings(find_inputfiler()),
        columns=[
            "journal",
            "fra",
            "til",
            "dH",
            "L",
            "opst",
            "σ",
            "kommentar",
            "dato",
            "tid",
            "T",
            "sky",
            "sol",
            "vind",
            "sigt",
            "kilde",
        ],
    )
    return observationer.sort_values(by="journal").set_index("journal").reset_index()

# ------------------------------------------------------------------------------

def find_punktoversigt(udførPunktliste, nyetablerede, allePunkter, nyePunkter):
    # Læs den foreløbige punktoversigt, for at kunne se om der skal gås i databasen
    try:
        punktoversigt = pd.read_excel(
            "projekt.xlsx", sheet_name="Punktoversigt", usecols="A:K"
        )
    except:
        punktoversigt = pd.DataFrame(
            columns=[
                "punkt",
                "fix",
                "upub",
                "år",
                "kote",
                "σ",
                "ny",
                "Δ",
                "kommentar",
                "φ",
                "λ",
            ]
        )
        assert punktoversigt.shape[0] == 0, "Forventede tom dataframe"
    if not udførPunktliste:
        return punktoversigt

    # Find og tilføj de punkter, der mangler i punktoversigten.
    manglendePunkter = set(allePunkter) - set(punktoversigt["punkt"])
    pkt = list(punktoversigt["punkt"]) + list(manglendePunkter)
    # Forlæng punktoversigt, så der er plads til alle punkter
    punktoversigt = punktoversigt.reindex(range(len(pkt)))
    punktoversigt["punkt"] = pkt
    # Geninstaller 'punkt'-søjlen som indexsøjle
    punktoversigt = punktoversigt.set_index("punkt")

    # Hent kote og placering fra databasen hvis vi ikke allerede har den
    print("Checker for manglende kote og placering")
    print(allePunkter)
    print(nyePunkter)
    print(observeredePunkter)

    koteid = np.nan
    for punkt in allePunkter:
        if not pd.isna(punktoversigt.at[punkt, "kote"]):
            continue
        if punkt in nyePunkter:
            continue
        # Vi undgår tilgang til databasen hvis vi allerede har alle koter
        # ved først at hente koteid når vi ved vi har brug for den
        if np.isnan(koteid):
            koteid = hent_sridid(firedb, "EPSG:5799")
            assert koteid != 0, "DVR90 (EPSG:5799) ikke fundet i srid-tabel"

        info = punkt_information(punkt)

        kote = punkt_kote(info, koteid)
        if kote is not None:
            punktoversigt.at[punkt, "kote"] = kote.z
            punktoversigt.at[punkt, "σ"] = kote.sz
            punktoversigt.at[punkt, "år"] = kote.registreringfra.year

        geom = punkt_geometri(info, punkt)
        if pd.isna(punktoversigt.at[punkt, "φ"]):
            punktoversigt.at[punkt, "φ"] = geom[1]
            punktoversigt.at[punkt, "λ"] = geom[0]

    # Nyetablerede punkter er ikke i databasen, så hent eventuelle manglende
    # koter og placeringskoordinater i fanebladet 'Nyetablerede punkter'
    for punkt in nyePunkter:
        if pd.isna(punktoversigt.at[punkt, "kote"]):
            punktoversigt.at[punkt, "kote"] = nyetablerede.at[punkt, "Foreløbig kote"]
        if pd.isna(punktoversigt.at[punkt, "φ"]):
            punktoversigt.at[punkt, "φ"] = nyetablerede.at[punkt, "φ"]
        if pd.isna(punktoversigt.at[punkt, "λ"]):
            punktoversigt.at[punkt, "λ"] = nyetablerede.at[punkt, "λ"]

    # Check op på placeringskoordinaterne. Hvis nogle ligner UTM, så regner vi
    # om til geografiske koordinater. NaN og 0 flyttes ud i Kattegat, så man kan
    # få øje på dem
    utm32 = Proj("proj=utm zone=32 ellps=GRS80", preserve_units=False)
    assert utm32 is not None, "Kan ikke initialisere projektionselelement utm32"
    for punkt in allePunkter:
        phi = punktoversigt.at[punkt, "φ"]
        lam = punktoversigt.at[punkt, "λ"]

        if pd.isna(phi) or pd.isna(lam) or 0 == phi or 0 == lam:
            punktoversigt.at[punkt, "φ"] = 56
            punktoversigt.at[punkt, "λ"] = 11
            continue

        # Heuristik til at skelne mellem UTM og geografiske koordinater.
        # Heuristikken fejler kun for UTM-koordinater fra et lille
        # område på 4 hektar ca. 500 km syd for Ghanas hovedstad, Accra.
        # Det er langt ude i Atlanterhavet, så det lever vi med.
        if abs(phi) < 100 and abs(lam) < 100:
            continue

        (lam, phi) = utm32(lam, phi, inverse=True)
        punktoversigt.at[punkt, "φ"] = phi
        punktoversigt.at[punkt, "λ"] = lam

    # Reformater datarammen så den egner sig til output
    return punktoversigt.sort_values(by="punkt").reset_index()

# ------------------------------------------------------------------------------

def netanalyse(observationer, allePunkter, fastholdtePunkter):
    print("Analyserer net")
    assert len(fastholdtePunkter) > 0, "Netanalyse kræver mindst et fastholdt punkt"
    # Initialiser
    net = dict()
    for punkt in allePunkter:
        net[punkt] = set()

    # Tilføj forbindelser alle steder hvor der er observationer
    for fra, til in zip(observationer["fra"], observationer["til"]):
        net[fra].add(til)
        net[til].add(fra)

    # Tilføj forbindelser fra alle fastholdte punkter til det første fastholdte punkt
    udgangspunkt = fastholdtePunkter[0]
    for punkt in fastholdtePunkter:
        if punkt != udgangspunkt:
            net[udgangspunkt].add(punkt)
            net[punkt].add(udgangspunkt)

    # Analysér netgraf
    forbundnePunkter = set()
    ensommePunkter = set()
    for punkt in allePunkter:
        if find_path(net, udgangspunkt, punkt) is None:
            ensommePunkter.add(punkt)
        else:
            forbundnePunkter.add(punkt)

    if len(ensommePunkter) != 0:
        print(
            "ADVARSEL: Følgende punkter er ikke observationsforbundne med fastholdt punkt. De medtages derfor ikke i udjævning"
        )
        print("Ensomme: ", ensommePunkter)

    # Vi vil ikke have de kunstige forbindelser mellem fastholdte punkter med
    # i output, så nu genopbygger vi nettet uden dem
    net = dict()
    for punkt in allePunkter:
        net[punkt] = set()
    for fra, til in zip(observationer["fra"], observationer["til"]):
        net[fra].add(til)
        net[til].add(fra)

    # De ensomme punkter skal heller ikke med i netgrafen
    for punkt in ensommePunkter:
        net.pop(punkt, None)

    # Nu kommer der noget grimt...
    # Tving alle rækker til at være lige lange, så vi kan lave en dataframe af dem
    maxAntalNaboer = max([len(net[e]) for e in net])
    nyt = dict()
    for punkt in net:
        naboer = list(net[punkt]) + maxAntalNaboer * [""]
        nyt[punkt] = tuple(naboer[0:maxAntalNaboer])

    # Ombyg og omdøb søjler med smart trick fra @piRSquared, https://stackoverflow.com/users/2336654/pirsquared
    # Se https://stackoverflow.com/questions/46078034/python-dict-with-values-as-tuples-to-pandas-dataframe
    netf = pd.DataFrame(nyt).T.rename_axis("Punkt").add_prefix("Nabo ").reset_index()
    netf.sort_values(by="Punkt", inplace=True)
    netf = netf.set_index("Punkt").reset_index()

    ensomme = pd.DataFrame(sorted(ensommePunkter), columns=["Punkt"])
    return netf, ensomme

# ------------------------------------------------------------------------------

def spredning(afstand_i_m, slope_i_mm_pr_sqrt_km=0.6, bias=0.0005):
    return 0.001 * (slope_i_mm_pr_sqrt_km * sqrt(afstand_i_m / 1000.0) + bias)

# ------------------------------------------------------------------------------

def designmatrix(observationer, punkter, estimerede, fastholdte):
    # Frasorter observationer mellem to fastholdte punkter, og
    # observationer som involverer punkt(er) som ikke indgår i
    # det sammenhængende net, udpeget af 'punkter'
    relevante = [
        not (e[0] in fastholdte and e[1] in fastholdte)
        and (e[0] in punkter and e[1] in punkter)
        for e in zip(observationer["fra"], observationer["til"])
    ]
    observationer = observationer[relevante]

    n = len(observationer)
    X = pd.DataFrame(0, columns=estimerede, index=range(n))
    P = np.zeros(n, dtype=np.float64)
    y = np.zeros(n, dtype=np.float64)

    # Opstil designmatrix, responsvektor og vægtvektor
    row = 0
    for obs in observationer[["fra", "til", "dH", "L", "σ"]].values:
        # Eliminer fastholdte ved at trække dem fra både
        # i designmatricen, X og i responsvektoren, y.
        # I designmatricen er de i forvejen trukket ud ved
        # overhovedet ikke at figurere blandt søjlerne.
        # Derfor udestår kun at trække dem fra i y
        y[row] = obs[2]
        if obs[0] in fastholdte:
            y[row] += fastholdte[obs[0]]
        else:
            X.at[row, obs[0]] = -1

        if obs[1] in fastholdte:
            y[row] -= fastholdte[obs[1]]
        else:
            X.at[row, obs[1]] = 1
        P[row] = 1.0 / spredning(obs[3], obs[4])
        row += 1

    return X, P, y

# ------------------------------------------------------------------------------
# Her starter hovedprogrammet...
# ------------------------------------------------------------------------------

@mtl.command()
@fire.cli.default_options()
@click.argument("projektnavn")
def go(ident: str, **kwargs) -> None:
    print("Så kører vi")

    # -----------------------------------------------------
    # Opbyg oversigt over nyetablerede punkter
    # -----------------------------------------------------
    nyetablerede = find_nyetablerede()
    nyePunkter = set(nyetablerede.index)

    # -----------------------------------------------------
    # Opbyg oversigt over alle observationer
    # -----------------------------------------------------
    observationer = find_observationer(True)
    observeredePunkter = set(observationer["fra"].append(observationer["til"]))
    # Vi er færdige med mængdeoperationer nu, så gør punktmængderne immutable
    allePunkter = tuple(observeredePunkter.union(nyePunkter))
    nyePunkter = tuple(nyePunkter)
    observeredePunkter = tuple(observeredePunkter)

    # -----------------------------------------------------
    # Opbyg oversigt over alle punkter
    # -----------------------------------------------------
    udførPunktliste = True
    punktoversigt = find_punktoversigt(
        udførPunktliste, nyetablerede, allePunkter, nyePunkter
    )
    fastholdtePunkter = tuple(punktoversigt[punktoversigt["fix"] == "x"]["punkt"])
    fastholdteKoter = tuple(punktoversigt[punktoversigt["fix"] == "x"]["kote"])
    if len(fastholdtePunkter) == 0:
        fastholdtePunkter = [observeredePunkter[0]]
        fastholdteKoter = [observeredeKoter[0]]

    # -----------------------------------------------------
    # Udfør netanalyse
    # -----------------------------------------------------
    (net, ensomme) = netanalyse(observationer, allePunkter, fastholdtePunkter)

    # -----------------------------------------------------
    # Opstil designmatrix, responsvektor og vægtvektor
    # -----------------------------------------------------
    forbundnePunkter = tuple(net["Punkt"])
    estimerede = tuple(sorted(set(forbundnePunkter) - set(fastholdtePunkter)))
    fastholdte = dict(zip(fastholdtePunkter, fastholdteKoter))
    (X, P, y) = designmatrix(observationer, forbundnePunkter, estimerede, fastholdte)

    # -----------------------------------------------------
    # Udfør beregning og rapporter i kort form
    # -----------------------------------------------------
    # Først en ikke-vægtet udjævning som sammenligningsgrundlag
    model = sm.OLS(y, X)
    result = model.fit()
    print("Ikke-vægtet")
    print(result.params)

    # Se https://www.statsmodels.org/devel/examples/notebooks/generated/wls.html
    model = sm.WLS(y, X, weights=P ** 2)
    result = model.fit()

    print("Vægtet")
    # Se https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.html
    print(result.params)
    print(result.HC0_se)
    # print(result.summary())
    print(result.summary2())
    wlsparams = result.params
    print(dir(result))

    # Geninstaller 'punkt'-søjlen som indexsøjle, så vi kan indicere fornuftigt
    punktoversigt = punktoversigt.set_index("punkt")
    for punkt, kote in zip(estimerede, wlsparams):
        punktoversigt.at[punkt, "ny"] = kote
    punktoversigt = punktoversigt.reset_index()

    # Ændring i millimeter
    d = list(abs(punktoversigt["kote"] - punktoversigt["ny"]) * 1000)
    print(d)
    dd = [e if e > 0.001 else None for e in d]
    print(dd)

    print(dd)
    punktoversigt["Δ"] = dd

    # -----------------------------------------------------
    # Skriv resultatfil
    # -----------------------------------------------------
    # Så kan vi skrive. Med lidt hjælp fra:
    # https://www.marsja.se/pandas-excel-tutorial-how-to-read-and-write-excel-files
    # https://pypi.org/project/XlsxWriter/
    # -----------------------------------------------------
    print("Skriver netoversigt")

    X["P"] = np.floor(100 * P / max(P) + 0.5)
    X["y"] = y

    ark = [
        ("Observationer", observationer),
        ("Punktoversigt", punktoversigt),
        ("Netgeometri", net),
        ("Ensomme", ensomme),
        ("Designmatrix", X),
    ]
    writer = pd.ExcelWriter("netoversigt.xlsx", engine="xlsxwriter")
    for a in ark:
        if a[1] is not None:
            a[1].to_excel(writer, sheet_name=a[0], index=False)
    writer.save()
    print("Færdig - output kan ses i [netoversigt.xlsx]")
