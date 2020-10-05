"""
Diverse redskaber til brug i fire.cli.
"""
import re

import click
from datetime import datetime


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

    # Vær mindre pedantisk mht. foranstillede nuller hvis identen er et landsnummer
    landsnummermønster = re.compile("^[0-9]*-[0-9]*-[0-9]*$")
    if landsnummermønster.match(ident):
        dele = ident.split("-")
        herred = int(dele[0])
        sogn = int(dele[1])
        lbnr = int(dele[2])
        ident = f"{herred}-{sogn:02}-{lbnr:05}"

    # Næsten samme procedure for købstadsnumre
    købstadsnummermønster = re.compile("^[Kk][ ]*-[0-9]*-[0-9]*$")
    if købstadsnummermønster.match(ident):
        dele = ident.split("-")
        stad = int(dele[1])
        lbnr = int(dele[2])
        ident = f"K-{stad:02}-{lbnr:05}"

    # GNSS-id'er er indeholder pr. def. kun A-Z0-9, så her kan vi også lette lidt på stringensen
    gnssid = re.compile("^[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]$")
    if gnssid.match(ident):
        ident = str(ident).upper()

    # Og nogle hjørneafskæringer for hyppigt brugte navne
    if ident.startswith("gi"):
        ident = ident.replace("gi", "G.I.", 1)
    if ident.startswith("GI"):
        ident = ident.replace("GI", "G.I.", 1)
    if ident.startswith("gm"):
        ident = ident.replace("gm", "G.M.", 1)
    if ident.startswith("GM"):
        ident = ident.replace("GM", "G.M.", 1)

    return ident
