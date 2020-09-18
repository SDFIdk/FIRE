from typing import Tuple

import click
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire.cli import firedb

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
    uønskede_punkter = {
        "ATTR:hjælpepunkt",
        "ATTR:tabtgået",
        "ATTR:teknikpunkt",
        "AFM:naturlig",
        "ATTR:MV_punkt",
    }

    # Disse attributter indgår ikke i punktrevisionen
    # (men det diskvalificerer ikke et punkt at have dem)
    ignorerede_attributter = {
        "REGION:DK",
        "IDENT:refgeo_id",
        "IDENT:station",
        "NET:10KM",
        "SKITSE:md5",
        "ATTR:fundamentalpunkt",
        "ATTR:tinglysningsnr",
    }

    fire.cli.print("Udtrækker punktinformation til revision")
    for distrikt in opmålingsdistrikter:
        fire.cli.print(f"Behandler distrikt {distrikt}")
        try:
            punkter = firedb.soeg_punkter(f"{distrikt}%")
        except NoResultFound:
            punkter = []
        fire.cli.print(f"Der er {len(punkter)} punkter i distrikt {distrikt}")

        for punkt in punkter:
            ident = punkt.ident
            infotypenavne = [i.infotype.name for i in punkt.punktinformationer]
            if not uønskede_punkter.isdisjoint(infotypenavne):
                continue

            # Hvis punktet har et landsnummer kan vi bruge det til at frasortere irrelevante punkter
            if "IDENT:landsnr" in infotypenavne:
                landsnrinfo = punkt.punktinformationer[
                    infotypenavne.index("IDENT:landsnr")
                ]
                landsnr = landsnrinfo.tekst
                løbenr = landsnr.split("-")[-1]

                # Frasorter numeriske løbenumre udenfor 1-10, 801-999, 9001-19999
                if løbenr.isnumeric():
                    i = int(løbenr)
                    if 10 < i < 801:
                        continue
                    if 1000 < i < 9001:
                        continue
                    if i > 20000:
                        continue

            fire.cli.print(f"Punkt: {ident}")

            # Find index for aktuelle punktbeskrivelse, for at kunne vise den først
            beskrivelse = 0
            for i, info in enumerate(punkt.punktinformationer):
                if info.registreringtil is not None:
                    continue
                if info.infotype.name != "ATTR:beskrivelse":
                    continue
                beskrivelse = i
                break
            indices = list(range(len(punkt.punktinformationer)))
            indices[0] = beskrivelse
            indices[beskrivelse] = 0

            anvendte_attributter = []

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
            lokation = punkt.geometri.koordinater
            revision = revision.append(
                {
                    "Punkt": ident,
                    "Attribut": "OVERVEJ:lokation",
                    # Centimeterafrunding for lokationskoordinaten er rigeligt
                    "Tekstværdi": f"{lokation[1]:.7f} N   {lokation[0]:.7f} Ø",
                },
                ignore_index=True,
            )

            # To blanklinjer efter hvert punktoversigt
            revision = revision.append({}, ignore_index=True)
            revision = revision.append({}, ignore_index=True)

    resultater = {"Revision": revision}
    skriv_ark(projektnavn, resultater, "-revision")
    fire.cli.print("Færdig!")
