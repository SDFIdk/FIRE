import subprocess
import sys
import webbrowser
from math import hypot, sqrt
from typing import Dict, List, Set, Tuple

import click
import pandas as pd
import xmltodict

import fire.cli
from fire import uuid
from fire.cli import firedb

# Typingelementer fra databaseAPIet.
from fire.api.model import (
    Punkt,
    Observation,
    PunktInformation,
)

from . import (
    ARKDEF_FILOVERSIGT,
    ARKDEF_OBSERVATIONER,
    ARKDEF_PUNKTOVERSIGT,
    anvendte,
    check_om_resultatregneark_er_lukket,
    find_nyetablerede,
    niv,
    normaliser_placeringskoordinat,
    punkter_geojson,
    skriv_ark,
)

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


# ------------------------------------------------------------------------------
def find_fastholdte(punktoversigt: pd.DataFrame) -> Dict[str, float]:
    relevante = punktoversigt[punktoversigt["Fasthold"] == "x"]
    fastholdte_punkter = tuple(relevante["Punkt"])
    fastholdteKoter = tuple(relevante["Kote"])
    return dict(zip(fastholdte_punkter, fastholdteKoter))


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
