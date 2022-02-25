import getpass

import click
from sqlalchemy.exc import NoResultFound
from cx_Oracle import DatabaseError

import fire
import fire.cli
from fire.cli import rød
from fire.api.model import Sag, Sagsinfo, Sagsevent, SagseventInfo, EventType
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
    sag = Sag(
        id=fire.uuid(),
        sagsinfos=[
            Sagsinfo(
                behandler=sagsbehandler,
                beskrivelse="Lukning af objekt med 'fire luk'",
                aktiv="true",
            )
        ],
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
