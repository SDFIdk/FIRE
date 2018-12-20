from fireapi import FireDb

from fireapi.model.punkttyper import PunktInformationType


def test_has_session(firedb: FireDb):
    assert hasattr(firedb, "session")
