from typing import Tuple

import click
import pandas as pd
from sqlalchemy.orm import joinedload
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
@click.argument("opmålingsdistrikter", nargs=-1, required=True)
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

        # Angiv ident og lokationskoordinat
        try:
            lokation = punkt.geometri.koordinater
        except AttributeError:
            fire.cli.print(
                f"NB! {ident} mangler lokationskoordinat - bruger (11,56)",
                fg="yellow",
                bold=True,
            )
            lokation = (11.0, 56.0)
        revision = revision.append(
            {
                "Punkt": ident,
                "Attribut": "LOKATION",
                # Centimeterafrunding for lokationskoordinaten er rigeligt
                "Tekstværdi": f"{lokation[1]:.7f} N   {lokation[0]:.7f} Ø",
                "Ikke besøgt": "x",
            },
            ignore_index=True,
        )

        # Find index for aktuelle datumstabilitetsstatus,
        # for at kunne vise den først
        indices = list(range(len(punkt.punktinformationer)))
        for i, info in enumerate(punkt.punktinformationer):
            if info.registreringtil is not None:
                continue
            if info.infotype.name != "ATTR:muligt_datumstabil":
                continue
            datumstabilt = True
            indices[0], indices[i] = indices[i], indices[0]
            break
        else:
            revision = revision.append(
                {
                    "Attribut": "ATTR:muligt_datumstabil",
                    "Sluk": "x",
                },
                ignore_index=True,
            )

        # Find index for aktuelle punktbeskrivelse, for at kunne vise den øverst
        for i, info in enumerate(punkt.punktinformationer):
            if info.registreringtil is not None:
                continue
            if info.infotype.name != "ATTR:beskrivelse":
                continue

            # ATTR:beskrivelse's placering i listen afhænger af om der findes
            # et ATTR:muligt_datumstabil i databasen eller ej
            pos = 1 if datumstabilt else 0
            indices[pos], indices[i] = indices[i], indices[pos]
            break

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

            tekst = info.tekst
            if tekst:
                tekst = tekst.strip()
            tal = info.tal
            revision = revision.append(
                {
                    "Sluk": "",
                    "Attribut": attributnavn,
                    "Talværdi": tal,
                    "Tekstværdi": tekst,
                    "id": info.objektid,
                },
                ignore_index=True,
            )

        # Fem blanklinjer efter hvert punktoversigt
        revision = revision.append(5 * [{}], ignore_index=True)

    resultater = {"Revision": revision}
    skriv_ark(projektnavn, resultater, "-revision")
    fire.cli.print("Færdig!")
