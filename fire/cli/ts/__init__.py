import click


@click.group()
def ts():
    """
    Håndtering af koordinattidsserier.
    """
    pass


from .gnss import gnss
