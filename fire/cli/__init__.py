import click

from fire.api import FireDb

firedb = FireDb()
_show_colors = True


# Create decorator that handles all default options
def _set_monochrome(ctx, param, value):
    """
    Anvend værdien af --monokrom og sæt den globale værdi af _show_colors.
    """
    global _show_colors
    _show_colors = not value


def _set_debug(ctx, param, value):
    """
    Ændrer debug tilstand på firedb object vha --debug.
    """
    global firedb
    firedb.engine.echo = value


_default_options = [
    click.option(
        "-m",
        "--monokrom",
        is_flag=True,
        callback=_set_monochrome,
        help="Vis ikke farver i terminalen",
    ),
    click.option("--debug", is_flag=True, callback=_set_debug, help="Vis debug output"),
    click.help_option(help="Vis denne hjælp tekst"),
]


def default_options(**kwargs):
    def _add_options(func):
        for option in reversed(_default_options):
            func = option(func)
        return func

    return _add_options


def print(*args, **kwargs):
    """
    FIRE-specifik print funktion baseret på click.secho.

    Tilsidesætter farven når --monokrom parameteren anvendes i
    kommandolinjekald.
    """
    kwargs["color"] = _show_colors
    click.secho(*args, **kwargs)


def override_firedb(new_firedb):
    """
    Tillad at bruge en anden firedb end den der oprettes automatisk af
    fire.cli. Primært brugbar i forbindelse med afvikling af test-suite,
    hvor fire.cli ellers vil arbejde op mod produktionsdatabasen.
    """
    global firedb
    firedb = new_firedb
