import click

from fireapi import FireDb
from adapter import GamaWriter


@click.group()
def cli():
    pass

@cli.command() 
@click.option("--db", help="Connection-streng til fire database")
@click.option("-o", "output", type=click.File(mode='w'), help="navn på gama input, der skal skabes (.xml)")
@click.option("-m", "metode", help="bla bla", type=click.Choice(['all']))
def write(db, metode, output):
    """Create a gama input file"""
    #https://docs.python.org/3.4/library/configparser.html
    fireDb = FireDb(db)
    writer = GamaWriter(fireDb, output)
    
    if metode == "all":
        writer.take_all_points()
        
    writer.write(True, False, "Created by fire-gama", None)


@cli.command()
@click.option("--db", help="Connection-streng til fire database")
@click.option("-i", "input", help="navn på gama output, der skal indlæses (.xml)")
def read(input):
    """Read a gama output file (read --help)"""
    pass


if __name__ == "__main__":
    cli()
