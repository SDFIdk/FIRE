import click


@click.group()
def indlæs():
    """
    Værktøjer til indlæsning af forskelligt data
    """
    pass


from .bernese import bernese
