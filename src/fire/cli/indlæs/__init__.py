import click


@click.group()
def indlæs():
    """
    Værktøjer til indlæsning af forskelligt data
    """
    pass


from fire.cli.indlæs.bernese import bernese
