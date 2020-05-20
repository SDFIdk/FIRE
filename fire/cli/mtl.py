# Python infrastrukturelementer
import subprocess
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
from fire.api import FireDb
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
import xmltodict
from datetime import datetime


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
        try:
            with open(filnavn, "rt", encoding="utf-8") as obsfil:
                for line in obsfil:
                    if "#" != line[0]:
                        continue
                    line = line.lstrip("#").strip()

                    # Check at observationen er i et af de kendte formater
                    tokens = line.split(" ", 13)
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
                    tid = " ".join((tokens[kol.dato], tokens[kol.tid]))
                    try:
                        isotid = datetime.strptime(tid, "%d.%m.%Y %H.%M")
                    except ValueError:
                        sys.exit(
                            "Argh - ikke-understøttet datoformat: '"
                            + tid
                            + "' i fil: "
                            + filnavn
                        )

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
                        isotid,
                        float(tokens[kol.T]),
                        int(tokens[kol.sky]),
                        int(tokens[kol.sol]),
                        int(tokens[kol.vind]),
                        int(tokens[kol.sigt]),
                        filnavn,
                    ]
                    observationer.append(reordered)
        except FileNotFoundError:
            print("Kunne ikke læse filen '" + filnavn + "'")
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
        fire.cli.print(f"Error! {ident} not found!", fg="red", err=True)
        sys.exit(1)
    if punktinfo is not None:
        fire.cli.print(f"Fandt {ident}", fg="green", err=False)
    else:
        fire.cli.print(f"Fandt ikke {ident}", fg="cyan", err=False)
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
        # TODO: Perhaps just return (56,11) Kattegat pain instead
        assert len(geo) == 2, "Bad geometry format: " + str(geom.geometri)
    except NoResultFound:
        fire.cli.print(f"Error! Geometry for {ident} not found!", fg="red", err=True)
        sys.exit(1)
    return geo


# ------------------------------------------------------------------------------
# TODO: Bør nok være en del af API
# ------------------------------------------------------------------------------
def hent_sridid(db: FireDb, srid: str) -> int:
    srider = db.hent_srider()
    for s in srider:
        if s.name == srid:
            return s.sridid
    # TODO: kast en undtagelse (throw an exception)
    return 0


# ------------------------------------------------------------------------------
def path_to_origin(graph: Dict[str, Set[str]], start: str, origin: str, path: List[str] = []):
    """
    Mikroskopisk backtracking netkonnektivitetstest. Baseret på et
    essay af GvR fra https://www.python.org/doc/essays/graphs/, men
    her moderniseret fra Python 1.5 til 3.7 og modificeret til
    at arbejde på dict-over-set (originalen brugte dict-over-list)
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
# print (path_to_origin (graph, 'A', 'C'))
# print (path_to_origin (graph, 'A', 'G'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def find_nyetablerede(projektnavn: str) -> pd.DataFrame:
    """Opbyg oversigt over nyetablerede punkter"""
    print("Finder nyetablerede punkter")
    try:
        nyetablerede = pd.read_excel(
            projektnavn + ".xlsx",
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
            columns=["Foreløbigt navn", "Endeligt navn", "φ", "λ", "Foreløbig kote"],
        )
        assert nyetablerede.shape[0] == 0, "Forventede tom dataframe"

    # Sæt 'Foreløbigt navn'-søjlen som index, så vi kan adressere
    # som nyetablerede.at[punktnavn, elementnavn]
    return nyetablerede.set_index("Foreløbigt navn")


# ------------------------------------------------------------------------------
def find_inputfiler(navn: str) -> List[Tuple[str, float]]:
    """Opbyg oversigt over alle input-filnavne og deres tilhørende spredning"""
    try:
        inputfiler = pd.read_excel(
            navn + ".xlsx", sheet_name="Filoversigt", usecols="C:E"
        )
    except:
        sys.exit("Kan ikke finde filoversigt i projektfil")
    inputfiler = inputfiler[inputfiler["Filnavn"].notnull()]  # Fjern blanklinjer
    filnavne = inputfiler["Filnavn"]
    spredning = inputfiler["σ"]
    assert len(filnavne) > 0, "Ingen inputfiler anført"
    return list(zip(filnavne, spredning))


# ------------------------------------------------------------------------------
def importer_observationer() -> pd.DataFrame:
    """Opbyg dataframe med observationer importeret fra rådatafil"""
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
            "hvornår",
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
def find_observationer(navn: str) -> pd.DataFrame:
    """Opbyg dataframe med allerede importerede observationer"""
    print("Læser observationer")
    try:
        observationer = pd.read_excel(
            navn + ".xlsx", sheet_name="Observationer", usecols="A:P"
        )
    except:
        observationer = importer_observationer()
    return observationer


# ------------------------------------------------------------------------------
def opbyg_punktoversigt(
    navn: str,
    nyetablerede: pd.DataFrame,
    alle_punkter: Tuple[str, ...],
    nye_punkter: Tuple[str, ...],
) -> pd.DataFrame:
    # Læs den foreløbige punktoversigt, for at kunne se om der skal gås i databasen
    try:
        punktoversigt = pd.read_excel(
            navn + ".xlsx", sheet_name="Punktoversigt", usecols="A:L"
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
                "ny σ",
                "Δ",
                "kommentar",
                "φ",
                "λ",
            ]
        )
        assert punktoversigt.shape[0] == 0, "Forventede tom dataframe"
    print("Opbygger punktoversigt")

    # Find og tilføj de punkter, der mangler i punktoversigten.
    manglende_punkter = set(alle_punkter) - set(punktoversigt["punkt"])
    pkt = list(punktoversigt["punkt"]) + list(manglende_punkter)
    # Forlæng punktoversigt, så der er plads til alle punkter
    punktoversigt = punktoversigt.reindex(range(len(pkt)))
    punktoversigt["punkt"] = pkt
    # Geninstaller 'punkt'-søjlen som indexsøjle
    punktoversigt = punktoversigt.set_index("punkt")

    # Hent kote og placering fra databasen hvis vi ikke allerede har den
    print("Checker for manglende kote og placering")

    koteid = np.nan
    for punkt in alle_punkter:
        if not pd.isna(punktoversigt.at[punkt, "kote"]):
            continue
        if punkt in nye_punkter:
            continue
        # Vi undgår tilgang til databasen hvis vi allerede har alle koter
        # ved først at hente koteid når vi ved vi har brug for den
        if np.isnan(koteid):
            koteid = hent_sridid(firedb, "EPSG:5799")
            # TODO: Klar det med try:..except i stedet
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
    for punkt in nye_punkter:
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
    for punkt in alle_punkter:
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
def find_punktoversigt(
    navn: str,
    nyetablerede: pd.DataFrame,
    alle_punkter: Tuple[str, ...],
    nye_punkter: Tuple[str, ...],
) -> pd.DataFrame:
    # Læs den foreløbige punktoversigt, for at kunne se om der skal gås i databasen
    try:
        punktoversigt = pd.read_excel(
            navn + ".xlsx", sheet_name="Punktoversigt", usecols="A:K"
        )
    except:
        punktoversigt = opbyg_punktoversigt(
            navn, nyetablerede, alle_punkter, nye_punkter
        )
    return punktoversigt


# ------------------------------------------------------------------------------
def netanalyse(
    observationer: pd.DataFrame,
    alle_punkter: Tuple[str, ...],
    fastholdte_punkter: Tuple[str, ...],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    print("Analyserer net")
    assert len(fastholdte_punkter) > 0, "Netanalyse kræver mindst et fastholdt punkt"
    # Initialiser
    net = dict()
    for punkt in alle_punkter:
        net[punkt] = set()

    # Tilføj forbindelser alle steder hvor der er observationer
    for fra, til in zip(observationer["fra"], observationer["til"]):
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

    if len(ensomme_punkter) != 0:
        print(
            "ADVARSEL: Følgende punkter er ikke observationsforbundne med fastholdt punkt. De medtages derfor ikke i udjævning"
        )
        print("Ensomme: ", ensomme_punkter)

    # Vi vil ikke have de kunstige forbindelser mellem fastholdte punkter med
    # i output, så nu genopbygger vi nettet uden dem
    net = dict()
    for punkt in alle_punkter:
        net[punkt] = set()
    for fra, til in zip(observationer["fra"], observationer["til"]):
        net[fra].add(til)
        net[til].add(fra)

    # De ensomme punkter skal heller ikke med i netgrafen
    for punkt in ensomme_punkter:
        net.pop(punkt, None)

    # Nu kommer der noget grimt...
    # Tving alle rækker til at være lige lange, så vi kan lave en dataframe af dem
    maxAntalNaboer = max([len(net[e]) for e in net])
    nyt = dict()
    for punkt in net:
        naboer = list(sorted(net[punkt])) + maxAntalNaboer * [""]
        nyt[punkt] = tuple(naboer[0:maxAntalNaboer])

    # Ombyg og omdøb søjler med smart trick fra @piRSquared, https://stackoverflow.com/users/2336654/pirsquared
    # Se https://stackoverflow.com/questions/46078034/python-dict-with-values-as-tuples-to-pandas-dataframe
    netf = pd.DataFrame(nyt).T.rename_axis("Punkt").add_prefix("Nabo ").reset_index()
    netf.sort_values(by="Punkt", inplace=True)
    netf = netf.set_index("Punkt").reset_index()

    ensomme = pd.DataFrame(sorted(ensomme_punkter), columns=["Punkt"])
    return netf, ensomme


def find_forbundne_punkter(
    navn: str,
    observationer: pd.date_range,
    alle_punkter: Tuple[str, ...],
    fastholdte_punkter: Tuple[str, ...],
) -> Tuple[str, ...]:
    """Læs net fra allerede foretaget netanalyse"""
    try:
        net = pd.read_excel(navn + ".xlsx", sheet_name="Netgeometri", usecols="A")
    except:
        (net, ensomme) = netanalyse(observationer, alle_punkter, fastholdte_punkter)
    return tuple(sorted(net["Punkt"]))


# ------------------------------------------------------------------------------
def spredning(
    afstand_i_m: float, slope_i_mm_pr_sqrt_km: float = 0.6, bias: float = 0.0005
) -> float:
    return 0.001 * (slope_i_mm_pr_sqrt_km * sqrt(afstand_i_m / 1000.0) + bias)


# ------------------------------------------------------------------------------
def find_workflow(navn):
    try:
        workflow = pd.read_excel(navn + ".xlsx", sheet_name="Workflow", usecols="B:C")
    except:
        workflow = pd.DataFrame(columns=["Betegnelse", "Udføres"])
        assert workflow.shape[0] == 0, "Forventede tom dataframe"
    workflow = workflow[workflow["Udføres"] == "x"]
    return list(workflow["Betegnelse"])


# ------------------------------------------------------------------------------
# Her starter hovedprogrammet...
# ------------------------------------------------------------------------------
@mtl.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn", nargs=1, type=str,
)
def go(projektnavn: str, **kwargs) -> None:
    print("Så kører vi")

    workflow = find_workflow(projektnavn)
    print(f"Dagsorden: {workflow}")

    # -----------------------------------------------------
    # Opbyg oversigt over nyetablerede punkter
    # -----------------------------------------------------
    nyetablerede = find_nyetablerede(projektnavn)
    nye_punkter = set(nyetablerede.index)

    # -----------------------------------------------------
    # Opbyg oversigt over alle observationer
    # -----------------------------------------------------
    if "Observationer" in workflow:
        observationer = importer_observationer()
    else:
        observationer = find_observationer(projektnavn)

    observerede_punkter = set(observationer["fra"].append(observationer["til"]))
    # Vi er færdige med mængdeoperationer nu, så gør punktmængderne immutable
    alle_punkter = tuple(sorted(observerede_punkter.union(nye_punkter)))
    nye_punkter = tuple(sorted(nye_punkter))
    observerede_punkter = tuple(sorted(observerede_punkter))

    # ------------------------------------------------------
    # Opbyg oversigt over alle punkter m. kote og placering
    # ------------------------------------------------------
    if "Punktoversigt" in workflow:
        punktoversigt = opbyg_punktoversigt(
            projektnavn, nyetablerede, alle_punkter, nye_punkter
        )
    else:
        punktoversigt = find_punktoversigt(
            projektnavn, nyetablerede, alle_punkter, nye_punkter
        )

    fastholdte_punkter = tuple(punktoversigt[punktoversigt["fix"] == 0]["punkt"])
    fastholdteKoter = tuple(punktoversigt[punktoversigt["fix"] == 0]["kote"])
    if len(fastholdte_punkter) == 0:
        fastholdte_punkter = [observerede_punkter[0]]
        fastholdteKoter = [0]
    fastholdte = dict(zip(fastholdte_punkter, fastholdteKoter))
    print(f"Fastholdte: {fastholdte_punkter}")

    holdte_punkter = tuple(punktoversigt[punktoversigt["fix"] > 0]["punkt"])
    holdteKoter = tuple(punktoversigt[punktoversigt["fix"] > 0]["kote"])
    holdteSpredning = tuple(punktoversigt[punktoversigt["fix"] > 0]["fix"])
    holdte = dict(zip(holdte_punkter, zip(holdteKoter, holdteSpredning)))
    if len(holdte_punkter) > 0:
        print(f"Holdte: {holdte_punkter}")

    # -----------------------------------------------------
    # Udfør netanalyse
    # -----------------------------------------------------
    if "Net" in workflow:
        (net, ensomme) = netanalyse(observationer, alle_punkter, fastholdte_punkter)
        forbundne_punkter = tuple(sorted(net["Punkt"]))
    else:
        forbundne_punkter = find_forbundne_punkter(
            projektnavn, observationer, alle_punkter, fastholdte_punkter
        )
    estimerede_punkter = tuple(sorted(set(forbundne_punkter) - set(fastholdte_punkter)))
    print(f"Forbundne punkter: {forbundne_punkter}")
    print(f"Estimerede punkter: {estimerede_punkter}")

    if "Regn" in workflow:
        # -----------------------------------------------------
        # Skriv Gama-inputfil i XML-format
        # -----------------------------------------------------
        with open(projektnavn + ".xml", "wt") as gamafil:
            # Preambel
            gamafil.writelines(
                [
                    '<?xml version="1.0" ?><gama-local>\n',
                    '<network angles="left-handed" axes-xy="en" epoch="0.0">\n',
                    "<parameters\n",
                    '    algorithm="gso" angles="400" conf-pr="0.95"\n',
                    '    cov-band="0" ellipsoid="grs80" latitude="55.7" sigma-act="apriori"\n',
                    '    sigma-apr="1.0" tol-abs="1000.0"\n',
                    '    update-constrained-coordinates="no"\n',
                    "/>\n\n",
                ]
            )

            gamafil.write(
                f"<description>\n"
                f'    {"Nivellementsprojekt " + projektnavn}\n'
                f"</description>\n"
                f"<points-observations>\n\n"
            )

            # Fastholdte punkter
            gamafil.write("\n\n<!-- Fixed -->\n\n")
            for key, val in fastholdte.items():
                gamafil.write(f'<point fix="Z" id="{key}" z="{val}"/>\n')

            # Punkter til udjævning
            gamafil.write("\n\n<!-- Adjusted -->\n\n")
            for punkt in estimerede_punkter:
                gamafil.write(f'<point adj="z" id="{punkt}"/>\n')

            # Observationer
            gamafil.write("\n\n<height-differences>\n\n")
            for obs in observationer[["fra", "til", "dH", "L", "σ"]].values:
                gamafil.write(
                    f'<dh from="{obs[0]}" to="{obs[1]}" '
                    f'val="{obs[2]:+.6f}" '
                    f'dist="{obs[3]/1000:.5f}" stdev="{1000*spredning(obs[3], obs[4]):.5f}"/>\n'
                )

            # Postambel
            gamafil.write(
                "</height-differences>\n"
                "</points-observations>\n"
                "</network>\n"
                "</gama-local>\n"
            )

        # ----------------------------------------------
        # Lad GNU Gama om at køre udjævningen
        # ----------------------------------------------
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

        if 0 != ret:
            fire.cli.print(
                f"ADVARSEL! GNU Gama fandt mistænkelige observationer - check {projektnavn}.html for detaljer",
                bg="red",
                fg="white",
                err=False,
            )

        # ----------------------------------------------
        # Grav resultater frem fra GNU Gamas outputfil
        # ----------------------------------------------
        with open(projektnavn + "-resultat.xml") as resultat:
            doc = xmltodict.parse(resultat.read())
        koteliste = doc["gama-local-adjustment"]["coordinates"]["adjusted"]["point"]
        punkter = [punkt["id"] for punkt in koteliste]
        koter = [float(punkt["z"]) for punkt in koteliste]
        varliste = doc["gama-local-adjustment"]["coordinates"]["cov-mat"]["flt"]
        varianser = [float(var) for var in varliste]
        assert len(koter) == len(varianser), "Mismatch mellem antal koter og varianser"

        # ----------------------------------------------
        # Skriv resultaterne til punktoversigten
        # ----------------------------------------------
        punktoversigt = punktoversigt.set_index("punkt")
        for index in range(len(punkter)):
            punktoversigt.at[punkter[index], "ny"] = koter[index]
            punktoversigt.at[punkter[index], "ny σ"] = sqrt(varianser[index])
        punktoversigt = punktoversigt.reset_index()

        # Ændring i millimeter
        d = list(abs(punktoversigt["kote"] - punktoversigt["ny"]) * 1000)
        # Men vi ignorerer ændringer under mikrometerniveau
        dd = [e if e > 0.001 else None for e in d]
        punktoversigt["Δ"] = dd

    # -----------------------------------------------------------------------------
    # Skriv resultatfil
    # -----------------------------------------------------------------------------
    # Så kan vi skrive. Med lidt hjælp fra:
    # https://www.marsja.se/pandas-excel-tutorial-how-to-read-and-write-excel-files
    # https://pypi.org/project/XlsxWriter/
    # -----------------------------------------------------------------------------
    # NB: et sted undervejs i eksporten af instrument-rådata bliver utf-8 tegn
    # tilsyneladende erstattet af sekvensen "EF BF BD (character place keeper)".
    # Så det er ikke en fejl i mtl.py, når kommentaren "tæt trafik"
    # bliver repræsenteret som "t�t trafik". Fejlen må rettes opstrøms.
    # -----------------------------------------------------------------------------
    ark = [("Punktoversigt", punktoversigt)]
    if "Net" in workflow:
        ark += [("Netgeometri", net), ("Ensomme", ensomme)]
    if "Observationer" in workflow:
        ark += [("Observationer", observationer)]

    print(f"Skriver resultat-ark: {[a[0] for a in ark]}")
    writer = pd.ExcelWriter(f"{projektnavn}-resultat.xlsx", engine="xlsxwriter")
    for a in ark:
        if a[1] is not None:
            a[1].to_excel(writer, sheet_name=a[0], encoding="utf-8", index=False)
    writer.save()
    print(f"Færdig - output kan ses i '{projektnavn}-resultat.xlsx'")
