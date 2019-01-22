'''
Main entry point for the "fire" command line interface to kvikler.
'''
from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins

@with_plugins(iter_entry_points('firecli.fire_commands'))
@click.group()
def fire():
    '''
    🔥 Kommandolinje adgang til FIRE.
    '''
    pass