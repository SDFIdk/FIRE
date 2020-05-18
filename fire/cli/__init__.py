import click

from fire.api import FireDb

_show_colors = True


# Create decorator that handles all default options
def _set_monochrome(ctx, param, value):
    """
    Grab value of --monokrom option and set global state of _show_colors
    """
    global _show_colors
    _show_colors = not value


_default_options = [
    click.option(
        "-m",
        "--monokrom",
        is_flag=True,
        callback=_set_monochrome,
        help="Vis ikke farver i terminalen",
    ),
    click.help_option(help="Vis denne hjælp tekst"),
]


def default_options():
    def _add_options(func):
        for option in reversed(_default_options):
            func = option(func)
        return func

    return _add_options


def print(*args, **kwargs):
    """
    Custom print function based on click.secho.

    Overrides color when 'monokrom' parameter is set applied in command
    line calls.
    """
    kwargs["color"] = _show_colors
    click.secho(*args, **kwargs)


firedb = FireDb()
