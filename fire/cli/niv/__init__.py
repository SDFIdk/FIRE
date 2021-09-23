import datetime
import json
import os
import os.path
import sys
from pathlib import Path
from typing import Dict, Tuple

import click
import pandas as pd
from pyproj import Proj

import fire.cli
from fire.api.model import (
    Point,
    Punkt,
    PunktInformation,
    Sag,
)


# Undgå ANSI farvekoder i Sphinx HTML docs
def grøn(tekst):
    if "sphinx" in sys.modules:
        return tekst
    return click.style(tekst, fg="green")


# ------------------------------------------------------------------------------
niv_help = f"""Nivellement: Arbejdsflow, beregning og analyse

Underkommandoerne:

    opret-sag

    udtræk-revision

    ilæg-revision

    ilæg-nye-punkter

    læs-observationer

    regn

    ilæg-observationer

    ilæg-nye-koter

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

REGN beregner nye koter til alle punkter, og genererer rapporter og
visualiseringsmateriale.

ILÆG-OBSERVATIONER lægger nye observationer i databasen.

ILÆG-NYE-KOTER lægger nyberegnede koter i databasen.

LUK-SAG arkiverer det afsluttende regneark og sætter sagens status til inaktiv.

Eksempel:

{grøn('fire niv opret-sag andeby_2020 "Vedligehold Andeby"')}

{grøn('fire niv udtræk-revision andeby_2020 K-99 102-08')}

{grøn('fire niv ilæg-revision andeby_2020')}

{grøn('fire niv ilæg-nye-punkter andeby_2020')}

{grøn('fire niv læs-observationer andeby_2020')}

{grøn('fire niv regn andeby_2020')}     <- kontrolberegning

{grøn('fire niv regn andeby_2020')}     <- endelig beregning

{grøn('fire niv ilæg-observationer andeby_2020')}

{grøn('fire niv ilæg-nye-koter andeby_2020')}

{grøn('fire niv luk-sag andeby_2020')}

"""


@click.group(help=niv_help)
def niv():
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
    "Fikspunktstype": str,
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
    "Hvornår": "datetime64[ns]",
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
    "Ny værdi": str,
    "id": float,
    "Ikke besøgt": str,
}

ARKDEF_SAG = {
    "Dato": "datetime64[ns]",
    "Hvem": str,
    "Hændelse": str,
    "Tekst": str,
    "uuid": str,
}

ARKDEF_PARAM = {
    "Navn": str,
    "Værdi": str,
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
def normaliser_lokationskoordinat(
    λ: float, φ: float, region: str = "DK", invers: bool = False
) -> Tuple[float, float]:
    """Check op på lokationskoordinaterne.
    En normaliseret lokationskoordinat er en koordinat der egner sig som
    WKT- og/eller geojson-geometriobjekt. Dvs. en koordinat anført i en
    afart af WGS84 og med akseorden længde, bredde (λ, φ).

    Hvis det ser ud som om akseordenen er gal, så bytter vi om på dem.

    Hvis input ligner UTM, så regner vi om til geografiske koordinater.
    NaN og 0 flyttes ud i Kattegat, så man kan få øje på dem.

    Disse korrektioner udføres med brug af bredt gyldige heuristikker,
    der dog er nødt til at gøre antagelser om hvor i verden vi befinder os.
    Dette kan eksplicit anføres med argumentet `region`, der som standard
    sættes til `"DK"`.

    Den omvendte vej (`invers==True`, input: geografiske koordinater,
    output: UTM-koordinater i traditionel lokationskoordinatorden)
    er indtil videre kun understøttet for `region=="DK"`.
    """
    # Gem kopi af oprindeligt input til brug i fejlmelding
    x, y = λ, φ

    global utm32
    if utm32 is None:
        utm32 = Proj("proj=utm zone=32 ellps=GRS80", preserve_units=False)
        assert utm32 is not None, "Kan ikke initialisere projektionselelement utm32"

    # Begrænset understøttelse af FO, GL, hvor UTM32 er meningsløst.
    # Der er gjort plads til indførelse af UTM24 og UTM29 hvis der skulle
    # vise sig behov, men det kræver en væsentlig algoritmeudvidelse.
    if region not in ("DK", ""):
        return (λ, φ)

    # Geometri-til-lokationskoordinat
    if invers:
        return utm32(λ, φ, inverse=False)

    if pd.isna(λ) or pd.isna(φ) or 0 == λ or 0 == φ:
        return (11.0, 56.0)

    # Heuristik til at skelne mellem UTM og geografiske koordinater.
    # Heuristikken fejler kun for UTM-koordinater fra et lille
    # område på 6 hektar ca. 500 km syd for Ghanas hovedstad, Accra.
    # Det er langt ude i Atlanterhavet, så det lever vi med.
    if abs(λ) > 181 and abs(φ) > 91:
        λ, φ = utm32(λ, φ, inverse=True)

    if region == "DK":
        if λ < 3.0 or λ > 15.5 or φ < 54.5 or φ > 58.0:
            raise ValueError(f"Koordinat ({x}, {y}) uden for dansk territorie")

    return (λ, φ)


# Globalt transformationsobjekt til normaliser_lokationskoordinat
utm32 = None

# -----------------------------------------------------------------------------
def skriv_ark(
    projektnavn: str, nye_faneblade: Dict[str, pd.DataFrame], suffix: str = ""
) -> bool:
    """Skriv resultater til excel-fil

    Basalt en temmeligt simpel operation, men virkemåden er næsten overskygget af
    kontroller af at filoperationer gik godt. Det er et vilkår ved interaktioner
    med filsystemer, så for overblikkets skyld kommer her en kort prosabeskrivelse.

    1. Flyt projektnavn.xlsx til projektnavn-ex.xlsx
    2. Læs dict gamle_faneblade fra projektnavn-ex.xlsx
    3. Fjern elementer fra gamle_faneblade hvis navnet også findes i nye_faneblade
    4. Skriv nye_faneblade til projektnavn.xlsx
    5. Skriv gamle_faneblade til projektnavn.xlsx

    Trin 4 kommer før trin 5 for at sikre at de nye faneblade er umiddelbart
    synlige når man åbner projektnavn.xlsx

    Eller mere direkte sagt:

    ```
    fil = Path(f"{projektnavn}{suffix}.xlsx")
    exfil = Path(f"{projektnavn}{suffix}-ex.xlsx")
    fil.replace(exfil)

    gamle_faneblade = pd.read_excel(exfil, sheet_name=None)
    for fanebladnavn in set(gamle_faneblade).intersection(nye_faneblade):
        gamle_faneblade.pop(fanebladnavn)

    with pd.ExcelWriter(fil) as writer:
        skriv nye_faneblade
        skriv gamle_faneblade
    ```

    Hvilket er i omegnen af en faktor 10 mindre end den implementerede
    version - men *it's a jungle out there*...
    """

    fil = Path(f"{projektnavn}{suffix}.xlsx")
    exfil = Path(f"{projektnavn}{suffix}-ex.xlsx")
    nye_navne = set(nye_faneblade)

    # Gå med seler og livrem: Læs fanebladsnavne fra originalfilen,
    #  så vi kan checke at alt kom helskindet med over i exfilen.
    #
    # NB: man kan læse en excelfil selv om den er åben. Derfor er
    # læsefejl her ikke tegn på at filen er åben (eller af anden
    # årsag låst), men på at filen ikke eksisterer.
    try:
        gamle_navne = set(pd.read_excel(fil, sheet_name=None))
    except Exception as ex:
        fire.cli.print(f"Filen '{fil}' findes ikke.")
        gamle_navne = set()

    fire.cli.print(f"Skriver: {nye_navne}")
    fire.cli.print(f"Til filen '{fil}'")

    # Størstedelen af "det der skal gøres" skal kun gøres hvis
    # vi skriver til en allerede eksisterende fil
    if gamle_navne:
        if len(gamle_navne.intersection(nye_navne)) > 0:
            fire.cli.print(
                f"Overskriver fanebladene {gamle_navne.intersection(nye_navne)}"
            )
            fire.cli.print(f"    med opdaterede versioner.")
            fire.cli.print(f"Foregående versioner beholdes i 'ex'-filen '{exfil}'")

        # Vi starter med at omdøbe fil.xlsx til fil-ex.xlsx - det giver sikkerhed
        # for på at ingen af filerne er i brug
        while True:
            try:
                fil.replace(exfil)
                break
            except Exception as ex:
                fire.cli.print(
                    f"Kan ikke håndtere '{fil}' - måske fordi den eller '{exfil}' er åben.",
                    fg="yellow",
                    bold=True,
                )
                fire.cli.print(f"Anden mulig årsag: {ex}")
                if input("Luk fil og prøv igen ([j]/n)? ") in ["j", "J", "ja", ""]:
                    continue
                fire.cli.print("Dropper skrivning")
                return False

        # Så læser vi de eksisterende faneblade.
        #
        # NB: Her er der er en mikroskopisk chance for en race-condition (hvad hedder det
        # på dansk?): Vi holder ikke en lås på exfilen når den opstår ved omdøbning af
        # projektfilen, så den kan overskrives af eksterne processer *efter* at vi har
        # omdøbt projektfilen og *inden* vi når videre hertil.
        #
        # Så her, og formodentlig overalt i FIRE, bortset fra databaseadgang, antager vi
        # at benspænd fra eksterne processer er sjældne og ignorable.
        #
        # Langt de fleste tænkelige benspænd af den slags vil enten fanges af
        # undtagelseshåndteringen, eller af "seler og livrem"-mekanismen omtalt ovenfor.
        try:
            gamle_faneblade = pd.read_excel(exfil, sheet_name=None)
        except Exception as ex:
            fire.cli.print(
                f"Kan ikke læse '{exfil}' - dropper skrivning af '{nye_navne}'.",
                fg="yellow",
                bold=True,
            )
            fire.cli.print(f"Systemfejlmeddelelse: {ex}")
            return False

        # Afslut seler og livrem: Check at fanebladnavnene stemmer
        if set(gamle_faneblade) != gamle_navne:
            fire.cli.print(
                f"Noget gik galt ved flytning af '{fil}' til '{exfil}'.",
                fg="yellow",
                bold=True,
            )
            fire.cli.print(f"    Dropper skrivning af '{nye_navne}'.")
            return False

        # Fjern gamle faneblade hvis der findes et nyt med samme navn
        for fanebladnavn in gamle_navne.intersection(nye_faneblade):
            gamle_faneblade.pop(fanebladnavn)
    else:
        gamle_faneblade = dict()

    # Skriv de nye faneblade, efterfulgt af de resterende gamle til den
    # opdaterede fil.
    # Derved bliver de nye faneblade umiddelbart synlige, når arket åbnes.
    try:
        with pd.ExcelWriter(fil) as writer:
            for navn in nye_faneblade:
                nye_faneblade[navn].replace("nan", "").to_excel(
                    writer, sheet_name=navn, encoding="utf-8", index=False
                )
            for navn in gamle_faneblade:
                gamle_faneblade[navn].replace("nan", "").to_excel(
                    writer, sheet_name=navn, encoding="utf-8", index=False
                )
    except Exception as ex:
        fire.cli.print(f"Kan ikke skrive opdateret '{fil}'!")
        if gamle_navne:
            fire.cli.print(f"Gammel version er stadig tilgængelig som '{exfil}'.")
        fire.cli.print(f"Systemfejlmeddelelse: {ex}")
        return False
    return True


# ------------------------------------------------------------------------------
def find_faneblad(
    projektnavn: str, faneblad: str, arkdef: Dict, ignore_failure: bool = False
) -> pd.DataFrame:
    try:
        return (
            pd.read_excel(
                f"{projektnavn}.xlsx",
                sheet_name=faneblad,
                usecols=anvendte(arkdef),
            )
            .dropna(how="all")
            .astype(arkdef)
            .replace("nan", "")
        )
    except Exception as ex:
        if ignore_failure:
            return None
        fire.cli.print(f"Kan ikke læse {faneblad} fra '{projektnavn}.xlsx'")
        fire.cli.print(f"Mulig årsag: {ex}")
        sys.exit(1)


# ------------------------------------------------------------------------------
def gyldighedstidspunkt(projektnavn: str) -> datetime.datetime:
    """Tid for sidste observation der har været brugt i beregningen"""
    obs = find_faneblad(projektnavn, "Observationer", ARKDEF_OBSERVATIONER)
    obs = obs[obs["Sluk"] != "x"]
    return max(obs["Hvornår"])


def find_parameter(projektnavn: str, parameter: str) -> str:
    """Find parameter fra et projektregneark"""
    param = find_faneblad(projektnavn, "Parametre", ARKDEF_PARAM)
    if parameter not in list(param["Navn"]):
        fire.cli.print(f"FEJL: '{parameter}' ikke angivet under fanebladet 'Parametre'")
        sys.exit(1)

    return param.loc[param["Navn"] == f"{parameter}"]["Værdi"].to_string(index=False)


# -----------------------------------------------------------------------------
def find_sag(projektnavn: str) -> Sag:
    """Bomb hvis sag for projektnavn ikke er oprettet. Ellers returnér sagen"""
    if not os.path.isfile(f"{projektnavn}.xlsx"):
        fire.cli.print(
            f"FEJL: Filen '{projektnavn}.xlsx' ikke fundet - står du i den rigtige folder?",
            bold=True,
            bg="red",
        )
        sys.exit(1)

    sagsgang = find_sagsgang(projektnavn)
    sagsid = find_sagsid(sagsgang)
    try:
        sag = fire.cli.firedb.hent_sag(sagsid)
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
        if punkter.at[i, "Ny kote"] is None:
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


def bekræft(spørgsmål: str, gentag=True) -> bool:
    """
    Bed bruger om at tage stilling til spørgsmålet.
    """
    fire.cli.print(f"{spørgsmål} (ja/NEJ):")
    svar = input()
    if svar in ("ja", "JA", "Ja"):
        if gentag:
            if input("Gentag svar for at bekræfte (ja/NEJ)\n") in ("ja", "JA", "Ja"):
                return True
        else:
            return True

    return False


def opret_region_punktinfo(punkt: Punkt) -> PunktInformation:
    """Opret regionspunktinfo for et nyt punkt"""

    e = punkt.geometri.koordinater[0]

    # Regionen kan detekteres alene ud fra længdegraden, hvis vi holder os til
    # {DK, EE, FO, GL}. EE er dog ikke understøttet her: Hvis man forsøger at
    # oprette nye estiske punkter vil de blive tildelt region DK
    if e > 0:
        region = "REGION:DK"
    elif e < -11:
        region = "REGION:GL"
    else:
        region = "REGION:FO"

    # indsæt region
    pit = fire.cli.firedb.hent_punktinformationtype(region)
    if pit is None:
        fire.cli.print(f"Kan ikke finde region '{region}'")
        sys.exit(1)

    return PunktInformation(infotype=pit, punkt=punkt)


def er_projekt_okay(projektnavn: str):
    """
    Kontroller om det er okay at brug et givent projekt.

    Afbryder programmet og udskriver en fejl hvis ikke projektet er okay.
    Ellers gøres intet.
    """
    projekt_db = find_parameter(projektnavn, "Database")
    if projekt_db != fire.cli.firedb.db:
        fire.cli.print(
            f"FEJL: '{projektnavn}' er oprettet i {projekt_db}-databasen - du forbinder til {fire.cli.firedb.db}-databasen!",
            bold=True,
            bg="red",
        )
        sys.exit(1)

    versionsnummer = find_parameter(projektnavn, "Version")
    if versionsnummer != fire.__version__:
        fire.cli.print(
            f"FEJL: '{projektnavn}' er oprettet med version {versionsnummer} - du har version {fire.__version__} installeret!",
            bold=True,
            bg="red",
        )
        sys.exit(1)


# moduler præfikset med _ for at undgå konflikter, der i visse tilfælde
# kan opstå. Med nedenstående kan man entydigt kende forskel på modulet
# fire.cli.niv._opret-sag og Click kommandoobjektet fire.cli.niv.opret-sag.
# Uden præfix kan der ikke skælnes mellem de to.
from ._opret_sag import opret_sag
from ._læs_observationer import læs_observationer
from ._ilæg_observationer import ilæg_observationer
from ._udtræk_revision import udtræk_revision
from ._ilæg_revision import ilæg_revision
from ._regn import regn
from ._ilæg_nye_koter import ilæg_nye_koter
from ._ilæg_nye_punkter import ilæg_nye_punkter
from ._netoversigt import netoversigt
from ._luk_sag import luk_sag
