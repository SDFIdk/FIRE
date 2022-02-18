from pathlib import Path
import time
import tempfile
import webbrowser
import getpass

import click
from sqlalchemy.exc import NoResultFound

import fire
import fire.cli
from fire.api.model import (
    Boolean,
    Grafik,
    GrafikType,
    Sag,
    Sagsinfo,
    Sagsevent,
    SagseventInfo,
    EventType,
)
from fire.enumtools import enum_values
from fire.cli.niv import bekræft


@click.group()
def grafik():
    """
    Håndtering af skitser og fotos af fikspunkter.
    """
    pass


@grafik.command()
@click.argument("filnavn")
@fire.cli.default_options()
def vis(filnavn: str, **kwargs) -> None:
    """
    Vis en grafik fra databasen.

    EKSEMPEL

    > fire grafik vis K-1-12345.png

    Filnavnet til en grafik kan fx findes med `fire info punkt`.

    """
    db = fire.cli.firedb

    try:
        grafik = db.hent_grafik(filnavn)
    except NoResultFound:
        raise SystemExit(f"Fandt ikke {filnavn}!")

    ext = grafik.filnavn[-4:]
    with tempfile.NamedTemporaryFile("wb", suffix=ext) as tmp:
        tmp.write(grafik.grafik)
        webbrowser.open_new_tab(f"file://{tmp.name}")
        # giv browseren tid til at starte inden filen fjernes igen
        time.sleep(5)


@grafik.command()
@click.argument(
    "ident",
)
@click.argument(
    "sti",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
@click.option(
    "--type",
    type=click.Choice(enum_values(GrafikType), case_sensitive=False),
    required=False,
    default=GrafikType.SKITSE.value,
    help="Angiv grafikkens type. Ved udeladelse sættes PNG-filer som skitse og JPG som foto.",
)
@click.option(
    "--filnavn",
    required=False,
    default=None,
    help="Filnavn der registreres i databasen. Sættes denne ikke bruges filens aktuelle navn.",
)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
@fire.cli.default_options()
def indsæt(
    ident: str, sti: Path, type: str, filnavn: str, sagsbehandler, **kwargs
) -> None:
    r"""
    Indsæt grafik i databasen.

    EKSEMPLER

    Indsæt skitse fra PNG-fil:

        > fire grafik indsæt K-01-01234 K-01-01234.png

    Anvend andet filnavn i databasen:

        > fire grafik indsæt G.M.902 IMG_5234.jpg --filnavn aarhus_domkirke.jpg

    Eksplicer grafiktype og filnavn:

        > fire grafik indsæt K-01-012345 C:\tmp\skitse.png --type skitse --filnavn K-01-012345.png

    """
    db = fire.cli.firedb
    try:
        g = db.hent_grafik(filnavn)
    except NoResultFound:
        g = None

    if g:
        if ident not in g.punkt.identer:
            raise SystemExit(
                f"Kan ikke indsætte {filnavn} på {ident},"
                " allerede regisreret på {g.punkt.ident}"
            )

    punkt = db.hent_punkt(ident)
    if not filnavn:
        filnavn = sti.name

    for grafik in punkt.grafikker:
        if grafik.filnavn == filnavn:
            spørgsmål = f"Grafik med filnavn {filnavn} allerede tilknyttet {punkt.ident} - vil du overskrive det?"
            if bekræft(spørgsmål, gentag=False):
                break
            else:
                raise SystemExit

    # sagshåndtering
    sag = db.ny_sag(
        behandler=sagsbehandler,
        beskrivelse="Indsættelse af ny grafik med 'fire grafik'",
    )
    db.indset_sag(sag, commit=False)
    try:
        fire.cli.firedb.session.flush()
    except Exception as ex:
        fire.cli.firedb.session.rollback()
        raise SystemExit(ex)

    # opret grafik
    grafik = Grafik.fra_fil(punkt, sti)
    grafik.type = type
    grafik.filnavn = filnavn

    sagsevent = sag.ny_sagsevent(
        f"Grafik {filnavn} indsættes på punkt {punkt.ident}",
        grafikker=[grafik],
    )
    db.indset_sagsevent(sagsevent, commit=False)
    db.luk_sag(sag, commit=False)
    try:
        # Indsæt alle objekter i denne session
        fire.cli.firedb.session.flush()
    except Exception as e:
        # rul tilbage hvis databasen smider en exception
        fire.cli.firedb.session.rollback()
        fire.cli.print(f"Der opstod en fejl - fil {filnavn} IKKE indsat!")
    else:
        spørgsmål = click.style(
            f"Er du sikker på at du vil tilknytte grafikken {filnavn} til {punkt.ident}?",
            bg="red",
            fg="white",
        )
        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()
            fire.cli.print(f"fil {filnavn} tilknyttet {punkt.ident}!")
        else:
            fire.cli.firedb.session.rollback()
            fire.cli.print(f"fil {filnavn} IKKE tilknyttet {punkt.ident}!")


@grafik.command()
@click.argument("filnavn")
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
@fire.cli.default_options()
def slet(filnavn: str, sagsbehandler: str, **kwargs) -> None:
    """
    Slet en grafik fra databasen.

    Grafikken identificeres ud fra sit filnavn. Filnavnet på en grafik kan findes ved
    opslag med ``fire info punkt <ident>``.
    """
    db = fire.cli.firedb

    try:
        grafik = db.hent_grafik(filnavn)
    except NoResultFound:
        raise SystemExit(f"Fandt ikke {filnavn}!")

    punkt = grafik.punkt

    # sagshåndtering
    sag = db.ny_sag(
        behandler=sagsbehandler,
        beskrivelse="Afregistrering af grafik med `fire grafik slet`",
    )
    db.indset_sag(sag, commit=False)
    try:
        fire.cli.firedb.session.flush()
    except Exception as ex:
        fire.cli.firedb.session.rollback()
        raise SystemExit(ex)

    sagsevent = sag.ny_sagsevent(
        beskrivelse=f"Grafik {filnavn} for {punkt.ident} afregistreret",
        grafikker_slettede=[grafik],
    )
    db.indset_sagsevent(sagsevent, commit=False)
    db.luk_sag(sag, commit=False)
    try:
        # Indsæt alle objekter i denne session
        fire.cli.firedb.session.flush()
    except Exception as e:
        # rul tilbage hvis databasen smider en exception
        fire.cli.firedb.session.rollback()
        fire.cli.print(f"Der opstod en fejl - fil {filnavn} IKKE slettet!")
    else:
        spørgsmål = click.style(
            f"Er du sikker på at du vil slettet grafikken {filnavn} tilhørende {punkt.ident}?",
            bg="red",
            fg="white",
        )
        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()
            fire.cli.print(f"fil {filnavn} slettet fra {punkt.ident}!")
        else:
            fire.cli.firedb.session.rollback()
            fire.cli.print(f"fil {filnavn} IKKE slettet fra {punkt.ident}!")
