import click

import fire.cli
from fire.cli.click_types import Datetime
from fire.api.model import Geometry
from fire.api.gama import GamaReader, GamaWriter


@click.group()
def gama():
    pass


@gama.command()
@click.option(
    "-o",
    "--out",
    "output",
    type=click.File(mode="w"),
    help="Navn på gama input, der skal skabes (.xml)",
    default="output.xml",
    show_default=True,
)
@click.option(
    "-g",
    "--geometri",
    help="wkt. Anvendes som geometri i udvælgelsen af observationer",
    required=False,
    type=str,
)
@click.option(
    "-gf",
    "--geometrifil",
    help="Fil, som indeholder en wkt-streng. Anvendes som geometri i udvælgelsen af observationer",
    required=False,
    type=click.File(mode="r"),
)
@click.option(
    "-b",
    "--buffer",
    help="Den buffer omkring den givne geometri som skal bruges i udvælgelsen af observationer",
    required=False,
    type=int,
    default=0,
    show_default=True,
)
@click.option(
    "-df",
    "--fra",
    help="Fra-dato, som bruges i udvælgelsen af observationer",
    required=False,
    type=Datetime(format="%d-%m-%Y"),
)
@click.option(
    "-dt",
    "--til",
    help="""Til-dato, som bruges i udvælgelsen af observationer.

    Datoen har tidspunktet 00:00:00, så hvis observationer til og med denne dato, skal dagen efter angives.""",
    required=False,
    type=Datetime(format="%d-%m-%Y"),
)
@click.option(
    "-f",
    "--fixpunkter",
    "fixpunkter",
    help="Komma-separeret liste af punkt-id'er, som skal fastholdes",
    required=False,
    type=str,
)
@click.option(
    "-ff",
    "--fixpunkterfil",
    "fixpunkterfil",
    help="Fil, som indeholder komma-separeret liste af punkt-id'er, som skal fastholdes",
    required=False,
    type=click.File(mode="r"),
)
def write(
    output,
    geometri,
    geometrifil,
    buffer,
    fra,
    til,
    fixpunkter,
    fixpunkterfil,
):
    """Skriv en gama input fil"""
    writer = GamaWriter(fire.cli.firedb, output)

    g = None

    if geometrifil is None and geometri is None:
        writer.take_all_points()
    else:
        if geometri is not None:
            g = Geometry(geometri)
        else:
            wkt = geometrifil.read()
            g = Geometry(wkt)

        if fra is not None and til is not None:
            observations = fire.cli.firedb.hent_observationer_naer_geometri(
                g, buffer, fra, til
            )
        else:
            observations = fire.cli.firedb.hent_observationer_naer_geometri(g, buffer)
        writer.take_observations(observations)

    if fixpunkter is not None or fixpunkterfil is not None:
        if fixpunkter is not None:
            fixpunkter_literal = fixpunkter
        else:
            fixpunkter_literal = fixpunkterfil.read()

        fixpunkter_list = [pkt.strip() for pkt in fixpunkter_literal.split(",")]
        writer.set_fixed_point_ids(fixpunkter_list)

    writer.write(True, False, "Created by fire-gama", fire.cli.firedb.config)


@gama.command()
@click.option(
    "-i", "--in", "input", help="navn på gama output, der skal indlæses (.xml)"
)
@click.option(
    "-c",
    "--cid",
    "case_id",
    help="Sagsnummer som beregningen gemmes under i databasen",
    type=str,
)
def read(input, case_id):
    """Læs en gama resultatfil (se --help)"""
    reader = GamaReader(fire.cli.firedb, input)
    reader.read(case_id)


if __name__ == "__main__":
    gama()
