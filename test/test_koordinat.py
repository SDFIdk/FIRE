from fireapi import FireDb
from fireapi.model import Koordinat


def test_koordinat(firedb: FireDb, koordinat: Koordinat):
    firedb.session.commit()
