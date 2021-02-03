import re
import sys

import click
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire.cli.utils import klargør_ident_til_søgning
from . import søg


@søg.command()
@fire.cli.default_options()
@click.argument("ident")
@click.option(
    "-n",
    "--antal",
    default=20,
    type=int,
    help="Begræns antallet af fundne søgeresultater",
)
def punkt(ident: str, antal: int, **kwargs):
    """
    Søg efter et punkt ud fra dets ident

    Søgeudtryk kan præciseres med wildcards givet ved %. Hvis ingen
    wildcards angives søges automatisk efter "%IDENT%". Der skælnes
    ikke mellem små og store bogstaver.

    Antallet af søgeresultater begrænses som standard til 20.
    """
    ident = klargør_ident_til_søgning(ident)
    if "%" not in ident:
        ident = f"%{ident}%"

    ident_pattern = ident.replace("%", ".*")

    try:
        punkter = fire.cli.firedb.soeg_punkter(ident, antal)
    except NoResultFound:
        fire.cli.print(
            f"Fejl: Kunne ikke finde {ident.replace('%', '')}.", fg="red", err=True
        )
        sys.exit(1)

    for punkt in punkter:
        for ident in punkt.identer:
            if re.match(ident_pattern, ident):
                fire.cli.print(f"{ident:20}", bold=True, fg="green", nl=False)
            else:
                fire.cli.print(f"{ident:20}", nl=False)
        fire.cli.print(nl=True)
