import subprocess
import webbrowser
from pathlib import Path
from math import hypot, sqrt
from typing import Dict, Tuple, Iterable, NamedTuple, List
from dataclasses import dataclass

import click
import pandas as pd
import numpy as np
import xmltodict

from fire.io.regneark import arkdef
import fire.cli

from . import (
    find_faneblad,
    gyldighedstidspunkt,
    niv,
    skriv_punkter_geojson,
    skriv_observationer_geojson,
    skriv_ark,
    er_projekt_okay,
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
    er_projekt_okay(projektnavn)

    fire.cli.print("Så regner vi")

    # Hvis der ikke allerede findes et kontrolberegningsfaneblad, så er det en
    # kontrolberegning vi skal i gang med.
    kontrol = (
        find_faneblad(projektnavn, "Kontrolberegning", arkdef.PUNKTOVERSIGT, True)
        is None
    )

    # ...og så kan vi vælge den korrekte fanebladsprogression
    if kontrol:
        aktuelt_faneblad = "Punktoversigt"
        næste_faneblad = "Kontrolberegning"
        infiks = "-kon"
    else:
        aktuelt_faneblad = "Kontrolberegning"
        næste_faneblad = "Endelig beregning"
        infiks = ""

    # Håndter fastholdte punkter og slukkede observationer.
    observationer = find_faneblad(projektnavn, "Observationer", arkdef.OBSERVATIONER)
    punktoversigt = find_faneblad(projektnavn, "Punktoversigt", arkdef.PUNKTOVERSIGT)
    arbejdssæt = find_faneblad(projektnavn, aktuelt_faneblad, arkdef.PUNKTOVERSIGT)

    # Til den endelige beregning skal vi bruge de oprindelige observationsdatoer
    if not kontrol:
        arbejdssæt["Hvornår"] = punktoversigt["Hvornår"]

    # tmp = Arbejdssæt()
    # arbejdssæt = from_pandas(tmp,arbejdssæt)
    # print(arbejdssæt)

    fastholdte = find_fastholdte(arbejdssæt.values.tolist(), kontrol)
    if 0 == len(fastholdte):
        fire.cli.print("Der skal fastholdes mindst et punkt i en beregning")
        raise SystemExit(1)

    # Ny netanalyse: Tag højde for slukkede observationer og fastholdte punkter.
    resultater = netanalyse(projektnavn)

    # Beregn nye koter for de ikke-fastholdte punkter...
    forbundne_punkter = tuple(sorted(resultater["Netgeometri"]["Punkt"]))
    estimerede_punkter = tuple(sorted(set(forbundne_punkter) - set(fastholdte)))
    fire.cli.print(
        f"Fastholder {len(fastholdte)} og beregner nye koter for {len(estimerede_punkter)} punkter"
    )

    # Skriv Gama-inputfil i XML-format
    skriv_gama(
        projektnavn, fastholdte, estimerede_punkter, observationer.values.tolist()
    )

    # Kør GNU Gama og skriv HTML rapport
    htmlrapportnavn = gama_udjævn(projektnavn, kontrol)

    # Indlæs nødvendige parametre til at skrive Gama output til xlsx
    punkter, koter, varianser, tg = læs_gnu_output(projektnavn)

    #
    beregning = gama_beregning(
        punkter, koter, varianser, arbejdssæt, len(punktoversigt), tg
    )
    beregning = pd.DataFrame(beregning, columns=list(arbejdssæt.columns))
    resultater[næste_faneblad] = beregning

    # ...og beret om resultaterne
    skriv_punkter_geojson(projektnavn, resultater[næste_faneblad], infiks=infiks)
    skriv_observationer_geojson(
        projektnavn,
        resultater[næste_faneblad].set_index("Punkt"),
        observationer,
        infiks=infiks,
    )
    skriv_ark(projektnavn, resultater)
    if fire.cli.firedb.config.getboolean("general", "niv_open_files"):
        webbrowser.open_new_tab(htmlrapportnavn)
        fire.cli.print("Færdig! - åbner regneark og resultatrapport for check.")
        fire.cli.åbn_fil(f"{projektnavn}.xlsx")


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

    opstillingsafhængig = sqrt(antal_opstillinger * (centreringsspredning_i_mm**2))

    if "MTL" == observationstype.upper():
        afstandsafhængig = afstandsafhængig_spredning_i_mm * afstand_i_m / 1000
        return hypot(afstandsafhængig, opstillingsafhængig)

    if "MGL" == observationstype.upper():
        afstandsafhængig = afstandsafhængig_spredning_i_mm * sqrt(afstand_i_m / 1000)
        return hypot(afstandsafhængig, opstillingsafhængig)

    raise ValueError(f"Ukendt observationstype: {observationstype}")


# ------------------------------------------------------------------------------
def find_fastholdte(punktoversigt: np.ndarray, kontrol: bool) -> Dict[str, float]:
    """Find fastholdte punkter til gama beregning"""
    punktoversigt = np.array(punktoversigt)
    if kontrol:
        relevante = punktoversigt[punktoversigt[:, 1] == "x"]
    else:
        relevante = punktoversigt[punktoversigt[:, 1] != ""]

    fastholdte_punkter = tuple(relevante[:, 0])
    fastholdte_koter = tuple(relevante[:, 4])
    return dict(zip(fastholdte_punkter, fastholdte_koter))


def skriv_gama(
    projektnavn: str,
    fastholdte: dict,
    estimerede_punkter: Tuple[str, ...],
    observationer: list,
):
    """
    Skriv gama-inputfil i XML-format
    """
    with open(f"{projektnavn}.xml", "wt") as gamafil:
        # Preambel
        gamafil.write(
            f"<?xml version='1.0' ?><gama-local>\n"
            f"<network angles='left-handed' axes-xy='en' epoch='0.0'>\n"
            f"<parameters\n"
            f"    algorithm='gso' angles='400' conf-pr='0.95'\n"
            f"    cov-band='0' ellipsoid='grs80' latitude='55.7' sigma-act='aposteriori'\n"
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
        for obs in observationer:
            if obs[1] == "x":
                continue
            gamafil.write(
                f"<dh from='{obs[2]}' to='{obs[3]}' "
                f"val='{obs[4]:+.6f}' "
                f"dist='{obs[5]:.5f}' stdev='{spredning(obs[17], obs[5], obs[6], obs[7], obs[8]):.5f}' "
                f"extern='{obs[0]}'/>\n"
            )

        # Postambel
        gamafil.write(
            "</height-differences>\n"
            "</points-observations>\n"
            "</network>\n"
            "</gama-local>\n"
        )


def gama_udjævn(projektnavn: str, kontrol: bool):
    """Lad GNU Gama om at køre udjævningen"""
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
        if not Path(f"{projektnavn}-resultat.xml").is_file():
            fire.cli.print(
                "FEJL: Beregning ikke gennemført. Kontroller om nettet er sammenhængende, og ved flere net om der mangler fastholdte punkter.",
                bg="red",
                fg="white",
            )
            raise SystemExit(1)

        fire.cli.print(
            f"Check {projektnavn}-resultat-{beregningstype}.html", bg="red", fg="white"
        )
    return htmlrapportnavn


def læs_gnu_output(
    projektnavn: str,
) -> Tuple[list[str], list[float], list[float], pd.Timestamp]:
    """
    Læser output fra GNU Gama og returnerer relevante parametre til at skrive xlsx fil
    """
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
    tg = gyldighedstidspunkt(projektnavn)
    return (punkter, koter, varianser, tg)


# ------------------------------------------------------------------------------
def gama_beregning(
    punkter: list[str],
    koter: list[float],
    varianser: list[float],
    arbejdssæt: List[float],
    n_punkter: int,
    tg: pd.Timestamp,
) -> List:

    arbejdssæt = np.array(arbejdssæt)
    # Tag højde for punkter der allerede eksisterer
    eksisterer = list(set(punkter).intersection(arbejdssæt[:, 0]))
    n_eksisterer = len(eksisterer)
    # Pre-allokér plads til dem der ikke gør
    tmp = np.ones((len(koter) - n_eksisterer, 14), dtype=float) * 99999
    # Sæt sammen og formattér
    arbejdssæt = np.vstack((arbejdssæt, tmp))
    arbejdssæt[:, 2][arbejdssæt[:, 2] == 99999] = pd.Timestamp("NaT")

    # Skriv resultaterne til arbejdssættet
    arbejdssæt[:, 9] = "DVR90"

    j = 0
    for i, (punkt, ny_kote, var) in enumerate(zip(punkter, koter, varianser)):
        i += n_punkter - j
        # Tjek om punkt allerede findes
        if arbejdssæt[:, 0].any() == punkt:
            i = np.where(arbejdssæt[:, 0] == punkt)[0][0]
            j += 1
        arbejdssæt[i, 0] = punkt
        arbejdssæt[i, 5] = ny_kote
        arbejdssæt[i, 6] = sqrt(var)

        # Ændring i millimeter...
        Delta = (ny_kote - arbejdssæt[i, 3]) * 1000.0
        # ...men vi ignorerer ændringer under mikrometerniveau
        if abs(Delta) < 0.001:
            Delta = 0
        arbejdssæt[i, 7] = Delta
        dt = tg - arbejdssæt[i, 2]
        dt = dt.total_seconds() / (365.25 * 86400)
        # t = 0 forekommer ved genberegning af allerede registrerede koter
        if dt == 0:
            continue
        arbejdssæt[i, 8] = Delta / dt
        arbejdssæt[i, 2] = tg

    arbejdssæt[arbejdssæt == 99999] = float("nan")

    return list(arbejdssæt)
