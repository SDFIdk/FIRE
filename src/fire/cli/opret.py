"""
Oprettelse af objekter i databasen via kommandolinjen.
"""

from datetime import datetime as dt
import getpass
import re

import click
from oracledb import DatabaseError

from fire import uuid
from fire.api.model import (
    Punkt,
    PunktInformation,
    PunktInformationTypeAnvendelse,
    GeometriObjekt,
    Point,
    FikspunktsType,
)
from fire.api.model.geometry import (
    normaliser_lokationskoordinat,
)
from fire.cli.info import punktinforapport
from fire.cli.niv import bekræft
import fire.cli

PUNKTSKABELONER = {
    "PERMANENT": [
        "NET:CORS",
        "IDENT:landsnummer",  # brug landsnummer-funktion
        "IDENT:GI",  # brug tildel_gi_numre()
        "IDENT:GNSS",  # prompt
        "REGION:DK",  #
        "AFM:højde_over_terræn",
        "ATTR:beskrivelse",
        "AFM:1981",  # AFM:xxxx kopier punktinfotypens beskrivelse til punktinfo'ens tekst-felt
        "ATTR:CORSKlasseA",
        "ATTR:gnss_egnet",
    ],
    "GNET": [
        "NET:GNET",
        "IDENT:GNSS",
        "AFM:højde_over_terræn",
        "ATTR:beskrivelse",
        "ATTR:gnss_egnet",
        "REGION:GL",
    ],
    "5D": [
        "NET:5D",
        "IDENT:landsnr",
        "IDENT:GI",
        "IDENT:GNSS",
        "AFM:højde_over_terræn",
        "ATTR:beskrivelse",
        "ATTR:gnss_egnet",
        "REGION:DK",
        "ATTR:GI_punkt",
        "AFM:1963",  # Skruepløk,1.5 m lang, med fedtpatron.
    ],
    "RTKCONNECT": [
        "NET:RTKCONNECT",
        "IDENT:landsnr",
        "IDENT:GNSS",
        "ATTR:beskrivelse",
        "REGION:DK",
        "ATTR:restricted",
        "AFM:1980",  # Permanent GPS-station
    ],
    "SMARTNET": [
        "NET:SMARTNET",
        "IDENT:landsnr",
        "IDENT:GNSS",
        "ATTR:beskrivelse",
        "REGION:DK",
        "ATTR:restricted",
        "AFM:1980",  # Permanent GPS-station
    ],
    "GPSNET": [
        "NET:GPSNET",
        "IDENT:landsnr",
        "IDENT:GNSS",
        "ATTR:beskrivelse",
        "REGION:DK",
        "ATTR:restricted",
        "AFM:1980",  # Permanent GPS-station
    ],
}

FIKSPUNKTSTYPER = PUNKTSKABELONER.keys()


def håndter_landsnummer(punkt: Punkt) -> PunktInformation:
    """Opret landsnummer"""
    try:
        return fire.cli.firedb.tilknyt_landsnumre([punkt], [FikspunktsType.GI])[0]
    except KeyError:
        raise ValueError(
            "Landsnummer kan ikke tildeles, da lokationskoordinat er udenfor opmålingsdistrikt"
        )


def håndter_gi_nummer(punkt: Punkt) -> PunktInformation:
    """Opret GI ident"""
    return fire.cli.firedb.tilknyt_gi_numre([punkt])[0]


def håndter_attr_beskrivelse(punkt: Punkt) -> PunktInformation:
    """Opret ATTR:beskrivelse"""
    pit = fire.cli.firedb.hent_punktinformationtype("ATTR:beskrivelse")
    beskrivelse = multilinje_input("Indtast beskrivelse")
    return PunktInformation(
        punkt=punkt,
        infotype=pit,
        tekst=beskrivelse,
    )


SPECIELLE_INFOTYPER = {
    "IDENT:landsnummer": håndter_landsnummer,
    "IDENT:GI": håndter_gi_nummer,
    "ATTR:beskrivelse": håndter_attr_beskrivelse,
}


class ClickKoordinat(click.ParamType):
    """
    Click type til angivelse af koordinat på kommandolinjen.

    Koordinat gives på kommandolinjen som "12.523,55.32", hvilket
    oversættes til [12.523, 55.32] når den gives videre til funktionen
    bag en kommando.
    """

    name = "koordinat"

    def convert(self, value, param, ctx):
        if isinstance(value, list):
            if isinstance(value[0], float) and isinstance(value[1], float):
                return value

        try:
            komponenter = value.split(",")
            if len(komponenter) != 2:
                raise ValueError
            koordinat = [float(k) for k in komponenter]
            return koordinat
        except ValueError:
            self.fail(f"{value!r} er ikke en gyldig koordinat", param, ctx)


KOORDINAT = ClickKoordinat()


def multilinje_input(tekst: str):
    """
    Læs mere end en linje ved brugerinput.
    """
    print(f"{tekst} (indsæt to tomme linjer for at gemme:")
    linjer = []
    forrige_linje = "_"
    while True:
        try:
            linje = input("  ")
            if forrige_linje == "" and linje == "":
                raise EOFError
        except EOFError:  # giver mulighed for også at afbryde via Ctrl+Z/Ctrl+D
            break
        linjer.append(linje)
        forrige_linje = linje

    return "\n".join(linjer).strip()


@click.group()
def opret():
    """
    Oprettelse af objekter i databasen via kommandolinjen.
    """


def vis_skabelon(ctx, param, fikspunktstype):
    """Vis indholdet af en skabelon"""
    # Hvis man ikke har brugt --skabelon, springes der ud med det samme, så resten af
    # kommandoen kan få lov at køre
    if fikspunktstype is None:
        return None

    attributter = PUNKTSKABELONER[fikspunktstype]

    fire.cli.print(f"Attributter for {fikspunktstype}-skabelon:", bold=True)
    for attribut in attributter:
        print(f"  {attribut}")

    raise SystemExit


HELPSTR = f"""
Oprettelse af nye standardiserede fikspunkter.

Let oprettelse af fx nye GNSS-stationer eller 5D-punkter i databasen. For hver
type fikspunkt er der lavet en skabelon, der indeholder de relevante attributter
for den givne type. Ved kørsel af kommandoen angiver man hvilken type fikspunkt
man vil oprette samt en lokationskoordinat til punktet. Herefter guider programmet
brugeren gennem oprettelsen, og beder om input hvor det er nødvendigt. Fx angivelse
af GNSS ident eller en beskrivelse af punktet.

Fikspunkter kan oprettes efter følgende skabeloner:

    {", ".join(FIKSPUNKTSTYPER)}

Se mere om de enkelte skabeloner med `fire opret punkt --skabelon <FIKSPUNKTSTYPE>`

Bemærk at alle landsnumre oprettes i GI-serien (løbenummer 0-10, 801-8999).

Eksempler
---------

Opret en permanent GNSS station i Danmark:

    > fire opret punkt permanent 12.34,55.67

Opret en GNET-station:

    > fire opret punkt gnet "52.23, 67.34"

Vis indholdet af en skabelon til oprettelse af punkter:

    > fire opret punkt --skabelon 5D
"""


@opret.command("punkt", help=HELPSTR)
@fire.cli.default_options()
@click.argument(
    "fikspunktstype", type=click.Choice(FIKSPUNKTSTYPER, case_sensitive=False)
)
@click.argument(
    "lokation",
    type=KOORDINAT,
)
@click.option(
    "--skabelon",
    type=click.Choice(FIKSPUNKTSTYPER, case_sensitive=False),
    is_eager=True,
    callback=vis_skabelon,
    help="Vis indhold af skabelon",
)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
def punktopret(
    fikspunktstype: str,
    lokation: list[float],
    sagsbehandler: str,
    **kwargs,
):
    """Oprettelse af nye standardiserede fikspunkter."""
    attributter = PUNKTSKABELONER[fikspunktstype]

    fire.cli.print(f"Opretter nyt fikspunkt af typen '{fikspunktstype}'\n", bold=True)

    region = [a for a in attributter if a.startswith("REGION:")][0]
    lokationskoordinat = normaliser_lokationskoordinat(*lokation, region)

    # Sagshåndtering
    sag = fire.cli.firedb.ny_sag(
        behandler=sagsbehandler,
        beskrivelse=f"Oprettelse af {fikspunktstype} via 'fire opret punkt'",
    )

    # Opret objekter til databasen
    punkt = Punkt(
        id=uuid(),
        geometriobjekter=[GeometriObjekt(geometri=Point(lokationskoordinat))],
    )
    sagsevent_punkt_opret = sag.ny_sagsevent(
        beskrivelse="Oprettelse af nyt punkt",
        punkter=[punkt],
    )
    try:
        fire.cli.firedb.indset_sagsevent(sagsevent_punkt_opret, commit=False)
        fire.cli.firedb.session.flush()
    except DatabaseError as e:
        fire.cli.firedb.session.rollback()
        fire.cli.print(f"Der opstod en fejl - punkt IKKE oprettet:")
        fire.cli.print(e)
        raise SystemExit

    # Opret punktinformationer
    punktinformationer = []
    for attribut in attributter:
        try:
            if attribut in SPECIELLE_INFOTYPER:
                punktinformationer.append(SPECIELLE_INFOTYPER[attribut](punkt))
                continue
        except ValueError as fejl:
            fire.cli.print(f"FEJL: {fejl}", bg="red", bold=True)
            raise SystemExit

        pit = fire.cli.firedb.hent_punktinformationtype(attribut)
        tekst = None
        tal = None

        if re.match(r"^AFM:\d+$", attribut):
            # punktinfotypens beskrivelse skal indsættes i punktinfo
            tekst = pit.beskrivelse
        elif pit.anvendelse == PunktInformationTypeAnvendelse.TEKST:
            tekst = input(f"Indtast værdi for {attribut}: ")
        elif pit.anvendelse == PunktInformationTypeAnvendelse.TAL:
            tal = float(input(f"Indtast værdi for {attribut}: "))

        punktinformationer.append(
            PunktInformation(
                punkt=punkt,
                infotype=pit,
                tekst=tekst,
                tal=tal,
            )
        )

    # Standardbemærkning
    punktinformationer.append(
        PunktInformation(
            punkt=punkt,
            infotype=fire.cli.firedb.hent_punktinformationtype("ATTR:bemærkning"),
            tekst=f"Nyetb. {dt.now().year} {sagsbehandler}",
        )
    )

    sagsevent_punktinfo_opret = sag.ny_sagsevent(
        beskrivelse="Tilføjelse af punktinformationer",
        punktinformationer=punktinformationer,
    )

    fire.cli.print("\nOpretter punkt med følgende karakteristika:\n", bold=True)
    fire.cli.print(f"  Lokation                    {punkt.geometri.geometri}")
    fire.cli.print(f"  Oprettelsesdato             {punkt.registreringfra}")
    punktinforapport(punktinformationer, historik=False)

    try:
        fire.cli.firedb.indset_sagsevent(sagsevent_punktinfo_opret, commit=False)
        fire.cli.firedb.session.flush()
        fire.cli.firedb.luk_sag(sag)
        fire.cli.firedb.session.flush()
    except DatabaseError as e:
        fire.cli.firedb.session.rollback()
        fire.cli.print("Der opstod en fejl - punkt IKKE oprettet:")
        fire.cli.print(e)
    else:
        spørgsmål = click.style(
            f"Er du sikker på at du vil oprette punktet i {fire.cli.firedb.db}-databasen med ovenstående information?",
            bg="red",
            fg="white",
        )
        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()
            fire.cli.print("Punkt oprettet!")
        else:
            fire.cli.firedb.session.rollback()
            fire.cli.print("Afbrudt, punkt ikke oprettet!")
