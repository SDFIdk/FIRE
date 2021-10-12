"""
Diverse redskaber til brug i fire.cli.
"""

import click
from datetime import datetime

from fire.util.ident import (
    kan_være_landsnummer,
    kan_være_købstadsnummer,
    kan_være_gnssid,
    reformater_landsnummer,
    reformater_købstadsnummer,
    reformater_gnssid,
    reformater_forstavelser,
)


class Datetime(click.ParamType):
    """
    A datetime object parsed via datetime.strptime.
    Format specifiers can be found here :
    https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior

    Stolen from
    https://github.com/click-contrib/click-datetime/blob/master/click_datetime/__init__.py
    """

    name = "date"

    def __init__(self, format):
        self.format = format

    def convert(self, value, param, ctx):
        if value is None:
            return value

        if isinstance(value, datetime):
            return value

        try:
            datetime_value = datetime.strptime(value, self.format)
            return datetime_value
        except ValueError as ex:
            self.fail(
                'Could not parse datetime string "{datetime_str}" formatted as {format} ({ex})'.format(
                    datetime_str=value, format=self.format, ex=ex
                ),
                param,
                ctx,
            )


def klargør_ident_til_søgning(ident: str) -> str:
    """
    Oversættelse af almindelige "fejl"-stavelser af identer, fx gi istedet for G.I.,
    forud for søgning efter punkter.
    """
    ident = ident.strip()

    if kan_være_landsnummer(ident):
        ident = reformater_landsnummer(ident)

    if kan_være_købstadsnummer(ident):
        ident = reformater_købstadsnummer(ident)

    if kan_være_gnssid(ident):
        ident = reformater_gnssid(ident)

    ident = reformater_forstavelser(ident)

    return ident
