'''
Main entry point for the "fire" command line interface to kvikler.
'''
from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins

import firecli

@with_plugins(iter_entry_points('firecli.fire_commands'))
@click.group()
@click.help_option(help='Vis denne hjælp tekst')
@click.version_option(version=firecli.__version__, prog_name='fire')
def fire():
    '''
    🔥 Kommandolinje adgang til FIRE.
    '''
    pass