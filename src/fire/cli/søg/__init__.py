import click


@click.group()
def søg():
    """
    Fremsøgning af objekter i FIRE
    """
    pass


from fire.cli.søg.punkt import punkt
