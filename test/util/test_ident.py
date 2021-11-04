import itertools as it

from fire.ident import (
    kan_være_landsnummer,
    kan_være_købstadsnummer,
    kan_være_gnssid,
    kan_være_ident,
)


def test_kan_være_landsnummer():
    eksisterende_landsnumre = ("1-00-06266",)
    for landsnummer in eksisterende_landsnumre:
        assert kan_være_landsnummer(
            landsnummer
        ), f"Forventede, at `{landsnummer}` kan være et landsnummer."


def test_kan_være_købstadsnummer():
    eksisterende_købstadsnumre = (
        "K -01-06663",
        "K -01-06742",
        "K -01-09003",
    )
    for købstadsnummer in eksisterende_købstadsnumre:
        assert kan_være_købstadsnummer(
            købstadsnummer
        ), f"Forventede, at `{købstadsnummer}` kan være et købstadsnummer."


def test_kan_være_gnssid():

    eksisterende_gnssider = [
        ["AAAL", "AARH", "AGGR", "ALSL", "ARNM"],
        ["AVER", "BANH", "BEJS", "BISL", "BLAR"],
        ["BOVB", "BROR", "BUD1", "CAMP", "DAMB"],
        ["DREJ", "DZMA", "EID1", "ESB1", "ESH4"],
        ["FAKK", "FEGG", "FEST", "FJLL", "FRED"],
        ["FSOE", "GABE", "GED6", "GLAM", "GOED"],
        ["GRST", "HAB3", "HAND", "HBYK", "HERL"],
        ["HIL1", "HJAR", "HLBY", "HODS", "HORH"],
        ["HOVG", "HSTD", "HVKE", "JELS", "JUNG"],
        ["KARL", "KGFL", "KLIN", "KOKI", "KORS"],
        ["KTS3", "LAEO", "LEMV", "LINT", "LOSN"],
        ["LYNE", "MALH", "MGL7", "MOSB", "MYGD"],
        ["NEEJ", "NOR1", "NYBO", "NYOR", "OEHU"],
        ["OLHM", "PBA1", "RAGR", "RAVN", "RIBE"],
        ["RKIB", "ROEN", "RORV", "RVNK", "SANB"],
        ["SIL1", "SKA1", "SKIB", "SKR2", "SLGL"],
        ["SNES", "SORV", "STAG", "STEG", "STOU"],
        ["SUL2", "SVND", "TEGL", "THB3", "TIRS"],
        ["TORE", "TRU1", "TYVH", "VAAB", "VBRG"],
        ["VENO", "VIRK", "VJLN", "VORD", "VVIG"],
    ]

    for gnssid in it.chain(*eksisterende_gnssider):
        assert kan_være_gnssid(
            gnssid
        ), f"Forventede, at `{gnssid}` kan være et GNSS-ID."


def test_kan_være_ident():
    eksisterende_identer = (
        # Landsnumre
        "1-00-06266",
        # Købstadsnumre
        "K -01-06663",
        "K -01-06742",
        "K -01-09003",
        # GNSS
        "SKA1",
        "SKAE",
        "SKAG",
        "SKAL",
        "SKAM",
        "SKAN",
        "SKAR",
        "SKAV",
        "SKGN",
        "SKI2",
    )
    for ident in eksisterende_identer:
        assert kan_være_ident(ident), f"Forventede, at `{ident}` kan være et ident."
