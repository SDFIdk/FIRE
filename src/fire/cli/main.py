"""
Hovedindgang for kommondolinjeinterface til FIRE.
"""
import importlib.metadata

import click
from click_plugins import with_plugins

import fire

entry_points = importlib.metadata.entry_points(group="fire.cli.fire_commands")

@with_plugins(entry_points)
@click.group()
@click.help_option(help="Vis denne hjælpetekst")
@click.version_option(
    version=fire.__version__, prog_name="fire", help="Vis versionsnummer"
)
def fire_cmd():
    """
    🔥 Kommandolinjeadgang til FIRE.
    """
    pass
