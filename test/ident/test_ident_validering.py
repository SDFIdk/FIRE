import itertools as it

from fire.ident import (
    kan_være_landsnummer,
    kan_være_købstadsnummer,
    kan_være_gnssid,
    kan_være_ident,
    kan_være_gi_nummer,
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


def test_kan_være_gi_nummer():

    eksisterende_gi_numre = [
        ["G.M.144", "G.M.144.1", "G.M.143/144", "G.M.1456.1"],
        ["G.M.1499/1500", "G.M.15", "G.M.2", "G.M.35/36.1"],
        ["G.I.1601", "G.I.1602.1", "G.I.1856", "G.I.2403"],
    ]

    for gi_nummer in it.chain(*eksisterende_gi_numre):
        assert kan_være_gi_nummer(
            gi_nummer
        ), f"Forventede, at `{gi_nummer}` kan være et GI-nummer."

        assert kan_være_gi_nummer(
            gi_nummer.replace(".", "")
        ), f"Forventede, at `{gi_nummer.replace('.', '')}` kan være et GI-nummer."

        assert kan_være_gi_nummer(
            gi_nummer.lower()
        ), f"Forventede, at `{gi_nummer.lower()}` kan være et GI-nummer."


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
        # G.M./G.I.
        "G.M.15",
        "G.M.1499/1500",
        "G.I.1602.1",
        "G.I.2403",
    )
    for ident in eksisterende_identer:
        assert kan_være_ident(ident), f"Forventede, at `{ident}` kan være et ident."
