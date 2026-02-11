import click


@click.group()
def info():
    """
    Information om objekter i FIRE
    """
    pass


# Udstil kommandoer
from fire.cli.info._info import (
    punkt,
    punktsamling,
    srid,
    obstype,
    infotype,
    sag,
    sagsevent,
)

# ... og visse hjælpefunktioner som bruges andre steder
from fire.cli.info._info import (
    punktinforapport,
)
