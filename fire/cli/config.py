"""
fire config - vis den lokale FIRE opsætning
"""

import click

import fire
import fire.cli


@click.command()
def config():
    """
    Udskriv den aktuelle opsætning af FIRE.

    Viser indholdet af konfigurationsfilen fire.ini, samt diverse opsætnignsparametre
    med standardværdier som ikke er sat eksplicit i konfigurationsfilen.
    """
    firedb = fire.cli.firedb

    sections = firedb.config.sections()

    for section in sections:
        fire.cli.print(f"[{section}]", fg="green")
        for option in firedb.config.options(section):
            value = firedb.config.get(section, option)
            if option == "password":
                value = "*" * 15
            fire.cli.print(f"    {option} = {value}")
        fire.cli.print()
