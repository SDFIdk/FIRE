import getpass

import click
from sqlalchemy.exc import NoResultFound
from cx_Oracle import DatabaseError

import fire
import fire.cli
from fire.cli import rød
from fire.api.model import (
    Sag,
    Sagsinfo,
    Sagsevent,
    SagseventInfo,
    EventType,
    Koordinat,
    Observation,
)
from fire.cli.niv import bekræft


STOP = rød(
    """
        ███████ ████████  ██████  ██████      ██ ██
        ██         ██    ██    ██ ██   ██     ██ ██
        ███████    ██    ██    ██ ██████      ██ ██
             ██    ██    ██    ██ ██
        ███████    ██     ██████  ██          ██ ██
"""
)


@click.group()
def luk():
    """
    Luk objekter i FIRE
    """
    pass


punkt_hjælp = f"""
    Luk et punkt i FIRE databasen.

    Lukker et punkt, identificeret ved dets UUID, og ALLE tilhørende databaseobjekter.
    Det vil sige at punktinformationer, koordinater, observationer og så videre
    der er tilknyttet punktet {rød('VIL BLIVE LUKKET')}.

    Når først et punkt er lukket kan det ikke åbnes igen.

        {rød('BRUG DERFOR DENNE FUNKTION MED OMTANKE!')}
    """


@luk.command(help=punkt_hjælp)
@click.argument("uuid", type=str)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
@fire.cli.default_options()
def punkt(uuid: str, sagsbehandler, **kwargs) -> None:
    """
    Luk et punkt i FIRE databasen.

    Se `punkt_hjælp` for yderligere information.
    """
    db = fire.cli.firedb

    sag = db.ny_sag(
        behandler=sagsbehandler, beskrivelse="Lukning af objekt med 'fire luk'"
        )
    db.session.add(sag)
    db.session.flush()
    sagsevent = Sagsevent(
        sag=sag,
        eventtype=EventType.PUNKT_NEDLAGT,
        sagseventinfos=[
            SagseventInfo(beskrivelse=f"'fire luk punkt {uuid}"),
        ],
    )

    try:
        punkt = db.hent_punkt(uuid)
    except NoResultFound:
        fire.cli.print(f"Punkt med UUID {uuid} ikke fundet!")
        raise SystemExit

    try:
        # Indsæt alle objekter i denne session
        db.luk_punkt(punkt, sagsevent, commit=False)
        db.session.flush()
        db.luk_sag(sag, commit=False)
        db.session.flush()
    except DatabaseError as e:
        # rul tilbage hvis databasen smider en exception
        db.session.rollback()
        fire.cli.print(f"Der opstod en fejl - punkt id {uuid} IKKE lukket!")
        print(e)
    else:
        tekst = f"Er du sikker på at du vil lukke punktet {punkt.ident} ({uuid})?"
        spørgsmål = f"{STOP}\n\n" + click.style(tekst, bg="red", fg="white")
        spørgsmål += "\n\n\nLukning af punktet KAN IKKE rulles tilbage. Denne ændring er irreversibel,\n"
        spørgsmål += "tænkt dig grundigt om inden du siger ja."
        if bekræft(spørgsmål):
            db.session.commit()
            fire.cli.print(f"Punkt {punkt.ident} ({uuid} lukket!")
        else:
            db.session.rollback()
            fire.cli.print(f"Punkt {punkt.ident} ({uuid} IKKE lukket!")


@luk.command()
@click.argument("objektid", type=str)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
@fire.cli.default_options()
def koordinat(objektid: str, sagsbehandler, **kwargs) -> None:
    """
    Fejlmeld en koordinat i FIRE databasen.

    Når en koordinat fejlmeldes afregistreres den i databasen og
    det angives samtidigt at koordinaten ikke er gyldig i tidsserier.

    Koordinatens objektid skal findes ved manuelt opslag i databasen.
    Det kan fx gøres med et udtræk som følgende:

    \b
        SELECT * FROM koordinat k
        JOIN PUNKTINFO p ON p.PUNKTID = k.PUNKTID
        JOIN SRIDTYPE s ON k.SRIDID = s.SRIDID
        WHERE p.tekst = '147-06-00001' AND s.srid = 'EPSG:5799';
    """
    db = fire.cli.firedb
    sag = db.ny_sag(
        sagsbehandler, beskrivelse="Fejlmelding af koordinat med 'fire luk'"
    )
    db.session.add(sag)
    db.session.flush()
    sagsevent = Sagsevent(
        sag=sag,
        eventtype=EventType.KOORDINAT_NEDLAGT,
        sagseventinfos=[
            SagseventInfo(beskrivelse=f"'fire luk koordinat med {objektid}"),
        ],
    )

    try:
        koordinat = (
            db.session.query(Koordinat)
            .filter(
                Koordinat.objektid == objektid,
            )
            .one()
        )
    except NoResultFound:
        fire.cli.print(f"Koordinat med objektid {objektid} ikke fundet!")
        raise SystemExit

    punkt = koordinat.punkt
    srid = koordinat.srid

    try:
        # Indsæt alle objekter i denne session
        db.fejlmeld_koordinat(koordinat, sagsevent, commit=False)
        db.session.flush()
        db.luk_sag(sag, commit=False)
        db.session.flush()
    except DatabaseError as e:
        # rul tilbage hvis databasen smider en exception
        db.session.rollback()
        fire.cli.print(
            f"Der opstod en fejl - koordinat med objektid {objektid} IKKE lukket!"
        )
        print(e)
    else:
        tekst = f"""
Er du sikker på at du vil lukke {punkt.ident}'s {srid.name}-koordinat med objektid={objektid}:

  {koordinat.registreringfra=}
  {koordinat.x=} ({koordinat.sx})
  {koordinat.y=} ({koordinat.sy})
  {koordinat.z=} ({koordinat.sz})
  {koordinat.t=}

"""
        if bekræft(tekst):
            db.session.commit()
            fire.cli.print(f"Koordinat ({objektid}) lukket!")
        else:
            db.session.rollback()
            fire.cli.print(f"Koordinat ({objektid}) IKKE lukket!")


@luk.command()
@click.argument("objektid", type=str)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
@fire.cli.default_options()
def observation(objektid: str, sagsbehandler, **kwargs) -> None:
    """
    Fejlmeld en observation i FIRE databasen.

    Når en observation fejlmeldes afregistreres den i databasen og
    det angives samtidigt at observationen ikke er fejlbehæftet.

    Observationens objektid kan fx findes ved opslag med
    ``fire info punkt -O niv <punkt>`` eller ved manuelt opslag i
    databasen. Sidstnævnte kan fx gøres med et udtræk som følgende:

    \b
        SELECT * FROM observation o
        JOIN punktinfo po ON po.punktid = o.opstillingspunktid
        JOIN punktinfo ps ON ps.punktid = o.sigtepunktid
        WHERE po.tekst = '41-06-09008' AND ps.tekst = '41-06-09023';
    """
    db = fire.cli.firedb
    sag = db.ny_sag(
        sagsbehandler, beskrivelse="Fejlmelding af observation med 'fire luk'"
    )
    db.session.add(sag)
    db.session.flush()
    sagsevent = Sagsevent(
        sag=sag,
        eventtype=EventType.OBSERVATION_NEDLAGT,
        sagseventinfos=[
            SagseventInfo(beskrivelse=f"'fire luk observation {objektid}"),
        ],
    )

    try:
        obs = (
            db.session.query(Observation)
            .filter(
                Observation.objektid == objektid,
            )
            .one()
        )
    except NoResultFound:
        fire.cli.print(f"Observation med objektid {objektid} ikke fundet!")
        raise SystemExit

    try:
        # Indsæt alle objekter i denne session
        db.fejlmeld_observation(obs, sagsevent, commit=False)
        db.session.flush()
        db.luk_sag(sag, commit=False)
        db.session.flush()
    except DatabaseError as e:
        # rul tilbage hvis databasen smider en exception
        db.session.rollback()
        fire.cli.print(
            f"Der opstod en fejl - observation med objektid {objektid} IKKE lukket!"
        )
        print(e)
    else:
        tekst = f"""Er du sikker på at du vil lukke observationen med {objektid}:

        {repr(obs)}
"""
        if bekræft(tekst):
            db.session.commit()
            fire.cli.print(f"Observation {objektid} lukket!")
        else:
            db.session.rollback()
            fire.cli.print(f"Observation {objektid} IKKE lukket!")
