import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import click
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire.cli import firedb

from . import (
    ARKDEF_FILOVERSIGT,
    ARKDEF_NYETABLEREDE_PUNKTER,
    ARKDEF_OBSERVATIONER,
    ARKDEF_PUNKTOVERSIGT,
    anvendte,
    find_faneblad,
    niv,
    normaliser_placeringskoordinat,
    punkter_geojson,
    skriv_ark,
)


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
def læs_observationer(projektnavn: str, **kwargs) -> None:
    """Importer data fra observationsfiler og opbyg punktoversigt"""
    fire.cli.print("Så kører vi")
    resultater = {}

    # Opbyg oversigt over nyetablerede punkter
    nyetablerede = find_faneblad(
        projektnavn, "Nyetablerede punkter", ARKDEF_NYETABLEREDE_PUNKTER
    )
    try:
        nyetablerede = nyetablerede.set_index("Landsnummer")
    except:
        fire.cli.print("Der mangler landsnumre til nyetablerede punkter.")
        fire.cli.print(
            "Har du husket at lægge dem i databasen - og at kopiere fanebladet fra resultatfilen?"
        )
        fire.cli.print("Fortsætter beregningen med brug af de foreløbige navne")
        nyetablerede = nyetablerede.set_index("Foreløbigt navn")
    nye_punkter = set(nyetablerede.index)

    # Opbyg oversigt over alle observationer
    observationer = importer_observationer(projektnavn)
    resultater["Observationer"] = observationer
    observerede_punkter = set(list(observationer["Fra"]) + list(observationer["Til"]))
    gamle_punkter = observerede_punkter - nye_punkter

    # Vi vil gerne have de nye punkter først i punktoversigten,
    # så vi sorterer gamle og nye hver for sig
    nye_punkter = tuple(sorted(nye_punkter))
    alle_punkter = nye_punkter + tuple(sorted(gamle_punkter))

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
def observationer_geojson(
    projektnavn: str,
    punkter: pd.DataFrame,
    observationer: pd.DataFrame,
) -> None:
    """Skriv observationer til geojson-fil"""

    with open(f"{projektnavn}-observationer.geojson", "wt") as obsfil:
        til_json = {
            "type": "FeatureCollection",
            "Features": list(obs_feature(punkter, observationer)),
        }
        json.dump(til_json, obsfil, indent=4)


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
def opbyg_punktoversigt(
    navn: str,
    nyetablerede: pd.DataFrame,
    alle_punkter: Tuple[str, ...],
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
                    for _ in range(len(tokens), 13):
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
def find_inputfiler(navn: str) -> pd.DataFrame:
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
