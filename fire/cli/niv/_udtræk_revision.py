from typing import Final

import click
from sqlalchemy.sql import text

from fire.ident import klargør_identer_til_søgning
from fire.api.model import Punkt
from fire.api.model.geometry import (
    normaliser_lokationskoordinat,
)
from fire.io.regneark import (
    nyt_ark,
    arkdef,
)
import fire.cli
from fire.cli.niv import (
    niv as niv_command_group,
    skriv_ark,
    find_sag,
    er_projekt_okay,
)
from fire.cli.typologi import (
    adskil_identer,
    adskil_distrikter,
)


CELLEVÆRDI_INGEN: Final[None] = None
"Regnearksceller tildelt værdien None er uden indhold."

ATTRIBUTTER_UØNSKEDE: Final[list[str]] = [
    "ATTR:hjælpepunkt",
    "ATTR:tabtgået",
    "ATTR:teknikpunkt",
    "ATTR:MV_punkt",
    "REGION:EE",
    "REGION:FO",
    "REGION:GL",
    "REGION:SE",
    "REGION:SJ",
]
"Punkter med bare EN af disse attributter ignoreres"


ATTRIBUTTER_IGNOREREDE: Final[list[str]] = [
    "REGION:DK",
    "IDENT:refgeo_id",
    "IDENT:station",
    "NET:10KM",
    "SKITSE:master_md5",
    "SKITSE:master_sti",
    "SKITSE:png_md5",
    "SKITSE:png_sti",
    "ATTR:fundamentalpunkt",
    "ATTR:tinglysningsnr",
]
"""
Disse attributter indgår ikke i punktrevisionen
(men det diskvalificerer ikke et punkt at have dem)
"""

LOKATION_DEFAULT: Final[tuple[float, float]] = (11.0, 56.0)


def hent_punkter_i_opmålingsdistrikter(
    opmålingsdistrikter: list[str],
) -> list:
    if not opmålingsdistrikter:
        return []

    distrikter = ",".join([f"'{d.upper()}'" for d in opmålingsdistrikter])
    uønsket = ",".join([f"'{p}'" for p in ATTRIBUTTER_UØNSKEDE])
    pkt_i_distrikter = f"""
        SELECT p.*
        FROM (
            SELECT DISTINCT g.punktid FROM geometriobjekt g
            JOIN herredsogn hs
            ON sdo_inside(g.geometri, SDO_GEOM.SDO_BUFFER(hs.geometri, 50, 0.1)) = 'TRUE'
            WHERE
                upper(hs.kode) IN ({distrikter})
            AND
                g.registreringtil IS NULL
        ) a
        LEFT JOIN (
            SELECT DISTINCT pi.punktid FROM punktinfo pi
            JOIN punktinfotype pit ON pit.infotypeid=pi.infotypeid
            WHERE pit.infotype IN ({uønsket}) AND pi.registreringtil IS NULL
        ) b
        ON a.punktid = b.punktid
        JOIN punkt p ON p.id = a.punktid
        WHERE b.punktid IS NULL AND p.registreringtil IS NULL
        ORDER BY p.registreringfra
    """
    stmt = text(pkt_i_distrikter).columns(Punkt.objektid)
    return fire.cli.firedb.session.query(Punkt).from_statement(stmt).all()


def lokations_streng(lokation: tuple[float, float]) -> str:
    """
    Returnerer teksstreng-repræsentation af lokationskoordinat.

    Centimeterafrunding for lokationskoordinaten er rigeligt.

    """
    return f"{lokation[1]:.3f} m   {lokation[0]:.3f} m"


def flyt_attributter_til_toppen(
    punkt_informationer: list, prioritering: list[str]
) -> list:
    """
    Find prioriterede attributter og placér dem øverst i samme rækkefølge.

    Funktionen finder først den nye rækkefølge for punktinformationer
    (linjer med attribut-data), hvorefter den foretager ombytningen af
    de enkelte linjer efter deres indekser.

    Forsimplet sker følgende:

        Input:
            punkt_informationer = [c, b, a, x, y, z]
            prioritering = [z, y, x]

        Output:
            punkt_informationer = [z, y, x, a, b, c]

        Foretagede ombytninger:

            [0 <-> 5] <=> [c <-> z]
            [1 <-> 4] <=> [b <-> y]
            [2 <-> 3] <=> [a <-> x]

        BEMÆRK: Har de prioriterede attributter en anden rækkefølge
                end i punktinformationerne, bliver de flyttede
                attributter tilsvarende ombyttet i deres rækkefølge.

    """
    # Dét næste ledige linje-indeks, som den næste prioriterede attribut flyttes til
    index_offset = 0

    # Liste med indekser for de eksisterende punktinformationslinjer
    indices = list(range(len(punkt_informationer)))

    # Flyt attributter til toppen i samme rækkefølge som angivet i prioritering
    # Første attribut står på første linje for punktet
    # Anden attribut står på anden linje for punktet
    # og så videre.
    for attribut_navn in prioritering:

        # Antag, at attributten ikke findes, og indeks dermed ikke skal
        # stige, inden vi går til den næste prioriterede attribut.
        skift_indeks = False

        # Start forfra med at løbe over linjerne for punktet
        for index, info in enumerate(punkt_informationer):

            # Fortsæt, hvis linjen ikke indeholder den aktuelle attribut
            if info.infotype.name != attribut_navn:
                continue

            # Byt plads med den punktinformation placeret ved `index_offset`
            # Analogi: a, b = b, a
            indices[index_offset], indices[index] = (
                indices[index],
                indices[index_offset],
            )

            # Da attributten blev fundet, er det nødvendigt at flytte
            # indeks for ombytningslinjen til den efterfølgende:
            skift_indeks = True
            break

        # Skift til næste linje-indeks, hvis aktuelle attribut
        # blev fundet og sat på det aktuelle indeks, ellers ikke.
        index_offset += 1 if skift_indeks else 0

    # Sortér efter rækkefølgen i `indices`
    return [punkt_informationer[i] for i in indices]


@niv_command_group.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.argument("kriterier", nargs=-1, required=True)
@click.option(
    "--alle-attributter",
    is_flag=True,
    type=bool,
    help="Inkludér alle attributter",
)
def udtræk_revision(
    projektnavn: str, kriterier: tuple[str], alle_attributter: bool, **kwargs
) -> None:
    """Gør klar til punktrevision: Udtræk eksisterende information.

    fire niv udtræk-revision projektnavn distrikts-eller-punktnavn(e)
    """
    er_projekt_okay(projektnavn)
    find_sag(projektnavn)
    ignorerede_attributter = [] if alle_attributter else ATTRIBUTTER_IGNOREREDE

    opmålingsdistrikter, kriterier = adskil_distrikter(kriterier)
    løse_punkter, ubrugelige = adskil_identer(kriterier)

    # Check input
    if len(ubrugelige) > 0:
        fire.cli.print("Fandt ugyldige ident-formater eller filnavne:", bold=True)
        fire.cli.print("* " + "\n* ".join(ubrugelige))

    # Hent data
    punkter = hent_punkter_i_opmålingsdistrikter(opmålingsdistrikter)
    løse_punkter = klargør_identer_til_søgning(løse_punkter)
    try:
        punkter.extend(
            fire.cli.firedb.hent_punkt_liste(løse_punkter, ignorer_ukendte=False)
        )
    except ValueError as ex:
        fire.cli.print(f"FEJL: {ex}", bg="red", fg="white")
        raise SystemExit(1)

    # Tilføj punkt-informationerne til et nyt revisionsark
    revision = nyt_ark(arkdef.REVISION)
    for punkt in sorted(punkter):
        ident = punkt.landsnummer
        fire.cli.print(f"Punkt: {ident}")

        # Angiv ident og lokationskoordinat
        lokations_id = CELLEVÆRDI_INGEN
        try:
            lokation = punkt.geometri.koordinater
            lokations_id = punkt.geometri.objektid
        except AttributeError:
            fire.cli.print(
                f"NB! {ident} mangler lokationskoordinat - bruger {LOKATION_DEFAULT}",
                fg="yellow",
                bold=True,
            )
            lokation = LOKATION_DEFAULT

        lokation = normaliser_lokationskoordinat(lokation[0], lokation[1], "DK", True)
        lokation_repr = lokations_streng(lokation)
        revision = revision.append(
            {
                "Punkt": ident,
                "Attribut": "LOKATION",
                # Centimeterafrunding for lokationskoordinaten er rigeligt
                "Tekstværdi": lokation_repr,
                "Ny værdi": lokation_repr,
                "id": lokations_id,
                "Ikke besøgt": "x",
            },
            ignore_index=True,
        )

        # Fjern punktinformationer, der ikke skal skrives til arket
        def har_landsnr_lig_ident(info) -> bool:
            """Vis kun landsnr for punkter med GM/GI/GNSS-primærident"""
            return info.infotype.name == "IDENT:landsnr" and info.tekst == ident

        punkt_informationer: list = [
            info
            for info in punkt.punktinformationer
            if info.registreringtil is None
            and info.infotype.name not in ignorerede_attributter
            and not har_landsnr_lig_ident(info)
        ]

        # Flyt attributter til toppen af listen med punktinformationer,
        # så de kommer først og i denne rækkefølge under hvert punkt.
        prioritering = [
            "ATTR:muligt_datumstabil",
            "ATTR:beskrivelse",
        ]
        punkt_informationer = flyt_attributter_til_toppen(
            punkt_informationer, prioritering
        )

        # Tilføj anden række til arket, hvis denne attribut ikke var sat i forvejen
        # Rationale: Spar måleren for indtastning, hvis de ønsker at tilføje denne attribut.
        if not punkt_informationer[0].infotype.name == "ATTR:muligt_datumstabil":
            attribut = {
                "Attribut": "ATTR:muligt_datumstabil",
                "Sluk": "x",
            }
            revision = revision.append(attribut, ignore_index=True)

        # Så itererer vi, med aktuelle beskrivelse først
        for info in punkt_informationer:
            attribut_navn = info.infotype.name
            tekst = info.tekst if info.tekst is None else info.tekst.strip()
            revision = revision.append(
                {
                    "Sluk": "",
                    "Attribut": attribut_navn,
                    "Talværdi": info.tal,
                    "Tekstværdi": tekst,
                    "Ny værdi": tekst,
                    "id": info.objektid,
                },
                ignore_index=True,
            )

        # Fem blanklinjer efter hvert punktoversigt
        revision = revision.append(5 * [{}], ignore_index=True)

    ark_revision = {"Revision": revision}
    skriv_ark(projektnavn, ark_revision, "-revision")
    fire.cli.print("Færdig!")
