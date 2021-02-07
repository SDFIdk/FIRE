import os
import os.path

import click
import pandas as pd
import sys

from fire import uuid
import fire.cli

from . import (
    ARKDEF_PARAM,
    find_faneblad,
    find_sag,
    niv,
)


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
def luk_sag(projektnavn: str, **kwargs) -> None:
    """Luk sag i databasen"""

    if not os.path.isfile(f"{projektnavn}.xlsx"):
        fire.cli.print(
            f"Filen '{projektnavn}.xlsx' eksisterer ikke - kan ikke lukke sag!"
        )
        sys.exit(1)

    param = find_faneblad(projektnavn, "Parametre", ARKDEF_PARAM)
    projekt_db = param.loc[param["Navn"] == "Database"]["Værdi"].to_string(index=False)

    if projekt_db != fire.cli.firedb.db:
        fire.cli.print(
            f"{projektnavn} er kan ikke indsættes i {fire.cli.firedb.db}-databansen, da det er oprettet i {projekt_db}-databasen!"
        )
        sys.exit(1)

    sag = find_sag(projektnavn)

    fire.cli.firedb.luk_sag(sag, commit=False)
    try:
        # Indsæt alle objekter i denne session
        fire.cli.firedb.session.flush()
    except:
        # rul tilbage hvis databasen smider en exception
        fire.cli.firedb.session.rollback()
    else:
        if (
            input(f"Er du sikker på at du vil lukke sagen {projektnavn}? ja/[nej]")
            == "ja"
        ):
            fire.cli.firedb.session.commit()
        else:
            fire.cli.firedb.session.rollback()
