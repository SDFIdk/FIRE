import click


@click.group()
def udst():
    """
    Information om FIRE-objekters udstillede form
    """
    pass


from ._punkt import punkt
