import os
import os.path
import getpass

import click
import pandas as pd

from fire import uuid
from fire.io.regneark import arkdef
import fire.cli

from fire.cli.niv import (
    niv,
    skriv_ark,
    bekræft,
)

from fire.api.model import (
    Sag,
    Sagsinfo,
)


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.argument(
    "beskrivelse",
    nargs=-1,
    type=str,
)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
def opret_sag(projektnavn: str, beskrivelse: str, sagsbehandler: str, **kwargs) -> None:
    """
    Registrer ny sag i databasen.

    \f
    Ved oprettelse af en ny sag skal angives et projektnavn samt en beskrivele af projektet.
    Man *kan* undlade beskrivelsen, men det vil oftest være en fordel at have den med, da
    det gør det nemmere at få et indblik i sagen hvis den på et tidspunkt skal genbesøges.
    En projektbeskrivelse kan fx være "Kommunalvedligeholdsopgave i Svendborg" eller
    "Ny GNSS station STAT oprettet i databasen".

    **Eksempel**

    .. code-block:: console

        > fire niv opret-sag SAG "Eksempel på oprettelse af en sag, inkl. beskrivelse"

    Når en sag oprettes, som i ovenstående eksempel, placeres en Excel-fil i den mappe kommandoen
    er kørt i. Det vil sige at hvis man afvikler ``fire niv opret-sag`` i mappen
    ``C:\\projekter\\svendborg_vedligehold`` vil regnearkets placering i filsystemet være
    ``C:\\projekter\\svendborg_vedligehold\\SAG.xlsx``.

    .. hint::

        Det kan være en fordel at lave en mappe for hver sag du arbejder med, så alle
        filer der er tilknyttet sagen er organiseret samme sted.

    Når :program:`fire niv opret-sag` kommandoen køres bliver du som bruger spurgt om
    du vil oprette sagen. Siger du "ja" til det bliver du bedt om at bekræfte dig valg
    med endnu et "ja". Bemærk at du her begge gange skal skrive "ja" - alt andet betragtes
    som et nej.

    Vælges "nej" første gang spørger programmet om man alligevel vil oprette et sagsregneark.
    Siges der ja til dette laves et sagsregneark, men sagen oprettes *ikke* i databasen. Formålet
    med denne funktionalitet er, at give mulighed for at lave udjævninger af eksisterende
    observationer uden at have intention om indlæse de resulterende koter i databasen.

    ====================== ===========================================================
    Faneblad               Beskrivelse
    ====================== ===========================================================
    Projektside            Her kan man løbende indtaste relevant info for projektet.
    Sagsgang               Her vil sagens hændelserne fremgå efterhånden som de
                           forekommer.
    Nyetablerede punkter   Her kan man indtaste nye punkter som oprettes i forbindelse
                           projektet.
    Notater                Egne noter om sagen.
    Filoversigt            Her kan man indtaste filnavnene på opmålingsfilerne. husk
                           at definere stien, hvis ikke filen ligger samme sted som
                           projektfilen.
    Parametre              Her er angivet relevante parametre for sagen, fx hvilken
                           database der arbejdes op imod og versionsnummer af FIRE.
    ====================== ===========================================================

    """

    if os.path.isfile(f"{projektnavn}.xlsx"):
        fire.cli.print(
            f"Filen '{projektnavn}.xlsx' eksisterer - sagen er allerede oprettet"
        )
        raise SystemExit(1)

    beskrivelse = " ".join(beskrivelse)

    sag = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "sagsoprettelse",
        "Tekst": f"{projektnavn}: {beskrivelse}",
        "uuid": uuid(),
    }
    sagsgang = pd.DataFrame([sag], columns=tuple(arkdef.SAG))

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag['uuid']})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")
    fire.cli.print(f"Beskrivelse:       {beskrivelse}")
    sagsinfo = Sagsinfo(
        aktiv="true",
        behandler=sagsbehandler,
        beskrivelse=f"{projektnavn}: {beskrivelse}",
    )
    fire.cli.firedb.indset_sag(Sag(id=sag["uuid"], sagsinfos=[sagsinfo]), commit=False)
    try:
        fire.cli.firedb.session.flush()
    except Exception as ex:
        fire.cli.firedb.session.rollback()
        fire.cli.print(
            f"Der opstod en fejl - sag {sag.id} for '{projektnavn}' IKKE oprettet"
        )
        return
    else:
        spørgsmål = click.style(
            f"Opretter ny sag i {fire.cli.firedb.db}-databasen - er du sikker? ",
            bg="red",
            fg="white",
        )
        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()
            fire.cli.print(f"Sag '{projektnavn}' oprettet")
        else:
            fire.cli.firedb.session.rollback()
            advarsel = click.style(
                f"BEMÆRK: Sag oprettes IKKE i databasen!",
                bg="yellow",
                fg="black",
            )
            fire.cli.print(advarsel)
            # Ved demonstration af systemet er det nyttigt at kunne oprette
            # et sagsregneark, uden at oprette en tilhørende sag
            if not bekræft("Vil du alligevel oprette et sagsregneark?", gentag=False):
                return

    fire.cli.print(f"Skriver sagsregneark '{projektnavn}.xlsx'")

    # Dummyopsætninger til sagsregnearkets sider
    forside = pd.DataFrame()
    nyetablerede = pd.DataFrame(columns=tuple(arkdef.NYETABLEREDE_PUNKTER)).astype(
        arkdef.NYETABLEREDE_PUNKTER
    )
    notater = pd.DataFrame([{"Dato": pd.Timestamp.now(), "Hvem": "", "Tekst": ""}])
    filoversigt = pd.DataFrame(columns=tuple(arkdef.FILOVERSIGT))
    param = pd.DataFrame(
        columns=["Navn", "Værdi"],
        data=[("Version", fire.__version__), ("Database", fire.cli.firedb.db)],
    )

    resultater = {
        "Projektforside": forside,
        "Sagsgang": sagsgang,
        "Nyetablerede punkter": nyetablerede,
        "Notater": notater,
        "Filoversigt": filoversigt,
        "Parametre": param,
    }

    if skriv_ark(projektnavn, resultater):
        fire.cli.print("Færdig!")
        fire.cli.åbn_fil(f"{projektnavn}.xlsx")
