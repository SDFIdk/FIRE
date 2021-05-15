"""
Hovedindgang for kommondolinjeinterface til FIRE.
"""
from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins

import fire


@with_plugins(iter_entry_points("fire.cli.fire_commands"))
@click.group()
@click.help_option(help="Vis denne hjælpetekst")
@click.version_option(
    version=fire.__version__, prog_name="fire", help="Vis versionsnummer"
)
def fire():
    """
    🔥 Kommandolinjeadgang til FIRE.
    """
    pass
