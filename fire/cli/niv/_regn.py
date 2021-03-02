import os
import subprocess
import sys
import webbrowser
from math import hypot, sqrt
from typing import Dict, List, Set, Tuple

import click
import pandas as pd
import xmltodict

import fire.cli

from fire.api.model import (
    Punkt,
    Observation,
)

from . import (
    ARKDEF_NYETABLEREDE_PUNKTER,
    ARKDEF_OBSERVATIONER,
    ARKDEF_PUNKTOVERSIGT,
    anvendte,
    find_faneblad,
    gyldighedstidspunkt,
    niv,
    punkter_geojson,
    skriv_ark,
)

from ._netoversigt import netanalyse


@niv.command()
@fire.cli.default_options()
@click.argument("projektnavn", nargs=1, type=str)
def regn(projektnavn: str, **kwargs) -> None:
    """Beregn nye koter.

    Hvis der allerede er foretaget kontrolberegning udfører vi en endelig
    beregning. Valget styres via navnet på seneste oversigtsfaneblad, som
    går fra 'Punktoversigt' (skabt af 'læs_observationer'), via
    'Kontrolberegning' (der skrives ved første kald til denne funktion),
    til 'Endelig beregning' (der skrives ved efterfølgende kald).
    """
    fire.cli.print("Så regner vi")

    # Hvis der ikke allerede findes et kontrolberegningsfaneblad, så er det en
    # kontrolberegning vi skal i gang med.
    kontrol = (
        find_faneblad(projektnavn, "Kontrolberegning", ARKDEF_PUNKTOVERSIGT, True)
        is None
    )

    # ...og så kan vi vælge den korrekte fanebladsprogression
    if kontrol:
        faneblad = "Punktoversigt"
        næste_faneblad = "Kontrolberegning"
    else:
        faneblad = "Kontrolberegning"
        næste_faneblad = "Endelig beregning"

    # Håndter fastholdte punkter og slukkede observationer.
    observationer = find_faneblad(projektnavn, "Observationer", ARKDEF_OBSERVATIONER)
    punktoversigt = find_faneblad(projektnavn, faneblad, ARKDEF_PUNKTOVERSIGT)
    fastholdte = find_fastholdte(punktoversigt)
    if 0 == len(fastholdte):
        fire.cli.print("Der skal fastholdes mindst et punkt i en beregning")
        sys.exit(1)

    # Ny netanalyse: Tag højde for slukkede observationer og fastholdte punkter.
    resultater = netanalyse(projektnavn)

    # Beregn nye koter for de ikke-fastholdte punkter...
    forbundne_punkter = tuple(sorted(resultater["Netgeometri"]["Punkt"]))
    estimerede_punkter = tuple(sorted(set(forbundne_punkter) - set(fastholdte)))
    fire.cli.print(
        f"Fastholder {len(fastholdte)} og beregner nye koter for {len(estimerede_punkter)} punkter"
    )
    beregning, htmlrapportnavn = gama_beregning(
        projektnavn, observationer, punktoversigt, estimerede_punkter, kontrol
    )
    resultater[næste_faneblad] = beregning

    # ...og beret om resultaterne
    punkter_geojson(projektnavn, resultater[næste_faneblad])
    skriv_ark(projektnavn, resultater)
    webbrowser.open_new_tab(htmlrapportnavn)
    if "startfile" in dir(os):
        fire.cli.print("Færdig! - åbner regneark og resultatrapport for check.")
        os.startfile(f"{projektnavn}.xlsx")


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

    Negative afstandsafhængig- eller centreringsspredninger
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
    kontrol: bool,
) -> Tuple[pd.DataFrame, str]:
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
            if obs.Sluk == "x":
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
    if kontrol:
        beregningstype = "kontrol"
    else:
        beregningstype = "endelig"

    htmlrapportnavn = f"{projektnavn}-resultat-{beregningstype}.html"
    ret = subprocess.run(
        [
            "gama-local",
            f"{projektnavn}.xml",
            "--xml",
            f"{projektnavn}-resultat.xml",
            "--html",
            htmlrapportnavn,
        ]
    )
    if ret.returncode:
        fire.cli.print(
            f"Check {projektnavn}-resultat-{beregningstype}.html", bg="red", fg="white"
        )

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
    punktoversigt["uuid"] = ""
    punktoversigt["Udelad publikation"] = ""
    punktoversigt["Fasthold"] = "x"
    punktoversigt["Ny kote"] = None
    punktoversigt["Ny σ"] = None
    punktoversigt["Δ-kote [mm]"] = None
    punktoversigt["Opløft [mm/år]"] = float("NaN")
    punktoversigt["System"] = "DVR90"
    tg = gyldighedstidspunkt(projektnavn)
    punktoversigt = punktoversigt.set_index("Punkt")

    for punkt, ny_kote, var in zip(punkter, koter, varianser):
        punktoversigt.at[punkt, "Ny kote"] = ny_kote
        punktoversigt.at[punkt, "Ny σ"] = sqrt(var)
        punktoversigt.at[punkt, "Fasthold"] = ""

        # Ændring i millimeter...
        Δ = (ny_kote - punktoversigt.at[punkt, "Kote"]) * 1000.0
        # ...men vi ignorerer ændringer under mikrometerniveau
        if abs(Δ) < 0.001:
            Δ = 0
        punktoversigt.at[punkt, "Δ-kote [mm]"] = Δ
        dt = punktoversigt.at[punkt, "Hvornår"] - tg
        dt = dt.total_seconds() / (365.25 * 86400)
        # t = 0 forekommer ved genberegning af allerede registrerede koter
        if dt == 0:
            continue
        punktoversigt.at[punkt, "Opløft [mm/år]"] = Δ / dt
    punktoversigt = punktoversigt.reset_index()
    return (punktoversigt, htmlrapportnavn)
