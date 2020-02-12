from fireapi import FireDb
from fireapi.model import Koordinat, Artskode


def test_koordinat(firedb: FireDb, koordinat: Koordinat):
    firedb.session.commit()


def test_artskode(firedb: FireDb, koordinat: Koordinat):
    koordinat.artskode = Artskode.TRANSFORMERET
    firedb.session.commit()
