import sys
import requests
from configparser import NoSectionError
from typing import Dict, List, Tuple

import click
import xmltodict
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import not_, or_

import fire.cli

from fire.cli.utils import klargør_ident_til_søgning
from fire.api.model import Punkt

from . import udst


@udst.command()
@fire.cli.default_options()
@click.argument("ident")
@click.option(
    "--dump",
    is_flag=True,
    default=False,
    help="Udskriv datafordeleroutput i fuld form",
)
@click.option(
    "--kanal",
    type=click.Choice(["prod", "test"]),
    default="prod",
    help="Vælg datafordelerkanal - 'prod' hvis intet anføres.",
)
def punkt(ident: str, dump: bool, kanal: str, **kwargs):
    """
    Grav et punkt (IDENT) frem fra FIRE. Vis dets aktive koordinater, og grav tilsvarende
    frem fra datafordeleren, så det kan checkes om koordinaterne kommer uskadt
    igennem turen.
    """

    punkt = hent_punkt_fra_FIRE(ident)
    fire.cli.print(80 * "-")
    fire.cli.print(
        f"{punkt.ident}: Rundtur FIRE -> Datafordeler, (Simpel/Fuld/Historik)"
    )
    fire.cli.print(80 * "-")

    # Vis alle aktuelle koordinater, som ikke er tidsserie-koordinater
    for k in punkt.koordinater:
        if k.registreringtil or k.sridid not in SRIDER:
            continue
        fire.cli.print(
            f"* {'t' if k.transformeret=='true' else 'n'} {SRIDER[k.sridid]:12}",
            nl=False,
        )
        fire.cli.print(
            (f"{k.x} " if k.x else "")
            + (f"{k.y} " if k.y else "")
            + (f"{k.z} " if k.z else "")
        )
    fire.cli.print(80 * "-")

    # Gør klar til søgning på Datafordeler
    bbox = byg_bbox(punkt)
    kanal_ini = hent_datafordeler_ini(kanal)
    metadata = {tjeneste: {} for tjeneste in TJENESTER}

    for datatype in TYPER:
        der_var_bid = False
        for tjeneste in TJENESTER:
            forespørgsel = byg_forespørgsel(kanal_ini, tjeneste, datatype, bbox)
            members = hent_wfs_members(forespørgsel)
            for m in members:
                mm = m["fiks:" + TYPER[datatype]]
                id = mm["fiks:fikspunktsnummer"]
                if id not in punkt.identer:
                    continue
                for k, v in mm.items():
                    if k not in STØJ:
                        kk = k.split(":")[-1]
                        metadata[tjeneste][kk] = v
                koord = find_koordinater(mm)
                if koord[0:3] == (None, None, None, None):
                    continue
                der_var_bid = True
                fire.cli.print(
                    f"{TJENESTEMARKØR[tjeneste]} . {SYSTEMNAVN[datatype]} ", nl=False
                )
                for k in koord:
                    if k:
                        fire.cli.print(f"{k} ", nl=False)
                fire.cli.print("")
        if der_var_bid:
            fire.cli.print(80 * "-")

    # Kontroller at delmængderelaionerne "simpel ⊆ fuld ⊆ historik" er opfyldt
    check_simpel = set(metadata["simpel"]) - set(metadata["fuld"])
    if check_simpel:
        fire.cli.print(f"Uventede elementer i 'simpel': {check_simpel}")
    check_fuld = set(metadata["fuld"]) - set(metadata["historik"])
    if check_fuld:
        fire.cli.print(f"Uventede elementer i 'fuld': {check_fuld}")

    allerede = set()
    desuden = ", metadataregistreringer"
    for tjeneste in TJENESTER:
        fire.cli.print(f"{tjeneste}{desuden}")
        fire.cli.print(80 * "-")
        desuden = ": desuden"
        for k in sorted(metadata[tjeneste]):
            if k in allerede:
                continue
            allerede.add(k)
            fire.cli.print(f"{k}: {metadata[tjeneste][k]}")
        fire.cli.print(80 * "-")


def hent_punkt_fra_FIRE(ident: str) -> Punkt:
    """Find punktet `ident` frem fra FIRE"""
    ident = klargør_ident_til_søgning(ident)
    try:
        punkter = fire.cli.firedb.soeg_punkter(ident, 3)
    except NoResultFound:
        fire.cli.print(f"Fejl: Kunne ikke finde {ident}.", fg="red", err=True)
        sys.exit(1)
    if len(punkter) > 1:
        fire.cli.print(f"Punktnavn {ident} er ikke entydigt.", fg="red", err=True)
        sys.exit(1)
    return punkter[0]


def byg_bbox(punkt: Punkt) -> str:
    """Konstruer en bbox på ca. 100m x 100m omkring interessepunktet"""
    if not punkt.geometriobjekter:
        fire.cli.print(
            f"Ingen gyldig geometri for punkt {punkt.ident} i FIRE.", fg="red", err=True
        )
        sys.exit(1)
    geometri = punkt.geometriobjekter[-1].geometri
    lon, lat = geometri.__geo_interface__["coordinates"]
    return f"BBOX={(lon-0.001):.5f},{(lat-0.0005):.5f},{(lon+0.001):.5f},{(lat+0.0005):.5f}"


def hent_datafordeler_ini(kanal: str) -> Dict:
    """Hent og valider datafordeler-`kanal`-konfiguration fra `fire.ini`"""
    try:
        config = fire.cli.firedb.config[kanal + "_datafordeler"]
        hostname = config["hostname"]
        username = config["username"]
        password = config["password"]
        return config
    except NoSectionError as ex:
        fire.cli.print(
            f"Fejl: Manglende afsnit om '{kanal}_datafordeler' i 'fire.ini'.",
            fg="red",
            err=True,
        )
        fire.cli.print(str(ex), fg="red", err=True)
    except KeyError as ex:
        fire.cli.print(
            f"Fejl: Manglende element {str(ex)} i '{kanal}_datafordeler' i 'fire.ini'.",
            fg="red",
            err=True,
        )
    sys.exit(1)


def byg_forespørgsel(config: Dict, tjeneste: str, datatype: str, bbox: str) -> str:
    try:
        hostname = config["hostname"]
        username = config["username"]
        password = config["password"]
        adgang = f"username={username}&password={password}&service=wfs&version=2.0.0"
        udvalg = f"request=getFeature&typeNames={TYPER[datatype]}&{bbox}"
        forespørgsel = f"https://{hostname}/{TJENESTER[tjeneste]}?{adgang}&{udvalg}"
    except KeyError as ex:
        fire.cli.print("Fejl: Ukendt tjeneste eller datatype")
        fire.cli.print(f"{ex}")
        sys.exit(1)
    return forespørgsel


def hent_wfs_members(forespørgsel: str) -> List:
    """Udfør wfs-forespørgsel og udtræk `wfs:member`-delen af respons"""
    response = requests.get(forespørgsel)
    doc = xmltodict.parse(response.text)
    try:
        members = doc["wfs:FeatureCollection"]["wfs:member"]
    except KeyError:
        return []
    if not isinstance(members, list):
        members = [members]
    return members


def find_koordinater(beskrivelse: dict) -> Tuple:
    """Søg efter koordinater i `beskrivelse`"""
    x = y = z = t = None

    for betegnelse in {"x", "easting"}:
        if "fiks:" + betegnelse in beskrivelse:
            x = beskrivelse["fiks:" + betegnelse]
            break
    for betegnelse in {"y", "northing"}:
        if "fiks:" + betegnelse in beskrivelse:
            y = beskrivelse["fiks:" + betegnelse]
            break
    for betegnelse in {"z", "kote", "ellipsoidehoejde"}:
        if "fiks:" + betegnelse in beskrivelse:
            z = beskrivelse["fiks:" + betegnelse]
            break
    for betegnelse in {"registreringFra"}:
        if "fiks:" + betegnelse in beskrivelse:
            t = beskrivelse["fiks:" + betegnelse].split("T")[0]
            break

    aktuel = "fiks:registreringTil" not in beskrivelse
    return x, y, z, t, aktuel


# ---------------------------------------------------------------------------
# Pseudo-konstanter til styring af navigationen gennem tjenester og datatyper
# ---------------------------------------------------------------------------

TJENESTER = {
    "simpel": "FIKSPUNKT/FIKSPUNKTER_GML3SFP_SIMPEL/1.0.0/Wfs",
    "fuld": "FIKSPUNKT/FIKSPUNKTER_GML3SFP/1.0.0/Wfs",
    "historik": "FIKSPUNKT/FIKSPUNKTER_HIST_GML3SFP/1.0.0/Wfs",
}

TJENESTEMARKØR = {"simpel": "S", "fuld": "F", "historik": "H"}

TYPER = {
    "s34": "FikspunktSys34",
    "kote-dk": "HoejdefikspunktDanmark",
    "kote-dnn": "HoejdefikspunktDNN",
    "kote-fo": "HoejdefikspunktFaeroeerne",
    "kote-gl": "HoejdefikspunktGroenland",
    "plan": "PlanfikspunktDanmark",
    "plan-fo": "PlanfikspunktFaeroeerne",
    "plan-gl": "PlanfikspunktGroenland",
}

SYSTEMNAVN = {
    "s34": "DK:S34",
    "kote-dk": "EPSG:5799",
    "kote-dnn": "DK:DNN",
    "kote-fo": "HoejdefikspunktFaeroeerne",
    "kote-gl": "HoejdefikspunktGroenland",
    "plan": "EPSG:25832",
    "plan-fo": "EPSG:25829",
    "plan-gl": "EPSG:3184",
}

# Til frasortering af mindre relevante metadataregistreringer,
# så vi kan se skovlen for bare tæer.
STØJ = {
    "@gml:id",
    "fiks:id",
    "fiks:specialnummer",
    "fiks:loebenummer",
    "fiks:geometri",
    "fiks:fikspunktsbeskrivelse",
    "fiks:maalskitse",
    "fiks:herredSogn",
    "fiks:kommunekode",
    "fiks:registreringFra",
    "fiks:registreringTil",
    "fiks:virkningFra",
    "fiks:virkningsaktoer",
    "fiks:registreringsaktoer",
    "fiks:forretningsomraade",
    "fiks:forretningsproces",
    "fiks:forretningshaendelse",
    "fiks:status",
    "fiks:x",
    "fiks:y",
    "fiks:easting",
    "fiks:northing",
    "fiks:kote",
    "fiks:ellipsoidehoejde",
    "fiks:refDK",
    "fiks:DK10kmNet",
}

# dict til opslag af sridnavn (EPSG:nnnn etc.) som funktion af sridid.
# Tidsserie-srider filtreres ud
from fire.api.model import Srid

SRIDER = {
    srid.sridid: srid.name
    for srid in fire.cli.firedb.session.query(Srid)
    .filter(not_(Srid.name.like("TS:%")))
    .all()
}
