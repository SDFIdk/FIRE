import configparser

import os

import click
from click_datetime import Datetime

from fireapi import FireDb
from fireapi.model import (
    Geometry,
)

from adapter import GamaWriter

@click.group()
def cli():
    pass

@cli.command() 
@click.option("-db", "db_con" , help="Connection-streng til fire database. [default: environment variabel %fire-db%]", type=str, required=False)
@click.option("-o", "--out", "output", type=click.File(mode='w'), help="Navn på gama input, der skal skabes (.xml)", default="output.xml", show_default=True)
@click.option("-g", "--geometri", help="wkt. Anvendes som geometri i udvælgelsen af observationer", required=False, type=str)
@click.option("-gf", "--geometrifil", help="Fil, som indeholder en wkt-streng. Anvendes som geometri i udvælgelsen af observationer", required=False, type=click.File(mode='r'))
@click.option("-b", "--buffer", help="Den buffer omkring den givne geometri som skal bruges i udvælgelsen af observationer", required=False, type=int, default=0, show_default=True)
@click.option("-df", "--fra", help="Fra-dato, som bruges i udvælgelsen af observationer", required=False, type=Datetime(format='%d-%m-%Y'))
@click.option("-dt", "--til", help="Til-dato, som bruges i udvælgelsen af observationer", required=False, type=Datetime(format='%d-%m-%Y'))
@click.option("-f", "--fixpunkter", "fixpunkter", help="Komma-separeret liste af punkt-id'er, som skal fastholdes", required=False, type=str)
@click.option("-ff", "--fixpunkterfil", "fixpunkterfil", help="Fil, som indeholder komma-separeret liste af punkt-id'er, som skal fastholdes", required=False, type=click.File(mode='r'))
@click.option("-pf", "--parameterfil", help="Fil, som indeholder netværks-parametre og -attributter", required=False, default="fire-gama.ini", show_default=True, type=click.File(mode='r'))

def write(db_con, output, geometri, geometrifil, buffer, fra, til, fixpunkter, fixpunkterfil, parameterfil):
    """Create a gama input file"""
    if db_con is None:
        db_con = os.environ.get("fire-db")
    fireDb = FireDb(db_con)
    writer = GamaWriter(fireDb, output)
    
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
            observations = fireDb.hent_observationer_naer_geometri(g, buffer, fra, til)
        else:
            observations = fireDb.hent_observationer_naer_geometri(g, buffer)
        writer.take_observations(observations)
    
    if fixpunkter is not None or fixpunkterfil is not None:
        if fixpunkter is not None:
            fixpunkter_literal = fixpunkter            
        else:
            fixpunkter_literal = fixpunkterfil.read()
            
        fixpunkter_list = fixpunkter_literal.split(",")
        #fixpunkter_list= ast.literal_eval("[" + fixpunkter_literal +"]")
        writer.set_fixed_point_ids(fixpunkter_list)
    
    parameters = configparser.ConfigParser()
    parameters.read(parameterfil)
    writer.write(True, False, "Created by fire-gama", parameters)


@cli.command()
@click.option("--db", help="Connection-streng til fire database")
@click.option("-i", "input", help="navn på gama output, der skal indlæses (.xml)")
def read(input):
    """Read a gama output file (read --help)"""
    pass


if __name__ == "__main__":
    cli()
