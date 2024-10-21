import subprocess
import webbrowser
from pathlib import Path
from math import hypot, sqrt
from typing import Dict, Tuple, List
from dataclasses import dataclass, asdict

import click
import xmltodict
from pandas import DataFrame, Timestamp, isna

from fire.api.model import (
    HøjdeTidsserie,
    Koordinat,
)
from fire.io.regneark import arkdef
import fire.cli

from fire.cli.ts.plot_ts import (
    plot_tidsserier,
)

from . import (
    find_faneblad,
    gyldighedstidspunkt,
    niv,
    skriv_punkter_geojson,
    skriv_observationer_geojson,
    skriv_ark,
    er_projekt_okay,
    hent_relevante_tidsserier,
    udled_jessenpunkt_fra_punktoversigt
)

from ._netoversigt import netanalyse


@dataclass
class Observationer:
    journal: List[str]
    sluk: List[str]
    fra: List[str]
    til: List[str]
    delta_H: List[float]
    L: List[int]
    opst: List[int]
    sigma: List[float]
    delta: List[float]
    kommentar: List[str]
    hvornår: List[Timestamp]
    T: List[float]
    sky: List[float]
    sol: List[float]
    vind: List[float]
    sigt: List[float]
    kilde: List[str]
    type: List[str]
    uuid: List[str]


@dataclass
class Arbejdssæt:
    punkt: List[int]
    fasthold: List[str]
    hvornår: List[Timestamp]
    kote: List[float]
    sigma: List[float]
    ny_kote: List[float]
    ny_sigma: List[float]
    Delta_kote: List[float]
    opløft: List[float]
    system: List[str]
    nord: List[float]
    øst: List[float]
    uuid: List[str]
    udelad: List[str]


@niv.command()
@fire.cli.default_options()
@click.argument("projektnavn", nargs=1, type=str)
@click.option(
    "-P",
    "--plot",
    type=bool,
    is_flag=True,
    default=False,
    help="Angiv om beregnede koter skal plottes som forlængelse af en tidsserie",
)
def regn(projektnavn: str, plot: bool, **kwargs) -> None:
    """Beregn nye koter.

    Forudsat nivellementsobservationer allerede er indlæst i sagsregnearket
    kan der beregnes nye koter på baggrund af disse observationer. Beregning
    af koter med dette program er en totrinsprocedure. Først udføres en
    kontrolberegning med et minimum af fastholdte punkter, med henblik på at
    kvaliteteskontrollere det tilgængelige observationsmateriale. Er der ingen
    åbenlyse fejl i observationerne kan der fortsættes til den endelige beregning.

    \f
    I den endelige beregning bør det overvejes mere grundigt hvilke punkter der
    fastholdes, samt om det kan være fordelagtigt at vægte nogle observationer
    højere eller lavere end andre.

    Hver kørsel af :program:`fire niv regn` starter med en analyse af det aktuelle
    nivellementsnet. Det er muligt at de indlæste observationer og punkter tilsammen
    udgør mere end et selvstændigt nivellementsnet, i så fald udgøres den samlede
    beregning af flere subnet. Udjævning i hvert subnet forudsætter mindst et
    fastholdt punkt. Når netanalysen er kørt vil programmet gøre opmærksom på hvis
    der er flere subnet og komme med forslag til et punkt i hvert subnet som kan
    fastholdes. Er der ingen fastholdte punkter afsluttes programmet med det samme.
    Netanalysen gemmes i sagsregnearket i fanebladene "Netgeometri" og "Singulære".
    Sidstnævnte er en oversigt over punkter der ikke er knyttet til resten af det
    målte net. "Netgeometri" beskriver hvordan nettet er opbygget ved at angive
    hvert punkts nabopunkter. Dette er blot en oversigt og bør ikke ændres af brugeren.

    Første gang :program:`fire niv regn` køres udføres kontrolberegningen. Den har
    til formål at sikre at opmålingsarbejdet er forløbet korrekt, herunder at

        1. der er målt til de rigtige punkter
        2. observationerne ikke helt er i skoven

    I fanebladet "Punktoversigt" angives hvilke punkter der skal fastholdes i
    kontrolberegningen. Sæt et "x" i kolonnen "Fasthold" for de relevante punkter.
    Typisk fastholdes kun et punkt pr subnet. Når beregningen er udført tilføjes
    fanebladet "Kontrolberegning" til sagsregnearket. Dette faneblad har samme opbygning
    som punktoversigten, dog nu med indhold i kolonnerne "Ny kote", "Ny σ", "Δ-kote"
    og "Opløft", der udgør beregningsresultatet.

    Den endelig beregning udføres ved at køre :program:`fire niv regn` igen. Hvis
    fanebladet "Kontrolberegning" er i sagsregnearket ved programmet det skal lave
    den endelige beregning. Er der behov for en ny kontrolberegning kan dette faneblad
    slettes og :program:`fire niv regn` køres på ny.
    I den endelige beregning finjusteres resultaterne fra kontrolberegningen. Formålet
    er, at producere de bedst mulige koter ud fra de tilgængelige observationer.
    Det *kan* indebære at fastholde andre punkter, eller måske flere end et.
    Det kan også være nødvendigt at vægte udvalgte observationer fra eller helt at
    udelukke dem fra udjævningen.
    Fastholdelse af punkter i den endelige beregning foretages i fanebladet "Kontrolberegning".
    Som udgangspunkt er de fastholdte punkter fra kontrolberegningen også markeret fastholdte
    i den endelige beregning. Er der behov for flere fastholdte punkter bør de angives med "e",
    så det er tydeligt hvilke fastholdte punkter der er forskellige fra kontrolberegningen.
    Vægten på de enkelte observationer kan justeres ved at ændre σ-værdien i fanebladet
    "Observationer" for den pågældende observation. Når den endelige beregning er udført
    findes resultatet i fanebladet "Endelig beregning".

    Udover beregningsresultaterne i sagsregnearket dannes der efter en beregning en række
    filer som placeres i samme mappe som sagsregnearket. Det drejer sig om beregningsrapporter
    m.m. fra udjævningsprogrammet GNU Gama og en række GIS-filer der indeholder et overblik
    over punkter og observationer, der indgår i udjævningen.

    Følgende filer relaterer sig til GNU Gama

    ==========================  =============================================================
    Filnavn                     Beskrivelse
    ==========================  =============================================================
    SAG.xml                     Input fil til gama, lavet ud fra data i regneark
    SAG-resultat.xml            Output fil fra gama, læses af fire og oversættes til regneark
    SAG-resultat-kontrol.html   Beregningsrapport for kontrolberegning
    SAG-resultat-endelig.html   Beregningsrapport for endelige beregning
    ==========================  =============================================================

    Input og output filer til Gama overskrives for hver beregning der udføres,
    men beregningsrapporten gemmes særskilt for kontrol og endelig beregning.

    De genererede GIS-filer er

    ==============================  ==============================================
    Filnavn                         Beskrivelse
    ==============================  ==============================================
    SAG-kon-punkter.geojson         Punkter brugt i kontrolberegningen
    SAG-kon-observationer.geojson   Observationer brugt i kontrolberegningen
    SAG-punkter.geojson             Punkter brugt i den endelige beregning
    SAG-observationer.geojson       Observationer brugt i den endelige beregning
    ==============================  ==============================================

    Formatet på GIS-filerne er GeoJSON, der let kan indlæses i QGIS for at danne et
    bedre overblik over nivellementsnettet der regnes på.
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

    arb_søjler = arbejdssæt.columns
    obs_søjler = observationer.columns
    # Konverter til dataklasse
    observationer = obs_til_dataklasse(observationer)
    arbejdssæt = arb_til_dataklasse(arbejdssæt)

    # Lokalisér fastholdte punkter
    fastholdte = find_fastholdte(arbejdssæt, kontrol)
    if 0 == len(fastholdte):
        fire.cli.print("Der skal fastholdes mindst et punkt i en beregning")
        raise SystemExit(1)

    if any([v for v in fastholdte.values() if isna(v)]):
        fire.cli.print(
            "Der skal angives koter for alle fastholdte punkter i en beregning"
        )
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
    skriv_gama_inputfil(projektnavn, fastholdte, estimerede_punkter, observationer)

    # Kør GNU Gama og skriv HTML rapport
    htmlrapportnavn = gama_udjævn(projektnavn, kontrol)

    # Indlæs nødvendige parametre til at skrive Gama output til xlsx
    punkter, koter, varianser = læs_gama_output(projektnavn)
    t_gyldig = gyldighedstidspunkt(projektnavn)

    # Opdater arbejdssæt med GNU Gama output
    beregning = opdater_arbejdssæt(punkter, koter, varianser, arbejdssæt, t_gyldig)
    værdier = []
    for _, værdi in asdict(beregning).items():
        værdier.append(værdi)
    beregning = DataFrame(list(zip(*værdier)), columns=arb_søjler)
    resultater[næste_faneblad] = beregning

    # Plot tidsserier forlænget med de nyberegnede koter.
    if plot == True:
        kotesystem = fire.cli.firedb.hent_srid(beregning["System"][0])

        # Hvis kotesystemet er Jessen, så skal Højdetidsserierne være angivet i Højdetidsserie-fanen.
        # Samme logik som i ilæg_nye_koter
        if kotesystem.name == "TS:jessen":
            fastholdt_kote, fastholdt_punkt = udled_jessenpunkt_fra_punktoversigt(
                beregning
            )
            hts_ark = find_faneblad(
                projektnavn,
                "Højdetidsserier",
                arkdef.HØJDETIDSSERIE,
                ignore_failure=False,
            )
            plot_titel = f"Højdetidsserier for jessenpunkt {fastholdt_punkt.jessennummer or fastholdt_punkt.ident}"
        else:
            plot_titel = f"Ad hoc {kotesystem.kortnavn or kotesystem.name}-tidsserier"

        tidsserier = []
        # Gennemgå alle punkter i beregningen, find eller konstruér tidsserier til plotting, og tilføj nyberegnede koter til dem
        for index, punktdata in beregning.iterrows():
            # Spring fastholdt punkt(er) over
            if punktdata["Fasthold"] != "":
                continue

            punkt = fire.cli.firedb.hent_punkt(punktdata["Punkt"])

            ny_kote = Koordinat(
                punkt=punkt,
                srid=kotesystem,
                z=punktdata["Ny kote"],
                sz=punktdata["Ny σ"],
                t=punktdata["Hvornår"],
            )

            # Find relevante tidsserier til plotting
            if kotesystem.name == "TS:jessen":
                relevante_tidsserier = hent_relevante_tidsserier(
                    hts_ark, punkt, fastholdt_punkt, fastholdt_kote
                )
                for ts in relevante_tidsserier:
                    ts.koordinater.append(ny_kote)

                tidsserier.extend(relevante_tidsserier)
            else:
                # Hvis kotesystemet ikke er Jessen, så laver vi en ad hoc tidsserie bestående af alle
                # koordinater tilhørende kotesystemet.
                koords = [
                    k
                    for k in punkt.koordinater
                    if k.srid == kotesystem and k.fejlmeldt == False
                ]
                tidsserie = HøjdeTidsserie(
                    punkt=punkt,
                    navn=f"{punkt.ident}_ADHOC_HTS_{kotesystem.kortnavn or kotesystem.name}",
                    formål=f"",
                    koordinater=koords,
                )

                tidsserier.append(tidsserie)
                tidsserie.koordinater.append(ny_kote)

        plot_tidsserier(plot_titel, tidsserier, fremhæv_nyeste_punkt=True)

    # ...og beret om resultaterne
    skriv_punkter_geojson(projektnavn, resultater[næste_faneblad], infiks=infiks)
    obs = []
    for _, o in asdict(observationer).items():
        obs.append(o)
    observationer = DataFrame(list(zip(*obs)), columns=obs_søjler)
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


# -----------------------------------------------------------------------------
def obs_til_dataklasse(obs: DataFrame):
    return Observationer(
        journal=list(obs["Journal"]),
        sluk=list(obs["Sluk"]),
        fra=list(obs["Fra"]),
        til=list(obs["Til"]),
        delta_H=list(obs["ΔH"]),
        L=list(obs["L"]),
        opst=list(obs["Opst"]),
        sigma=list(obs["σ"]),
        delta=list(obs["δ"]),
        kommentar=list(obs["Kommentar"]),
        hvornår=list(obs["Hvornår"]),
        T=list(obs["T"]),
        sky=list(obs["Sky"]),
        sol=list(obs["Sol"]),
        vind=list(obs["Vind"]),
        sigt=list(obs["Sigt"]),
        kilde=list(obs["Kilde"]),
        type=list(obs["Type"]),
        uuid=list(obs["uuid"]),
    )


def arb_til_dataklasse(arb: DataFrame):
    return Arbejdssæt(
        punkt=list(arb["Punkt"]),
        fasthold=list(arb["Fasthold"]),
        hvornår=list(arb["Hvornår"]),
        kote=list(arb["Kote"]),
        sigma=list(arb["σ"]),
        ny_kote=list(arb["Ny kote"]),
        ny_sigma=list(arb["Ny σ"]),
        Delta_kote=list(arb["Δ-kote [mm]"]),
        opløft=list(arb["Opløft [mm/år]"]),
        system=list(arb["System"]),
        nord=list(arb["Nord"]),
        øst=list(arb["Øst"]),
        uuid=list(arb["uuid"]),
        udelad=list(arb["Udelad publikation"]),
    )


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
def find_fastholdte(arbejdssæt: Arbejdssæt, kontrol: bool) -> Dict[str, float]:
    """Find fastholdte punkter til gama beregning"""
    if kontrol:
        # I kontrolberegningen markeres fastholdte punkter med "x" ...
        relevante = [i for i, f in enumerate(arbejdssæt.fasthold) if f == "x"]
    else:
        # ... men i den endelige beregning kan andre tegn også bruges, fx
        # "e". Formålet er, at let kunne skelne mellem punkter fastholdt
        # i kontrolberegningen og yderligere punkter der fastholdes i
        # den endelige beregning
        relevante = [i for i, f in enumerate(arbejdssæt.fasthold) if f != ""]

    fastholdte_punkter = (arbejdssæt.punkt[i] for i in relevante)
    fastholdte_koter = (arbejdssæt.kote[i] for i in relevante)

    return dict(zip(fastholdte_punkter, fastholdte_koter))


def skriv_gama_inputfil(
    projektnavn: str,
    fastholdte: dict,
    estimerede_punkter: Tuple[str, ...],
    observationer: Observationer,
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
        for sluk, fra, til, delta_H, L, type, opst, sigma, delta, journal in zip(
            observationer.sluk,
            observationer.fra,
            observationer.til,
            observationer.delta_H,
            observationer.L,
            observationer.type,
            observationer.opst,
            observationer.sigma,
            observationer.delta,
            observationer.journal,
        ):
            if sluk == "x":
                continue
            gamafil.write(
                f"<dh from='{fra}' to='{til}' "
                f"val='{delta_H:+.6f}' "
                f"dist='{L:.5f}' stdev='{spredning(type, L, opst, sigma, delta):.5f}' "
                f"extern='{journal}'/>\n"
            )

        # Postambel
        gamafil.write(
            "</height-differences>\n"
            "</points-observations>\n"
            "</network>\n"
            "</gama-local>\n"
        )


def gama_udjævn(projektnavn: str, kontrol: bool):
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


def læs_gama_output(
    projektnavn: str,
) -> Tuple[List[str], List[float], List[float], Timestamp]:
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
    varliste = doc["gama-local-adjustment"]["coordinates"]["cov-mat"]["flt"]

    punkter = [punkt["id"] for punkt in koteliste]
    koter = [float(punkt["z"]) for punkt in koteliste]
    varianser = [float(var) for var in varliste]
    assert len(koter) == len(varianser), "Mismatch mellem antal koter og varianser"

    return (punkter, koter, varianser)


# ------------------------------------------------------------------------------
def opdater_arbejdssæt(
    punkter: List[str],
    koter: List[float],
    varianser: List[float],
    arbejdssæt: Arbejdssæt,
    tg: Timestamp,
) -> Arbejdssæt:

    if len(set(arbejdssæt.system)) > 1:
        fire.cli.print(
            "FEJL: Flere forskellige højdereferencesystemer er angivet!",
            fg="white",
            bg="red",
            bold=True,
        )
        raise SystemExit()

    kotesystem = arbejdssæt.system[0]

    for punkt, ny_kote, var in zip(punkter, koter, varianser):
        if punkt in arbejdssæt.punkt:
            # Hvis punkt findes, sæt indeks til hvor det findes
            i = arbejdssæt.punkt.index(punkt)

            # Overskriv info i punkt der findes
            arbejdssæt.ny_kote[i] = ny_kote
            arbejdssæt.ny_sigma[i] = sqrt(var)

            # Ændring i millimeter...
            Delta = (ny_kote - arbejdssæt.kote[i]) * 1000.0
            # ...men vi ignorerer ændringer under mikrometerniveau
            if abs(Delta) < 0.001:
                Delta = 0
            arbejdssæt.Delta_kote[i] = Delta
            dt = tg - arbejdssæt.hvornår[i]
            dt = dt.total_seconds() / (365.25 * 86400)
            # t = 0 forekommer ved genberegning af allerede registrerede koter
            if dt == 0:
                continue
            arbejdssæt.opløft[i] = Delta / dt
            arbejdssæt.hvornår[i] = tg
        else:
            # Tilføj nye punkter
            arbejdssæt.punkt.append(punkt)
            arbejdssæt.ny_sigma.append(sqrt(var))
            arbejdssæt.hvornår.append(tg)
            arbejdssæt.ny_kote.append(ny_kote)
            arbejdssæt.system.append(kotesystem)

            # Fyld
            arbejdssæt.fasthold.append("")
            arbejdssæt.kote.append(None)
            arbejdssæt.sigma.append(None)
            arbejdssæt.Delta_kote.append(None)
            arbejdssæt.opløft.append(None)
            arbejdssæt.øst.append(None)
            arbejdssæt.nord.append(None)
            arbejdssæt.uuid.append(None)
            arbejdssæt.udelad.append("")

    fastholdte = [i for i, f in enumerate(arbejdssæt.fasthold) if f != ""]
    for i in fastholdte:
        arbejdssæt.ny_kote[i] = None
        arbejdssæt.ny_sigma[i] = None
        arbejdssæt.Delta_kote[i] = None
        arbejdssæt.ny_kote[i] = None
        arbejdssæt.opløft[i] = None

    return arbejdssæt
