from typing import Final
from functools import partial

import click
from sqlalchemy.sql import text
from fire.api.model.punkttyper import PunktInformationType

from fire.ident import klargør_identer_til_søgning
from fire.api.model import (
    Punkt,
    PunktInformation,
)
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

ATTRIBUT_PRIORITERING: Final[list[str]] = [
    "ATTR:muligt_datumstabil",
    "ATTR:beskrivelse",
]
"""
Attributter, der, hvis de eksisterer for et punkt, skal
være øverst og i angivne rækefølge under hvert punkt.
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


def lokationskoordinat_streng(lokation: tuple[float, float]) -> str:
    """
    Returnerer tekst-repræsentation af lokationskoordinat.

    Centimeterafrunding for lokationskoordinaten er rigeligt.

    """
    return f"{lokation[1]:.3f} m   {lokation[0]:.3f} m"



def punkt_informationer_aktive(punkt_informationer: list[PunktInformation]) -> list[PunktInformation]:
    return [
        info
        for info in punkt_informationer
        if info.registreringtil is None
    ]


def fjern_ignorerede(punkt_informationer: list[PunktInformation], ignorerede: list[str]) -> list[PunktInformation]:
    return [
        info
        for info in punkt_informationer
        if info.infotype.name not in ignorerede
    ]


def har_landsnr_lig_ident(info: PunktInformation, ident: str) -> bool:
    """Vis kun landsnr for punkter med GM/GI/GNSS-primærident"""
    return info.infotype.name == "IDENT:landsnr" and info.tekst == ident


def fjern_alle_med_ident(punkt_informationer: list[PunktInformation], ident: str) -> list[PunktInformation]:
    return [
        info
        for info in punkt_informationer
        if not har_landsnr_lig_ident(info, ident)
    ]


def flyt_attributter_til_toppen(
    punkt_informationer: list[PunktInformation], *, prioritering: list[str] = ATTRIBUT_PRIORITERING
) -> list:
    """
    Find prioriterede attributter og placér dem øverst i samme rækkefølge.

    Resten af atributterne får samme sorterings-indeks, hvorfor
    deres rækkefølge i forhold til hinanden forbliver uændret.

    """
    def key(info: PunktInformation) -> int:
        if info.infotype.name not in prioritering:
            return 9999
        return prioritering.index(info.infotype.name)

    return sorted(punkt_informationer, key=key)


def har_infotype(punkt_information: PunktInformation, attribut: str) -> bool:
    return punkt_information.infotype.name == attribut


mulig_datumstabil = partial(har_infotype, attribut="ATTR:muligt_datumstabil")


def har_attr_muligt_datumstabil(punkt_informationer: list[PunktInformation]) -> bool:
    return any(
        mulig_datumstabil(punkt_info)
        for punkt_info
        in punkt_informationer
    )


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
        lokation_repr = lokationskoordinat_streng(lokation)
        revision = revision.append(
            {
                "Punkt": ident,
                "Attribut": "LOKATION",
                "Tekstværdi": lokation_repr,
                "Ny værdi": lokation_repr,
                "id": lokations_id,
                "Ikke besøgt": "x",
            },
            ignore_index=True,
        )

        # Fjern punktinformationer, der ikke skal skrives til arket
        punkt_informationer = punkt_informationer_aktive(punkt.punktinformationer)
        punkt_informationer = fjern_ignorerede(punkt_informationer, ignorerede_attributter)
        punkt_informationer = fjern_alle_med_ident(punkt_informationer, ident)

        # Inden punkt-informationerne føjes til regnearket, flyt
        # prioriterede attributter til toppen i den valgte rækkefølge.
        punkt_informationer = flyt_attributter_til_toppen(punkt_informationer)

        # Spar måleren for indtastning, hvis de ønsker at tilføje denne attribut:
        # Tilføj række til arket, hvis attribut om mulig datumstabil ej sat i forvejen
        if not har_attr_muligt_datumstabil(punkt_informationer):
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
