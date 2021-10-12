"""
Ident-værktøjer

"""

import re


# Vær mindre pedantisk mht. foranstillede nuller hvis identen er et landsnummer
LANDSNUMMERMØNSTER = re.compile("^[0-9]*-[0-9]*-[0-9]*$")
"Generaliseret mønster for landsnumre"

KØBSTADSNUMMERMØNSTER = re.compile("^[Kk][ ]*-[0-9]*-[0-9]*$")
"Generaliseret mønster for købstadsnumre"

GNSSID = re.compile("^[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]$")
"Generaliseret mønster for GNSS-ID'er"


def kan_være_landsnummer(s: str) -> bool:
    """
    Returnerer sand, hvis `s` matcher landsnummermønsteret.

    """
    return LANDSNUMMERMØNSTER.match(s.strip())


def kan_være_købstadsnummer(s: str) -> bool:
    """
    Returnerer sand, hvis `s` matcher købstadsnummermønsteret.

    Procedure minder om dén for landnumre.

    """
    return KØBSTADSNUMMERMØNSTER.match(s.strip())


def kan_være_gnssid(s: str) -> bool:
    """
    Returnerer sand, hvis `s` kan være et GNSS-ID.

    GNSS-id'er er indeholder pr. def. kun A-Z0-9

    """
    return GNSSID.match(s.strip())


def kan_være_ident(s: str):
    """
    Returnerer sand, hvis `s` kan være en ident.

    """
    return kan_være_landsnummer(s) or kan_være_købstadsnummer(s) or kan_være_gnssid(s)


def reformater_landsnummer(ident: str) -> str:
    dele = ident.split("-")
    herred = int(dele[0])
    sogn = int(dele[1])
    lbnr = int(dele[2])
    return f"{herred}-{sogn:02}-{lbnr:05}"


def reformater_købstadsnummer(ident: str) -> str:
    dele = ident.split("-")
    stad = int(dele[1])
    lbnr = int(dele[2])
    return f"K-{stad:02}-{lbnr:05}"


def reformater_gnssid(ident: str) -> str:
    return str(ident).upper()


def reformater_forstavelser(ident: str) -> str:
    """
    Nogle hjørneafskæringer for hyppigt brugte navne.

    """
    if ident.startswith("gi"):
        ident = ident.replace("gi", "G.I.", 1)
    if ident.startswith("GI"):
        ident = ident.replace("GI", "G.I.", 1)
    if ident.startswith("gm"):
        ident = ident.replace("gm", "G.M.", 1)
    if ident.startswith("GM"):
        ident = ident.replace("GM", "G.M.", 1)
    return ident
