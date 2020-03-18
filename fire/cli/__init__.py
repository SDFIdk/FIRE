import os
import json
import getpass
from pathlib import Path

import click

from fire.api import FireDb

# Used for controlling the database setup when running the test suite
RC_NAME = "fire_settings.json"

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


# Find settings file and read database credentials
if os.environ.get("HOME"):
    home = Path(os.environ["HOME"])
else:
    home = Path("")

search_files = [
    home / Path(RC_NAME),
    home / Path("." + RC_NAME),
    Path("/etc") / Path(RC_NAME),
    Path("C:\\Users") / Path(getpass.getuser()) / Path(RC_NAME),
    Path("C:\\Users\\Default\\AppData\\Local\\fire") / Path(RC_NAME),
]

for conf_file in search_files:
    if os.path.isfile(conf_file):
        with open(conf_file) as conf:
            settings = json.load(conf)
            if "connection" in settings:
                conf_db = settings["connection"]
                if not (
                    "username" in conf_db
                    and "password" in conf_db
                    and "hostname" in conf_db
                    and "database" in conf_db
                    and "service" in conf_db
                ):
                    raise ValueError(
                        "Fejl i konfigurationsfil. Konsulter dokumentationen!"
                    )
        break
else:
    raise EnvironmentError("Konfigurationsfil ikke fundet!")

# Establish connection to database
_username = conf_db["username"]
_password = conf_db["password"]
_hostname = conf_db["hostname"]
_database = conf_db["database"]
_service = conf_db["service"]
if "port" in conf_db:
    _port = conf_db["port"]
else:
    _port = 1521

firedb = FireDb(f"{_username}:{_password}@{_hostname}:{_port}/{_database}")
