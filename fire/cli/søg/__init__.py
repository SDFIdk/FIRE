import click


@click.group()
def søg():
    pass


from .punkt import punkt
