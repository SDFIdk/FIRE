import configparser
import datetime
import ast

import os

import click

from fireapi import FireDb
from fireapi.model import (
    Geometry,
)

from adapter import GamaWriter
import string

@click.group()
def cli():
    pass

@cli.command() 
@click.option("-db", "db_con" , help="Connection-streng til fire database", type=string, required=False)
@click.option("-o", "--output", type=click.File(mode='w'), help="navn på gama input, der skal skabes (.xml)", default="output.xml")
@click.option("-g", "--geometri", help="wkt. Anvendes som geometri i udvælgelsen af observationer", required=False, type=string)
@click.option("-gf", "--geometrifil", help="Fil, som indeholder en wkt-streng. Anvendes som geometri i udvælgelsen af observationer", required=False, type=click.File(mode='r'))
@click.option("-b", "--buffer", help="Den buffer omkring den givne geometri som skal bruges i udvælgelsen af observationer", required=False, type=int, default=0)
@click.option("-d", "--fratil", nargs=2, help="Fra- og tildato, som bruges i udvælgelsen af observationer", required=False, type=datetime)
@click.option("-f", "--fixpunkter", "fixpunkter", help="Komma-separeret liste af punkt-id'er, som skal fastholdes", required=False, type=string)
@click.option("-ff", "--fixpunkterfil", "fixpunkterfil", help="Fil, som indeholder komma-separeret liste af punkt-id'er, som skal fastholdes", required=False, type=click.File(mode='r'))

def write(db, output, geometri, geometrifil, buffer, fratil, fixpunkter, fixpunkterfil):
    """Create a gama input file"""
    if db is None:
        db = os.environ.get("fire_db")
    fireDb = FireDb(db)
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
            
        if fratil is not None:
            os = fireDb.hent_observationer_naer_geometri(g, buffer, fratil[0], fratil[1])
        else:
            os = fireDb.hent_observationer_naer_geometri(g, buffer)

        
        writer.take_observations(os)
    
    if fixpunkter is not None or fixpunkterfil is not None:
        if fixpunkter is not None:
            fixpunkter_literal = fixpunkter            
        else:
            fixpunkter_literal = fixpunkterfil.read()
            
        fixpunkter_list= ast.literal_eval("[" + fixpunkter_literal +"]")
        writer.set_fixed_point_ids(fixpunkter_list)
    
    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "Created by fire-gama", None)


@cli.command()
@click.option("--db", help="Connection-streng til fire database")
@click.option("-i", "input", help="navn på gama output, der skal indlæses (.xml)")
def read(input):
    """Read a gama output file (read --help)"""
    pass


if __name__ == "__main__":
    cli()
