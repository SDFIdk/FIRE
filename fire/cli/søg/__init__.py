import click


@click.group()
def søg():
    """
    Fremsøgning af objekter i FIRE
    """
    pass


from .punkt import punkt
