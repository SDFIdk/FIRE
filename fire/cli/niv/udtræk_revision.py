from typing import Tuple

import click
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import text

import fire.cli
from fire.api.model import Punkt

from . import (
    ARKDEF_REVISION,
    niv,
    skriv_ark,
)


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
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
    uønskede_punkter = [
        "ATTR:hjælpepunkt",
        "ATTR:tabtgået",
        "ATTR:teknikpunkt",
        "AFM:naturlig",
        "ATTR:MV_punkt",
        "IDENT:ekstern",
    ]

    # Disse attributter indgår ikke i punktrevisionen
    # (men det diskvalificerer ikke et punkt at have dem)
    ignorerede_attributter = [
        "REGION:DK",
        "IDENT:refgeo_id",
        "IDENT:station",
        "NET:10KM",
        "SKITSE:md5",
        "ATTR:fundamentalpunkt",
        "ATTR:tinglysningsnr",
    ]

    distrikter = ",".join([f"'{d}'" for d in opmålingsdistrikter])
    uønsket = ",".join([f"'{p}'" for p in uønskede_punkter])
    pkt_i_distrikter = f"""
                SELECT p.*
                FROM (
                    SELECT DISTINCT g.punktid FROM geometriobjekt g
                    JOIN herredsogn hs
                    ON sdo_inside(g.geometri, hs.geometri) = 'TRUE'
                    WHERE hs.kode IN ({distrikter}) AND g.registreringtil IS NULL
                ) a
                LEFT JOIN (
                    SELECT DISTINCT pi.punktid FROM punktinfo pi
                    JOIN punktinfotype pit ON pit.infotypeid=pi.infotypeid
                    WHERE pit.infotype IN ({uønsket}) AND pi.registreringtil IS NULL
                ) b
                ON a.punktid = b.punktid
                JOIN punkt p ON p.id = a.punktid
                WHERE b.punktid IS NULL AND p.registreringtil IS NULL
                ORDER BY p.registreringfra"""

    stmt = text(pkt_i_distrikter).columns(Punkt.objektid)
    punkter = fire.cli.firedb.session.query(Punkt).from_statement(stmt).all()

    for punkt in punkter:
        ident = punkt.ident
        fire.cli.print(f"Punkt: {ident}")

        # Find index for aktuelle punktbeskrivelse, for at kunne vise den først
        indices = list(range(len(punkt.punktinformationer)))
        beskrivelse = 0
        for i, info in enumerate(punkt.punktinformationer):
            if info.registreringtil is not None:
                continue
            if info.infotype.name != "ATTR:beskrivelse":
                continue
            beskrivelse = i
            indices[0] = beskrivelse
            indices[beskrivelse] = 0
            break

        anvendte_attributter = []

        # Nedenfor sætter vi ident=None efter første linje, for at få en mere
        # overskuelig rapportering. Men vi skal stadig have adgang til identen
        # for at kunne fejlmelde undervejs
        ident_til_fejlmelding = ident

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

            # Vis kun identnavn i første række af hvert punkt
            if i != indices[0]:
                ident = None

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
                    "Tekstværdi": "Hvis ja: Ret 'OVERVEJ:' til 'ATTR:'",
                },
                ignore_index=True,
            )
            try:
                lokation = punkt.geometri.koordinater
            except AttributeError:
                fire.cli.print(
                    f"NB! {ident_til_fejlmelding} mangler lokationskoordinat - bruger (11,56)",
                    fg="yellow",
                    bold=True,
                )
                lokation = (11.0, 56.0)
            revision = revision.append(
                {
                    "Punkt": ident,
                    "Attribut": "OVERVEJ:lokation",
                    # Centimeterafrunding for lokationskoordinaten er rigeligt
                    "Tekstværdi": f"{lokation[1]:.7f} N   {lokation[0]:.7f} Ø",
                },
                ignore_index=True,
            )

            # Fem blanklinjer efter hvert punktoversigt
            revision = revision.append(5 * [{}], ignore_index=True)

    resultater = {"Revision": revision}
    skriv_ark(projektnavn, resultater, "-revision")
    fire.cli.print("Færdig!")
